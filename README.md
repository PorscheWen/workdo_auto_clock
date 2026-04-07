# Workdo API 自動打卡系統

使用 Workdo API 實現自動上下班打卡功能的 Python 應用程式。

## 功能特色

- ✅ 自動上下班打卡
- ⏰ 可自訂打卡時間排程
- 🔐 安全的環境變數管理
- 📊 打卡狀態查詢
- 🎯 支援手動和自動兩種模式

## 快速開始

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
```
WORKDO_EMAIL=your_email@example.com
WORKDO_PASSWORD=your_password
WORKDO_COMPANY_ID=your_company_id
WORKDO_API_URL=https://api.workdo.co
```

### 3. 使用 Jupyter Notebook

開啟 `notebooks/main.ipynb` 並依照說明執行：
- 手動打卡測試
- 設定自動排程
- 查詢打卡狀態

## 使用方式

### 本機使用
詳細的使用說明請參考 `notebooks/main.ipynb` 或 [USAGE.md](USAGE.md)。

### 使用 GitHub Actions 自動執行（推薦）⭐
完全免費、無需伺服器，設定後自動執行！

詳細設定步驟請參考：[GitHub Actions 設定指南](docs/GITHUB_ACTIONS_SETUP.md)

## 注意事項

- 請確保 Workdo API 網址正確
- 系統時間需正確設定
- 建議先進行手動打卡測試
- 生產環境建議搭配系統排程工具使用

## 授權

本專案僅供學習與個人使用。
