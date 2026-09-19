#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
archive.py — 歷史資料庫收集器（跟 radar.py 分開：radar 管「本週新東西」，archive 管「過去全部」）

  python archive.py                 跑所有任務，每個任務有時間預算，跑不完下次接著跑
  python archive.py --only ptt      只跑某一個任務（law / pcc / ptt）
  python archive.py --budget 40     這次總共最多跑幾分鐘（預設 45）

產出（全部在 archive/ 底下，CSV，方便任何人／Claude 下載後直接 grep）：
  archive/law/index.csv          全國法規（法律＋命令）總表：名稱、類別、最後修正日、是否廢止
  archive/law/fee_tables.csv     所有收費表類法規，按「多久沒改」排序 → 家族 A 死表／活表清單
  archive/law/time_signals.csv   條文裡帶「落日、過渡、屆滿、施行日期」的條文 → H-1 時間訊號
  archive/law/fulltext.jsonl.gz  全部條文全文（太大，不進 git，由 workflow 放到 GitHub Release）
  archive/pcc/YYYY/YYYYMM.csv    政府採購公告（招標、決標、無法決標…），2012 年起逐日回補
  archive/ptt/<版>/<年>.csv       PTT 各版歷年全部文章標題、推文數、連結，從最新往回補到開版
  archive/_state.json            各任務進度（跑到哪了），不要手動改
