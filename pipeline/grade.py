"""Grade frozen events - D001, computed by code, never judged (rule 4).

    python pipeline/grade.py            # fetch any exit prices now available, then (re)compute outcomes
    python pipeline/grade.py --no-fetch # recompute outcomes from stored prices only

Two layers, kept apart:
  1. RAW, fetch-once (D001 §2): outcomes/<season>/prices/<T>_<date>.jsonl - one row per (symbol, session,
     field, source), with the fetch time. A row is never rewritten; a correction is a new row with a reason,
     and the newest row for a key is the one in force. Beta is stored once. The 8-K list is re-read
     each run until three days after exit C, then stored as final.
  2. DERIVED: outcomes/<season>/<T>_<date>.json - recomputed from the raw rows on every run by the same
     code, so anyone can re-derive every number.

How D001 is applied where it leaves a choice (registered in D005 §6):
  - Prices: yfinance history(auto_adjust=False) Open/Close. Yahoo's series is already split-adjusted, so
    entry and exit are on one basis and D001 §3's split division is already applied; a split in the
    window is flagged split_in_window. Cash dividends with entry < ex-date <= exit are added to the exit.
  - Check source: Alpha Vantage TIME_SERIES_DAILY (needs ALPHAVANTAGE_API_KEY; at most 20 calls a run,
    1.2 s apart). Agree when |diff| <= 0.10% or <= $0.01. No check value -> flag single_source.
  - Print timing (D001 §6 "print date or session differs"): the company's Item 2.02 8-K acceptance time
    from SEC EDGAR. Inside the frozen release window -> verified. Inside the opposite window (the print
    was really the other session) -> VOID print_session_differs. Before the frozen window opens -> VOID
    print_date_differs (an 8-K can lag its release, never precede it). During market hours, after the
    window, or no 2.02 8-K within D-3..D+3 -> timing_unverified, reported with and without.
  - Exit A with no price (even delayed 5 sessions) -> VOID no_price. Prices are fetched from 06:00 ET the
    day after the session. Exit A is also split, as a secondary, into the pre-print session
    (entry open -> entry close) and the print gap (entry close -> exit A open).
  - Confounds: every other 8-K item filed from the entry session to exit C is listed; items other than
    2.02 / 7.01 / 9.01 set the flag confound_8k (CLAUDE.md: read every filing in the event window).
  - Leave-one-out: no issuer holdings file is captured, so every excess return is flagged
    bench_weight_missing (D003 §8 fallback).
"""
import datetime
import glob
import json
import os
import subprocess
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ET, ROOT, Sec, now_et, registry, write_json  # noqa: E402
from sessions import shift  # noqa: E402

D001 = registry("D001_outcome_v1.json")
D003 = registry("D003_universe_screen_v1.json")
P = D001["prices"]
OK_8K_ITEMS = {"2.02", "7.01", "9.01"}
AV_MAX_CALLS = 20


def r4(x):
    return None if x is None else round(float(x), P["round_decimals"])


# ---------------------------------------------------------------- raw layer (fetch once)

class Store:
    def __init__(self, path):
        self.path = path
        self.rows = [json.loads(line) for line in open(path, encoding="utf-8")] if os.path.exists(path) else []

    def get(self, symbol, session, field, source):
        """The row in force: the LAST one for that key, so a correction row supersedes the original."""
        hit = None
        for r in self.rows:
            if (r["symbol"], r["session"], r["field"], r["source"]) == (symbol, session, field, source):
                hit = r
        return hit

    def add(self, symbol, session, field, source, value, reason=None, **extra):
        """Fetch once: a key that already has a row is skipped. A correction (D001 §2) is only ever a NEW
        row that carries a reason; the old row stays in the file."""
        old = self.get(symbol, session, field, source)
        if old and not reason:
            return
        row = {"symbol": symbol, "session": session, "field": field, "source": source, "value": value,
               "fetched_et": now_et().isoformat(timespec="seconds"), **extra}
        if old:
            row.update(correction_of=old["fetched_et"], reason=reason)
        self.rows.append(row)
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(row) + "\n")


def settled(session, field):
    """A price is fetched only once it is final: from 06:00 ET the next calendar day, after the vendor's
    overnight revision of the daily bar (implementation v2; v1 used the same day's close + 15 min)."""
    d = datetime.date.fromisoformat(session) + datetime.timedelta(days=1)
    return now_et() >= datetime.datetime.combine(d, datetime.time(6, 0), ET)


