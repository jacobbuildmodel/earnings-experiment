"""D019 §3(b): the Layer-1 capture - code only; it diagnoses the reaction layer at Gate 1 and tests nothing.

    python pipeline/layer1.py capture <season> [<season> ...] [--commit]   # fetch what is missing, append-only
    python pipeline/layer1.py status <season>                              # coverage from the store, no fetch

After each print, what the company reported against what was expected:
- Events: every D009 SH-M / SH-W event in outcomes/shadow/<season>/graded.json (pipeline/shadow.py builds it) that
  is not void and printed before today (ET). One row per ticker and print date, whichever tracks hold it.
- EPS: estimate, reported and surprise (%) from yfinance's timestamped get_earnings_dates(), the row whose ET date
  is the print date (CLAUDE.md: .calendar is a day late for AMC); a near date is never taken. Captured once,
  when Reported EPS is in. Stored as Yahoo states them (its adjusted basis), never recomputed.
- Revenue: the quarterly actual from SEC EDGAR XBRL frames (/api/xbrl/frames/us-gaap/<concept>/USD/CY####Q#.json),
  concepts in CONCEPTS order: the CIK's row whose period ends before the print and at most MAX_LAG days before
  it. The shortest quarter is 12 weeks (84 days: the 16/12/12/12 retail calendar, e.g. ACI's ending 2026-09-12)
  and no print comes within 7 days of its quarter's end, so the previous quarter ends 91+ days before the print
  and is never taken while the new 10-Q is unfiled. The year-ago quarter is the same concept's row ending 365 +- 14 days
  earlier. Fiscal Q4 usually has no quarterly fact (the 10-K reports the year): missing, disclosed.
- Write-once per field: outcomes/layer1/<season>.jsonl, one row per (ticker, date, field) with its source tier,
  never rewritten (D001 §2: fetch once). A missing field is retried by later runs inside its window (EPS 30
  days, revenue 100 days after the print), then stays missing with its last reason. Nothing is filled.
- outcomes/layer1/<season>.json is the table rebuilt from the store on every run: values, sources and each
  missing field's reason. outcomes/ is fenced from every AI step.
"""
import datetime
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ET, ROOT, Sec, now_et, write_json  # noqa: E402

RULE = "D019_reframe_v1 §3(b)"
TRACKS = ("SH-M", "SH-W")
CONCEPTS = ("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
            "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet", "RevenuesNetOfInterestExpense")
MAX_LAG = 90           # days from the quarter's end to the print
YEAR_AGO_TOL = 14      # days around end - 365 (52/53-week years move by 7)
EPS_WINDOW = 30        # days after the print a missing EPS is retried
REVENUE_WINDOW = 100   # days after the print a missing revenue is retried (a 10-K can take 90)
YF_STOP = 15           # consecutive failed yfinance calls end this run's EPS fetch
EPS_FIELDS = (("eps_estimate", "EPS Estimate"), ("eps_reported", "Reported EPS"), ("eps_surprise_pct", "Surprise(%)"))
FIELDS = tuple(f for f, _ in EPS_FIELDS) + ("revenue", "revenue_year_ago")
YF = ("yfinance get_earnings_dates", "aggregator (Yahoo Finance; its adjusted EPS basis)")
SEC = ("SEC EDGAR XBRL frames", "filed (10-Q / 10-K XBRL; the frame's last-filed value)")
NO_QUARTER = (f"no quarterly fact ending <= {MAX_LAG} days before the print (fiscal Q4 is often annual-only; "
              "the 10-Q may be unfiled; a foreign filer reports in IFRS)")


def out_dir():
    return os.path.join(ROOT, "outcomes", "layer1")


def d(s):
    return datetime.date.fromisoformat(s)


class Store:
    """outcomes/layer1/<season>.jsonl - one row per (ticker, date, field), never rewritten."""

    def __init__(self, season):
        self.path = os.path.join(out_dir(), f"{season}.jsonl")
        self.rows, self.new = {}, []
        if os.path.exists(self.path):
            for line in open(self.path, encoding="utf-8"):
                r = json.loads(line)
                self.rows[(r["ticker"], r["date"], r["field"])] = r

    def get(self, t, date, field):
        r = self.rows.get((t, date, field))
        return None if r is None else r["value"]

    def add(self, t, date, field, value, src, detail):
        k = (t, date, field)
        if k in self.rows or value is None:
            return
        r = {"ticker": t, "date": date, "field": field, "value": value, "source": src[0], "tier": src[1],
             "detail": detail, "captured_et": now_et().isoformat(timespec="seconds")}
        self.rows[k] = r
        self.new.append(r)

    def save(self):
        if not self.new:
            return
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "a", encoding="utf-8", newline="\n") as f:
            for r in self.new:
                f.write(json.dumps(r) + "\n")
        self.new = []


