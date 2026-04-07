# Workdo 自動打卡系統使用說明

## 兩種使用方式

### 方式 A: 使用 Jupyter Notebook（推薦用於開發和測試）

1. **開啟 Notebook**
   ```bash
   jupyter notebook notebooks/main.ipynb
   ```
   
   或直接在 VS Code 中開啟 `notebooks/main.ipynb`

2. **依序執行 Cells**
   - 導入套件
   - 設定環境變數
   - 測試登入
   - 執行手動打卡或啟動自動排程

### 方式 B: 使用命令列腳本（推薦用於生產環境）

1. **手動上班打卡**
   ```bash
   python workdo_auto_clock.py in
   ```

2. **手動下班打卡**
   ```bash
   python workdo_auto_clock.py out
   ```

3. **查詢打卡狀態**
   ```bash
   python workdo_auto_clock.py status
   ```

4. **啟動自動排程（預設 09:00 上班，18:00 下班）**
   ```bash
   python workdo_auto_clock.py auto
   ```

5. **自訂打卡時間**
   ```bash
   python workdo_auto_clock.py auto --clock-in 08:30 --clock-out 17:30
   ```

## 環境設定

### 1. 安裝依賴套件

```bash
pip install -r requirements.txt
```

### 2. 設定環境變數

複製範本檔案：
```bash
cp .env.example .env
```

編輯 `.env` 檔案，填入您的 Workdo 帳號資訊：
```env
WORKDO_EMAIL=your_email@example.com
WORKDO_PASSWORD=your_password
WORKDO_COMPANY_ID=your_company_id
WORKDO_API_URL=https://api.workdo.co
```

## 生產環境部署

### 使用 GitHub Actions（推薦）⭐

**優點**：
- ✅ 完全免費
- ✅ 無需自己的伺服器
- ✅ 自動執行，無需維護
- ✅ 安全可靠

詳細設定指南請參考：[GitHub Actions 設定指南](docs/GITHUB_ACTIONS_SETUP.md)

### 使用 Cron（Linux/Mac）

1. 編輯 crontab：
   ```bash
   crontab -e
   ```

2. 加入排程任務：
   ```cron
   # 每天 09:00 上班打卡
   0 9 * * 1-5 cd /path/to/project && /usr/bin/python3 workdo_auto_clock.py in
   
   # 每天 18:00 下班打卡
   0 18 * * 1-5 cd /path/to/project && /usr/bin/python3 workdo_auto_clock.py out
   ```

### 使用 systemd Service（Linux）

1. 建立服務檔案 `/etc/systemd/system/workdo-clock.service`：
   ```ini
   [Unit]
   Description=Workdo Auto Clock Service
   After=network.target

   [Service]
   Type=simple
   User=yourusername
   WorkingDirectory=/path/to/project
   ExecStart=/usr/bin/python3 /path/to/project/workdo_auto_clock.py auto
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

2. 啟動服務：
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable workdo-clock.service
   sudo systemctl start workdo-clock.service
   ```

3. 檢查狀態：
   ```bash
   sudo systemctl status workdo-clock.service
   ```

### 使用 Docker

1. 建立 `Dockerfile`：
   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY workdo_auto_clock.py .
   COPY .env .
   
   CMD ["python", "workdo_auto_clock.py", "auto"]
   ```

2. 建立並執行容器：
   ```bash
   docker build -t workdo-clock .
   docker run -d --name workdo-clock --restart unless-stopped workdo-clock
   ```

## 常見問題

### Q: 如何測試 API 連線？
A: 先執行手動打卡測試：
```bash
python workdo_auto_clock.py in
```

### Q: 登入失敗怎麼辦？
A: 
1. 檢查 `.env` 檔案是否正確填寫
2. 確認 API 網址是否正確
3. 檢查帳號密碼是否有效

### Q: 自動排程沒有執行？
A: 
1. 確認系統時間是否正確
2. 確認程式是否在背景持續執行
3. 檢查是否有錯誤訊息

### Q: 如何停止自動排程？
A: 
- Jupyter Notebook: 點擊停止按鈕
- 命令列: 按 `Ctrl+C`
- systemd: `sudo systemctl stop workdo-clock`

## 安全建議

1. **不要將 `.env` 檔案上傳到版本控制系統**
   - 已在 `.gitignore` 中設定忽略

2. **定期更換密碼**
   - 建議每 3 個月更換一次

3. **使用專用帳號**
   - 建議為自動化程式建立專用帳號

4. **監控執行日誌**
   - 定期檢查打卡記錄是否正常

## 授權與免責聲明

本程式僅供學習與個人使用。使用者需自行承擔使用風險，開發者不對任何因使用本程式造成的問題負責。請確保遵守您公司的打卡規定。
