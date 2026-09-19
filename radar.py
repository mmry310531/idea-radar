#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
radar.py — Idea 專案的「法規雷達」收集器

為什麼要有這支程式
------------------
Claude 每次做研究，光是「把網頁抓進來讀一遍」就會吃掉大部分的 token，
而其中九成的內容是「跟上次一樣，沒有異動」。
把「抓取 + 比對 + 只留下變動的部分」交給 Python 做，Claude 就只需要讀一份幾 KB 的摘要，
把 token 全部花在真正需要腦袋的地方：交叉撞擊與判斷。

另一個好處：Claude 的 WebFetch 被不少政府網站擋掉（robots / 403），
但這支程式用你自己的 IP 去抓，那些來源多半是通的。

它做三件事
----------
1. **清單型（list / feed）**：抓法規公告清單，跟上次比對，只輸出「新出現的項目」。
2. **數字型（numbers）**：抓固定頁面上的數字，存成 CSV 時間序列，數字變了才報。
   這就是 `00-運作規範.md` 裡 J-1 通則說的護城河——時間序列只能靠「比別人早開始記錄」取得，
   而這件事必須自動化，人不會記得每個月去看一次。
3. 產出 `digest-YYYY-MM-DD.md`，一份只有異動的摘要。沒異動就明講沒異動。

用法
----
    python3 radar.py                 # 正常跑一次
    python3 radar.py --init          # 第一次跑：建立基線，不產出摘要（因為全部都是「新的」）
    python3 radar.py --out DIR       # 指定輸出目錄（預設 ./out）
    python3 radar.py --config F      # 指定來源設定檔（預設 ./sources.json，不存在就用內建預設）