def fetch_yf(store, symbol, points, start, end):
    import yfinance as yf
    need = [(s, f) for s, f in points if settled(s, f) and not store.get(symbol, s, f, "yfinance")]
    if not need:
        return
    tk = yf.Ticker(symbol)
    h = tk.history(start=start, end=(datetime.date.fromisoformat(end) + datetime.timedelta(days=1)).isoformat(),
                   auto_adjust=False, actions=True)
    h.index = [x.date().isoformat() for x in h.index.tz_convert(ET)]
    for s, f in need:
        if s in h.index:
            v = h.loc[s, "Open" if f == "open" else "Close"]
            if v == v:  # not NaN
                store.add(symbol, s, f, "yfinance", r4(v), how="history(auto_adjust=False)")
    for s in h.index:  # corporate actions anywhere in the fetched range
        if h.loc[s, "Dividends"]:
            store.add(symbol, s, "dividend", "yfinance", float(h.loc[s, "Dividends"]), how="ex-date")
        if h.loc[s, "Stock Splits"]:
            store.add(symbol, s, "split", "yfinance", float(h.loc[s, "Stock Splits"]))


class AlphaVantage:
    def __init__(self):
        self.key = os.environ.get("ALPHAVANTAGE_API_KEY")
        self.calls, self.last, self.cache = 0, 0.0, {}

    def daily(self, symbol):
        if not self.key or self.calls >= AV_MAX_CALLS:
            return None
        if symbol in self.cache:
            return self.cache[symbol]
        time.sleep(max(0, 1.2 - (time.time() - self.last)))
        r = requests.get("https://www.alphavantage.co/query", timeout=30,
                         params={"function": "TIME_SERIES_DAILY", "symbol": symbol, "outputsize": "compact",
                                 "apikey": self.key})
        self.calls, self.last = self.calls + 1, time.time()
        data = r.json().get("Time Series (Daily)")
        self.cache[symbol] = data
        return data


def fetch_av(store, av, symbol, points):
    need = [(s, f) for s, f in points if settled(s, f) and not store.get(symbol, s, f, "alphavantage")]
    if not need:
        return
    data = av.daily(symbol)
    if not data:
        return
    for s, f in need:
        if s in data:
            store.add(symbol, s, f, "alphavantage", r4(data[s]["1. open" if f == "open" else "4. close"]),
                      how="TIME_SERIES_DAILY (unadjusted)")


def fetch_beta(store, symbol, etf, snap):
    if store.get(symbol, snap, "beta", "yfinance"):
        return
    import numpy as np
    import yfinance as yf
    b = D003["benchmark"]
    start = (datetime.date.fromisoformat(snap) - datetime.timedelta(days=400)).isoformat()
    end = (datetime.date.fromisoformat(snap) + datetime.timedelta(days=1)).isoformat()
    closes = {}
    for sym in (symbol, etf):
        h = yf.Ticker(sym).history(start=start, end=end, auto_adjust=True)
        h.index = [x.date().isoformat() for x in h.index.tz_convert(ET)]
        closes[sym] = h["Close"]
    both = closes[symbol].to_frame("s").join(closes[etf].to_frame("e"), how="inner").dropna()
    rets = both.pct_change().dropna().iloc[-b["beta_sessions"]:]
    flags = []
    if len(rets) < b["beta_min_sessions"]:
        beta, flags = b["beta_default"], ["beta_default"]
    else:
        beta = float(np.polyfit(rets["e"], rets["s"], 1)[0])
        lo, hi = b["beta_clip"]
        if not lo <= beta <= hi:
            beta, flags = min(max(beta, lo), hi), ["beta_clipped"]
    store.add(symbol, snap, "beta", "yfinance", round(beta, 6), etf=etf, sessions=len(rets), flags=flags,
              how="OLS of adjusted daily close-to-close returns, 252 sessions to the snapshot session")


