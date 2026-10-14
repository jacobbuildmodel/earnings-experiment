"""D014 §3: per-event first-hour prices for the D006 history events. Alpaca market data (free plan, feed sip,
adjustment raw). Writes analysis/d014/raw/chunks/<YYYY-MM>.csv, one per month of R. A month whose every request
succeeded is written and later skipped, so a rerun resumes. A month with a failed request is NOT written, so the
rerun retries it. It then writes raw/events_intraday.csv.gz and raw/manifest.json. These hold derived per-event
prices only, never raw bars.

    python analysis/d014/fetch.py [--commit]

Keys come from APCA_API_KEY_ID / APCA_API_SECRET_KEY (GitHub secrets); they are never printed or stored.
"""
import csv
import datetime
import gzip
import hashlib
import json
import os
import sys
import time

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
from common import ET  # noqa: E402

BASE = "https://data.alpaca.markets/v2/stocks"
RAW = os.path.join(HERE, "raw")
CHUNKS = os.path.join(RAW, "chunks")
HORIZONS = (5, 10, 30, 60)
QUOTE_TIMES = ("09:35", "09:40", "10:00", "10:30")
SIGNAL_CUT = datetime.time(9, 27)  # the gap's sign is read from trades before 09:27, when a MOO order can still go in
SPLIT_TOL = 0.01
TRAIN = (datetime.date(2022, 9, 1), datetime.date(2025, 8, 31))
VALID = (datetime.date(2025, 9, 1), datetime.date(2026, 9, 18))
PAUSE = 0.32                       # about 180 requests a minute; the free plan allows 200
UTC = datetime.timezone.utc
QT = [t.replace(":", "") for t in QUOTE_TIMES]
FIELDS = (["ticker", "date", "session", "cluster", "R", "segment", "mcap", "r1", "accepted_et", "c0", "c0_src",
           "pm", "pm_t", "o", "o_src", "o_t"] + [f"p{h}" for h in HORIZONS] + ["pc", "pc_src"]
          + [f"hs{t}" for t in QT] + [f"mid{t}" for t in QT] + ["pmv", "split_check", "void"]
          + ["spy_c0", "spy_pm", "spy_o"] + [f"spy_p{h}" for h in HORIZONS] + ["spy_pc", "surprise"])
stats = {"requests": 0, "retries": 0, "failed": 0}


class FetchFailed(Exception):
    pass


def headers():
    return {"APCA-API-KEY-ID": os.environ["APCA_API_KEY_ID"], "APCA-API-SECRET-KEY": os.environ["APCA_API_SECRET_KEY"]}


def get(path, params):
    """The JSON body, or None after the first try and 3 retries. A 429 waits 30 s."""
    for attempt in range(4):
        time.sleep(PAUSE)
        stats["requests"] += 1
        try:
            r = requests.get(f"{BASE}/{path}", params=params, headers=headers(), timeout=60)
        except requests.RequestException:
            r = None
        if r is not None and r.status_code == 200:
            return r.json()
        stats["retries"] += 1
        time.sleep(30 if r is not None and r.status_code == 429 else 3 * (attempt + 1))
    stats["failed"] += 1
    return None


def paged(path, params, key):
    """{symbol: [items]} over every page. Raises FetchFailed if any page failed."""
    out, token = {}, None
    while True:
        js = get(path, dict(params, **({"page_token": token} if token else {})))
        if js is None:
            raise FetchFailed(path)
        for s, xs in (js.get(key) or {}).items():
            out.setdefault(s, []).extend(xs)
        token = js.get("next_page_token")
        if not token:
            return out


def at(day, hhmm):
    h, m = map(int, hhmm.split(":"))
    return datetime.datetime.combine(day, datetime.time(h, m), ET)


def utc(day, hhmm):
    return at(day, hhmm).astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def et_of(t):
    return datetime.datetime.fromisoformat(t.replace("Z", "+00:00")).astimezone(ET)


def segment(r):
    return "TRAIN" if TRAIN[0] <= r <= TRAIN[1] else "VALIDATION" if VALID[0] <= r <= VALID[1] else None


def spy_sessions():
    js = paged("bars", {"symbols": "SPY", "timeframe": "1Day", "feed": "sip", "adjustment": "raw",
                        "start": "2022-06-01", "end": "2026-09-30T23:00:00Z", "limit": 10000}, "bars")
    return sorted(et_of(b["t"]).date() for b in js["SPY"])