def events(graded, today):
    """One row per (ticker, print date) among the non-void SH-M / SH-W events that printed before today."""
    out = {}
    for ev in graded:
        if ev.get("track") not in TRACKS or ev.get("void") or ev["date"] >= today.isoformat():
            continue
        row = out.setdefault((ev["ticker"], ev["date"]), {"ticker": ev["ticker"], "date": ev["date"],
                                                          "session": ev.get("session"), "tracks": []})
        row["tracks"].append(ev["track"])
    return [out[k] for k in sorted(out)]


# ---------------------------------------------------------------- EPS (yfinance)

def yf_rows(t):
    """[(timestamp, {column: value})] from yfinance get_earnings_dates(); raises when the call fails."""
    import yfinance as yf
    df = yf.Ticker(t).get_earnings_dates(limit=12)
    if df is None:
        return []
    return [(ts.to_pydatetime(), {c: row[c] for c in df.columns}) for ts, row in df.iterrows()]


def num(v):
    """A float, or None for a missing value (None, NaN, pandas NA)."""
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return None if x != x else x


def eps_of(rows, date):
    """({field: value}, yahoo timestamp) for the row whose ET date is the print date, or (None, reason)."""
    near = None
    for ts, cols in rows:
        x = ts.astimezone(ET)
        if x.date().isoformat() == date:
            if num(cols.get("Reported EPS")) is None:
                return None, "Yahoo's row for the date has no Reported EPS yet"
            return {f: num(cols.get(c)) for f, c in EPS_FIELDS}, x.isoformat()
        gap = abs((x.date() - d(date)).days)
        if near is None or gap < near[0]:
            near = (gap, x.date().isoformat())
    return None, f"no Yahoo row dated {date}" + (f" (nearest {near[1]})" if near else " (no rows)")


# ---------------------------------------------------------------- revenue (EDGAR XBRL frames)

