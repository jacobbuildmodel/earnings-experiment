"""D003 S1 - the season screen.

    python pipeline/s1_screen.py <season> nasdaq     # capture slot only: pull the Nasdaq calendar
    python pipeline/s1_screen.py <season> av         # capture slot only: Alpha Vantage calendar (needs the key)
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
from common import ROOT, WEB_HEADERS, Sec, now_et, registry, rule_for, write_json, write_once  # noqa: E402

RULE = registry("D003_universe_screen_v1.json")  # replaced in __main__ by the version governing the season
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


def nasdaq_day(d, attempts=4):
    """One day of the Nasdaq earnings calendar. A transient failure is retried; a persistent one raises,
    because a calendar with a silently missing day would drop that day's reporters from the season."""
    for i in range(attempts):
        try:
            r = requests.get("https://api.nasdaq.com/api/calendar/earnings",
                             params={"date": d.isoformat()}, headers=WEB_HEADERS, timeout=30)
            r.raise_for_status()
            return (r.json().get("data") or {}).get("rows") or []
        except (requests.RequestException, ValueError):
            if i == attempts - 1:
                raise
            time.sleep(10 * (i + 1))


def capture_nasdaq(season):
    now = in_slot(season)
    _, raw = dirs(season)
    lo, hi = span(season)
    out = {"source": "nasdaq", "captured_et": now.isoformat(), "days": {}}
    d = lo
    while d <= hi:
        if d.weekday() < 5:
            out["days"][d.isoformat()] = nasdaq_day(d)
            time.sleep(1)
        d += datetime.timedelta(days=1)
    write_once(os.path.join(raw, "nasdaq_calendar.json"), out)
    print(f"nasdaq: {sum(len(v) for v in out['days'].values())} rows over {len(out['days'])} days")


def capture_av(season):
    """The Alpha Vantage EARNINGS_CALENDAR, pulled in the capture slot with ALPHAVANTAGE_API_KEY (before
    2026-09-21 this was saved by hand from the MCP tool)."""
    now = in_slot(season)
    _, raw = dirs(season)
    key = os.environ.get("ALPHAVANTAGE_API_KEY")
    if not key:
        raise SystemExit("no ALPHAVANTAGE_API_KEY - the Alpha Vantage calendar cannot be pulled")
    r = requests.get("https://www.alphavantage.co/query", timeout=60,
                     params={"function": "EARNINGS_CALENDAR", "horizon": "3month", "apikey": key})
    r.raise_for_status()
    if not r.text.startswith("symbol,"):
        raise SystemExit(f"Alpha Vantage did not return a calendar: {r.text[:200]}")
    path = os.path.join(raw, "av_calendar.csv")
    if os.path.exists(path):
        raise SystemExit(f"{path} already exists - raw captures are never overwritten")
    os.makedirs(raw, exist_ok=True)
    open(path, "w", encoding="utf-8", newline="").write(r.text)
    write_once(os.path.join(raw, "av_calendar.meta.json"),
               {"source": "alphavantage EARNINGS_CALENDAR horizon=3month", "captured_et": now.isoformat(),
                "rows": len(r.text.splitlines()) - 1})
    print(f"alphavantage: calendar saved, captured {now:%H:%M} ET")


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
    av_path = os.path.join(raw, "av_calendar.csv")
    if not os.path.exists(av_path):
        if not RULE.get("s1_alphavantage_optional"):
            raise SystemExit("no Alpha Vantage calendar - D003 v1 requires it")
        return rows  # D003 v2: Nasdaq alone, the screen is flagged single_calendar
    text = open(av_path, encoding="utf-8").read()
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
    # A season calendar holds ~4,300 names (Season A preview, 2026-09-28): about 70 minutes of Yahoo
    # calls. Progress is checkpointed so a runner that dies part-way resumes instead of starting over,
    # and a name that fails is retried before it is recorded as an error.
    part = os.path.join(ROOT, "cache", f"s1_{season}_market_partial.json")
    out = (json.load(open(part, encoding="utf-8")) if os.path.exists(part)
           else {"source": "yfinance Ticker.info", "captured_et": now.isoformat(), "tickers": {}})
    todo = [t for t in sorted(union) if t not in out["tickers"] or "error" in out["tickers"][t]]
    print(f"market: {len(union)} names, {len(todo)} to fetch")
    for i, t in enumerate(todo):
        if ticker_excluded(t):  # screen_one drops these before it reads market data
            out["tickers"][t] = {"skipped": "ticker_suffix"}
            continue
        for attempt in range(3):
            try:
                info = yf.Ticker(t).info or {}
                out["tickers"][t] = {k: info.get(k) for k in keep}
                break
            except Exception as exc:  # recorded, never fabricated
                out["tickers"][t] = {"error": f"{type(exc).__name__}: {exc}"}
                if "404" in str(exc) or "Not Found" in str(exc):
                    break
                time.sleep(60 if "Too Many Requests" in str(exc) or "429" in str(exc) else 5)
        if i % 100 == 99:
            print(f"  {i + 1}/{len(todo)}", flush=True)
            write_json(part, out)
        time.sleep(0.3)
    in_slot(season)  # the capture must also END inside the slot
    out["finished_et"] = now_et().isoformat()
    write_once(os.path.join(raw, "yfinance_market.json"), out)
    errors = sum(1 for v in out["tickers"].values() if "error" in v)
    print(f"market: {len(out['tickers'])} tickers ({errors} errors), captured {now:%H:%M} ET")


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
    if t in RULE.get("named_exclude", {}):
        return out("named_exclude", detail=RULE["named_exclude"][t])
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
    sic_rule = RULE.get("sic_filter")
    if sic_rule and industry in sic_rule["industries"]:
        sic = sec.submission(cik).get("sic")
        rec["sic"] = sic
        ok = sic and any(lo <= int(sic) <= hi for lo, hi in sic_rule["allowed_ranges"])
        if not ok:
            return out("sic_out", detail=f"SIC {sic} outside {sic_rule['allowed_ranges']}")
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


