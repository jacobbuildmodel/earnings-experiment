"""D003 S1 - the season screen.

    python pipeline/s1_screen.py <season> nasdaq     # capture slot only: pull the Nasdaq calendar
    (Alpha Vantage calendar is saved by hand from the MCP tool to universe/<season>/raw/av_calendar.csv)
    python pipeline/s1_screen.py <season> market     # capture slot only: yfinance quote data for the union
    python pipeline/s1_screen.py <season> screen     # any time after: SEC + filing tests -> candidates.json
    python pipeline/s1_screen.py <season>|active midseason   # Fridays (D003 §7): new calendar names through S1

Rule source: registry/D003_universe_screen_v1.json (hash-checked). Raw captures are write-once.
"""
import csv
import datetime
import io
import json
import os
import re
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, WEB_HEADERS, Sec, now_et, registry, write_json, write_once  # noqa: E402

RULE = registry("D003_universe_screen_v1.json")
EXCHANGES = {"NMS": "Nasdaq", "NGM": "Nasdaq", "NCM": "Nasdaq", "NYQ": "NYSE", "ASE": "NYSE American"}
PERIODIC = {"10-K", "10-Q", "10-K/A", "10-Q/A", "20-F", "40-F", "20-F/A", "40-F/A"}
DOMESTIC = {"10-K", "10-Q", "10-K/A", "10-Q/A"}


def dirs(season):
    base = os.path.join(ROOT, "universe", season)
    return base, os.path.join(base, "raw")


def in_slot(season):
    lo, hi = (datetime.datetime.fromisoformat(x).replace(tzinfo=now_et().tzinfo)
              for x in RULE["seasons"][season]["capture_et"])
    now = now_et()
    if not lo <= now <= hi:
        raise SystemExit(f"ET {now:%Y-%m-%d %H:%M} is outside the {season} capture slot {lo} - {hi}. "
                         "D003 §2: a capture outside its slot does not count.")
    return now


def span(season):
    start, end = (datetime.date.fromisoformat(x) for x in RULE["seasons"][season]["window"])
    return start - datetime.timedelta(days=3), end + datetime.timedelta(days=3)


def capture_nasdaq(season):
    now = in_slot(season)
    _, raw = dirs(season)
    lo, hi = span(season)
    out = {"source": "nasdaq", "captured_et": now.isoformat(), "days": {}}
    d = lo
    while d <= hi:
        if d.weekday() < 5:
            r = requests.get("https://api.nasdaq.com/api/calendar/earnings",
                             params={"date": d.isoformat()}, headers=WEB_HEADERS, timeout=30)
            r.raise_for_status()
            out["days"][d.isoformat()] = (r.json().get("data") or {}).get("rows") or []
            time.sleep(1)
        d += datetime.timedelta(days=1)
    write_once(os.path.join(raw, "nasdaq_calendar.json"), out)
    print(f"nasdaq: {sum(len(v) for v in out['days'].values())} rows over {len(out['days'])} days")


def calendar_union(season):
    _, raw = dirs(season)
    lo, hi = span(season)
    rows = {}
    nas = json.load(open(os.path.join(raw, "nasdaq_calendar.json"), encoding="utf-8"))
    for day, items in nas["days"].items():
        for it in items:
            t = it["symbol"].strip().upper()
            rows.setdefault(t, {"ticker": t, "sources": {}})["sources"].setdefault("nasdaq", []).append(
                {"date": day, "time": it.get("time"), "marketCap": it.get("marketCap"), "name": it.get("name")})
    text = open(os.path.join(raw, "av_calendar.csv"), encoding="utf-8").read()
    for it in csv.DictReader(io.StringIO(text)):
        d = datetime.date.fromisoformat(it["reportDate"])
        if lo <= d <= hi:
            t = it["symbol"].strip().upper()
            rows.setdefault(t, {"ticker": t, "sources": {}})["sources"].setdefault("alphavantage", []).append(
                {"date": it["reportDate"], "time": it.get("timeOfTheDay"), "name": it.get("name")})
    return rows


