#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
radar.py — Idea 專案的雷達收集器（v2，2026-09-19）

兩種模式
--------
  python radar.py --collect   每小時跑：抓「到期」的來源，新項目先存進 state.json 的 pending
  python radar.py --digest    每週跑：把一週累積的 pending 整理成一份摘要，然後清空

為什麼分兩段：PTT 熱門版一小時就洗掉一整頁，一週抓一次會漏掉大部分；
但摘要一小時寄一封會變垃圾信。所以「抓」高頻、「讀」低頻。

來源分三級（tier），摘要裡分開放，信任度不同：
  官方  政府公報、法規資料庫、主管機關公告 —— 可以直接當事實
  新聞  Google 新聞 RSS —— 事件存在的證據，但數字要回官方查
  社群  PTT —— 只當「有人在痛」的線索，**任何數字或說法都不能直接當事實**

只依賴 requests：pip install requests
"""

import argparse
import csv
import datetime as dt
import hashlib
import html as htmllib
import json
import os
import re
import sys
import time
from urllib.parse import urljoin, quote

try:
    import requests
except ImportError:
    sys.exit("需要 requests：pip install requests")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# ---------------------------------------------------------------- 關鍵字
# 依來源性質用不同的字典。官方用「錢與門檻」字；社群／新聞用「痛點」字。

KEYWORDS = {
    # 官方公告：只留跟錢、門檻、時間點直接相關的。
    # 單獨的「修正」「廢止」太廣（整份公報都會進來），已拿掉。
    "law": [
        "費率", "收費", "費額", "規費", "計價", "計費", "報酬", "酬金", "價格", "費用",
        "基準", "標準表", "附表", "對照表", "級距", "上限",
        "落日", "過渡", "輔導期", "宣導期", "施行日期", "分年", "期程", "屆期",
        "換發", "延展", "展延", "檢定", "證照", "資格", "執照",
        "申報", "檢修", "查驗", "罰鍰", "裁罰", "裁罰基準", "按次處罰",
        "自由化", "解除管制", "回歸市場", "停止適用", "分類", "分級", "認定",
        "限制使用", "禁用", "補助",
    ],
    # 社群與新聞：有人在抱怨、在問、在算。
    "pain": [
        "超收", "多收", "亂收", "被收", "收費", "費用", "價格", "報價", "行情", "合理嗎",
        "太貴", "好貴", "漲價", "退費", "罰單", "被罰", "罰款", "罰鍰", "糾紛", "申訴",
        "檢舉", "客訴", "新制", "上路", "規定", "補助", "怎麼算", "看不懂", "請益",
        "要付", "要錢", "收據", "發票", "違法嗎", "有沒有規定",
    ],
}

NEG_KEYWORDS = ["人事", "任免", "獎懲", "褒揚", "更正錯誤", "訃聞",
                "公示送達", "處分書", "處務規程", "居留許可",
                "[公告]", "置底", "版規", "徵才", "[協尋]"]

# ---------------------------------------------------------------- 預設來源

def gnews(q):
    return ("https://news.google.com/rss/search?q=" + quote(q + " when:7d")
            + "&hl=zh-TW&gl=TW&ceid=TW:zh-Hant")

A = r'<a[^>]+href="([^"]+)"[^>]*>\s*([^<]{6,120}?)\s*</a>'

DEFAULT_SOURCES = [
    # ---- 官方（一天抓一次就夠，對政府網站客氣一點）
    {"name": "行政院公報-最新", "tier": "官方", "type": "list", "every_hours": 24,
     "url": "https://gazette.nat.gov.tw/egFront/", "item_re": A, "keywords": "law",
     "why": "法規修正條文與附表的最佳來源。附表就是家族 A 的原料。"},
    {"name": "全國法規資料庫-最新訊息", "tier": "官方", "type": "list", "every_hours": 24,
     "url": "https://law.moj.gov.tw/News/NewsList.aspx?tid=1", "item_re": A, "keywords": "law",
     "why": "Claude 的 WebFetch 抓不到這個站，但一般瀏覽器可以。"},
    {"name": "內政部消防署-法規動態", "tier": "官方", "type": "list", "every_hours": 24,
     "url": "https://www.nfa.gov.tw/cht/index.php?code=list&ids=23", "item_re": A, "keywords": "law",
     "why": "#7 的主管機關。2028-06-22 消防設備暫行人員落日。"},
    {"name": "內政部消防署-行政公告", "tier": "官方", "type": "list", "every_hours": 24,
     "url": "https://www.nfa.gov.tw/cht/index.php?code=list&ids=21", "item_re": A, "keywords": "law",
     "why": "同上。"},
    {"name": "智財局-首頁", "tier": "官方", "type": "list", "every_hours": 24,
     "url": "https://www.tipo.gov.tw/tw/", "item_re": A, "keywords": "law",
     "why": "#12。集管費率審議公告會出現在這裡。"},
    {"name": "財政部法規-執行業務者費用標準", "tier": "官方", "type": "list", "every_hours": 24,
     "url": "https://law-out.mof.gov.tw/LawQuery.aspx", "item_re": A, "keywords": "law",
     "why": "每年公告一次，分類一次決定 55 個百分點。"},

    # ---- 新聞（Google 新聞 RSS，一天抓一次；查詢詞綁點子池）
    *[{"name": f"新聞：{q}", "tier": "新聞", "type": "feed", "every_hours": 24,
       "url": gnews(q), "keywords": "all", "why": why}
      for q, why in [
          ("收費標準 修正", "家族 A：收費表改版。"),
          ("落日條款 業者", "H-1：帶日期的時間訊號。"),
          ("過渡期 屆滿 業者", "H-1。"),
          ("超收 消保官", "家族 A／B：有人被多收錢，而且已經鬧到官方。"),
          ("新制上路 罰款", "義務＋罰則＝動機強度。"),
          ("公播 著作權 店家", "#12 店家播音樂。"),
          ("時間電價", "#15。"),
          ("消防安全設備 檢修 費用", "#7。"),
          ("履約保證", "#13。"),
          ("調解 爭議 免費", "#14。"),
      ]],

    # ---- 社群（PTT 的 Atom 訂閱，每小時抓，因為熱門版一頁很快被洗掉）
    *[{"name": f"PTT：{b}", "tier": "社群", "type": "feed", "every_hours": 1,
       "url": f"https://www.ptt.cc/atom/{b}.xml", "keywords": "pain", "why": why}
      for b, why in [
          ("Lifeismoney", "省錢版：價差、被多收、比價——家族 B 的溫床。"),
          ("home-sale", "房地產：規費、仲介費、稅費怎麼算。"),
          ("e-shopping", "網購糾紛與退費。"),
          ("car", "汽車：罰單、規費、驗車、保險。"),
          ("Insurance", "保險理賠爭議（注意 #10 已冷凍，只當線索）。"),
          ("BabyMother", "育兒補助與規定，家長算不清楚的東西很多。"),
          ("PublicServan", "公務員版：規定在第一線怎麼被執行、哪裡卡住。"),
          ("Salary", "職場：勞基法、加班費、資遣費怎麼算。"),
          ("Hsinchu", "在地：竹北新竹生活與店家。"),
      ]],
]

DEFAULT_NUMBER_SOURCES = [
    {"name": "彰化縣消防局-暫行人員執業執照清冊", "tier": "官方", "type": "numbers",
     "enabled": True, "every_hours": 24,
     "url": "https://www.chfd.gov.tw/form/index.aspx?Parser=3%2C9%2C324",
     "number_re": {"清冊筆數": r"共\s*(\d[\d,]*)\s*筆"},
     "why": "J-1 時間序列。2028 落日前逐年往下掉的人數，只能靠比別人早開始記錄取得。"},
]

# ---------------------------------------------------------------- 工具

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")
WARN = []


def clean(s):
    s = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", s, flags=re.S)
    s = htmllib.unescape(TAG_RE.sub("", s))
    return WS_RE.sub(" ", s).strip()


def hit(title, profile):
    if any(n in title for n in NEG_KEYWORDS):
        return False
    if profile == "all":
        return True
    return any(k in title for k in KEYWORDS.get(profile, KEYWORDS["law"]))


def key_of(url, title):
    return hashlib.sha1((url + "|" + title).encode("utf-8")).hexdigest()[:16]


def now():
    return dt.datetime.now()


def fetch(url, timeout=30, retries=2):
    last, verify = None, True
    cookies = {"over18": "1"} if "ptt.cc" in url else None
    for i in range(retries + 1):
        try:
            r = requests.get(url, headers={"User-Agent": UA, "Accept-Language": "zh-TW,zh;q=0.9"},
                             timeout=timeout, verify=verify, cookies=cookies)
            r.raise_for_status()
            if not r.encoding or r.encoding.lower() in ("iso-8859-1", "ascii"):
                r.encoding = r.apparent_encoding or "utf-8"
            return r.text
        except requests.exceptions.SSLError as e:
            # 政府網站常漏掛中繼憑證；只讀公開頁、不送帳密，退一步不驗證並記下
            last = e
            if verify:
                verify = False
                requests.packages.urllib3.disable_warnings()
                WARN.append(f"{url}：憑證鏈不完整，已改用不驗證憑證的方式讀取")
                continue
        except Exception as e:  # noqa: BLE001
            last = e
        if i < retries:
            time.sleep(2 * (i + 1))
    raise last


# ---------------------------------------------------------------- 解析

ITEM_RE = re.compile(r"<(item|entry)\b.*?</\1>", re.S | re.I)


def parse_feed(xml):
    """RSS <item> 或 Atom <entry> → [(url, title, publisher)]"""
    out = []
    for m in ITEM_RE.finditer(xml):
        blk = m.group(0)
        t = re.search(r"<title[^>]*>(.*?)</title>", blk, re.S)
        l = (re.search(r'<link[^>]+href="([^"]+)"', blk)
             or re.search(r"<link>(.*?)</link>", blk, re.S))
        src = re.search(r"<source[^>]*>(.*?)</source>", blk, re.S)
        if t and l:
            out.append((clean(l.group(1)), clean(t.group(1)), clean(src.group(1)) if src else ""))
    return out


def extract(src, text):
    if src.get("type") == "feed":
        return parse_feed(text)
    pat = re.compile(src.get("item_re", A), re.I | re.S)
    return [(urljoin(src["url"], htmllib.unescape(h.strip())), clean(t), "")
            for h, t in pat.findall(text)]


# ---------------------------------------------------------------- 收集

def collect(sources, state, out_dir, force=False):
    seen = set(state.get("seen", []))
    baselined = set(state.get("baselined", []))
    last = state.setdefault("last_fetch", {})
    pending = state.setdefault("pending", [])
    changes = state.setdefault("pending_changes", [])
    errs = state.setdefault("errors", {})
    notes = state.setdefault("notes", [])
    n_new = 0

    for src in sources:
        if not src.get("enabled", True):
            continue
        name = src["name"]
        every = float(src.get("every_hours", 24))
        prev = last.get(name)
        if not force and prev and (now() - dt.datetime.fromisoformat(prev)).total_seconds() < every * 3600 - 300:
            continue
        print(f"[.] {name}")
        try:
            text = fetch(src["url"])
        except Exception as e:  # noqa: BLE001
            errs.setdefault(name, {"count": 0})
            errs[name]["count"] += 1
            errs[name]["last"] = f"{type(e).__name__}: {str(e)[:160]}"
            continue
        last[name] = now().isoformat(timespec="seconds")

        if src.get("type") == "numbers":
            changes += do_numbers(src, text, state, os.path.join(out_dir, "history"))
            errs.pop(name, None)
            continue

        rows = extract(src, text)
        if not rows:
            errs.setdefault(name, {"count": 0})
            errs[name]["count"] += 1
            errs[name]["last"] = f"頁面抓到了但一個項目都沒抽出來（{len(text)} 字元）——網址或 item_re 要修"
            continue
        errs.pop(name, None)

        first = name not in baselined
        got = 0
        for url, title, publisher in rows:
            if len(title) < 6 or not hit(title, src.get("keywords", "law")):
                continue
            k = key_of(url, title)
            if k in seen:
                continue
            seen.add(k)
            if first:
                continue
            pending.append({"source": name, "tier": src.get("tier", "官方"), "title": title,
                            "url": url, "publisher": publisher,
                            "at": now().isoformat(timespec="minutes")})
            got += 1
        if first:
            notes.append(f"{name}：第一次抓成功，已建立基線，下次起才報新項目")
            baselined.add(name)
        n_new += got
        time.sleep(1.5)

    state["seen"] = sorted(seen)[-50000:]
    state["baselined"] = sorted(baselined)
    for w in WARN:
        if w not in notes:
            notes.append(w)
    return n_new


def do_numbers(src, text, state, history_dir):
    today = dt.date.today().isoformat()
    prev = state.setdefault("numbers", {}).setdefault(src["name"], {})
    changes, row = [], {"date": today}
    for field, rx in src.get("number_re", {}).items():
        m = re.search(rx, text, re.S)
        if not m:
            continue
        val = m.group(1).replace(",", "")
        row[field] = val
        if prev.get(field) is not None and prev[field] != val:
            changes.append({"source": src["name"], "field": field, "old": prev[field],
                            "new": val, "url": src["url"], "at": today})
        prev[field] = val
    if len(row) > 1:
        os.makedirs(history_dir, exist_ok=True)
        path = os.path.join(history_dir, re.sub(r"[^\w一-鿿-]", "_", src["name"]) + ".csv")
        new_file = not os.path.exists(path)
        with open(path, "a", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(row.keys()))
            if new_file:
                w.writeheader()
            w.writerow(row)
    return changes


# ---------------------------------------------------------------- 摘要

TIER_HEAD = {
    "官方": "## 一、官方公告（可以直接當事實）",
    "新聞": "## 二、新聞（事件存在的證據；數字要回官方原文核對）",
    "社群": "## 三、社群線索（⚠ 未查證，只代表「有人在痛」，不能當事實引用）",
}
PER_SOURCE_CAP = 15


def digest(state, out_dir, n_sources):
    today = dt.date.today().isoformat()
    items, changes = state.get("pending", []), state.get("pending_changes", [])

    # 同一個網址只留一次；新聞的同一事件被幾家報導只列一次，記下家數當佐證強度
    def head(t):
        return re.sub(r"\s*-\s*[^-]+$", "", t)[:18]
    uniq, urls, heads = [], set(), {}
    for it in items:
        if it["url"] in urls:
            continue
        urls.add(it["url"])
        if it["tier"] == "新聞":
            h = head(it["title"])
            if h in heads:
                heads[h]["pubs"].add(it.get("publisher") or it["url"])
                continue
            it = dict(it, pubs={it.get("publisher") or it["url"]})
            heads[h] = it
        uniq.append(it)

    L = [f"# 雷達摘要 {today}", "",
         f"掃描來源 {n_sources} 個｜本週新項目 {len(uniq)} 筆｜數字異動 {len(changes)} 筆", ""]

    if changes:
        L += ["## ⚠ 數字異動（優先看，這是時間序列）", ""]
        for c in changes:
            L.append(f"- **{c['source']} / {c['field']}**：`{c['old']}` → `{c['new']}`（{c['at']}） <{c['url']}>")
        L.append("")

    for tier in ("官方", "新聞", "社群"):
        lst = [x for x in uniq if x["tier"] == tier]
        if not lst:
            continue
        L += [TIER_HEAD[tier], ""]
        by_src = {}
        for it in lst:
            by_src.setdefault(it["source"], []).append(it)
        for name, xs in by_src.items():
            shown = xs[-PER_SOURCE_CAP:]
            more = f"，只列最新 {PER_SOURCE_CAP}" if len(xs) > PER_SOURCE_CAP else ""
            L.append(f"### {name}（{len(xs)}{more}）")
            for it in shown:
                extra = ""
                if tier == "新聞" and len(it.get("pubs", ())) >= 2:
                    extra = f"  〔{len(it['pubs'])} 家媒體報導〕"
                L.append(f"- {it['title']}{extra}  ")
                L.append(f"  <{it['url']}>")
            L.append("")

    if not uniq and not changes:
        L += ["## 本週無異動", "", "沒有命中關鍵字的新項目，追蹤中的數字也沒有變。", ""]

    errs = state.get("errors", {})
    if errs:
        L += ["## 抓取失敗（下次要修）", ""]
        for name, e in errs.items():
            L.append(f"- {name}：本週失敗 {e['count']} 次 — {e.get('last','')}")
        L.append("")
    if state.get("notes"):
        L += ["## 備註", ""] + [f"- {n}" for n in state["notes"]] + [""]

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"digest-{today}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    state["pending"], state["pending_changes"], state["notes"] = [], [], []
    state["errors"] = {}
    state["last_digest"] = now().isoformat(timespec="seconds")
    return path, len(errs)


# ---------------------------------------------------------------- main

def load_sources(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    s = DEFAULT_SOURCES + DEFAULT_NUMBER_SOURCES
    with open(path, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)
    return s


def main():
    ap = argparse.ArgumentParser(description="Idea 專案雷達")
    ap.add_argument("--config", default="sources.json")
    ap.add_argument("--out", default="out")
    ap.add_argument("--state", default="state.json")
    ap.add_argument("--collect", action="store_true", help="抓到期的來源，累積進 pending")
    ap.add_argument("--digest", action="store_true", help="先抓一輪（全部），再產生摘要並清空 pending")
    args = ap.parse_args()
    if not (args.collect or args.digest):
        args.collect = True

    sources = load_sources(args.config)
    state = {}
    if os.path.exists(args.state):
        with open(args.state, encoding="utf-8") as f:
            state = json.load(f)
    state.setdefault("pending", [])

    n = collect(sources, state, args.out, force=args.digest)
    print(f"[✓] 本次新項目 {n}｜累積待讀 {len(state['pending'])}")

    gh = os.environ.get("GITHUB_OUTPUT")
    if args.digest:
        active = sum(1 for s in sources if s.get("enabled", True))
        path, nerr = digest(state, args.out, active)
        print(f"[✓] 摘要：{path}")
        if gh:
            with open(gh, "a", encoding="utf-8") as f:
                f.write(f"digest={path}\nfailed={nerr}\n")

    state["last_run"] = now().isoformat(timespec="seconds")
    with open(args.state, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