def biggest(prints, not_before=None):
    """The largest-size print of an auction list (the listing exchange's official cross), and its ET time.
    not_before drops early prints (an Arca 04:00 early-open print is not the 09:30 cross)."""
    ps = [p for p in prints or [] if p.get("p") and p.get("s")
          and (not_before is None or not p.get("t") or et_of(p["t"]) >= not_before)]
    if not ps:
        return None, None
    b = max(ps, key=lambda p: p["s"])
    return b["p"], (et_of(b["t"]) if b.get("t") else None)


def auction(auc, sym, day, side, not_before=None):
    for d in (auc or {}).get(sym, []):
        if d.get("d") == day.isoformat():
            return biggest(d.get(side), not_before)
    return None, None


def regular(bars):
    out = []
    for b in bars or []:
        t = et_of(b["t"])
        if datetime.time(9, 30) <= t.time() < datetime.time(16, 0):
            out.append((t, b))
    return out


def price_at(reg, day, minutes, o_t):
    """The last trade at or before 09:30 + minutes: the close of the latest regular bar starting before it.
    Missing when the official open came at or after that time (a delayed opening)."""
    cut = at(day, "09:30") + datetime.timedelta(minutes=minutes)
    if o_t is not None and o_t >= cut:
        return None
    xs = [b for t, b in reg if t < cut]
    return xs[-1]["c"] if xs else None


def premarket(sym, day, minute, after_hours, accepted):
    """The last trade before 09:27 ET on R, from R's pre-market and (AMC only, passed in) R-1 after hours, and at or
    after the release's SEC acceptance minute when it is known. (price, ET time) or (None, None)."""
    cut = datetime.datetime.combine(day, SIGNAL_CUT, ET)
    floor = accepted.replace(second=0, microsecond=0) if accepted else None
    xs = [(et_of(b["t"]), b) for b in (after_hours or {}).get(sym, []) + (minute or {}).get(sym, [])]
    xs = sorted(((t, b) for t, b in xs if t < cut and (floor is None or t >= floor)), key=lambda x: x[0])
    xs = [(t, b) for t, b in xs if t.date() == day or t.time() >= datetime.time(16, 0)]
    return (xs[-1][1]["c"], xs[-1][0]) if xs else (None, None)


def prices(sym, day, r1, minute, daily, auc):
    """c0, o (+ its time), p_h and pc, with their sources."""
    reg = regular((minute or {}).get(sym))
    dbars = {et_of(b["t"]).date(): b for b in (daily or {}).get(sym, [])}
    c0, _ = auction(auc, sym, r1, "c")
    c0_src = "auction"
    if c0 is None and r1 in dbars:
        c0, c0_src = dbars[r1]["c"], "c0_from_bar"
    o, o_t = auction(auc, sym, day, "o", not_before=at(day, "09:30"))
    o_src = "auction"
    if o is None and reg:
        o, o_t, o_src = reg[0][1]["o"], reg[0][0], "open_from_bar"
    pc, _ = auction(auc, sym, day, "c")
    pc_src = "auction"
    if pc is None and reg:
        pc, pc_src = reg[-1][1]["c"], "close_from_bar"
    return {"c0": c0, "c0_src": c0_src if c0 is not None else None, "o": o, "o_src": o_src if o is not None else None,
            "o_t": o_t.isoformat() if o_t else None, **{f"p{h}": price_at(reg, day, h, o_t) for h in HORIZONS},
            "pc": pc, "pc_src": pc_src if pc is not None else None}


