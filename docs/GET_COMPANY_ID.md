# 如何取得 Workdo Company ID

## 方法 1: 從網頁 URL 查詢（最簡單） ✅

1. **登入 Workdo 網頁版**
   - 前往 https://www.workdo.co 或您公司的 Workdo 網址
   - 使用您的帳號登入

2. **查看網址列**
   - 登入後，網址通常會包含 Company ID
   
   **常見 URL 格式範例：**
   
   - **格式 1**：`https://www.workdo.co/!#/aa6pd97f/aa6pd97f/...`
     - Company ID = `aa6pd97f`（斜線後的第一個或第二個字串）
   
   - **格式 2**：`https://app.workdo.co/company/12345/...`
     - Company ID = `12345`
   
   - **格式 3**：`https://your-company.workdo.co/c/67890/...`
     - Company ID = `67890`
   
   - **格式 4**：`https://www.workdo.co/company/abc123/dashboard`
     - Company ID = `abc123`

   💡 **提示**：Company ID 可能是純數字（如 `12345`）或英數混合（如 `aa6pd97f`）

## 方法 2: 從個人設定頁面查詢

1. **進入個人設定**
   - 點擊右上角的個人頭像
   - 選擇「設定」或「Settings」

2. **查看公司資訊**
   - 進入「公司設定」或「Company Settings」
   - 尋找「Company ID」或「公司識別碼」欄位

## 方法 3: 從瀏覽器開發者工具查詢

1. **開啟開發者工具**
   - Windows/Linux: 按 `F12` 或 `Ctrl + Shift + I`
   - Mac: 按 `Cmd + Option + I`

2. **查看 Network 請求**
   - 切換到「Network」分頁
   - 重新整理頁面（F5）
   - 尋找 API 請求（通常是 `/api/...` 開頭的請求）
   - 檢查請求的 Headers 或 Payload，找到 `company_id` 欄位

3. **查看 Local Storage**
   - 切換到「Application」或「Storage」分頁
   - 展開「Local Storage」
   - 查看儲存的資料中是否有 `company_id` 或類似的鍵值

## 方法 4: 使用 API 測試（適合技術人員）

如果您已經有帳號密碼，可以透過登入 API 取得：

```python
import requests

# 登入 API
url = "https://api.workdo.co/api/v1/auth/login"
payload = {
    "email": "your_email@example.com",
    "password": "your_password"
}

response = requests.post(url, json=payload)
data = response.json()

# 查看回應內容，通常會包含 company_id
print(data)
```

## 方法 5: 聯絡管理員或客服

如果以上方法都無法取得 Company ID：

1. **聯絡公司 IT 管理員**
   - 詢問 Workdo 管理員
   - 他們通常可以在管理後台查看

2. **聯絡 Workdo 客服**
   - Email: support@workdo.co
   - 提供您的公司名稱和註冊 Email
   - 客服會協助您取得 Company ID

## 常見問題

### Q: Company ID 是什麼格式？
A: 可能是以下格式：
- 純數字：`12345`、`67890`
- 英數混合：`aa6pd97f`、`abc123`
- 英文字母和數字的組合，通常 8 位左右

### Q: 每個公司的 Company ID 是唯一的嗎？
A: 是的，每個公司在 Workdo 系統中都有唯一的識別碼

### Q: 我可以使用公司名稱代替 Company ID 嗎？
A: 不行，API 需要使用數字格式的 Company ID

### Q: Company ID 會改變嗎？
A: 通常不會，一旦建立就是固定的

## 測試驗證

取得 Company ID 後，可以使用以下方式驗證是否正確：

```bash
# 方法 1: 使用我們的測試腳本
python workdo_auto_clock.py status

# 方法 2: 使用 Jupyter Notebook
# 執行登入測試 cell，如果成功登入表示 Company ID 正確
```

## 安全提醒 ⚠️

- **不要分享** Company ID 給不信任的第三方
- **不要上傳** 包含 Company ID 的 `.env` 檔案到公開的 Git 倉庫
- **定期檢查** `.gitignore` 確保 `.env` 被排除在版本控制之外

---

如果仍有問題，請參考 [USAGE.md](../USAGE.md) 或查閱 Workdo 官方文件。
