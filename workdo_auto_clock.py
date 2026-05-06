#!/usr/bin/env python3
"""
Workdo 自動打卡系統
參考: https://github.com/akitosun/WorkDoAuto
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime, timedelta
from functools import lru_cache
from dotenv import load_dotenv
import logging

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('workdo_clock.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 與 WorkdoAPI.TAIWAN_CALENDAR_URL 相同來源，供 is_holiday 快取讀取
TAIWAN_CALENDAR_DATA_URL = "https://cdn.jsdelivr.net/gh/ruyut/TaiwanCalendar/data/{year}.json"


def normalize_workdo_date(date_val):
    """將 API 可能回傳的日期統一成 YYYY-MM-DD。"""
    if date_val is None:
        return None
    s = str(date_val).strip()
    if not s:
        return None
    s = s.replace("/", "-")
    parts = s.split("-")
    if len(parts) != 3:
        return s
    y, m, d = parts[0], parts[1], parts[2]
    if not (y.isdigit() and m.isdigit() and d.isdigit()):
        return s
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"


@lru_cache(maxsize=8)
def fetch_taiwan_public_holiday_dates(year: int) -> frozenset:
    """自台灣公開行事曆取得該年所有放假日（YYYY-MM-DD）。"""
    url = TAIWAN_CALENDAR_DATA_URL.format(year=year)
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    data = response.json()
    out = set()
    for day in data:
        if not day.get("isHoliday") or not day.get("description"):
            continue
        date_str = day.get("date")
        if not date_str or len(str(date_str)) < 8:
            continue
        ds = str(date_str)
        formatted = f"{ds[:4]}-{ds[4:6]}-{ds[6:8]}"
        out.add(formatted)
    return frozenset(out)


class WorkdoAPI:
    """Workdo API 自動打卡類別"""
    
    # API 端點
    BASE_URL = "https://www.workdo.co"
    LOGIN_URL = f"{BASE_URL}/bdddweb/api/dweb/BDD771M/userLogin"
    PUNCH_URL = f"{BASE_URL}/ccndweb/api/dweb/CCN102M/saveFromCreate102M3"
    STATUS_URL = f"{BASE_URL}/ccndweb/api/dweb/CCN102M/execute102M2FromMenu"
    HOLIDAY_URL = f"{BASE_URL}/bddaweb/api/aweb/BDD901W/queryFromQuery901W2"
    MISSING_PUNCH_QUERY_URL = f"{BASE_URL}/ccnraweb/api/aweb/CCN002W/queryFromQuery002W1"
    MISSING_PUNCH_SAVE_URL = f"{BASE_URL}/ccndweb/api/dweb/CCN102M/saveFromCreate102M4"
    
    # 台湾政府公开假日数据源（备用）
    TAIWAN_CALENDAR_URL = "https://cdn.jsdelivr.net/gh/ruyut/TaiwanCalendar/data/{year}.json"
    
    def __init__(self):
        self.email = os.getenv('WORKDO_EMAIL')
        self.password = os.getenv('WORKDO_PASSWORD')
        self.gps_location = os.getenv('WORKDO_GPS_LOCATION', '25.033,121.564')
        self.gps_place = os.getenv('WORKDO_GPS_PLACE', '台北市信義區')
        self.use_leave_api = os.getenv('WORKDO_USE_LEAVE_API', 'false').lower() == 'true'
        # 與 leave_days.json、Workdo 假日 API 並用：預設啟用台灣公開行事曆略過國定假日（未設定或空字串皆為啟用）
        _tw = (os.getenv('WORKDO_USE_TW_CALENDAR') or 'true').strip().lower()
        self.use_tw_calendar = _tw in ('true', '1', 'yes')
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json;charset=UTF-8',
            'tenant_id': 'aa6pd97f',
            'timezone': 'GMT+0800',
            'brandName': 'WorkDo',
            'app_version_code': 'wd_aweb_7.6.20',
            'userLocale': 'zh_TW',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'sec-ch-ua': '"Google Chrome";v="100", "Not?A_Brand";v="8", "Chromium";v="100"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        })
    
    def login(self):
        """登入 Workdo 取得 Cookie"""
        try:
            login_data = {
                'clientType': 'Web',
                'clientModel': 'Chrome 100.0.4896.127',
                'clientOs': 'Windows 10',
                'appVersion': 'wd_aweb_7.6.20',
                'timeZone': 'GMT+0800',
                'loginEmail': self.email,
                'password': self.password,
                'loginId': self.email,
                'loginPhone': None
            }
            
            logger.info("🔐 正在登入...")
            response = self.session.post(self.LOGIN_URL, json=login_data)
            response.raise_for_status()
            
            data = response.json()
            if 'bddUserData' in data:
                logger.info(f"✅ 登入成功 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                return True
            else:
                logger.error("❌ 登入失敗: 無法取得使用者資料")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 登入失敗: {str(e)}")
            if hasattr(e.response, 'text'):
                logger.error(f"回應內容: {e.response.text}")
            return False
    
    def punch(self, punch_type):
        """
        執行打卡
        Args:
            punch_type: 'ClockIn' 或 'ClockOut'
        """
        try:
            # 解析 GPS 座標
            lat, lon = self.gps_location.split(',')
            # 嘗試 WKT POINT 格式（經度 緯度）
            gps_point = f"POINT({lon.strip()} {lat.strip()})"
            
            punch_data = {
                'type': punch_type,
                'place': 'OtherCity',
                'gpsLocation': {'text': gps_point},
                'gpsPlace': self.gps_place
            }
            
            punch_name = "上班" if punch_type == "ClockIn" else "下班"
            logger.info(f"⏰ 執行{punch_name}打卡...")
            
            response = self.session.post(self.PUNCH_URL, json=punch_data)
            response.raise_for_status()
            
            data = response.json()
            if 'punchTime' in data:
                punch_time = data['punchTime'].replace('+0800', '')
                logger.info(f"✅ {punch_name}打卡成功 - {punch_time}")
                return True
            else:
                logger.warning(f"⚠️ {punch_name}打卡可能失敗，請檢查回應")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ {punch_name}打卡失敗: {str(e)}")
            if hasattr(e.response, 'text'):
                logger.error(f"回應內容: {e.response.text}")
            return False
    
    def clock_in(self):
        """上班打卡"""
        return self.punch('ClockIn')
    
    def clock_out(self):
        """下班打卡"""
        return self.punch('ClockOut')
    
    def get_punch_status(self):
        """查詢今日打卡狀態"""
        try:
            logger.info("📊 查詢打卡狀態...")
            
            # 空的 POST body
            response = self.session.post(self.STATUS_URL, json={})
            response.raise_for_status()
            
            data = response.json()
            if 'list' in data and len(data['list']) > 0:
                logger.info("📋 今日打卡記錄:")
                for i, record in enumerate(data['list'][:2]):  # 顯示前兩筆（上下班）
                    record_type = "上班" if record.get('type') == 'ClockIn' else "下班"
                    punch_time = record.get('punchTime', '未打卡')
                    if punch_time and punch_time != '未打卡':
                        punch_time = punch_time.replace('+0800', '')
                    logger.info(f"   {record_type}: {punch_time}")
                return data
            else:
                logger.info("📋 今日尚無打卡記錄")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 查詢狀態失敗: {str(e)}")
            return None

    def has_punched_type_today(self, punch_type: str) -> bool:
        """檢查今天是否已經打過指定類型（ClockIn/ClockOut）。"""
        status = self.get_punch_status()
        if not status or "list" not in status:
            return False
        for record in status.get("list", []):
            if record.get("type") == punch_type and record.get("punchTime"):
                return True
        return False
    
    def query_holidays(self):
        """查詢假日列表（如果有使用請假 API）"""
        if not self.use_leave_api:
            return []
        
        try:
            logger.info("🗓️ 查詢假日列表...")
            
            # 查詢今年度假日
            current_year = datetime.now().year
            query_data = {
                'year': current_year
            }
            
            # 使用 GET 方法，將參數作為 query parameters
            response = self.session.get(self.HOLIDAY_URL, params=query_data)
            response.raise_for_status()
            
            data = response.json()
            holidays = []
            
            # 解析假日資料（依實際 API 回應格式調整）
            if 'list' in data:
                for holiday in data['list']:
                    if 'date' in holiday:
                        nd = normalize_workdo_date(holiday['date'])
                        if nd:
                            holidays.append(nd)
            
            logger.info(f"✅ 找到 {len(holidays)} 個假日")
            return holidays
            
        except Exception as e:
            logger.warning(f"⚠️ 查詢假日失敗: {str(e)}")
            return []
    
    def update_leave_days_from_api(self):
        """從 Workdo API 查詢假日並更新 leave_days.json"""
        
        # 讀取現有的 leave_days.json（如果存在）
        existing_leave_days = {}
        if os.path.exists('leave_days.json'):
            try:
                with open('leave_days.json', 'r', encoding='utf-8') as f:
                    existing_leave_days = json.load(f)
                logger.info(f"📖 讀取現有請假日設定: {len(existing_leave_days)} 筆")
            except Exception as e:
                logger.warning(f"⚠️ 讀取現有設定失敗: {str(e)}")
        
        new_holidays = {}
        api_success = False
        
        try:
            logger.info("🔄 開始從 Workdo API 更新假日資料...")
            
            # 查詢今年度假日
            current_year = datetime.now().year
            query_data = {
                'year': current_year
            }
            
            logger.info(f"🗓️ 查詢 {current_year} 年度假日...")
            logger.info(f"📍 API URL: {self.HOLIDAY_URL}")
            logger.info(f"📤 請求資料: {query_data}")
            
            # 使用 GET 方法，將參數作為 query parameters
            response = self.session.get(self.HOLIDAY_URL, params=query_data)
            logger.info(f"📥 HTTP 狀態碼: {response.status_code}")
            
            # 如果狀態碼不是 2xx，記錄錯誤但不中斷
            if response.status_code >= 400:
                logger.error(f"❌ API 返回錯誤狀態碼: {response.status_code}")
                logger.error(f"📋 回應內容: {response.text[:500]}")
            else:
                response.raise_for_status()
                
                data = response.json()
                logger.info(f"📋 API 回應內容: {json.dumps(data, ensure_ascii=False, indent=2)}")
                
                # 解析假日資料
                if 'list' in data:
                    for holiday in data['list']:
                        if 'date' in holiday and 'name' in holiday:
                            raw = holiday['date']
                            date_str = normalize_workdo_date(raw) or str(raw)
                            name = holiday.get('name', '假日')
                            new_holidays[date_str] = name
                            logger.info(f"   📅 {date_str}: {name}")
                    api_success = True
                
                if not new_holidays:
                    logger.warning("⚠️ API 未返回任何假日資料")
                    logger.info(f"💡 完整 API 回應: {json.dumps(data, ensure_ascii=False, indent=2)}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ API 請求失敗: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"📥 HTTP 狀態碼: {e.response.status_code}")
                logger.error(f"📋 回應內容: {e.response.text[:500]}")
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON 解析失敗: {str(e)}")
        except Exception as e:
            logger.error(f"❌ 查詢假日資料時發生未預期的錯誤: {str(e)}")
            import traceback
            logger.error(f"錯誤堆疊: {traceback.format_exc()}")
        
        # 無論 API 是否成功，都要生成文件
        logger.info("=" * 60)
        logger.info("📝 準備生成 leave_days.json 文件...")
        
        if not new_holidays and not existing_leave_days:
            logger.warning("⚠️ 無任何假日資料（無 API 資料也無現有資料），將建立空的 JSON 文件")
            sorted_leave_days = {}
        elif not new_holidays:
            logger.info(f"📝 API 無新資料，保留現有的 {len(existing_leave_days)} 筆假日資料")
            sorted_leave_days = dict(sorted(existing_leave_days.items()))
        else:
            # 合併現有資料和新查詢的假日（新查詢的假日會覆蓋舊的）
            merged_leave_days = {**existing_leave_days, **new_holidays}
            sorted_leave_days = dict(sorted(merged_leave_days.items()))
        
        logger.info(f"💾 準備寫入 leave_days.json...")
        
        # 寫入 leave_days.json（無論有無資料都寫入）
        try:
            with open('leave_days.json', 'w', encoding='utf-8') as f:
                json.dump(sorted_leave_days, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ 成功寫入 leave_days.json")
        except Exception as e:
            logger.error(f"❌ 寫入檔案失敗: {str(e)}")
            import traceback
            logger.error(f"錯誤堆疊: {traceback.format_exc()}")
            return False
        
        # 驗證文件是否正確寫入
        if not os.path.exists('leave_days.json'):
            logger.error(f"❌ 驗證失敗: leave_days.json 不存在")
            return False
        
        file_size = os.path.getsize('leave_days.json')
        logger.info(f"✅ 檔案驗證通過 (大小: {file_size} bytes)")
        logger.info(f"📊 統計資訊:")
        logger.info(f"   • 總計: {len(sorted_leave_days)} 筆假日資料")
        logger.info(f"   • 從 API 新增/更新: {len(new_holidays)} 筆")
        logger.info(f"   • 保留現有設定: {len(existing_leave_days)} 筆")
        
        # 即使沒有新資料，只要成功建立檔案就算成功
        if len(sorted_leave_days) == 0:
            logger.warning("⚠️ 檔案中沒有任何假日資料，但檔案已成功建立")
        
        return True
    
    def update_holidays_from_taiwan_calendar(self):
        """從台湾公开日历数据源更新假日資料"""
        
        # 讀取現有的 leave_days.json（如果存在）
        existing_leave_days = {}
        if os.path.exists('leave_days.json'):
            try:
                with open('leave_days.json', 'r', encoding='utf-8') as f:
                    existing_leave_days = json.load(f)
                logger.info(f"📖 讀取現有請假日設定: {len(existing_leave_days)} 筆")
            except Exception as e:
                logger.warning(f"⚠️ 讀取現有設定失敗: {str(e)}")
        
        new_holidays = {}
        api_success = False
        
        try:
            logger.info("🔄 從台灣公開日曆數據源更新假日資料...")
            
            # 查詢今年度假日
            current_year = datetime.now().year
            calendar_url = self.TAIWAN_CALENDAR_URL.format(year=current_year)
            
            logger.info(f"🗓️ 查詢 {current_year} 年度台灣假日...")
            logger.info(f"📍 API URL: {calendar_url}")
            
            response = requests.get(calendar_url, timeout=10)
            logger.info(f"📥 HTTP 狀態碼: {response.status_code}")
            
            if response.status_code >= 400:
                logger.error(f"❌ API 返回錯誤狀態碼: {response.status_code}")
            else:
                response.raise_for_status()
                
                data = response.json()
                logger.info(f"📋 成功獲取日曆資料，共 {len(data)} 天")
                
                # 解析假日資料（只取有描述的假日）
                for day in data:
                    if day.get('isHoliday') and day.get('description'):
                        date_str = day['date']  # 格式: 20260101
                        # 轉換為 YYYY-MM-DD 格式
                        formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
                        name = day['description']
                        new_holidays[formatted_date] = name
                        logger.info(f"   📅 {formatted_date}: {name}")
                
                api_success = True
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ API 請求失敗: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON 解析失敗: {str(e)}")
        except Exception as e:
            logger.error(f"❌ 查詢假日資料時發生未預期的錯誤: {str(e)}")
            import traceback
            logger.error(f"錯誤堆疊: {traceback.format_exc()}")
        
        # 無論 API 是否成功，都要生成文件
        logger.info("=" * 60)
        logger.info("📝 準備生成 leave_days.json 文件...")
        
        if not new_holidays and not existing_leave_days:
            logger.warning("⚠️ 無任何假日資料（無 API 資料也無現有資料），將建立空的 JSON 文件")
            sorted_leave_days = {}
        elif not new_holidays:
            logger.info(f"📝 API 無新資料，保留現有的 {len(existing_leave_days)} 筆假日資料")
            sorted_leave_days = dict(sorted(existing_leave_days.items()))
        else:
            # 合併現有資料和新查詢的假日（新查詢的假日會覆蓋舊的）
            merged_leave_days = {**existing_leave_days, **new_holidays}
            sorted_leave_days = dict(sorted(merged_leave_days.items()))
        
        logger.info(f"💾 準備寫入 leave_days.json...")
        
        # 寫入 leave_days.json（無論有無資料都寫入）
        try:
            with open('leave_days.json', 'w', encoding='utf-8') as f:
                json.dump(sorted_leave_days, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ 成功寫入 leave_days.json")
        except Exception as e:
            logger.error(f"❌ 寫入檔案失敗: {str(e)}")
            import traceback
            logger.error(f"錯誤堆疊: {traceback.format_exc()}")
            return False
        
        # 驗證文件是否正確寫入
        if not os.path.exists('leave_days.json'):
            logger.error(f"❌ 驗證失敗: leave_days.json 不存在")
            return False
        
        file_size = os.path.getsize('leave_days.json')
        logger.info(f"✅ 檔案驗證通過 (大小: {file_size} bytes)")
        logger.info(f"📊 統計資訊:")
        logger.info(f"   • 總計: {len(sorted_leave_days)} 筆假日資料")
        logger.info(f"   • 從 API 新增/更新: {len(new_holidays)} 筆")
        logger.info(f"   • 保留現有設定: {len(existing_leave_days)} 筆")
        
        if len(sorted_leave_days) == 0:
            logger.warning("⚠️ 檔案中沒有任何假日資料，但檔案已成功建立")
        
        return True
    
    def query_missing_punch(self):
        """查詢缺卡記錄"""
        try:
            logger.info("🔍 查詢缺卡記錄...")
            
            response = self.session.post(
                self.MISSING_PUNCH_QUERY_URL,
                json={'displayName': 'ClockPunchReq'}
            )
            response.raise_for_status()
            
            data = response.json()
            missing_records = []
            
            if 'list' in data:
                for record in data['list']:
                    if record.get('result') == 'Missing':
                        missing_records.append(record)
            
            if missing_records:
                logger.info(f"⚠️ 發現 {len(missing_records)} 筆缺卡記錄")
                return missing_records
            else:
                logger.info("✅ 無缺卡記錄")
                return []
                
        except Exception as e:
            logger.warning(f"⚠️ 查詢缺卡記錄失敗: {str(e)}")
            return []
    
    def supplement_missing_punch(self, record):
        """補打卡"""
        try:
            punch_type = record.get('type', 'ClockIn')
            punch_day = record.get('punchDay')
            punch_name = "上班" if punch_type == "ClockIn" else "下班"
            
            logger.info(f"📝 補{punch_name}打卡 - {punch_day}")
            
            # 解析 GPS 座標為 WKT POINT 格式
            lat, lon = self.gps_location.split(',')
            gps_point = f"POINT({lon.strip()} {lat.strip()})"
            
            # 建立補打卡請求
            supplement_data = {
                'reqOid': record.get('reqOid'),
                'punchDay': punch_day,
                'reqPunchTime': record.get('reqPunchTime'),
                'reqPlace': 'OtherCity',
                'reqOidEnc': record.get('reqOidEnc'),
                'type': punch_type,
                'fileInfoList': record.get('fileInfoList', []),
                'reqWifiPoint': record.get('reqWifiPoint'),
                'reqWifiMac': record.get('reqWifiMac'),
                'reqGpsPlace': self.gps_place,
                'reqGpsLocation': {'text': gps_point},
                'reqFaceDeviceName': record.get('reqFaceDeviceName'),
                'reqFaceDeviceOid': record.get('reqFaceDeviceOid')
            }
            
            response = self.session.post(self.MISSING_PUNCH_SAVE_URL, json=supplement_data)
            response.raise_for_status()
            
            logger.info(f"✅ 補打卡成功 - {punch_day}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 補打卡失敗: {str(e)}")
            return False
    
    def is_holiday(self):
        """檢查今天是否為假日（週末 / leave_days.json / 台灣行事曆 / Workdo 假日 API 並用）"""
        now = datetime.now()
        today = now.strftime('%Y-%m-%d')
        
        # 檢查週末
        if now.weekday() >= 5:  # 5=週六, 6=週日
            logger.info("📅 今天是週末")
            return True
        
        # 檢查請假日設定（從 JSON 檔案；可含手動請假、或由 update-holidays* 合併）
        if os.path.exists('leave_days.json'):
            try:
                with open('leave_days.json', 'r', encoding='utf-8') as f:
                    leave_days = json.load(f)
                    if today in leave_days:
                        logger.info(f"📅 今天是請假日: {leave_days[today]}")
                        return True
            except Exception as e:
                logger.warning(f"⚠️ 讀取請假日設定失敗: {str(e)}")
        
        # 台灣公開行事曆（國定假日等），不需 Workdo 登入額外權限
        if self.use_tw_calendar:
            try:
                tw_dates = fetch_taiwan_public_holiday_dates(now.year)
                if today in tw_dates:
                    logger.info("📅 今天是台灣公開行事曆之放假日")
                    return True
            except Exception as e:
                logger.warning(f"⚠️ 台灣行事曆取得失敗，略過此項: {str(e)}")
        
        # Workdo 公司行事曆（需 WORKDO_USE_LEAVE_API=true）
        holidays = self.query_holidays()
        if today in holidays:
            logger.info("📅 今天是 Workdo 行事曆假日")
            return True
        
        return False


def main():
    """主程式"""
    # 載入環境變數
    load_dotenv()
    
    # 解析命令列參數
    parser = argparse.ArgumentParser(description='Workdo 自動打卡系統')
    parser.add_argument(
        'action',
        choices=['in', 'out', 'status', 'check-missing', 'auto', 'update-holidays', 'update-holidays-tw'],
        help='執行動作: in(上班打卡), out(下班打卡), status(查詢狀態), check-missing(檢查並補缺卡), auto(智慧判斷), update-holidays(從Workdo更新假日), update-holidays-tw(從台灣政府公開資料更新假日)'
    )
    parser.add_argument(
        '--skip-holiday-check',
        action='store_true',
        help='跳過假日檢查，強制執行打卡'
    )
    
    args = parser.parse_args()
    
    # update-holidays-tw 不需要 Workdo 登入，可以跳過環境變數檢查
    if args.action == 'update-holidays-tw':
        # 直接執行台灣假日更新，不需要建立 WorkdoAPI 實例
        try:
            logger.info("=" * 60)
            logger.info("🚀 開始從台灣公開日曆數據源更新假日資料")
            logger.info("=" * 60)
            
            # 創建一個臨時實例只用於調用該方法
            temp_api = WorkdoAPI.__new__(WorkdoAPI)
            success = temp_api.update_holidays_from_taiwan_calendar()
            
            logger.info("=" * 60)
            if success:
                logger.info("✅ 假日資料更新任務完成")
                # 驗證文件是否存在
                if os.path.exists('leave_days.json'):
                    file_size = os.path.getsize('leave_days.json')
                    logger.info(f"✅ leave_days.json 已生成 (大小: {file_size} bytes)")
                    
                    # 顯示部分內容
                    try:
                        with open('leave_days.json', 'r', encoding='utf-8') as f:
                            holidays = json.load(f)
                        logger.info(f"📅 已載入 {len(holidays)} 個假日")
                        if holidays:
                            logger.info("前 5 個假日:")
                            for i, (date, name) in enumerate(list(holidays.items())[:5]):
                                logger.info(f"   {date}: {name}")
                    except Exception as e:
                        logger.warning(f"無法讀取文件內容: {str(e)}")
                else:
                    logger.error("❌ leave_days.json 未生成")
                    success = False
            else:
                logger.error("❌ 假日資料更新任務失敗")
                logger.info("💡 提示:")
                logger.info("   1. 檢查網路連線是否正常")
                logger.info("   2. 確認台灣日曆數據源是否可存取")
            logger.info("=" * 60)
            
            if not success:
                sys.exit(1)
            else:
                logger.info("✨ 執行完成")
                sys.exit(0)
                
        except Exception as e:
            logger.error(f"❌ 更新假日資料時發生異常: {str(e)}")
            import traceback
            logger.error("完整錯誤堆疊:")
            logger.error(traceback.format_exc())
            sys.exit(1)
    
    # 其他操作需要檢查環境變數
    # 檢查環境變數
    required_vars = ['WORKDO_EMAIL', 'WORKDO_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ 錯誤: 缺少環境變數: {', '.join(missing_vars)}")
        logger.error("請建立 .env 檔案並設定必要的環境變數")
        sys.exit(1)
    
    # 建立 API 實例
    workdo = WorkdoAPI()
    
    # 登入
    if not workdo.login():
        logger.error("❌ 登入失敗，程式結束")
        sys.exit(1)
    
    # 檢查是否為假日（自動打卡模式時跳過假日）
    if args.action in ['in', 'out', 'auto'] and not args.skip_holiday_check:
        if workdo.is_holiday():
            logger.info("🎉 今天是假日，不需要打卡")
            sys.exit(0)
    
    # 執行對應動作
    if args.action == 'in':
        # 上班打卡
        if workdo.has_punched_type_today('ClockIn'):
            logger.info("ℹ️ 今日已完成上班打卡，略過重複執行")
        else:
            workdo.clock_in()
        workdo.get_punch_status()
        
    elif args.action == 'out':
        # 下班打卡
        if workdo.has_punched_type_today('ClockOut'):
            logger.info("ℹ️ 今日已完成下班打卡，略過重複執行")
        else:
            workdo.clock_out()
        workdo.get_punch_status()
        
    elif args.action == 'status':
        # 查詢狀態
        workdo.get_punch_status()
        
    elif args.action == 'check-missing':
        # 檢查並補缺卡
        missing_records = workdo.query_missing_punch()
        for record in missing_records:
            workdo.supplement_missing_punch(record)
    
    elif args.action == 'update-holidays':
        # 從 Workdo API 更新假日資料
        try:
            logger.info("=" * 60)
            logger.info("🚀 開始執行假日資料更新任務")
            logger.info("=" * 60)
            
            success = workdo.update_leave_days_from_api()
            
            logger.info("=" * 60)
            if success:
                logger.info("✅ 假日資料更新任務完成")
                # 驗證文件是否存在
                if os.path.exists('leave_days.json'):
                    file_size = os.path.getsize('leave_days.json')
                    logger.info(f"✅ leave_days.json 已生成 (大小: {file_size} bytes)")
                else:
                    logger.error("❌ leave_days.json 未生成")
                    success = False
            else:
                logger.error("❌ 假日資料更新任務失敗")
                logger.info("💡 提示:")
                logger.info("   1. 確認已設定 WORKDO_USE_LEAVE_API=true")
                logger.info("   2. 確認帳號有權限存取假日資料")
                logger.info("   3. 檢查 API 回應格式是否正確")
            logger.info("=" * 60)
            
            # 在 CI 環境中，即使失敗也不要退出，讓 workflow 能完成
            if not success and not os.environ.get('CI'):
                sys.exit(1)
                
        except Exception as e:
            logger.error(f"❌ 更新假日資料時發生異常: {str(e)}")
            import traceback
            logger.error("完整錯誤堆疊:")
            logger.error(traceback.format_exc())
            if not os.environ.get('CI'):
                sys.exit(1)
    
    elif args.action == 'auto':
        # 智慧判斷：根據時間自動打卡
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute
        current_time = current_hour * 100 + current_minute  # 例如 8:30 = 830, 18:00 = 1800
        
        # 先檢查並補缺卡
        missing_records = workdo.query_missing_punch()
        if missing_records:
            logger.info("🔧 先處理缺卡記錄...")
            for record in missing_records:
                workdo.supplement_missing_punch(record)
        
        # 根據時間判斷上下班
        # 上班打卡：8:30-9:00（含 9:00）
        if 830 <= current_time <= 900:
            logger.info(f"🌅 早上時段 ({current_hour:02d}:{current_minute:02d})，執行上班打卡")
            if workdo.has_punched_type_today('ClockIn'):
                logger.info("ℹ️ 今日已完成上班打卡，略過重複執行")
            else:
                workdo.clock_in()
        # 下班打卡：18:00-18:30（含 18:30）
        elif 1800 <= current_time <= 1830:
            logger.info(f"🌆 傍晚時段 ({current_hour:02d}:{current_minute:02d})，執行下班打卡")
            if workdo.has_punched_type_today('ClockOut'):
                logger.info("ℹ️ 今日已完成下班打卡，略過重複執行")
            else:
                workdo.clock_out()
        else:
            logger.info(f"⏰ 目前時間 {current_hour:02d}:{current_minute:02d} 不在打卡時段內（上班: 8:30-9:00, 下班: 18:00-18:30）")
        
        workdo.get_punch_status()
    
    logger.info("✨ 執行完成")


if __name__ == '__main__':
    main()
