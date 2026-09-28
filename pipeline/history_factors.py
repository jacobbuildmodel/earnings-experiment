"""The H factors of D006 §4, computed ONE way for the history study and for live events (source match).

Everything here is point-in-time: prices up to the snapshot-session close, SEC XBRL facts FILED before
the snapshot session, prints (SEC 8-K Item 2.02 + yfinance timestamp) before the event. No function
takes an outcome.
"""
import datetime
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ET  # noqa: E402
import sessions  # noqa: E402


class Calendar:
    """Trading sessions. Live: sessions.py (nyse.com table, 2026-2027). History: the session dates of
    SPY's daily bars, so no holiday table has to be typed from memory for 2022-2025."""

    def __init__(self, days=None):
        self.days = sorted(days) if days else None
        self._set = set(self.days) if days else None

    def is_session(self, d):
        return d in self._set if self.days else sessions.is_session(d)

    def shift(self, d, n):
        if not self.days:
            return sessions.shift(d, n)
        import bisect
        if n == 0:
            if d not in self._set:
                raise ValueError(f"{d} is not a trading session")
            return d
        i = bisect.bisect_left(self.days, d)
        if n > 0:
            j = i + n if d in self._set else i + n - 1
        else:
            j = i + n
        if not 0 <= j < len(self.days):
            raise ValueError(f"{d} shifted by {n} is outside the calendar")
        return self.days[j]


LIVE = Calendar()

# H8 revenue (D006 §4): the D004 §4 tags plus the "including assessed tax" variant some filers use (AAR)
REVENUE_TAGS = ("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet",
                "RevenueFromContractWithCustomerIncludingAssessedTax")


# --------------------------------------------------------------------------- event timing
def session_of(ts_et, cal=LIVE):
    """(date, session) of a timestamp: before 09:30 on a session -> BMO that day; at/after 16:00 -> AMC
    that day; a non-session day -> BMO on the next session; during the session -> (date, INTRADAY)."""
    d, t = ts_et.date(), ts_et.time()
    if not cal.is_session(d):
        return cal.shift(d, 1), "BMO"
    if t < datetime.time(9, 30):
        return d, "BMO"
    if t >= datetime.time(16, 0):
        return d, "AMC"
    return d, "INTRADAY"


def sec_prints(sec, cik, cal=LIVE):
    """Every 8-K with Item 2.02 in EDGAR's recent block: (date, session, accepted_et, accession)."""
    rec = sec.submission(cik)["filings"]["recent"]
    out = []
    for i, form in enumerate(rec["form"]):
        if form.startswith("8-K") and "2.02" in rec["items"][i].split(","):
            ts = datetime.datetime.fromisoformat(rec["acceptanceDateTime"][i].replace("Z", "+00:00")).astimezone(ET)
            try:
                d, s = session_of(ts, cal)
            except ValueError:
                continue
            out.append({"date": d.isoformat(), "session": s, "accepted_et": ts.isoformat(),
                        "accession": rec["accessionNumber"][i]})
    return out


def yf_prints(tk, limit=24, cal=LIVE):
    ed = tk.get_earnings_dates(limit=limit)
    out = []
    for ts in ed.index:
        try:
            d, s = session_of(ts.astimezone(ET), cal)
        except ValueError:  # beyond the calendar (an upcoming print)
            continue
        out.append({"date": d.isoformat(), "session": s, "yf_ts": ts.isoformat()})
    return out


def agreed_prints(sec_list, yf_list, cal=LIVE):
    """Prints where SEC and yfinance agree on the TRADE (D006 §2): the same entry and exit-A sessions.
    AMC on D and BMO on the next session are the same trade - same snapshot, entry and exit - and an 8-K
    is often filed the morning after an evening release, so matching labels would drop real prints.
    The event takes yfinance's date and session (the release; the 8-K is a filing about it).
    Returns (agreed, rejected)."""
    def window(p):
        if p["session"] not in ("BMO", "AMC"):
            return None
        try:
            t = timing(p["date"], p["session"], cal)
        except ValueError:
            return None
        return t["entry"], t["exit_A"]
    yf_by_window = {}
    for y in yf_list:
        w = window(y)
        if w:
            yf_by_window.setdefault(w, []).append(y)
    agreed, rejected = [], []
    for s in sec_list:
        w = window(s)
        if s["session"] == "INTRADAY":
            rejected.append({**s, "why": "intraday_8k"})
        elif w is None:
            rejected.append({**s, "why": "outside_calendar"})
        elif w in yf_by_window:
            y = yf_by_window[w][0]
            agreed.append({**s, "date": y["date"], "session": y["session"], "sec_date": s["date"],
                           "sec_session": s["session"], "yf_ts": y["yf_ts"]})
        else:
            rejected.append({**s, "why": "no_yfinance_same_trade"})
    # one print per trade (an amended 8-K for the same results is the same print)
    seen, uniq = set(), []
    for a in sorted(agreed, key=lambda x: x["accepted_et"]):
        key = (a["date"], a["session"])
        if key not in seen:
            seen.add(key)
            uniq.append(a)
    return sorted(uniq, key=lambda x: x["date"]), rejected