def capture_market(season):
    import yfinance as yf
    now = in_slot(season)
    _, raw = dirs(season)
    union = calendar_union(season)
    keep = ["quoteType", "exchange", "marketCap", "industry", "sector", "longName", "shortName", "currency"]
    out = {"source": "yfinance Ticker.info", "captured_et": now.isoformat(), "tickers": {}}
    for i, t in enumerate(sorted(union)):
        try:
            info = yf.Ticker(t).info or {}
            out["tickers"][t] = {k: info.get(k) for k in keep}
        except Exception as exc:  # recorded, never fabricated
            out["tickers"][t] = {"error": f"{type(exc).__name__}: {exc}"}
        if i % 25 == 24:
            print(f"  {i + 1}/{len(union)}")
        time.sleep(0.3)
    write_once(os.path.join(raw, "yfinance_market.json"), out)
    print(f"market: {len(out['tickers'])} tickers, captured {now:%H:%M} ET")


def ticker_excluded(t):
    ex = RULE["s1"]["exclude_ticker"]
    if any(c in t for c in ex["contains"]):
        return True
    for suf in ex["suffixes"]:
        if suf.endswith("*"):
            if re.search(re.escape(suf[:-1]) + r"\w*$", t):
                return True
        elif t.endswith(suf):
            return True
    return False


def parse_cap(s):
    if not s:
        return None
    digits = re.sub(r"[^0-9.]", "", str(s))
    return float(digits) if digits else None


def to_text(body):
    from bs4 import BeautifulSoup
    import warnings
    warnings.filterwarnings("ignore")
    text = BeautifulSoup(body, "lxml").get_text(" ")
    return re.sub(r"\s+", " ", text).lower()


def filing_test(name, texts):
    spec = RULE["filing_tests"][name]
    total, hits = 0, []
    for doc, text in texts.items():
        for pat in spec["patterns"]:
            for m in re.finditer(pat, text):
                total += 1
                a, b = max(0, m.start() - 80), m.end() + 80
                hits.append({"doc": doc, "pattern": pat, "context": text[a:b]})
    return {"test": name, "count": total, "min": spec["min"], "passed": total >= spec["min"], "hits": hits}


def screen_one(t, sources, m, sec, screen_date, base):
    """Every S1 test (D003 §3) for one company. Returns (record, None) if it is a candidate, or
    (record, reason) if excluded. Shared by the season screen and the Friday mid-season screen."""
    s1 = RULE["s1"]
    rec = {"ticker": t, "calendar": sources, "yfinance": m}

    def out(reason, **extra):
        rec.update(reason=reason, **extra)
        return rec, reason

    if ticker_excluded(t):
        return out("ticker_suffix")
    if "error" in m:
        return out("no_market_data")
    if m.get("quoteType") != s1["quote_type"] or m.get("exchange") not in EXCHANGES:
        return out("listing", detail=f"{m.get('quoteType')} on {m.get('exchange')}")
    industry = m.get("industry")
    if industry in s1["exclude_industries"]:
        return out("shell_company")
    named = RULE["named"].get(t)
    mapping = named or RULE["industry_map"].get(industry)
    if not mapping:
        return out("industry_out", detail=industry)

    cap = m.get("marketCap")
    cap2 = next((parse_cap(x["marketCap"]) for x in sources.get("nasdaq", []) if x.get("marketCap")), None)
    band = s1["market_cap_second_source_band"]
    if cap is None and cap2 is None:
        return out("no_cap")
    if cap is None or band[0] <= cap <= band[1]:
        ok = cap2 is not None and cap2 >= s1["market_cap_min"] and (cap is None or cap >= s1["market_cap_min"])
        rec["cap_second_source"] = cap2
        if not ok:
            return out("size_borderline", detail=f"yf={cap} nasdaq={cap2}")
    elif cap < s1["market_cap_min"]:
        return out("size", detail=cap)
    floor = mapping.get("market_cap_min")
    if floor and (cap or 0) < floor:
        return out("size_cluster_floor", detail=f"{cap} < {floor}")

    cik = sec.cik(t)
    if not cik:
        return out("no_sec_cik")
    rec["cik"] = cik
    fil = [f for f in sec.filings(cik) if f["filingDate"] <= screen_date.isoformat()]
    periodic = [f for f in fil if f["form"] in PERIODIC]
    if not periodic:
        return out("no_prior_print")
    if periodic[0]["form"] not in DOMESTIC:
        return out("foreign_filer", detail=periodic[0]["form"])
    rec["latest_periodic"] = periodic[0]

    tests = mapping.get("tests", [])
    if tests:
        oldest = (screen_date - datetime.timedelta(days=400)).isoformat()
        docs = {}
        for form in ("10-K", "10-Q"):
            f = next((x for x in fil if x["form"] == form and x["filingDate"] >= oldest), None)
            if f:
                docs[f"{form} {f['filingDate']} {f['accessionNumber']}"] = to_text(sec.document(cik, f))
        results = ([filing_test(n, docs) for n in tests] if docs
                   else [{"test": n, "count": 0, "passed": False, "reason": "no_filing"} for n in tests])
        write_json(os.path.join(base, "filing_tests", f"{t}.json"), {"ticker": t, "docs": list(docs), "results": results})
        rec["filing_tests"] = {r["test"]: {"count": r["count"], "passed": r["passed"]} for r in results}
        if not all(r["passed"] for r in results):
            return out("filing_test_failed")

    rec.update(cluster=mapping["cluster"], etf=mapping["etf"], industry=industry, market_cap=cap)
    return rec, None


