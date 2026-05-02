# Workdo 自動打卡系統 (Python 版)

一個基於 Python 的 Workdo 自動打卡系統，參考自 [akitosun/WorkDoAuto](https://github.com/akitosun/WorkDoAuto) 並轉換為 Python 實作。

## ✨ 功能特色

- ✅ 自動上下班打卡
- ⏰ 智慧時段判斷
- 🗓️ 假日與週末自動偵測
- 📝 自動補缺卡功能
- 📊 打卡狀態查詢
- 🔒 安全的環境變數管理
- 🤖 支援 GitHub Actions 自動化部署
- 📍 GPS 定位設定

## 🚀 快速開始

### 1. 安裝依賴套件

```bash
pip install -r requirements.txt
```

### 2. 設定環境變數

複製 `.env.example` 為 `.env` 並填入您的 Workdo 帳號資訊：

```bash
cp .env.example .env
```

編輯 `.env` 檔案：
```env
WORKDO_EMAIL=your_email@example.com
WORKDO_PASSWORD=your_password
WORKDO_GPS_LOCATION=25.033,121.564
WORKDO_GPS_PLACE=台北市信義區
```

### 3. 使用方式

#### 手動上班打卡
```bash
python workdo_auto_clock.py in
```

#### 手動下班打卡
```bash
python workdo_auto_clock.py out
```

#### 查詢打卡狀態
```bash
python workdo_auto_clock.py status
```

#### 檢查並補缺卡
```bash
python workdo_auto_clock.py check-missing
```

#### 智慧自動打卡（根據時間自動判斷）
```bash
python workdo_auto_clock.py auto
```

智慧模式會根據當前時間自動判斷：
- **08:30-09:00**: 執行上班打卡
- **18:00-18:30**: 執行下班打卡
- 自動檢查並補缺卡
- 自動跳過週末和假日

#### 跳過假日檢查（強制打卡）
```bash
python workdo_auto_clock.py in --skip-holiday-check
```

#### 從 Workdo API 更新假日資料 ✨ **新功能**
```bash
python workdo_auto_clock.py update-holidays
```

此功能會：
- 📡 從 Workdo API 查詢公司假日
- 🔄 自動更新 `leave_days.json` 檔案
- 📝 保留您手動新增的請假日
- 📊 顯示更新結果統計

**注意**: 需要先設定 `WORKDO_USE_LEAVE_API=true` 才能使用此功能。

## 🗓️ 請假日設定

如果您有請假或特殊假日，可以建立 `leave_days.json` 檔案：

```json
{
  "2026-04-15": "請假",
  "2026-05-01": "勞動節",
  "2026-10-10": "國慶日"
}
```

系統會自動跳過這些日期的打卡。

**為什麼 GitHub 上沒有 `leave_days.json`？** 此檔案已列入 [`.gitignore`](.gitignore)，避免個人請假日期被提交到公開儲存庫。請在本機複製範例：`cp leave_days.json.example leave_days.json` 再自行編輯。於 GitHub Actions 執行時，可使用 Secret **`LEAVE_DAYS_JSON`** 注入同等 JSON；排程 workflow 也會先執行 `update-holidays-tw` 合併台灣國定假日。

## 🤖 使用 GitHub Actions 自動執行（推薦）

完全免費、無需自己的伺服器！

**📚 詳細設定指南**:
- [Secrets 設定完整文件](docs/SECRETS_SETUP.md) - 詳細的 Secrets 設定說明
- [圖文設定指南](docs/SECRETS_SCREENSHOTS.md) - 步驟截圖說明（文字版） ⭐ **推薦新手**
- [快速參考](SECRETS_QUICK_REFERENCE.md) - 一頁式快速查詢
- [設定流程圖](docs/SECRETS_FLOWCHART.md) - 視覺化設定步驟

### 1. 設定 GitHub Secrets

**必填 Secrets（2 個）**

| Secret Name | 說明 | 範例 |
|------------|------|------|
| `WORKDO_EMAIL` | Workdo 登入 Email | your_email@example.com |
| `WORKDO_PASSWORD` | Workdo 登入密碼 | your_password |

**選填 Secrets（4 個）**

| Secret Name | 說明 | 預設值 | 範例 |
|------------|------|--------|------|
| `WORKDO_GPS_LOCATION` | GPS 座標 | 25.033,121.564 | 25.041234,121.567890 |
| `WORKDO_GPS_PLACE` | GPS 地址 | 台北市信義區 | 台北市信義區信義路五段7號 |
| `WORKDO_USE_LEAVE_API` | 使用請假 API | false | true 或 false |
| `LEAVE_DAYS_JSON` | 請假日 JSON | (空) | 見下方「請假日設定」 |

**設定位置**: Repository → Settings → Secrets and variables → Actions → New repository secret

📚 **詳細設定指南**: 請參考 [Secrets 設定完整文件](docs/SECRETS_SETUP.md) 或 [快速參考](SECRETS_QUICK_REFERENCE.md)

### 2. 排程說明

#### 自動打卡排程（`.github/workflows/auto-clock.yml`）
- **上班打卡**: 每週一至週五 08:30（台灣時間）
- **下班打卡**: 每週一至週五 18:00（台灣時間）

#### 自動更新假日資料（`.github/workflows/update-holidays.yml`）✨ **新增**
- **執行時間**: 每週一 08:00（台灣時間）
- **功能**: 自動從 Workdo API 查詢並更新公司假日
- **條件**: 需設定 `WORKDO_USE_LEAVE_API=true`
- **結果**: 更新後的假日資料會儲存為 Artifact，可下載查看

### 3. 測試設定

**手動觸發測試**：
1. 進入 Actions 分頁
2. 選擇工作流程：
   - **"Workdo 自動打卡"** - 測試打卡功能
   - **"更新假日資料"** - 測試假日更新功能
3. 點擊 Run workflow
4. 選擇執行動作（打卡工作流程）：
   - `status` - **推薦先執行此項**，查詢打卡狀態驗證設定
   - `update-holidays` - 更新假日資料
   - `in` - 測試上班打卡
   - `out` - 測試下班打卡
   - `check-missing` - 檢查並補缺卡
   - `auto` - 智慧自動判斷

**查看執行結果**：
- 點擊執行記錄查看詳細日誌
- 下載 Artifacts 中的日誌檔案

## 📋 API 端點說明

本系統使用以下 Workdo API 端點：

| 端點 | 用途 |
|------|------|
| `/bdddweb/api/dweb/BDD771M/userLogin` | 使用者登入 |
| `/ccndweb/api/dweb/CCN102M/saveFromCreate102M3` | 上下班打卡 |
| `/ccndweb/api/dweb/CCN102M/execute102M2FromMenu` | 查詢打卡狀態 |
| `/ccnraweb/api/aweb/CCN002W/queryFromQuery002W1` | 查詢缺卡記錄 |
| `/ccndweb/api/dweb/CCN102M/saveFromCreate102M4` | 補打卡 |

## 🔧 進階功能

### 補打卡功能

系統會自動檢查缺卡記錄並嘗試補打卡：

```bash
python workdo_auto_clock.py check-missing
```

或在 `auto` 模式下自動執行。

### GPS 位置設定

如果您的公司有 GPS 打卡限制，請在 `.env` 中設定正確的座標：

```env
WORKDO_GPS_LOCATION=25.041234,121.567890
WORKDO_GPS_PLACE=台北市信義區信義路五段7號
```

您可以使用 Google Maps 找到座標：
1. 在 Google Maps 上找到位置
2. 右鍵點擊該位置
3. 點擊座標即可複製

## 📝 日誌記錄

系統會自動記錄所有操作到 `workdo_clock.log` 檔案中，方便追蹤和除錯。

## ⚠️ 注意事項

1. **環境變數安全**: 不要將 `.env` 檔案上傳到版本控制系統
2. **GitHub Secrets**: 使用 GitHub Actions 時，務必使用 Secrets 存放敏感資訊
3. **時區設定**: GitHub Actions 使用 UTC 時間，需要減 8 小時
4. **執行頻率**: 免費 GitHub Actions 每月有 2000 分鐘額度，本系統每天約使用 1 分鐘
5. **網路穩定**: 確保執行環境能穩定連接到 Workdo 服務
6. **假日處理**: 系統會自動跳過週末，國定假日請使用 `leave_days.json` 設定

## 🛠️ 故障排除

### 登入失敗
- 檢查 `.env` 檔案中的帳號密碼是否正確
- 確認 Workdo 帳號沒有被鎖定
- 檢查網路連線是否正常

### 打卡失敗
- 檢查 GPS 座標設定是否正確
- 確認公司是否有 GPS 打卡限制
- 查看 `workdo_clock.log` 了解詳細錯誤訊息

### GitHub Actions 沒有執行
- 檢查 Actions 是否已啟用（Settings → Actions → General）
- 確認 Secrets 是否設定正確
- 檢查 Cron 表達式是否正確

## 📚 參考資源

**本專案文件**:
- [專案文件總覽](PROJECT_FILES.md) - 所有檔案說明與閱讀路徑建議 📁
- [API 技術文件](docs/API_DOCUMENTATION.md) - Workdo API 完整規格

**外部資源**:
- 原始 C# 專案: [akitosun/WorkDoAuto](https://github.com/akitosun/WorkDoAuto)
- [GitHub Actions 文件](https://docs.github.com/actions)
- [Cron 表達式工具](https://crontab.guru/)

## 🤝 貢獻

歡迎提交 Issue 或 Pull Request！

## 📄 授權與免責聲明

本程式僅供學習與個人使用。使用者需自行承擔使用風險，開發者不對任何因使用本程式造成的問題負責。請確保遵守您公司的打卡規定。

## 🙏 致謝

- 感謝 [akitosun/WorkDoAuto](https://github.com/akitosun/WorkDoAuto) 提供的 C# 原始實作
- 感謝 Workdo 提供的企業協作平台
