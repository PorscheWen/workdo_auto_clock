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
    
    def __init__(self):
        self.email = os.getenv('WORKDO_EMAIL')
        self.password = os.getenv('WORKDO_PASSWORD')
        self.gps_location = os.getenv('WORKDO_GPS_LOCATION', '25.033,121.564')
        self.gps_place = os.getenv('WORKDO_GPS_PLACE', '台北市信義區')
        self.use_leave_api = os.getenv('WORKDO_USE_LEAVE_API', 'false').lower() == 'true'
        
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
            
            response = self.session.post(self.HOLIDAY_URL, json=query_data)
            response.raise_for_status()
            
            data = response.json()
            holidays = []
            
            # 解析假日資料（依實際 API 回應格式調整）
            if 'list' in data:
                for holiday in data['list']:
                    if 'date' in holiday:
                        holidays.append(holiday['date'])
            
            logger.info(f"✅ 找到 {len(holidays)} 個假日")
            return holidays
            
        except Exception as e:
            logger.warning(f"⚠️ 查詢假日失敗: {str(e)}")
            return []
    
    def update_leave_days_from_api(self):
        """從 Workdo API 查詢假日並更新 leave_days.json"""
        try:
            logger.info("🔄 開始從 Workdo API 更新假日資料...")
            
            # 讀取現有的 leave_days.json（如果存在）
            existing_leave_days = {}
            if os.path.exists('leave_days.json'):
                try:
                    with open('leave_days.json', 'r', encoding='utf-8') as f:
                        existing_leave_days = json.load(f)
                    logger.info(f"📖 讀取現有請假日設定: {len(existing_leave_days)} 筆")
                except Exception as e:
                    logger.warning(f"⚠️ 讀取現有設定失敗: {str(e)}")
            
            # 查詢今年度假日
            current_year = datetime.now().year
            query_data = {
                'year': current_year
            }
            
            logger.info(f"🗓️ 查詢 {current_year} 年度假日...")
            response = self.session.post(self.HOLIDAY_URL, json=query_data)
            response.raise_for_status()
            
            data = response.json()
            new_holidays = {}
            
            # 解析假日資料
            if 'list' in data:
                for holiday in data['list']:
                    if 'date' in holiday and 'name' in holiday:
                        date_str = holiday['date']
                        name = holiday.get('name', '假日')
                        new_holidays[date_str] = name
                        logger.info(f"   📅 {date_str}: {name}")
            
            if not new_holidays:
                logger.warning("⚠️ 未找到任何假日資料，可能需要檢查 API 回應格式")
                logger.info(f"API 回應: {data}")
                return False
            
            # 合併現有資料和新查詢的假日（新查詢的假日會覆蓋舊的）
            merged_leave_days = {**existing_leave_days, **new_holidays}
            
            # 按日期排序
            sorted_leave_days = dict(sorted(merged_leave_days.items()))
            
            # 寫入 leave_days.json
            with open('leave_days.json', 'w', encoding='utf-8') as f:
                json.dump(sorted_leave_days, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 成功更新 leave_days.json")
            logger.info(f"📊 總計: {len(sorted_leave_days)} 筆假日資料")
            logger.info(f"   • 從 API 新增/更新: {len(new_holidays)} 筆")
            logger.info(f"   • 保留現有設定: {len(existing_leave_days)} 筆")
            
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ API 查詢失敗: {str(e)}")
            if hasattr(e.response, 'text'):
                logger.error(f"回應內容: {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"❌ 更新假日資料失敗: {str(e)}")
            return False
    
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
        """檢查今天是否為假日"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 檢查週末
        if datetime.now().weekday() >= 5:  # 5=週六, 6=週日
            logger.info("📅 今天是週末")
            return True
        
        # 檢查請假日設定（從 JSON 檔案）
        if os.path.exists('leave_days.json'):
            try:
                with open('leave_days.json', 'r', encoding='utf-8') as f:
                    leave_days = json.load(f)
                    if today in leave_days:
                        logger.info(f"📅 今天是請假日: {leave_days[today]}")
                        return True
            except Exception as e:
                logger.warning(f"⚠️ 讀取請假日設定失敗: {str(e)}")
        
        # 使用 API 查詢假日
        holidays = self.query_holidays()
        if today in holidays:
            logger.info("📅 今天是假日")
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
        choices=['in', 'out', 'status', 'check-missing', 'auto', 'update-holidays'],
        help='執行動作: in(上班打卡), out(下班打卡), status(查詢狀態), check-missing(檢查並補缺卡), auto(智慧判斷), update-holidays(更新假日資料)'
    )
    parser.add_argument(
        '--skip-holiday-check',
        action='store_true',
        help='跳過假日檢查，強制執行打卡'
    )
    
    args = parser.parse_args()
    
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
        workdo.clock_in()
        workdo.get_punch_status()
        
    elif args.action == 'out':
        # 下班打卡
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
        success = workdo.update_leave_days_from_api()
        if not success:
            logger.error("❌ 更新假日資料失敗")
            logger.info("💡 提示:")
            logger.info("   1. 確認已設定 WORKDO_USE_LEAVE_API=true")
            logger.info("   2. 確認帳號有權限存取假日資料")
            logger.info("   3. 檢查 API 回應格式是否正確")
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
        # 上班打卡：8:30-9:00
        if 830 <= current_time < 900:
            logger.info(f"🌅 早上時段 ({current_hour:02d}:{current_minute:02d})，執行上班打卡")
            workdo.clock_in()
        # 下班打卡：18:00-18:30
        elif 1800 <= current_time < 1830:
            logger.info(f"🌆 傍晚時段 ({current_hour:02d}:{current_minute:02d})，執行下班打卡")
            workdo.clock_out()
        else:
            logger.info(f"⏰ 目前時間 {current_hour:02d}:{current_minute:02d} 不在打卡時段內（上班: 8:30-9:00, 下班: 18:00-18:30）")
        
        workdo.get_punch_status()
    
    logger.info("✨ 執行完成")


if __name__ == '__main__':
    main()