def timing(date, session, cal=LIVE):
    """D001 exit A and the D003 snapshot session."""
    d = datetime.date.fromisoformat(date)
    if session == "BMO":
        return {"snapshot": cal.shift(d, -2), "entry": cal.shift(d, -1), "exit_A": d, "reaction": d}
    return {"snapshot": cal.shift(d, -1), "entry": d, "exit_A": cal.shift(d, 1), "reaction": cal.shift(d, 1)}


# --------------------------------------------------------------------------- XBRL, point in time
def _duration_facts(facts, tag, as_of):
    """{end: (start, value, derived)} of ~3-month facts filed on/before as_of, latest filing wins; Q4 derived
    as annual minus three quarters where the 3-month fact is missing (same method as factors.py)."""
    units = facts.get("us-gaap", {}).get(tag, {}).get("units", {})
    rows = units.get("USD") or units.get("USD/shares") or []
    q, a = {}, {}
    for u in sorted(rows, key=lambda u: u.get("filed", "")):
        if u.get("form") not in ("10-Q", "10-K", "10-Q/A", "10-K/A") or u["filed"] > as_of or "start" not in u:
            continue
        days = (datetime.date.fromisoformat(u["end"]) - datetime.date.fromisoformat(u["start"])).days
        if 80 <= days <= 100:
            q[u["end"]] = (u["start"], u["val"], False)
        elif 350 <= days <= 380:
            a[u["end"]] = (u["start"], u["val"])
    for end, (start, val) in sorted(a.items()):
        inside = sorted((e, v) for e, (s, v, _) in q.items() if start <= s and e < end)
        if end not in q and len(inside) == 3:
            q4_start = (datetime.date.fromisoformat(inside[-1][0]) + datetime.timedelta(days=1)).isoformat()
            q[end] = (q4_start, val - sum(v for _, v in inside), True)
    return q


def _instant_latest(facts, taxonomy, tag, as_of, unit="USD"):
    rows = facts.get(taxonomy, {}).get(tag, {}).get("units", {}).get(unit, [])
    rows = [u for u in rows if u.get("filed", "9999") <= as_of]
    if not rows:
        return None, None
    last_filed = max(u["filed"] for u in rows)
    latest = [u for u in rows if u["filed"] == last_filed]
    end = max(u["end"] for u in latest)
    same = [u for u in latest if u["end"] == end]
    return sum(u["val"] for u in same) if taxonomy == "dei" else same[-1]["val"], end


def revenue_quarters(facts, as_of):
    rev = {}
    for tag in REVENUE_TAGS:
        for end, v in _duration_facts(facts, tag, as_of).items():
            rev.setdefault(end, v)
    return rev


def _near(ends, target, tol=25):
    """The key in `ends` closest to target date (within tol days), or None."""
    best = None
    for e in ends:
        gap = abs((datetime.date.fromisoformat(e) - target).days)
        if gap <= tol and (best is None or gap < best[0]):
            best = (gap, e)
    return best[1] if best else None


def sue(facts, as_of):
    """H6: seasonal-random-walk SUE of the latest quarter filed by as_of; None if < 6 differences."""
    eps = _duration_facts(facts, "EarningsPerShareDiluted", as_of)
    ends = sorted(eps)
    diffs = []
    for e in ends:
        prior = _near(ends, datetime.date.fromisoformat(e) - datetime.timedelta(days=364))
        if prior and prior != e:
            diffs.append((e, eps[e][1] - eps[prior][1]))
    if len(diffs) < 7:  # the latest + >= 6 before it
        return None, None
    last_end, last = diffs[-1]
    hist = [d for _, d in diffs[-9:-1]]
    if len(hist) < 6:
        return None, None
    m = sum(hist) / len(hist)
    sd = math.sqrt(sum((x - m) ** 2 for x in hist) / (len(hist) - 1))
    return (last / sd if sd > 0 else None), last_end


def seasonality(facts, as_of):
    """H7: 1 if the quarter about to be reported had the highest mean diluted EPS among the four quarter
    positions over the last three fiscal years, else 0; None if the history is too short."""
    eps = _duration_facts(facts, "EarningsPerShareDiluted", as_of)
    ends = sorted(eps)
    if not ends:
        return None
    latest = datetime.date.fromisoformat(ends[-1])
    target = latest + datetime.timedelta(days=91)
    means = []
    for pos in range(4):  # pos 0 = the position of the quarter being reported
        vals = []
        for yr in (1, 2, 3):
            e = _near(ends, target - datetime.timedelta(days=91 * pos + 364 * yr))
            if e:
                vals.append(eps[e][1])
        if len(vals) < 2:
            return None
        means.append(sum(vals) / len(vals))
    return 1 if means[0] == max(means) and means.count(max(means)) == 1 else 0


def ttm(q, as_of_end):
    """Sum of the four quarters ending at as_of_end, or None."""
    ends = sorted(e for e in q if e <= as_of_end)
    if not ends:
        return None, None
    last = datetime.date.fromisoformat(ends[-1])
    picks = [_near(ends, last - datetime.timedelta(days=91 * k)) for k in range(4)]
    if None in picks or len(set(picks)) < 4:
        return None, ends[-1]
    return sum(q[p][1] for p in picks), ends[-1]


