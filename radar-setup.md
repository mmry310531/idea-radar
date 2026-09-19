# 法規雷達（radar.py）怎麼架

## 為什麼要拆成兩半

一輪研究的 token，大部分不是花在「想」，是花在「把網頁抓進來讀一遍」，
而其中九成內容跟上次一模一樣。

所以把工作拆開：

| | 誰做 | 成本 |
|---|---|---|
| 抓網頁、跟上次比對、丟掉沒變的 | **Python（radar.py）** | 幾乎為零 |
| 讀那份只剩異動的摘要、做交叉撞擊、下判斷 | **Claude** | 貴，但花在刀口上 |

**⚠ 關鍵限制：`radar.py` 不能跑在 Claude 的雲端容器裡。**
那個容器的對外連線走一個有白名單的閘道，只放行 pypi / npm 這類套件庫，
一般網站一律回 403（已實測 `gazette.nat.gov.tw`）。
Claude 的 WebFetch 走的是另一條路，所以「WebFetch 抓得到、Python 抓不到」是正常的，不是設定壞掉。

**附帶好處**：`30-已探索主題.md` 裡那份「擋 fetch 的黑名單」，有一半是擋 Claude 而不是擋瀏覽器。
`law.moj.gov.tw`（全國法規資料庫）、`data.gov.tw`、台電全站、`mydata.nat.gov.tw` 這些
目前這個代理人根本讀不到的來源，從自己的 IP 用 Python 抓多半是通的。
**所以這支程式不只省 token，它會解鎖現在讀不到的來源。**

---

## 方案 A：GitHub Actions（推薦）

不需要電腦開著，免費，而且產出天然就有版本紀錄——
`git log` 本身就是 J-1 通則要的那條時間序列。

1. 開一個 private repo，例如 `idea-radar`。
2. 放進 `radar.py`。
3. 建 `.github/workflows/radar.yml`：

```yaml
name: radar
on:
  schedule:
    - cron: "0 19 * * 1"      # UTC 19:00 = 台北週二 03:00
  workflow_dispatch:           # 也可以手動按一下就跑

permissions:
  contents: write

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install requests
      - run: python radar.py --out out
      - name: commit
        run: |
          git config user.name  "radar"
          git config user.email "radar@users.noreply.github.com"
          git add -A
          git diff --staged --quiet || git commit -m "radar $(date -u +%F)"
          git push
```

4. 第一次先在本機或用 `workflow_dispatch` 跑一次 `python radar.py --init`，
   建立基線（否則第一份摘要會把站上所有東西都當成「新的」）。

5. Claude 這邊怎麼讀到摘要：
   - repo 設 public 的話，最省事——直接 WebFetch
     `https://raw.githubusercontent.com/<你>/idea-radar/main/out/digest-YYYY-MM-DD.md`
   - 想保持 private，就把 `out/` 那個資料夾同步到 Google Drive（你已經接了 Drive connector），
     Claude 用 `mcp__Google_Drive__search_files` 找當週的 digest 再讀。

## 方案 B：自己的電腦

Windows 用「工作排程器」、Mac/Linux 用 `cron`：

```
# 每週二 03:00
0 3 * * 2  cd ~/idea-radar && /usr/bin/python3 radar.py --out out >> radar.log 2>&1
```

把 `out/` 設成 Google Drive 同步資料夾裡的一個目錄，Claude 就讀得到。
缺點是電腦要開著。

---

## 設定檔怎麼改

第一次執行會自動生出 `sources.json`，之後直接改那個檔。

**清單型**（抓公告列表，只報新出現的）：

```json
{
  "name": "內政部營建署-公告",
  "type": "list",
  "url": "https://xxx.gov.tw/list",
  "item_re": "<a[^>]+href=\"([^\"]+)\"[^>]*>\\s*([^<]{6,120}?)\\s*</a>",
  "why": "為什麼這個來源值得每週看一次——寫給未來的自己"
}
```

`item_re` 要抓到兩個 group：第一個是連結、第二個是標題。
不同網站的 HTML 都不一樣，**設好之後一定要跑一次確認有抓到東西**，
不然它會安靜地每週回報「無異動」，而你以為它在工作。

**數字型**（追一個數字的變化，這是最有價值的一型）：

```json
{
  "name": "彰化縣消防局-暫行人員清冊",
  "type": "numbers",
  "enabled": true,
  "url": "https://www.chfd.gov.tw/form/index.aspx?Parser=3%2C9%2C324",
  "number_re": { "清冊筆數": "共\\s*(\\d[\\d,]*)\\s*筆" },
  "why": "J-1 時間序列。2028 落日前逐年往下掉的人數。"
}
```

每次執行都會把值追加進 `out/history/<來源名>.csv`，數字變了才會出現在摘要裡。
**這份 CSV 就是護城河本身**——任何人都可以現在去查那一頁今天的數字，
但沒有人可以回頭跟你要「過去三年每一次改版的紀錄」。

## 關鍵字清單

`radar.py` 開頭的 `KEYWORDS` 決定什麼會進摘要。
那份清單是這個專案幾十輪研究累積出來的「哪種公告會長出點子」，
**不是通用的法規關鍵字，會過期，要定期回頭改。**
覺得摘要太吵就加 `NEG_KEYWORDS`；覺得漏掉東西就翻 `00-運作規範.md` 的 Step 3 搜尋詞庫補進去。