def screen(season, only=None):
    base, raw = dirs(season)
    screen_date = datetime.date.fromisoformat(RULE["seasons"][season]["screen_date"])
    union = calendar_union(season)
    market = json.load(open(os.path.join(raw, "yfinance_market.json"), encoding="utf-8"))
    sec = Sec(os.path.join(ROOT, "cache", "sec"))
    candidates, excluded = [], []
    for t in sorted(union):
        if only and t not in only:
            continue
        rec, reason = screen_one(t, union[t]["sources"], market["tickers"].get(t, {}), sec, screen_date, base)
        if reason:
            excluded.append(rec)
        else:
            candidates.append(rec)
            print(f"  IN  {t:6} {rec['cluster']:30} {rec['industry']}")

    result = {
        "season": season, "rule": "D003_universe_screen_v1", "screen_date": screen_date.isoformat(),
        "window": RULE["seasons"][season]["window"], "screened_et": now_et().isoformat(),
        "market_captured_et": market["captured_et"], "calendar_names": len(union),
        "n_candidates": len(candidates), "candidates": candidates,
        "excluded_counts": {}, "excluded": excluded,
    }
    for e in excluded:
        result["excluded_counts"][e["reason"]] = result["excluded_counts"].get(e["reason"], 0) + 1
    name = "candidates.json" if not only else "candidates_partial.json"
    write_json(os.path.join(base, name), result)
    print(f"{len(candidates)} candidates of {len(union)} calendar names; excluded {result['excluded_counts']}")


def active_seasons(today):
    return [s for s, v in RULE["seasons"].items() if v["window"][0] <= today.isoformat() <= v["window"][1]]


