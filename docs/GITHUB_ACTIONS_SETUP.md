# GitHub Actions 自動打卡設定指南

使用 GitHub Actions 實現完全自動化的 Workdo 打卡，無需自己的伺服器！

## 🌟 優點

- ✅ **完全免費** - GitHub Actions 提供免費額度
- ✅ **無需伺服器** - 在 GitHub 雲端執行
- ✅ **自動執行** - 設定後完全自動化
- ✅ **安全可靠** - 使用 GitHub Secrets 保護敏感資訊
- ✅ **執行記錄** - 完整的執行日誌和歷史

## 📋 設定步驟

### 步驟 1: 推送程式碼到 GitHub

1. **建立新的 GitHub Repository**
   ```bash
   # 在 GitHub 網站上建立新 repository（例如：workdo-auto-clock）
   # 可設為 Private 保護隱私
   ```

2. **推送程式碼**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Workdo auto clock system"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/workdo-auto-clock.git
   git push -u origin main
   ```

### 步驟 2: 設定 GitHub Secrets

在 GitHub Repository 中設定敏感資訊：

1. **進入 Repository Settings**
   - 點擊 Repository 頁面上方的 `Settings`

2. **新增 Secrets**
   - 左側選單選擇 `Secrets and variables` → `Actions`
   - 點擊 `New repository secret`

3. **依序新增以下 Secrets**：

   | Secret Name | 說明 | 範例 |
   |------------|------|------|
   | `WORKDO_EMAIL` | Workdo 登入 Email | your_email@example.com |
   | `WORKDO_PASSWORD` | Workdo 登入密碼 | your_password |
   | `WORKDO_COMPANY_ID` | 公司 ID | 12345 |
   | `WORKDO_API_URL` | Workdo API 網址 | https://api.workdo.co |

   **新增方式**：
   - Name: 填入上表的 Secret Name（例如 `WORKDO_EMAIL`）
   - Value: 填入對應的實際值
   - 點擊 `Add secret`

### 步驟 3: 調整打卡時間（可選）

預設打卡時間：
- 上班：週一至週五 09:00 (台灣時間)
- 下班：週一至週五 18:00 (台灣時間)

如需修改，編輯 `.github/workflows/auto-clock.yml`：

```yaml
schedule:
  # 上班打卡：UTC 01:00 = 台灣 09:00
  - cron: '0 1 * * 1-5'
  # 下班打卡：UTC 10:00 = 台灣 18:00
  - cron: '0 10 * * 1-5'
```

**時區換算工具**：
- GitHub Actions 使用 UTC 時間
- 台灣時間 (UTC+8) = UTC 時間 + 8 小時
- 例如：台灣 09:00 = UTC 01:00

**Cron 語法說明**：
```
分鐘 小時 日 月 星期
 |   |   |  |   |
 |   |   |  |   └─ 0-6 (0=週日, 1-5=週一至週五)
 |   |   |  └───── 1-12
 |   |   └──────── 1-31
 |   └──────────── 0-23 (UTC)
 └──────────────── 0-59