def one_per_issuer(candidates, taken=()):
    """D003 v3: share classes of one issuer (same SEC CIK) are one event; the alphabetically first ticker
    is kept, the others are excluded as second_share_class. `taken`: CIKs already in the season."""
    if not RULE.get("one_per_issuer"):
        return candidates, []
    seen, keep, drop = set(taken), [], []
    for rec in sorted(candidates, key=lambda r: r["ticker"]):
        if rec.get("cik") in seen:
            drop.append(dict(rec, reason="second_share_class"))
        else:
            seen.add(rec.get("cik"))
            keep.append(rec)
    return keep, drop


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

    candidates, extra = one_per_issuer(candidates)
    excluded += extra

    result = {
        "season": season, "rule": RULE["id"], "screen_date": screen_date.isoformat(),
        "flags": [] if os.path.exists(os.path.join(raw, "av_calendar.csv")) else ["single_calendar"],
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
            tk = yf.Ticker(t)
            info = tk.info or {}
            m = {k: info.get(k) for k in keep}
            if RULE.get("midseason_cap_as_of_screen_date"):
                # D003 v2: size as of the season screen date, so a name cannot qualify because it just rose
                sd = datetime.date.fromisoformat(RULE["seasons"][season]["screen_date"])
                h = tk.history(start=(sd - datetime.timedelta(days=10)).isoformat(), end=sd.isoformat(), auto_adjust=False)
                close = float(h["Close"].dropna().iloc[-1]) if len(h) else None
                shares = info.get("sharesOutstanding")
                m["marketCap_at_repull"] = m.get("marketCap")
                m["marketCap"] = shares * close if shares and close else None
                m["cap_basis"] = f"sharesOutstanding {shares} x close {close} before {sd}"
        except Exception as exc:
            m = {"error": f"{type(exc).__name__}: {exc}"}
        rec, reason = screen_one(t, rows[t], m, sec, now.date(), base)
        rec["flags"] = ["added_midseason"]
        (excluded if reason else added).append(rec)
        time.sleep(0.3)
    taken = set()
    for name in ("candidates.json", "candidates_midseason.json"):
        cp = os.path.join(base, name)
        if os.path.exists(cp):
            taken |= {c.get("cik") for c in json.load(open(cp, encoding="utf-8"))["candidates"]}
    added, extra = one_per_issuer(added, taken)
    excluded += extra
    write_once(os.path.join(mdir, f"{now.date().isoformat()}.json"),
               {"season": season, "rule": f"{RULE['id']} §7", "captured_et": now.isoformat(),
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
            RULE = rule_for("D003_universe_screen", s)
            midseason(s)
        raise SystemExit(0)
    RULE = rule_for("D003_universe_screen", season)
    {"nasdaq": capture_nasdaq, "av": capture_av, "market": capture_market, "screen": screen}[step](season)