def midseason(season):
    """D003 §7: each Friday of a season, re-pull the calendars. A company that was not in the S1 calendar
    and now shows a print inside the window is run through S1 with its market data at this moment; if it
    passes it joins, flagged added_midseason. A company already tested this season is never re-tested.
    The Alpha Vantage calendar is pulled only if ALPHAVANTAGE_API_KEY is set; otherwise that is recorded."""
    import yfinance as yf
    now = now_et()
    if now.weekday() != 4:
        raise SystemExit("D003 §7: the mid-season screen runs on Fridays only")
    base, _ = dirs(season)
    start, end = (datetime.date.fromisoformat(x) for x in RULE["seasons"][season]["window"])
    mdir = os.path.join(base, "midseason")
    tested = set(calendar_union(season))
    for p in sorted(os.listdir(mdir)) if os.path.isdir(mdir) else []:
        tested |= set(json.load(open(os.path.join(mdir, p), encoding="utf-8"))["tested"])
    rows, d = {}, max(now.date(), start)
    while d <= end:
        if d.weekday() < 5:
            r = requests.get("https://api.nasdaq.com/api/calendar/earnings",
                             params={"date": d.isoformat()}, headers=WEB_HEADERS, timeout=30)
            r.raise_for_status()
            for it in (r.json().get("data") or {}).get("rows") or []:
                t = it["symbol"].strip().upper()
                rows.setdefault(t, {}).setdefault("nasdaq", []).append(
                    {"date": d.isoformat(), "time": it.get("time"), "marketCap": it.get("marketCap"), "name": it.get("name")})
            time.sleep(1)
        d += datetime.timedelta(days=1)
    av_note = "not pulled - no ALPHAVANTAGE_API_KEY (deviation from D003 §7, recorded)"
    key = os.environ.get("ALPHAVANTAGE_API_KEY")
    if key:
        r = requests.get("https://www.alphavantage.co/query", timeout=60,
                         params={"function": "EARNINGS_CALENDAR", "horizon": "3month", "apikey": key})
        n = 0
        for it in csv.DictReader(io.StringIO(r.text)):
            if it.get("reportDate") and start.isoformat() <= it["reportDate"] <= end.isoformat() and it["reportDate"] >= now.date().isoformat():
                rows.setdefault(it["symbol"].strip().upper(), {}).setdefault("alphavantage", []).append(
                    {"date": it["reportDate"], "time": it.get("timeOfTheDay"), "name": it.get("name")})
                n += 1
        av_note = f"pulled: {n} rows in window"
    new = sorted(t for t in rows if t not in tested)
    sec = Sec(os.path.join(ROOT, "cache", "sec"))
    added, excluded = [], []
    keep = ["quoteType", "exchange", "marketCap", "industry", "sector", "longName", "shortName", "currency"]
    for t in new:
        try:
            info = yf.Ticker(t).info or {}
            m = {k: info.get(k) for k in keep}
        except Exception as exc:
            m = {"error": f"{type(exc).__name__}: {exc}"}
        rec, reason = screen_one(t, rows[t], m, sec, now.date(), base)
        rec["flags"] = ["added_midseason"]
        (excluded if reason else added).append(rec)
        time.sleep(0.3)
    write_once(os.path.join(mdir, f"{now.date().isoformat()}.json"),
               {"season": season, "rule": "D003_universe_screen_v1 §7", "captured_et": now.isoformat(),
                "alphavantage": av_note, "calendar_names": len(rows), "tested": new,
                "added": added, "excluded": excluded})
    if added:
        cpath = os.path.join(base, "candidates_midseason.json")
        cm = json.load(open(cpath, encoding="utf-8")) if os.path.exists(cpath) else {"season": season, "candidates": []}
        cm["candidates"] += added
        write_json(cpath, cm)
        spath = os.path.join(base, "event_status.json")
        st = json.load(open(spath, encoding="utf-8"))
        for rec in added:
            dates = sorted({x["date"] for src in rec["calendar"].values() for x in src})
            st["events"].setdefault(rec["ticker"], {"status": "PENDING", "flags": ["added_midseason"],
                                                    "note": f"added by the {now.date()} mid-season screen; calendars {dates}; "
                                                            "needs a company date + session (D003 §6)"})
        write_json(spath, st)
    print(f"{season} mid-season {now.date()}: {len(rows)} calendar names, {len(new)} new, "
          f"{len(added)} added {[r['ticker'] for r in added]}; alphavantage {av_note}")


if __name__ == "__main__":
    season, step = sys.argv[1], sys.argv[2]
    if step == "midseason":
        for s in (active_seasons(now_et().date()) if season == "active" else [season]):
            midseason(s)
        raise SystemExit(0)
    if season not in RULE["seasons"]:
        raise SystemExit(f"unknown season {season}")
    {"nasdaq": capture_nasdaq, "market": capture_market, "screen": screen}[step](season)