def quarters(lo, hi):
    """Calendar quarters (CY####Q#) that overlap [lo, hi]."""
    out, y, q = [], lo.year, (lo.month - 1) // 3 + 1
    while (y, q) <= (hi.year, (hi.month - 1) // 3 + 1):
        out.append(f"CY{y}Q{q}")
        y, q = (y + 1, 1) if q == 4 else (y, q + 1)
    return out


def frames_for(date):
    """(current, year-ago) frames that can hold the quarter a print on `date` reports. A frame holds the
    periods that most closely fit its calendar quarter, so a period ending up to MAX_LAG days back can sit in
    the quarter before the one its end falls in."""
    D = d(date)
    cur = quarters(D - datetime.timedelta(days=MAX_LAG + 100), D)
    return cur, [f"CY{int(f[2:6]) - 1}{f[6:]}" for f in cur]


def frame_url(concept, frame):
    return f"https://data.sec.gov/api/xbrl/frames/us-gaap/{concept}/USD/{frame}.json"


def sec_frames(sec, keys):
    """{(concept, frame): {cik: row}}, None where the call failed. A 404 is an empty frame (no filer used the
    concept that quarter), not a failure."""
    import requests
    out = {}
    for concept, frame in sorted(keys):
        try:
            body = json.loads(sec.get(frame_url(concept, frame)))
            out[(concept, frame)] = {int(r["cik"]): r for r in body.get("data", [])}
        except requests.HTTPError as exc:
            gone = exc.response is not None and exc.response.status_code == 404
            out[(concept, frame)] = {} if gone else None
            if not gone:
                print(f"frames {concept} {frame}: {exc}")
        except (requests.RequestException, ValueError) as exc:
            out[(concept, frame)] = None
            print(f"frames {concept} {frame}: {type(exc).__name__}: {exc}")
    return out


def hits(frames, concept, names, cik, lo, hi):
    """The CIK's rows in these frames of one concept whose period ends in [lo, hi], latest end first."""
    rows = [dict(frames[(concept, f)][cik], frame=f) for f in names if cik in (frames.get((concept, f)) or {})]
    return sorted((r for r in rows if lo <= d(r["end"]) <= hi), key=lambda r: r["end"], reverse=True)


def detail(concept, r):
    return {"concept": concept, "frame": r["frame"], "start": r.get("start"), "end": r["end"], "accn": r.get("accn"),
            "cik": r.get("cik"), "unit": "USD"}


def revenue_of(frames, cik, date, stored=None):
    """({field: (value, detail)}, reason or None). `stored` (a captured actual's detail) pins the year-ago lookup to
    that row's concept and period, so the pair always comes from one concept. Any failed frame call blocks the
    event for this run: it could hide a higher-priority concept, and the store is write-once."""
    cur, ago = frames_for(date)
    names = [stored["concept"]] if stored else list(CONCEPTS)
    if any(frames.get((c, f)) is None for c in names for f in cur + ago):
        return {}, "an EDGAR frames call failed (retried next run)"
    D = d(date)
    for c in names:
        if stored:
            r, out = stored, {}
        else:
            now = hits(frames, c, cur, cik, D - datetime.timedelta(days=MAX_LAG), D - datetime.timedelta(days=1))
            if not now:
                continue
            r = now[0]
            out = {"revenue": (r["val"], detail(c, r))}
        e = d(r["end"]) - datetime.timedelta(days=365)
        prev = hits(frames, c, ago, cik, e - datetime.timedelta(days=YEAR_AGO_TOL), e + datetime.timedelta(days=YEAR_AGO_TOL))
        if prev:
            out["revenue_year_ago"] = (prev[0]["val"], detail(c, prev[0]))
        return out, None if prev else f"no year-ago quarter in {c}"
    return {}, NO_QUARTER


# ---------------------------------------------------------------- the run

def graded_events(season):
    src = os.path.join(ROOT, "outcomes", "shadow", season, "graded.json")
    if not os.path.exists(src):
        raise SystemExit(f"{src} missing - run `python pipeline/shadow.py grade {season}` first")
    return json.load(open(src, encoding="utf-8"))["events"]


def capture(season, sec=None, yf_get=yf_rows, frames_get=sec_frames, today=None, pause=0.4):
    today = today or now_et().date()
    evs = events(graded_events(season), today)
    store = Store(season)
    sec = sec or Sec(os.path.join(ROOT, "cache", "sec"))
    why = {}

    def note(ev, fields, reason):
        for f in fields:
            why.setdefault((ev["ticker"], ev["date"]), {})[f] = reason

    # EPS: one yfinance call per ticker, while Reported EPS is missing and the window is open
    eps_fields = [f for f, _ in EPS_FIELDS]
    todo = {}
    for ev in evs:
        if store.get(ev["ticker"], ev["date"], "eps_reported") is None and (today - d(ev["date"])).days <= EPS_WINDOW:
            todo.setdefault(ev["ticker"], []).append(ev)
    fails = 0
    for i, t in enumerate(sorted(todo)):
        if fails >= YF_STOP:
            for ev in todo[t]:
                note(ev, eps_fields, f"yfinance stopped answering ({YF_STOP} failed calls in a row)")
            continue
        try:
            rows = yf_get(t)
            fails = 0
        except Exception as exc:  # yfinance raises many types; any failure leaves the field missing
            fails += 1
            for ev in todo[t]:
                note(ev, eps_fields, f"yfinance failed: {type(exc).__name__}")
            continue
        for ev in todo[t]:
            got, info = eps_of(rows, ev["date"])
            if got is None:
                note(ev, eps_fields, info)
                continue
            for f in eps_fields:
                store.add(t, ev["date"], f, got[f], YF, {"yahoo_timestamp": info})
                if got[f] is None:
                    note(ev, [f], "Yahoo's row has no value for it")
        if i % 50 == 49:
            store.save()
        time.sleep(pause)
    store.save()

    # revenue: the frames every open event needs, fetched once this run
    open_ = [ev for ev in evs if (today - d(ev["date"])).days <= REVENUE_WINDOW
             and any(store.get(ev["ticker"], ev["date"], f) is None for f in ("revenue", "revenue_year_ago"))]
    ciks, keys = {}, set()   # ticker -> CIK, 0 (none) or the lookup's error
    for ev in open_:
        t = ev["ticker"]
        if t not in ciks:
            try:
                ciks[t] = sec.cik(t) or 0
            except Exception as exc:
                ciks[t] = f"SEC ticker lookup failed: {type(exc).__name__}"
        if isinstance(ciks[t], int) and ciks[t]:
            cur, ago = frames_for(ev["date"])
            keys |= {(c, f) for c in CONCEPTS for f in cur + ago}
    frames = frames_get(sec, keys) if keys else {}
    for ev in open_:
        t, date = ev["ticker"], ev["date"]
        cik = ciks[t]
        if not isinstance(cik, int) or not cik:
            note(ev, ["revenue", "revenue_year_ago"], cik or "no SEC CIK for the ticker")
            continue
        stored = store.rows.get((t, date, "revenue"))
        got, reason = revenue_of(frames, cik, date, stored["detail"] if stored else None)
        for f, (v, det) in got.items():
            store.add(t, date, f, v, SEC, det)
        if reason:
            note(ev, [f for f in ("revenue", "revenue_year_ago") if f not in got], reason)
    store.save()
    tab = table(season, evs, store, why, today)
    write_json(os.path.join(out_dir(), f"{season}.json"), tab)
    print_counts(tab)
    return tab


def table(season, evs, store, why, today):
    """Every event with each field's stored value or why it is missing. A reason from an earlier run is kept
    when this run did not try (its window closed)."""
    p = os.path.join(out_dir(), f"{season}.json")
    prior = {}
    if os.path.exists(p):
        for e in json.load(open(p, encoding="utf-8")).get("events", []):
            prior[(e["ticker"], e["date"])] = {f: v.get("missing") for f, v in e["fields"].items() if "missing" in v}
    rows = []
    for ev in evs:
        k = (ev["ticker"], ev["date"])
        age = (today - d(ev["date"])).days
        fields = {}
        for f in FIELDS:
            r = store.rows.get((*k, f))
            if r:
                fields[f] = {key: r[key] for key in ("value", "source", "tier", "detail", "captured_et")}
                continue
            window = EPS_WINDOW if f.startswith("eps") else REVENUE_WINDOW
            reason = why.get(k, {}).get(f) or prior.get(k, {}).get(f) or "not tried yet"
            fields[f] = {"value": None, "missing": reason, "final": age > window}
        rows.append({**ev, "fields": fields})
    return {"season": season, "rule": RULE, "captured_by": "pipeline/layer1.py",
            "run_et": now_et().isoformat(timespec="seconds"), "store": f"outcomes/layer1/{season}.jsonl",
            "windows_days": {"eps": EPS_WINDOW, "revenue": REVENUE_WINDOW}, "events": rows}


def print_counts(tab):
    n = len(tab["events"])
    print(f"{tab['season']} Layer 1: {n} printed SH-M / SH-W events")
    for f in FIELDS:
        got = sum(1 for e in tab["events"] if e["fields"][f]["value"] is not None)
        reasons = {}
        for e in tab["events"]:
            m = e["fields"][f].get("missing")
            if m:
                key = m.split(" (")[0]
                reasons[key] = reasons.get(key, 0) + 1
        top = "; ".join(f"{c} {r}" for r, c in sorted(reasons.items(), key=lambda x: -x[1])[:3])
        print(f"  {f:18s} {got:5d} / {n}" + (f"   missing: {top}" if top else ""))


def status(season):
    today = now_et().date()
    tab = table(season, events(graded_events(season), today), Store(season), {}, today)
    print_counts(tab)
    return tab


def busy(now):
    """Inside the S2 / paper window (90 min before the close to 30 min after it, on a session): no commit."""
    from sessions import close_time, is_session
    if not is_session(now.date()):
        return False
    close = datetime.datetime.combine(now.date(), close_time(now.date()), ET)
    return close - datetime.timedelta(minutes=90) <= now < close + datetime.timedelta(minutes=30)


def commit(msg):
    from freeze import git, push_all
    if busy(now_et()):
        print("inside the S2 window - not committing; the next run commits the store")
        return
    git("add", os.path.join("outcomes", "layer1"))
    if not git("diff", "--cached", "--name-only"):
        print("nothing new to commit")
        return
    git("commit", "-q", "-m", msg)
    print(f"pushed: {push_all()}")


if __name__ == "__main__":
    a = sys.argv[1:]
    seasons = [x for x in a[1:] if not x.startswith("--")]
    if a[:1] == ["capture"] and seasons:
        for s in seasons:
            capture(s)
        if "--commit" in a:
            commit(f"Layer 1 capture {now_et():%Y-%m-%d %H:%M} ET (code, D019 §3(b))")
    elif a[:1] == ["status"] and seasons:
        for s in seasons:
            status(s)
    else:
        raise SystemExit(__doc__)