def quote(sym, day, hhmm):
    """(half spread, mid) from the last NBBO quote at or before hh:mm, within 5 minutes; (None, None) if missing,
    crossed or zero-bid."""
    end = at(day, hhmm)
    js = get(f"{sym}/quotes", {"feed": "sip", "limit": 1, "sort": "desc",
                                "start": (end - datetime.timedelta(minutes=5)).astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                "end": end.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")})
    q = (js or {}).get("quotes") or []
    if not q:
        return None, None
    bid, ask = q[0].get("bp"), q[0].get("ap")
    if not bid or not ask or bid <= 0 or ask < bid:
        return None, None
    return (ask - bid) / (ask + bid), (ask + bid) / 2


def surprises(tickers):
    """{ticker: [(ET date, Surprise(%))]} from yfinance, and the tickers that failed."""
    import yfinance as yf
    out, failed = {}, []
    for t in sorted(tickers):
        try:
            ed = yf.Ticker(t).get_earnings_dates(limit=28)
            rows = []
            for ts, row in (ed.iterrows() if ed is not None else []):
                v = row.get("Surprise(%)")
                if v is not None and v == v:
                    rows.append((ts.astimezone(ET).date().isoformat(), float(v)))
            out[t] = rows
        except Exception:
            failed.append(t)
        time.sleep(0.5)
    return out, failed


def surprise_for(sp, ticker, report_date):
    best = None
    for d, v in sp.get(ticker, []):
        gap = abs((datetime.date.fromisoformat(d) - report_date).days)
        if gap <= 1 and (best is None or gap < best[0]):
            best = (gap, v)
    return best[1] if best else None


def build_date(day, evs, sessions, sp):
    """Every event reacting on `day`. Raises FetchFailed if a bar or auction request failed."""
    i = sessions.index(day)
    r1, d20 = sessions[i - 1], sessions[i - 20]
    syms = sorted({e["ticker"] for e in evs} | {"SPY"})
    amc = sorted({e["ticker"] for e in evs if e["session"] == "AMC"})
    base = {"symbols": ",".join(syms), "feed": "sip", "limit": 10000}
    minute = paged("bars", dict(base, timeframe="1Min", adjustment="raw", start=utc(day, "04:00"),
                                end=utc(day, "16:00")), "bars")
    after = paged("bars", dict(base, symbols=",".join(amc), timeframe="1Min", adjustment="raw", start=utc(r1, "16:00"),
                               end=utc(r1, "20:00")), "bars") if amc else {}
    daily = paged("bars", dict(base, timeframe="1Day", adjustment="raw", start=d20.isoformat(),
                               end=utc(day, "20:00")), "bars")
    dsplit = paged("bars", dict(base, timeframe="1Day", adjustment="split", start=r1.isoformat(),
                                end=utc(day, "20:00")), "bars")
    auc = paged("auctions", {"symbols": ",".join(syms), "feed": "sip", "start": r1.isoformat(),
                             "end": utc(day, "20:00"), "limit": 10000}, "auctions")
    spy = prices("SPY", day, r1, minute, daily, auc)
    spy["pm"], _ = premarket("SPY", day, minute, {}, None)
    rows = []
    for e in evs:
        t = e["ticker"]
        p = prices(t, day, r1, minute, daily, auc)
        acc = datetime.datetime.fromisoformat(e["accepted_et"]).astimezone(ET) if e.get("accepted_et") else None
        pm, pm_t = premarket(t, day, minute, after if e["session"] == "AMC" else {}, acc)
        dr = {et_of(b["t"]).date(): b for b in daily.get(t, [])}
        ds = {et_of(b["t"]).date(): b for b in dsplit.get(t, [])}
        if all(x in dr and x in ds and ds[x]["c"] for x in (r1, day)):
            f1, f2 = dr[r1]["c"] / ds[r1]["c"], dr[day]["c"] / ds[day]["c"]
            split_check = "split" if abs(f1 / f2 - 1) > SPLIT_TOL else "ok"
        else:
            split_check = "unchecked"
        prior = [dr[x]["v"] for x in sessions[i - 20:i] if x in dr]
        vol = sum(b["v"] for b in minute.get(t, []) if et_of(b["t"]).time() < SIGNAL_CUT)
        if e["session"] == "AMC":
            vol += sum(b["v"] for b in after.get(t, []))
        pmv = vol / (sum(prior) / len(prior)) if len(prior) == 20 and sum(prior) > 0 else None
        void = ("no_c0" if p["c0"] is None else "no_open" if p["o"] is None else
                "split" if split_check == "split" else "no_premarket" if pm is None else "")
        row = {"ticker": t, "date": e["date"], "session": e["session"], "cluster": e["cluster"], "R": day.isoformat(),
               "segment": segment(day), "mcap": (e.get("factors") or {}).get("market_cap_pit"), "r1": r1.isoformat(),
               "accepted_et": e.get("accepted_et"), **p, "pm": pm, "pm_t": pm_t.isoformat() if pm_t else None,
               "pmv": pmv, "split_check": split_check, "void": void,
               **{f"spy_{k}": spy[k] for k in ["c0", "pm", "o"] + [f"p{h}" for h in HORIZONS] + ["pc"]},
               "surprise": surprise_for(sp, t, datetime.date.fromisoformat(e["date"]))}
        for hhmm, k in zip(QUOTE_TIMES, QT):
            row[f"hs{k}"], row[f"mid{k}"] = (None, None) if void else quote(t, day, hhmm)
        rows.append(row)
    return rows


def commit(msg):
    from freeze import git, push_all
    git("add", "analysis/d014/raw")
    if git("diff", "--cached", "--name-only"):
        git("commit", "-q", "-m", f"{msg}\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
        print("pushed:", push_all())


def load_surprises(tickers):
    path = os.path.join(RAW, "surprise.json")
    if os.path.exists(path):
        js = json.load(open(path, encoding="utf-8"))
        sp, failed = js["by_ticker"], js["failed"]
        if failed:
            more, failed = surprises(failed)
            sp.update(more)
    else:
        sp, failed = surprises(tickers)
    json.dump({"source": "yfinance get_earnings_dates(limit=28) Surprise(%) - EPS basis vendor-defined",
               "failed": failed, "by_ticker": sp}, open(path, "w", encoding="utf-8", newline="\n"), indent=0)
    return sp


def main(do_commit=False):
    os.makedirs(CHUNKS, exist_ok=True)
    evs = json.load(open(os.path.join(ROOT, "analysis", "history", "graded_events.json"), encoding="utf-8"))["events"]
    evs = [e for e in evs if segment(datetime.date.fromisoformat(e["exit_A"]))]
    sessions = spy_sessions()
    sp = load_surprises({e["ticker"] for e in evs})
    by_month = {}
    for e in evs:
        by_month.setdefault(e["exit_A"][:7], {}).setdefault(e["exit_A"], []).append(e)
    last, failed_months = time.time(), []
    for month in sorted(by_month):
        path = os.path.join(CHUNKS, f"{month}.csv")
        if os.path.exists(path):
            continue
        rows = []
        try:
            for day in sorted(by_month[month]):
                d = datetime.date.fromisoformat(day)
                if d not in sessions:
                    rows += [{"ticker": e["ticker"], "date": e["date"], "session": e["session"], "cluster": e["cluster"],
                              "R": day, "segment": segment(d), "void": "not_a_session"} for e in by_month[month][day]]
                    continue
                rows += build_date(d, by_month[month][day], sessions, sp)
        except FetchFailed as exc:
            failed_months.append(month)
            print(f"{month}: NOT written, a request failed ({exc}); a rerun retries it", flush=True)
            continue
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, FIELDS, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
        print(f"{month}: {len(rows)} events, {sum(1 for r in rows if r.get('void'))} void, {stats}", flush=True)
        if do_commit and time.time() - last > 1200:
            commit(f"D014 fetch: chunks through {month}")
            last = time.time()
    if failed_months:
        if do_commit:
            commit(f"D014 fetch: partial, {len(failed_months)} month(s) to retry")
        raise SystemExit(f"months to retry: {failed_months}")
    rows = []
    for month in sorted(by_month):
        rows += list(csv.DictReader(open(os.path.join(CHUNKS, f"{month}.csv"), encoding="utf-8")))
    with gzip.open(os.path.join(RAW, "events_intraday.csv.gz"), "wt", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    sha = hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()
    json.dump({"rule": "D014_exploration_postprint_v1 section 3", "run_utc": datetime.datetime.now(UTC).isoformat(timespec="seconds"),
               "fetch_sha256": sha, "events": len(rows), "void": sum(1 for r in rows if r.get("void")),
               "source": "Alpaca market data v2, free plan, feed sip, adjustment raw", "requests": stats},
              open(os.path.join(RAW, "manifest.json"), "w", encoding="utf-8", newline="\n"), indent=1)
    print(f"done: {len(rows)} events, {stats}")
    if do_commit:
        commit(f"D014 fetch: {len(rows)} events built")


if __name__ == "__main__":
    main("--commit" in sys.argv)