只依賴 requests：  pip install requests
"""

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    sys.exit("需要 requests：pip install requests")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# ---------------------------------------------------------------- 關鍵字

# 只有標題命中這些詞的項目才會進摘要。
# 這份清單是這個專案幾十輪研究累積出來的「哪種公告會長出點子」，
# 不是通用的法規關鍵字——會過期，要定期回頭改。
KEYWORDS = [
    # 錢的基準（家族 A / B-1 的溫床）
    "費率", "收費", "收費標準", "費額", "規費", "計價", "計費", "報酬", "酬金", "價格",
    "基準", "標準表", "附表", "對照表", "級距",
    # 表的生死（A-2c / L-1）
    "修正", "訂定", "廢止", "停止適用", "不再", "回歸市場", "自由化", "解除管制",
    # 時間訊號（H-1）
    "落日", "過渡", "輔導期", "宣導期", "施行日期", "分年", "期程", "屆期",
    "換發", "延展", "展延", "申請變更",
    # 義務與罰則（動機強度）
    "申報", "檢修", "查驗", "檢查", "登記", "備查", "罰鍰", "裁罰", "按次處罰",
    # 分類決定點（G-1）
    "分類", "分級", "類別", "等級", "認定",
]

NEG_KEYWORDS = ["人事", "任免", "獎懲", "褒揚", "更正錯誤", "訃聞"]

# ---------------------------------------------------------------- 預設來源

# type:
#   "list"    → 抓 HTML，用 item_re 抽出 (連結, 標題)
#   "numbers" → 抓 HTML，用 number_re 抽出具名數字，做時間序列
#
# 說明欄 why 是寫給未來的自己看的：這個來源為什麼值得每週看一次。
DEFAULT_SOURCES = [
    {
        "name": "行政院公報-最新",
        "type": "list",
        "url": "https://gazette.nat.gov.tw/egFront/",
        "item_re": r'<a[^>]+href="([^"]+)"[^>]*>([^<]{6,80})</a>',
        "why": "法規修正條文與附表的最佳來源。附表就是家族 A 的原料。",
    },
    {
        "name": "全國法規資料庫-最新訊息",
        "type": "list",
        "url": "https://law.moj.gov.tw/News/NewsList.aspx?tid=1",
        "item_re": r'<a[^>]+href="([^"]+)"[^>]*>([^<]{6,120})</a>',
        "why": "Claude 的 WebFetch 抓不到這個站（黑名單），但一般瀏覽器可以。這是解鎖來源。",
    },
    {
        "name": "內政部消防署-公告",
        "type": "list",
        "url": "https://www.nfa.gov.tw/cht/index.php?code=list&ids=20",
        "item_re": r'<a[^>]+href="([^"]+)"[^>]*>\s*([^<]{6,120}?)\s*</a>',
        "why": "#7 的主管機關。2028-06-22 消防設備暫行人員落日，任何鬆動都會先出現在這裡。",
    },
    {
        "name": "智財局-著作權集管費率審議",
        "type": "list",
        "url": "https://www.tipo.gov.tw/tw/np-853-1.html",
        "item_re": r'<a[^>]+href="([^"]+)"[^>]*>\s*([^<]{6,120}?)\s*</a>',
        "why": "#12 的核心。審議書會把「原申請 vs 審定」的砍幅算給你看，歷年砍幅 24%–90%。",
    },
    {
        "name": "財政部法規-執行業務者費用標準",
        "type": "list",
        "url": "https://law-out.mof.gov.tw/LawQuery.aspx",
        "item_re": r'<a[^>]+href="([^"]+)"[^>]*>\s*([^<]{6,120}?)\s*</a>',
        "why": "每年公告一次。程式設計 20% / 著作人 30% / 自行出版 75%，分類一次決定 55 個百分點。",
    },
]

# 數字型來源要逐一手工設定（每個頁面的 HTML 都不一樣），
# 這裡放一個範例格式，實際要用時把 enabled 改成 true 並把 regex 調對。
DEFAULT_NUMBER_SOURCES = [
    {
        "name": "彰化縣消防局-暫行人員執業執照清冊",
        "type": "numbers",
        "enabled": False,
        "url": "https://www.chfd.gov.tw/form/index.aspx?Parser=3%2C9%2C324",
        # 具名擷取：key 是欄位名，value 是 regex（要有一個 group 抓數字）
        "number_re": {"清冊筆數": r"共\s*(\d[\d,]*)\s*筆"},
        "why": "J-1 時間序列。落日前逐年往下掉的人數，只能靠比別人早開始記錄取得。",
    },
]

# ---------------------------------------------------------------- 工具

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def clean(s: str) -> str:
    s = TAG_RE.sub("", s)
    s = (s.replace("&nbsp;", " ").replace("&amp;", "&")
          .replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"'))
    return WS_RE.sub(" ", s).strip()


def hit(title: str) -> bool:
    if any(n in title for n in NEG_KEYWORDS):
        return False
    return any(k in title for k in KEYWORDS)


def key_of(url: str, title: str) -> str:
    return hashlib.sha1((url + "|" + title).encode("utf-8")).hexdigest()[:16]


WARNINGS = []   # 非致命的狀況，會寫進摘要最後面


def fetch(url: str, timeout: int = 30, retries: int = 2) -> str:
    last = None
    verify = True
    for i in range(retries + 1):
        try:
            r = requests.get(url, headers={"User-Agent": UA,
                                           "Accept-Language": "zh-TW,zh;q=0.9"},
                             timeout=timeout, verify=verify)
            r.raise_for_status()
            # 政府網站常常沒宣告或宣告錯編碼
            if not r.encoding or r.encoding.lower() in ("iso-8859-1", "ascii"):
                r.encoding = r.apparent_encoding or "utf-8"
            return r.text
        except requests.exceptions.SSLError as e:
            # 不少政府網站漏掛中繼憑證（例如消防署），瀏覽器會自己補、Python 不會。
            # 這裡只是「讀公開網頁」，不送任何帳密，所以退一步不驗證憑證，並記一筆。
            last = e
            if verify:
                verify = False
                requests.packages.urllib3.disable_warnings()
                WARNINGS.append(f"{url}：憑證鏈不完整，已改用不驗證憑證的方式讀取")
                continue
            if i < retries:
                time.sleep(2 * (i + 1))
        except Exception as e:          # noqa: BLE001
            last = e
            if i < retries:
                time.sleep(2 * (i + 1))
    raise last


# ---------------------------------------------------------------- 各型處理

def do_list(src: dict, seen: set) -> tuple[list, list]:
    """回傳 (命中關鍵字的未見項目, 錯誤訊息)。項目是 dict(title, url)。"""
    try:
        html = fetch(src["url"])
    except Exception as e:                              # noqa: BLE001
        return [], [f"{src['name']}：抓取失敗 — {type(e).__name__}: {e}"]

    pat = re.compile(src.get("item_re", r'<a[^>]+href="([^"]+)"[^>]*>([^<]{6,120})</a>'),
                     re.I | re.S)
    fresh, dedup = [], set()
    links = pat.findall(html)
    if not links:
        # 這是最危險的失敗：它不會報錯，只會每週安靜地回報「無異動」。
        return [], [f"{src['name']}：頁面抓到了，但一個連結都沒抽出來"
                    f"（{len(html)} 字元）——item_re 或網站改版，要修"]
    for href, raw_title in links:
        title = clean(raw_title)
        if len(title) < 6 or not hit(title):
            continue
        url = urljoin(src["url"], href.strip())
        k = key_of(url, title)
        if k in seen or k in dedup:
            continue
        dedup.add(k)
        fresh.append({"key": k, "title": title, "url": url, "source": src["name"]})
    return fresh, []


def do_numbers(src: dict, state: dict, history_dir: str) -> tuple[list, list]:
    """回傳 (變動清單, 錯誤訊息)。同時把每次的值追加進 CSV。"""
    try:
        html = fetch(src["url"])
    except Exception as e:                              # noqa: BLE001
        return [], [f"{src['name']}：抓取失敗 — {type(e).__name__}: {e}"]

    today = dt.date.today().isoformat()
    prev = state.get("numbers", {}).get(src["name"], {})
    changes, row = [], {"date": today}

    for field, rx in src.get("number_re", {}).items():
        m = re.search(rx, html, re.S)
        if not m:
            continue
        val = m.group(1).replace(",", "")
        row[field] = val
        old = prev.get(field)
        if old is not None and old != val:
            changes.append({"source": src["name"], "field": field,
                            "old": old, "new": val, "url": src["url"]})
        prev[field] = val

    state.setdefault("numbers", {})[src["name"]] = prev

    if len(row) > 1:
        os.makedirs(history_dir, exist_ok=True)
        safe = re.sub(r"[^\w一-鿿-]", "_", src["name"])
        path = os.path.join(history_dir, f"{safe}.csv")
        new_file = not os.path.exists(path)
        with open(path, "a", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(row.keys()))
            if new_file:
                w.writeheader()
            w.writerow(row)
    return changes, []


# ---------------------------------------------------------------- 摘要

def write_digest(out_dir, items, changes, errors, n_sources, init):
    today = dt.date.today().isoformat()
    path = os.path.join(out_dir, f"digest-{today}.md")
    L = [f"# 法規雷達摘要 {today}", ""]
    L.append(f"掃描來源 {n_sources} 個｜命中關鍵字的新項目 {len(items)} 筆｜數字異動 {len(changes)} 筆")
    L.append("")
    if init:
        L += ["> **本次為 `--init` 基線建立**，上面的數字只代表目前站上有多少符合條件的項目，",
              "> 不代表它們是新的。從下次開始才會有真正的「異動」。", ""]

    if changes:
        L += ["## ⚠ 數字異動（優先看，這是時間序列）", ""]
        for c in changes:
            L.append(f"- **{c['source']} / {c['field']}**：`{c['old']}` → `{c['new']}`  ")
            L.append(f"  <{c['url']}>")
        L.append("")

    if items:
        L += ["## 新公告", ""]
        by_src = {}
        for it in items:
            by_src.setdefault(it["source"], []).append(it)
        for name, lst in by_src.items():
            L.append(f"### {name}（{len(lst)}）")
            for it in lst:
                L.append(f"- {it['title']}  ")
                L.append(f"  <{it['url']}>")
            L.append("")
    elif not changes:
        L += ["## 本週無異動", "",
              "沒有命中關鍵字的新公告，追蹤中的數字也沒有變。",
              "這是有訊息量的結果，不是失敗——代表這幾個來源這週是靜止的。", ""]

    if errors:
        L += ["## 抓取失敗（下次要修）", ""]
        L += [f"- {e}" for e in errors]
        L.append("")

    if WARNINGS:
        L += ["## 備註", ""]
        L += [f"- {w}" for w in WARNINGS]
        L.append("")

    os.makedirs(out_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    return path


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="Idea 專案法規雷達")
    ap.add_argument("--config", default="sources.json")
    ap.add_argument("--out", default="out")
    ap.add_argument("--state", default="state.json")
    ap.add_argument("--init", action="store_true",
                    help="建立基線：把目前站上所有項目標記為已見過")
    args = ap.parse_args()

    if os.path.exists(args.config):
        with open(args.config, encoding="utf-8") as f:
            sources = json.load(f)
    else:
        sources = DEFAULT_SOURCES + DEFAULT_NUMBER_SOURCES
        with open(args.config, "w", encoding="utf-8") as f:
            json.dump(sources, f, ensure_ascii=False, indent=2)
        print(f"[i] 沒有 {args.config}，已用內建預設建立一份，之後可以直接改那個檔。")

    state = {}
    if os.path.exists(args.state):
        with open(args.state, encoding="utf-8") as f:
            state = json.load(f)
    seen = set(state.get("seen", []))

    all_items, all_changes, errors = [], [], []
    # 舊版 state.json 沒有 baselined：有 seen 紀錄就把「上次沒失敗」的來源視為已建基線
    baselined = set(state.get("baselined", []))
    active = [s for s in sources if s.get("enabled", True)]

    for src in active:
        kind = src.get("type", "list")
        print(f"[.] {src['name']} ({kind})")
        if kind == "numbers":
            ch, err = do_numbers(src, state, os.path.join(args.out, "history"))
            all_changes += ch
        else:
            it, err = do_list(src, seen)
            if not err and src["name"] not in baselined:
                # 新加入（或過去都抓失敗）的來源：這次看到的全部當基線，不當成「新的」
                for x in it:
                    seen.add(x["key"])
                WARNINGS.append(f"{src['name']}：第一次抓成功，已建立基線（{len(it)} 筆），下次起才報異動")
                it = []
            if not err:
                baselined.add(src["name"])
            all_items += it
        errors += err
        time.sleep(1.5)          # 對政府網站客氣一點

    # 不管是不是 init，看過的都要記下來
    for it in all_items:
        seen.add(it["key"])
    state["baselined"] = sorted(baselined)
    state["seen"] = sorted(seen)[-20000:]          # 上限，免得無限長大
    state["last_run"] = dt.datetime.now().isoformat(timespec="seconds")
    with open(args.state, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    path = write_digest(args.out, [] if args.init else all_items,
                        all_changes, errors, len(active), args.init)
    print(f"[✓] 摘要：{path}")
    print(f"    新項目 {0 if args.init else len(all_items)}｜數字異動 {len(all_changes)}｜失敗 {len(errors)}")
    # 給 GitHub Actions 用：把摘要路徑交給下一步（寄信）
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write(f"digest={path}\n")
            f.write(f"failed={len(errors)}\n")


if __name__ == "__main__":
    main()