def fetch_filings(season, ev, cik, report_date, first, last):
    """8-Ks accepted from 3 days before the print to exit C, stored once exit C has settled."""
    path = os.path.join(ROOT, "outcomes", season, "filings", f"{ev}.json")
    if os.path.exists(path) and load(path).get("final"):
        return load(path)
    sub = json.loads(Sec(os.path.join(ROOT, "cache", "sec")).get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json"))
    rec = sub["filings"]["recent"]
    lo = (datetime.date.fromisoformat(min(first, report_date)) - datetime.timedelta(days=3)).isoformat()
    hi = (datetime.date.fromisoformat(max(last, report_date)) + datetime.timedelta(days=3)).isoformat()
    rows = []
    for i, form in enumerate(rec["form"]):
        if form.startswith("8-K") and lo <= rec["filingDate"][i] <= hi:
            rows.append({"form": form, "filed": rec["filingDate"][i], "accepted_utc": rec["acceptanceDateTime"][i],
                         "items": rec["items"][i], "accession": rec["accessionNumber"][i],
                         "document": rec["primaryDocument"][i]})
    out = {"cik": cik, "window": [lo, hi], "fetched_et": now_et().isoformat(timespec="seconds"),
           "final": settled(last, "close") and now_et().date() > datetime.date.fromisoformat(hi), "filings": rows}
    write_json(path, out)
    return out


# ---------------------------------------------------------------- derived layer (pure)

def load(path):
    return json.load(open(path, encoding="utf-8"))


def price(store, sym, session, field):
    """Graded value, check comparison, and flags for one price point (D001 §2)."""
    y = store.get(sym, session, field, "yfinance")
    a = store.get(sym, session, field, "alphavantage")
    if not y:
        return None, []
    flags = []
    if a is None:
        flags.append("single_source")
    else:
        # Alpha Vantage is as-traded; Yahoo back-adjusts for every split after the session. Put the AV
        # value on Yahoo's basis with the splits recorded after this session before comparing.
        ratio = 1.0
        for r in store.rows:
            if r["symbol"] == sym and r["field"] == "split" and r["session"] > session:
                ratio *= r["value"]
        diff = abs(y["value"] - a["value"] / ratio)
        if not (diff <= P["agree_if_abs_diff_usd_lte"] or diff / y["value"] * 100 <= P["agree_if_abs_diff_pct_lte"]):
            flags.append("price_dispute")
    return y["value"], flags


def point(store, sym, session, field, limit=5):
    """D001 §2 missing exit: the next official price of the same kind, flag exit_delayed."""
    s = session
    for k in range(limit + 1):
        v, fl = price(store, sym, s, field)
        if v is not None:
            return v, s, fl + (["exit_delayed"] if k else [])
        s = shift(datetime.date.fromisoformat(s), 1).isoformat()
    return None, session, []


def timing_check(filings, report_date, session):
    d = datetime.date.fromisoformat(report_date)
    prev_close = datetime.datetime.combine(shift(d, -1), datetime.time(16, 0), ET)
    d_open = datetime.datetime.combine(d, datetime.time(9, 30), ET)
    d_close = datetime.datetime.combine(d, datetime.time(16, 0), ET)
    next_open = datetime.datetime.combine(shift(d, 1), datetime.time(9, 30), ET)
    windows = {"BMO": (prev_close, d_open), "AMC": (d_close, next_open)}
    hits = []
    for f in filings:
        if "2.02" not in f["items"].split(","):
            continue
        t = datetime.datetime.fromisoformat(f["accepted_utc"].replace("Z", "+00:00")).astimezone(ET)
        where = next((k for k, (a, b) in windows.items() if a <= t < b), None)
        hits.append({"accepted_et": t.isoformat(), "window": where or "other"})
    if any(h["window"] == session for h in hits):
        return "verified", hits
    other = "AMC" if session == "BMO" else "BMO"
    if any(h["window"] == other for h in hits):
        return "contradicted", hits
    # An 8-K can lag its press release, but it can never precede it: a 2.02 filing accepted before the
    # frozen release window opens means the results were public earlier (external review 2026-09-21).
    if any(datetime.datetime.fromisoformat(h["accepted_et"]) < windows[session][0] for h in hits):
        return "early", hits
    return "unverified", hits


def grade_event(season, edir, fetch, av):
    man = load(os.path.join(edir, "manifest.json"))
    gate = load(os.path.join(edir, "gate.json"))
    ev = os.path.basename(edir)
    out_path = os.path.join(ROOT, "outcomes", season, f"{ev}.json")
    base = {"event": ev, "season": season, "gate_status": man["status"], "graded_by": "pipeline/grade.py",
            "graded_et": now_et().isoformat(timespec="seconds"), "rule": "D001_outcome_v1 + D005 §6"}
    if man["status"] != "PASS":
        write_json(out_path, {**base, "graded": False, "reason": "not eligible - never graded (D003 §1)"})
        return
    tm, sym = gate["timing"], gate["ticker"]
    cand = {}
    for name in ("candidates.json", "candidates_midseason.json"):  # D003 §7 additions carry the same fields
        cp = os.path.join(ROOT, "universe", season, name)
        if os.path.exists(cp):
            cand.update({c["ticker"]: c for c in load(cp)["candidates"]})
    etf = cand.get(sym, {}).get("etf")
    cik = cand.get(sym, {}).get("cik")
    store = Store(os.path.join(ROOT, "outcomes", season, "prices", f"{ev}.jsonl"))
    pts = [(tm["entry"]["session"], "open"), (tm["entry"]["session"], "close")]
    pts += [(tm[k]["session"], tm[k]["price"]) for k in ("exit_A", "exit_B", "exit_C")]
    # room for exit_delayed: up to 5 sessions past exit C
    ext = [(shift(datetime.date.fromisoformat(tm["exit_C"]["session"]), i).isoformat(), f)
           for i in range(1, 6) for f in ("open", "close")]
    start = (datetime.date.fromisoformat(tm["entry"]["session"]) - datetime.timedelta(days=7)).isoformat()
    last = ext[-1][0]
    filings = None
    if fetch:
        for s in (sym, etf) if etf else (sym,):
            try:
                fetch_yf(store, s, pts + ext, start, last)
            except Exception as exc:
                print(f"{ev}: yfinance {s} failed: {type(exc).__name__}: {exc}")
            try:
                fetch_av(store, av, s, pts)
            except Exception as exc:
                print(f"{ev}: alphavantage {s} failed: {type(exc).__name__}: {exc}")
        if etf and settled(tm["entry"]["session"], "open"):
            try:
                fetch_beta(store, sym, etf, gate["snapshot_session"])
            except Exception as exc:
                print(f"{ev}: beta failed: {type(exc).__name__}: {exc}")
        if cik and settled(tm["exit_A"]["session"], "open"):
            try:
                filings = fetch_filings(season, ev, cik, gate["report_date"], tm["entry"]["session"], tm["exit_C"]["session"])
            except Exception as exc:
                print(f"{ev}: SEC filings failed: {type(exc).__name__}: {exc}")
    fp = os.path.join(ROOT, "outcomes", season, "filings", f"{ev}.json")
    if filings is None and os.path.exists(fp):
        filings = load(fp)

    flags, void = [], None
    # rule 1: the freeze commit must precede the entry open
    commit_iso = subprocess.run(["git", "log", "--diff-filter=A", "--format=%cI", "--",
                                 os.path.relpath(os.path.join(edir, "manifest.json"), ROOT).replace(os.sep, "/")],
                                cwd=ROOT, capture_output=True, text=True).stdout.split()
    entry_open = datetime.datetime.fromisoformat(man["entry_open_et"])
    if commit_iso and datetime.datetime.fromisoformat(commit_iso[-1]) >= entry_open:
        void = "freeze_after_entry_open"
    timing, hits = ("pending", [])
    if filings:
        timing, hits = timing_check(filings["filings"], gate["report_date"], gate["session"])
        if timing == "contradicted":
            void = void or "print_session_differs"
        elif timing == "early":
            void = void or "print_date_differs"
        elif timing == "unverified":
            flags.append("timing_unverified")
        other = sorted({i for f in filings["filings"] for i in f["items"].split(",")} - OK_8K_ITEMS - {""})
        if other:
            flags.append("confound_8k")
    beta_row = store.get(sym, gate["snapshot_session"], "beta", "yfinance")

    def leg(symbol, key):
        e, e_s, e_fl = point(store, symbol, tm["entry"]["session"], "open", limit=0)
        x, x_s, x_fl = point(store, symbol, tm[key]["session"], tm[key]["price"])
        if e is None or x is None:
            return None
        divs = [r["value"] for r in store.rows if r["symbol"] == symbol and r["field"] == "dividend"
                and tm["entry"]["session"] < r["session"] <= x_s]
        splits = [r for r in store.rows if r["symbol"] == symbol and r["field"] == "split"
                  and tm["entry"]["session"] < r["session"] <= x_s]
        fl = sorted(set(e_fl + x_fl + (["dividend_adjusted"] if divs else []) + (["split_in_window"] if splits else [])))
        xp = x + sum(divs)
        return {"entry": e, "entry_session": e_s, "exit": x, "exit_session": x_s, "dividends": sum(divs),
                "raw_return": xp / e - 1, "flags": fl}

    exits = {}
    for key in ("exit_A", "exit_B", "exit_C"):
        s = leg(sym, key)
        if s is None:
            exits[key] = {"status": "pending" if not settled(tm[key]["session"], tm[key]["price"]) else "no_price"}
            continue
        s["WIN_raw"] = s["raw_return"] > 0
        s["WIN_net"] = s["raw_return"] > D001["outcome"]["secondary"][0]["round_trip_cost"]
        b = leg(etf, key) if etf else None
        if b and beta_row:
            s["bench"] = {"etf": etf, "beta": beta_row["value"], "bench_return": b["raw_return"],
                          "flags": sorted(set(b["flags"] + beta_row.get("flags", []) + ["bench_weight_missing"]))}
            s["excess_return"] = s["raw_return"] - beta_row["value"] * b["raw_return"]
            s["WIN_excess"] = s["excess_return"] > 0
        s["label"] = "PRIMARY" if key == D001["primary_exit"] else "secondary"
        exits[key] = s
    a = exits["exit_A"]
    if void is None and a.get("status") == "no_price":  # the primary exit has no price, even delayed
        void = "no_price"
    # Secondary split of exit A (external review 2026-09-21): the session before the print, then the gap.
    ec, _ = price(store, sym, tm["entry"]["session"], "close")
    if "raw_return" in a and ec:
        a["legs"] = {"pre_print": ec / a["entry"] - 1, "print_gap": a["exit"] / ec - 1,
                     "entry_close": ec, "label": "secondary"}
    dec = load(os.path.join(edir, "decision.json"))
    tracks = {"T0": dec["t0"]["decision"], "T1": dec["t1"].get("decision"), "T2": dec["t2"].get("decision")}
    graded = "raw_return" in a and void is None
    out = {**base, "graded": graded, "void": void, "ticker": sym, "report_date": gate["report_date"],
           "session": gate["session"], "entry_session": tm["entry"]["session"], "cluster": cand.get(sym, {}).get("cluster"),
           "flags": sorted(set(flags)), "timing_check": timing, "timing_evidence": hits, "exits": exits,
           "decisions": tracks, "t2_confidence": dec["t2"].get("confidence")}
    if graded:
        out["correct"] = {t: (d == "BUY") == a["WIN_raw"] for t, d in tracks.items() if d in ("BUY", "NO_BUY")}
    write_json(out_path, out)
    print(f"{ev}: {'graded' if graded else 'VOID ' + void if void else 'pending'}"
          + (f" raw_A={a['raw_return']:+.4f} WIN={a['WIN_raw']}" if "raw_return" in a else ""))


def run(fetch=True):
    av = AlphaVantage()
    if fetch and not av.key:
        print("note: no ALPHAVANTAGE_API_KEY - check prices not fetched; events flagged single_source")
    for m in sorted(glob.glob(os.path.join(ROOT, "events", "*", "*", "manifest.json"))):
        edir = os.path.dirname(m)
        season = os.path.basename(os.path.dirname(edir))
        try:
            grade_event(season, edir, fetch, av)
        except Exception as exc:
            print(f"{os.path.basename(edir)}: grading failed: {type(exc).__name__}: {exc}")


def commit_outcomes():
    from freeze import git, push_all
    # Nothing graded yet is the normal state before the first exit settles - `git add` on a path that
    # does not exist is fatal, and the nightly grade job failed on it every night from 2026-09-21.
    # A no-op must not look like a failure, or a real failure stops standing out.
    if not os.path.isdir(os.path.join(ROOT, "outcomes")):
        print("no outcomes/ yet - nothing has been graded, nothing to commit")
        return
    git("add", "outcomes")
    if not git("diff", "--cached", "--name-only"):
        print("nothing new to commit")
        return
    git("commit", "-q", "-m", f"Grade: outcomes as of {now_et():%Y-%m-%d %H:%M} ET (code, D001 + D005)"
        + chr(10) * 2 + "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>")
    print(f"pushed: {push_all()}")


if __name__ == "__main__":
    run(fetch="--no-fetch" not in sys.argv[1:])
    if "--commit" in sys.argv[1:]:
        commit_outcomes()