def shares_pit(facts, as_of, max_age_days=200):
    """Shares outstanding known at as_of, for PIT size (D006 §2). First FRESH value (period end within
    max_age_days of as_of) of: dei cover-page shares (summed over classes), us-gaap balance-sheet shares,
    diluted weighted-average shares of the latest quarter. Some filers stopped tagging the cover page
    (ACMR: last dei value 2019), so a stale value must never be used. Returns (shares, source)."""
    ref = datetime.date.fromisoformat(as_of)

    def fresh(end):
        return end and (ref - datetime.date.fromisoformat(end)).days <= max_age_days

    v, end = _instant_latest(facts, "dei", "EntityCommonStockSharesOutstanding", as_of, unit="shares")
    if v and fresh(end):
        return v, "dei:EntityCommonStockSharesOutstanding"
    rows = [u for u in facts.get("us-gaap", {}).get("CommonStockSharesOutstanding", {}).get("units", {}).get("shares", [])
            if u.get("filed", "9999") <= as_of]
    if rows:
        last = max(rows, key=lambda u: (u["end"], u["filed"]))
        if fresh(last["end"]):
            return last["val"], "us-gaap:CommonStockSharesOutstanding"
    rows = [u for u in facts.get("us-gaap", {}).get("WeightedAverageNumberOfDilutedSharesOutstanding", {})
            .get("units", {}).get("shares", []) if u.get("filed", "9999") <= as_of and "start" in u
            and 80 <= (datetime.date.fromisoformat(u["end"]) - datetime.date.fromisoformat(u["start"])).days <= 100]
    if rows:
        last = max(rows, key=lambda u: (u["end"], u["filed"]))
        if fresh(last["end"]):
            return last["val"], "us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding (quarter)"
    return None, None


# --------------------------------------------------------------------------- prices
def unsplit_close(hist, splits, day):
    """The actual traded close of `day`: yfinance back-adjusts for later splits, so undo those."""
    c = float(hist.loc[hist.index.date == day, "Close"].iloc[0])
    for when, ratio in splits.items():
        if when.astimezone(ET).date() > day and ratio:
            c *= float(ratio)
    return c


def compute(snap, past, facts, adj, raw, splits, report_date, cal=LIVE):
    """All ten H factors for one event.

    snap: the snapshot session (date)       past: the agreed prints before this one, newest last
    facts: SEC companyfacts                 adj / raw: yfinance daily bars, auto_adjust True / False
    splits: yfinance splits series          report_date: the print date (date)
    """
    out = {}
    h = adj[adj.index.date <= snap].dropna(subset=["Close"])
    c, v = h["Close"], h["Volume"]
    r = c.pct_change()
    ok = len(c) and c.index[-1].date() == snap
    out["H1"] = float(c.iloc[-1] / c.iloc[-253] - 1) if ok and len(c) > 253 else None
    out["H2"] = float(c.iloc[-1] / c.iloc[-6] - 1) if ok and len(c) > 6 else None
    out["H3"] = float(r.iloc[-21:].max()) if ok and len(r) > 22 else None
    out["H4"] = float(r.iloc[-60:].std() * math.sqrt(252)) if ok and len(r) > 61 else None
    # H5: reaction-day volume at the previous four prints / mean daily volume of the 250 sessions to snapshot
    base = float(v.iloc[-250:].mean()) if ok and len(v) >= 250 else None
    vols = []
    for p in past[-4:]:
        rd = timing(p["date"], p["session"], cal)["reaction"]
        row = adj[adj.index.date == rd]
        if len(row):
            vols.append(float(row["Volume"].iloc[0]))
    out["H5"] = (sum(vols) / len(vols) / base) if base and len(vols) == 4 else None
    as_of = snap.isoformat()
    out["H6"], _ = sue(facts, as_of)
    out["H7"] = seasonality(facts, as_of)
    shares, out["shares_source"] = shares_pit(facts, as_of)
    close_actual = unsplit_close(raw, splits, snap) if ok and (raw.index.date == snap).any() else None
    cap = shares * close_actual if shares and close_actual else None
    out["market_cap_pit"] = cap
    rev_ttm, _ = ttm(revenue_quarters(facts, as_of), as_of)
    out["H8"] = rev_ttm / cap if rev_ttm is not None and cap else None
    prior = [p for p in past if 330 <= (report_date - datetime.date.fromisoformat(p["date"])).days <= 400]
    if prior:
        pd_ = min(prior, key=lambda p: abs((report_date - datetime.date.fromisoformat(p["date"])).days - 364))
        out["H9"] = (report_date - datetime.date.fromisoformat(pd_["date"])).days - 364
    else:
        out["H9"] = None
    op_ttm, _ = ttm(_duration_facts(facts, "OperatingIncomeLoss", as_of), as_of)
    assets, _ = _instant_latest(facts, "us-gaap", "Assets", as_of)
    out["H10"] = op_ttm / assets if op_ttm is not None and assets else None
    return out
