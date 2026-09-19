# idea-radar

每週自動掃一次政府公告，只把「新出現、而且命中關鍵字」的項目寫成摘要。
Claude 每週的點子研究輪讀這份摘要，不再自己抓網頁，省下 AI 額度。

- 排程：台北每週二 00:17（`.github/workflows/radar.yml`）
- 產出：`out/digest-YYYY-MM-DD.md`、`out/history/*.csv`（數字型來源的時間序列）
- 記憶：`state.json`（看過哪些項目）—— 由 Actions 自動提交回來，不要手動刪
- 來源：`sources.json`，改完推上來即可，新來源第一次會自動建基線、不會洗版
- 手動跑一次：Actions 分頁 → radar → Run workflow

寄信（選用）：在 Settings → Secrets and variables → Actions 加
`MAIL_USER`（Gmail 地址）與 `MAIL_APP_PASSWORD`（Google 應用程式密碼），
每次跑完會寄一份摘要給自己。沒設就只提交到 repo。