```

**常用時間範例**：
- 台灣 08:30 → `30 0 * * 1-5` (UTC 00:30)
- 台灣 09:00 → `0 1 * * 1-5` (UTC 01:00)
- 台灣 17:30 → `30 9 * * 1-5` (UTC 09:30)
- 台灣 18:00 → `0 10 * * 1-5` (UTC 10:00)

### 步驟 4: 啟用 GitHub Actions

1. **檢查 Actions 權限**
   - Settings → Actions → General
   - 確保 `Allow all actions and reusable workflows` 已啟用

2. **驗證 Workflow**
   - 前往 `Actions` 分頁
   - 應該會看到 `Workdo 自動打卡` workflow

### 步驟 5: 測試執行

第一次設定完成後，建議先手動測試：

1. **進入 Actions 分頁**
   - 點擊 Repository 上方的 `Actions`

2. **選擇 Workflow**
   - 左側選擇 `Workdo 自動打卡`

3. **手動觸發**
   - 點擊右側 `Run workflow` 按鈕
   - 選擇執行動作：
     - `in` - 上班打卡測試
     - `out` - 下班打卡測試
     - `status` - 查詢狀態
   - 點擊綠色的 `Run workflow` 確認

4. **查看執行結果**
   - 等待執行完成（通常 30 秒內）
   - 點擊執行記錄查看詳細日誌
   - 確認是否成功打卡

## 📊 監控與管理

### 查看執行歷史

1. 進入 `Actions` 分頁
2. 查看所有執行記錄
3. 點擊任一記錄查看詳細日誌

### 下載執行日誌

如果程式有生成日誌檔案：
1. 進入執行記錄
2. 下方 `Artifacts` 區域會顯示上傳的日誌
3. 點擊下載

### 暫停自動執行

如果需要臨時停止自動打卡：

**方法 1: 停用 Workflow**
1. Actions → 選擇 `Workdo 自動打卡`
2. 點擊右上角 `...` → `Disable workflow`

**方法 2: 註解 Schedule**
編輯 `.github/workflows/auto-clock.yml`：
```yaml
# schedule:
#   - cron: '0 1 * * 1-5'
#   - cron: '0 10 * * 1-5'
```

### 重新啟用

1. Actions → 選擇 `Workdo 自動打卡`
2. 點擊 `Enable workflow`

## 🔒 安全建議

### 1. 使用 Private Repository
- 建議將 Repository 設為 Private
- Settings → General → Danger Zone → Change visibility

### 2. 限制 Actions 權限
- Settings → Actions → General → Workflow permissions
- 選擇 `Read repository contents and packages permissions`

### 3. 定期更換密碼
- 定期在 Workdo 更換密碼
- 同步更新 GitHub Secrets 中的 `WORKDO_PASSWORD`

### 4. 啟用雙因素認證
- 為 GitHub 帳號啟用 2FA
- Settings → Password and authentication

## ⚠️ 注意事項

### 1. GitHub Actions 執行時間限制
- 免費帳號每月有 2000 分鐘額度
- 本專案每天執行 2 次，每次約 30 秒
- 一個月約使用 20 分鐘，完全足夠

### 2. 時區問題
- GitHub Actions 使用 UTC 時間
- 記得將台灣時間轉換為 UTC（減 8 小時）
- 使用線上工具驗證：https://crontab.guru

### 3. Cron 不保證精確執行
- GitHub Actions 的 schedule 可能延遲 3-10 分鐘
- 這是正常現象，不影響打卡功能
- 如需精確時間，建議設定提前幾分鐘

### 4. API 限制
- 注意 Workdo API 是否有頻率限制
- 避免短時間內重複執行

### 5. 假日處理
- 目前設定為週一至週五執行（1-5）
- 如需包含週末，改為 `0-6` 或 `*`
- 國定假日需手動停用 workflow

## 🛠️ 進階配置

### 加入通知功能

可以在 workflow 中加入 Email 或 Slack 通知：

```yaml
- name: 發送通知
  if: failure()
  uses: dawidd6/action-send-mail@v3
  with:
    server_address: smtp.gmail.com
    server_port: 465
    username: ${{ secrets.EMAIL_USERNAME }}
    password: ${{ secrets.EMAIL_PASSWORD }}
    subject: Workdo 打卡失敗通知
    body: 打卡執行失敗，請檢查日誌
    to: your_email@example.com
```

### 加入日誌記錄

修改 `workdo_auto_clock.py`，加入檔案日誌功能：

```python
import logging

logging.basicConfig(
    filename='workdo_clock.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

## 📚 相關資源

- [GitHub Actions 官方文件](https://docs.github.com/en/actions)
- [Cron 語法產生器](https://crontab.guru)
- [時區轉換工具](https://www.timeanddate.com/worldclock/converter.html)
- [如何取得 Company ID](GET_COMPANY_ID.md)

## ❓ 常見問題

### Q: 為什麼執行時間不準確？
A: GitHub Actions 的 schedule 可能有 3-10 分鐘延遲，這是正常現象。可以設定提前幾分鐘執行。

### Q: 如何確認是否成功執行？
A: 進入 Actions 分頁查看執行記錄，綠色勾勾表示成功，紅色叉叉表示失敗。

### Q: 假日也會執行嗎？
A: 不會，預設設定為週一至週五（1-5），週末不執行。

### Q: 可以設定多個時間嗎？
A: 可以，在 schedule 中加入多個 cron 表達式：
```yaml
schedule:
  - cron: '0 1 * * 1-5'   # 09:00
  - cron: '0 10 * * 1-5'  # 18:00
  - cron: '0 5 * * 1-5'   # 13:00 (午休回來)
```

### Q: 如何取消某一天的執行？
A: 臨時停用 workflow 或使用 workflow_dispatch 手動控制。

### Q: 免費額度用完了怎麼辦？
A: 免費帳號每月 2000 分鐘，本專案用不到 1%。如真的用完，可等下個月或升級 GitHub Pro。

---

如有任何問題，請參考 [USAGE.md](../USAGE.md) 或查閱 GitHub Actions 官方文件。
