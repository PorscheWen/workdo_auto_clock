#!/usr/bin/env python3
"""
Workdo API 自動打卡程式
可直接在命令列執行，無需 Jupyter Notebook
"""

import os
import sys
import argparse
import requests
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv


class WorkdoAPI:
    """Workdo API 自動打卡類別"""
    
    def __init__(self):
        self.email = os.getenv('WORKDO_EMAIL')
        self.password = os.getenv('WORKDO_PASSWORD')
        self.company_id = os.getenv('WORKDO_COMPANY_ID')
        self.api_url = os.getenv('WORKDO_API_URL', 'https://api.workdo.co')
        self.token = None
        self.session = requests.Session()
        
    def login(self):
        """登入 Workdo 取得存取權杖"""
        try:
            url = f"{self.api_url}/api/v1/auth/login"
            payload = {
                'email': self.email,
                'password': self.password,
                'company_id': self.company_id
            }
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            self.token = data.get('token')
            self.session.headers.update({'Authorization': f'Bearer {self.token}'})
            
            print(f"✅ 登入成功 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 登入失敗: {str(e)}")
            return False
    
    def clock_in(self):
        """上班打卡"""
        try:
            url = f"{self.api_url}/api/v1/attendance/clock-in"
            payload = {
                'timestamp': datetime.now().isoformat(),
                'type': 'clock_in'
            }
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            print(f"✅ 上班打卡成功 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 上班打卡失敗: {str(e)}")
            return False
    
    def clock_out(self):
        """下班打卡"""
        try:
            url = f"{self.api_url}/api/v1/attendance/clock-out"
            payload = {
                'timestamp': datetime.now().isoformat(),
                'type': 'clock_out'
            }
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            print(f"✅ 下班打卡成功 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 下班打卡失敗: {str(e)}")
            return False
    
    def get_attendance_status(self):
        """查詢今日打卡狀態"""
        try:
            url = f"{self.api_url}/api/v1/attendance/status"
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            print(f"📊 今日打卡狀態: {data}")
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 查詢狀態失敗: {str(e)}")
            return None


class AutoClockScheduler:
    """自動打卡排程器"""
    
    def __init__(self, workdo_api, clock_in_time="09:00", clock_out_time="18:00"):
        self.workdo = workdo_api
        self.clock_in_time = clock_in_time
        self.clock_out_time = clock_out_time
        
    def job_clock_in(self):
        """上班打卡任務"""
        print(f"\n🔔 執行上班打卡任務...")
        if not self.workdo.token:
            self.workdo.login()
        self.workdo.clock_in()
    
    def job_clock_out(self):
        """下班打卡任務"""
        print(f"\n🔔 執行下班打卡任務...")
        if not self.workdo.token:
            self.workdo.login()
        self.workdo.clock_out()
    
    def setup_schedule(self):
        """設定排程"""
        schedule.clear()
        schedule.every().day.at(self.clock_in_time).do(self.job_clock_in)
        schedule.every().day.at(self.clock_out_time).do(self.job_clock_out)
        
        print(f"⏰ 排程設定完成:")
        print(f"   - 上班打卡時間: {self.clock_in_time}")
        print(f"   - 下班打卡時間: {self.clock_out_time}")
    
    def run(self):
        """啟動排程器"""
        self.setup_schedule()
        
        print(f"\n🚀 自動打卡排程器已啟動")
        print(f"   當前時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n💡 提示: 按 Ctrl+C 停止執行\n")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分鐘檢查一次
                    
        except KeyboardInterrupt:
            print(f"\n⏹️ 排程器已停止")
            schedule.clear()


def main():
    """主程式"""
    # 載入環境變數
    load_dotenv()
    
    # 解析命令列參數
    parser = argparse.ArgumentParser(description='Workdo API 自動打卡程式')
    parser.add_argument('action', choices=['in', 'out', 'status', 'auto'], 
                        help='執行動作: in(上班打卡), out(下班打卡), status(查詢狀態), auto(自動排程)')
    parser.add_argument('--clock-in', default='09:00', 
                        help='上班打卡時間 (預設: 09:00)')
    parser.add_argument('--clock-out', default='18:00', 
                        help='下班打卡時間 (預設: 18:00)')
    
    args = parser.parse_args()
    
    # 檢查環境變數
    required_vars = ['WORKDO_EMAIL', 'WORKDO_PASSWORD', 'WORKDO_COMPANY_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ 錯誤: 缺少環境變數: {', '.join(missing_vars)}")
        print("請建立 .env 檔案並設定必要的環境變數")
        sys.exit(1)
    
    # 建立 API 實例
    workdo = WorkdoAPI()
    
    # 執行對應動作
    if args.action == 'in':
        # 手動上班打卡
        if workdo.login():
            workdo.clock_in()
    
    elif args.action == 'out':
        # 手動下班打卡
        if workdo.login():
            workdo.clock_out()
    
    elif args.action == 'status':
        # 查詢打卡狀態
        if workdo.login():
            workdo.get_attendance_status()
    
    elif args.action == 'auto':
        # 自動排程打卡
        scheduler = AutoClockScheduler(
            workdo_api=workdo,
            clock_in_time=args.clock_in,
            clock_out_time=args.clock_out
        )
        scheduler.run()


if __name__ == '__main__':
    main()