"""

import argparse
import csv
import datetime as dt
import gzip
import io
import json
import os
import re
import sys
import time
import zipfile

try:
    import requests
except ImportError:
    sys.exit("需要 requests：pip install requests")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
ROOT = "archive"
STATE = os.path.join(ROOT, "_state.json")
S = requests.Session()
S.headers.update({"User-Agent": UA, "Accept-Language": "zh-TW,zh;q=0.9"})
LOG = []


def log(msg):
    print(msg, flush=True)
    LOG.append(msg)


def get(url, **kw):
    last = None
    for i in range(3):
        try:
            r = S.get(url, timeout=kw.pop("timeout", 60), **kw)
            r.raise_for_status()
            return r
        except requests.exceptions.SSLError as e:
            last = e
            kw["verify"] = False
            requests.packages.urllib3.disable_warnings()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(3 * (i + 1))
    raise last


def append_csv(path, header, rows):
    if not rows:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(header)
        w.writerows(rows)


def write_csv(path, header, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


# ============================================================ 1. 全國法規資料庫

FEE_RE = re.compile(r"收費|費額|規費|費率|計費|酬金|報酬|收取.*費|費用.*標準|收費基準|價格")
TIME_RE = re.compile(r"落日|過渡期|過渡期間|屆滿|輔導期|緩衝期|施行日期|停止適用|自.{0,12}年.{0,6}月.{0,6}日(起|施行)")


def roc_to_date(s):
    s = re.sub(r"\D", "", str(s or ""))
    if len(s) == 8:
        return f"{s[:4]}-{s[4:6]}-{s[6:]}"
    return ""


def task_law(state, deadline):
    st = state.setdefault("law", {})
    if st.get("done_at") and (dt.datetime.now() - dt.datetime.fromisoformat(st["done_at"])).days < 7:
        log("[law] 7 天內已更新過，跳過")
        return
    today = dt.date.today()
    index, fees, signals, full = [], [], [], []
    for kind, url in [("法律", "https://law.moj.gov.tw/api/Ch/Law/JSON"),
                      ("命令", "https://law.moj.gov.tw/api/Ch/Order/JSON")]:
        log(f"[law] 下載 {kind}：{url}")
        r = get(url, timeout=300)
        data = r.content
        if data[:2] == b"PK":
            z = zipfile.ZipFile(io.BytesIO(data))
            name = [n for n in z.namelist() if n.lower().endswith(".json")][0]
            data = z.read(name)
        doc = json.loads(data.decode("utf-8-sig"))
        laws = doc.get("Laws") or doc.get("laws") or []
        log(f"[law] {kind} {len(laws)} 部，資料日期 {doc.get('UpdateDate')}")
        for L in laws:
            name = L.get("LawName", "")
            mod = roc_to_date(L.get("LawModifiedDate"))
            abandon = (L.get("LawAbandonNote") or "").strip()
            arts = L.get("LawArticles") or []
            url_ = L.get("LawURL", "")
            index.append([kind, L.get("LawLevel", ""), name, L.get("LawCategory", ""), mod,
                          roc_to_date(L.get("LawEffectiveDate")), abandon, len(arts), url_])
            if FEE_RE.search(name) and not abandon:
                age = ""
                if mod:
                    age = round((today - dt.date.fromisoformat(mod)).days / 365.25, 1)
                fees.append([age, mod, name, L.get("LawCategory", ""), kind, url_])
            for a in arts:
                txt = (a.get("ArticleContent") or "").replace("\r", "").replace("\n", " ")
                if not abandon and TIME_RE.search(txt):
                    m = TIME_RE.search(txt)
                    s0 = max(0, m.start() - 60)
                    signals.append([name, a.get("ArticleNo", ""), mod, txt[s0:m.end() + 80], url_])
            full.append({"kind": kind, "name": name, "category": L.get("LawCategory"),
                         "modified": mod, "abandon": abandon, "url": url_,
                         "histories": L.get("LawHistories"),
                         "articles": [[a.get("ArticleNo", ""), a.get("ArticleContent", "")] for a in arts]})
    fees.sort(key=lambda x: (x[0] == "", -(x[0] or 0)))
    write_csv(f"{ROOT}/law/index.csv",
              ["種類", "層級", "名稱", "類別", "最後修正日", "生效日", "廢止註記", "條數", "網址"], index)
    write_csv(f"{ROOT}/law/fee_tables.csv",
              ["幾年沒改", "最後修正日", "名稱", "類別", "種類", "網址"], fees)
    write_csv(f"{ROOT}/law/time_signals.csv",
              ["法規", "條號", "法規最後修正日", "條文片段", "網址"], signals)
    with gzip.open(f"{ROOT}/law/fulltext.jsonl.gz", "wt", encoding="utf-8") as f:
        for x in full:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    st["done_at"] = dt.datetime.now().isoformat(timespec="seconds")
    log(f"[law] 完成：總表 {len(index)}、收費表 {len(fees)}、時間訊號條文 {len(signals)}")


# ============================================================ 2. 政府採購（g0v 標案 API）

PCC = "https://pcc-api.openfun.app/api/listbydate?date={}"
PCC_START = dt.date(2012, 7, 1)


def task_pcc(state, deadline):
    st = state.setdefault("pcc", {})
    # 兩個方向：先補「最近」（往前追到今天），再往過去回補
    newest = dt.date.fromisoformat(st["newest"]) if st.get("newest") else None
    oldest = dt.date.fromisoformat(st["oldest"]) if st.get("oldest") else None
    today = dt.date.today()
    todo = []
    if newest is None:
        start = today - dt.timedelta(days=1)
        todo = [start - dt.timedelta(days=i) for i in range(0, 100000) if start - dt.timedelta(days=i) >= PCC_START]
    else:
        todo = [newest + dt.timedelta(days=i) for i in range(1, (today - newest).days)]
        todo += [oldest - dt.timedelta(days=i) for i in range(1, (oldest - PCC_START).days + 1)]
    n = 0
    for d in todo:
        if time.time() > deadline:
            break
        try:
            r = get(PCC.format(d.strftime("%Y%m%d")))
            recs = r.json().get("records") or []
        except Exception as e:  # noqa: BLE001
            log(f"[pcc] {d} 失敗：{type(e).__name__}: {str(e)[:120]}")
            st["errors"] = st.get("errors", 0) + 1
            if st["errors"] > 20:
                log("[pcc] 連續錯誤太多，這次先停")
                break
            continue
        rows = []
        for x in recs:
            b = x.get("brief") or {}
            comp = b.get("companies") or {}
            rows.append([d.isoformat(), b.get("type", ""), b.get("title", ""), b.get("category", ""),
                         x.get("unit_name", ""), "|".join(comp.get("names") or []),
                         x.get("url", ""), x.get("tender_api_url", "")])
        append_csv(f"{ROOT}/pcc/{d.year}/{d.strftime('%Y%m')}.csv",
                   ["日期", "公告類型", "標案名稱", "標的分類", "機關", "廠商", "網址", "明細API"], rows)
        if newest is None or d > newest:
            newest = d
        if oldest is None or d < oldest:
            oldest = d
        st["newest"], st["oldest"] = newest.isoformat(), oldest.isoformat()
        n += 1
        time.sleep(0.8)
    log(f"[pcc] 本次補了 {n} 天；目前涵蓋 {st.get('oldest')} ~ {st.get('newest')}")


# ============================================================ 3. PTT 各版全歷史

PTT_BOARDS = ["Lifeismoney", "home-sale", "e-shopping", "car", "Insurance", "BabyMother",
              "PublicServan", "Salary", "Hsinchu", "Tech_Job", "Boss_Life", "Soft_Job",
              "Accounting", "Tax", "Lawyer", "Rent_tao", "MobilePay", "Stock"]
ENT_RE = re.compile(r'<div class="r-ent">(.*?)<div class="mark">', re.S)
NREC_RE = re.compile(r'<div class="nrec">(?:<span[^>]*>)?([^<]*)')
TITLE_RE = re.compile(r'<a href="(/bbs/[^"]+/M\.(\d+)\.[^"]+)">(.*?)</a>', re.S)
PREV_RE = re.compile(r'href="/bbs/[^/]+/index(\d+)\.html">[^<]*上頁')


def nrec_num(s):
    s = s.strip()
    if s == "爆":
        return 100
    if s.startswith("X"):
        return -10 if s == "XX" else -int(s[1:] or 1) * 10
    return int(s) if s.isdigit() else 0


def ptt_page(board, n):
    r = get(f"https://www.ptt.cc/bbs/{board}/index{n}.html", cookies={"over18": "1"})
    rows = []
    for blk in ENT_RE.findall(r.text):
        t = TITLE_RE.search(blk)
        if not t:
            continue   # 被刪除的文
        ts = int(t.group(2))
        rows.append([dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M"),
                     nrec_num((NREC_RE.search(blk) or [None, ""])[1]),
                     re.sub(r"\s+", " ", t.group(3)).strip(),
                     "https://www.ptt.cc" + t.group(1)])
    return r.text, rows


def task_ptt(state, deadline):
    st = state.setdefault("ptt", {})
    boards = PTT_BOARDS
    per_board = max(60.0, (deadline - time.time()) / max(1, len(boards)))
    for b in boards:
        if time.time() > deadline:
            break
        bst = st.setdefault(b, {})
        if bst.get("dead"):
            continue
        t_end = min(deadline, time.time() + per_board)
        try:
            r = get(f"https://www.ptt.cc/bbs/{b}/index.html", cookies={"over18": "1"})
        except Exception as e:  # noqa: BLE001
            bst["errors"] = bst.get("errors", 0) + 1
            if bst["errors"] >= 3:
                bst["dead"] = True
            log(f"[ptt] {b} 打不開：{type(e).__name__}（累計 {bst['errors']} 次）")
            continue
        m = PREV_RE.search(r.text)
        latest = int(m.group(1)) + 1 if m else 1
        high, low = bst.get("high"), bst.get("low")
        pages = []
        if high is None:
            pages = list(range(latest - 1, 0, -1))           # 第一次：從最新的完整頁往回
        else:
            pages = list(range(high + 1, latest))             # 先補新的
            pages += list(range(low - 1, 0, -1))              # 再往回補舊的
        done = 0
        for n in pages:
            if time.time() > t_end:
                break
            try:
                _, rows = ptt_page(b, n)
            except Exception:  # noqa: BLE001
                continue
            by_year = {}
            for row in rows:
                by_year.setdefault(row[0][:4], []).append(row)
            for y, rs in by_year.items():
                append_csv(f"{ROOT}/ptt/{b}/{y}.csv", ["時間", "推文數", "標題", "網址"], rs)
            high = n if high is None or n > high else high
            low = n if low is None or n < low else low
            bst["high"], bst["low"] = high, low
            done += 1
            time.sleep(0.5)
        log(f"[ptt] {b}：本次 {done} 頁；已涵蓋 index{bst.get('low')}~{bst.get('high')}（最新 {latest}）"
            + ("｜已補到開版" if bst.get("low") == 1 else ""))


# ============================================================ main

TASKS = {"law": task_law, "pcc": task_pcc, "ptt": task_ptt}
SHARE = {"law": 0.15, "pcc": 0.35, "ptt": 0.50}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=list(TASKS))
    ap.add_argument("--budget", type=float, default=45, help="分鐘")
    args = ap.parse_args()
    os.makedirs(ROOT, exist_ok=True)
    state = json.load(open(STATE, encoding="utf-8")) if os.path.exists(STATE) else {}
    t0 = time.time()
    total = args.budget * 60
    names = [args.only] if args.only else list(TASKS)
    for name in names:
        share = 1.0 if args.only else SHARE[name]
        deadline = min(t0 + total, time.time() + total * share)
        if name == "ptt":
            deadline = t0 + total           # 最後一個任務吃掉剩下的時間
        try:
            TASKS[name](state, deadline)
        except Exception as e:  # noqa: BLE001
            log(f"[{name}] 任務失敗：{type(e).__name__}: {str(e)[:200]}")
        with open(STATE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=1)
    state["last_run"] = dt.datetime.now().isoformat(timespec="seconds")
    state["last_log"] = LOG[-40:]
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
