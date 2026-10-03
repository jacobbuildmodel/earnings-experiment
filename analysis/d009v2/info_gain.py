"""D009 v2 draft - how much information would off-season sessions add to the market-wide shadow (SH-M)?
Exploratory, on the D006 history (analysis/history/graded_events.json, 2022-09 -> 2026-09, allowlist names).
No network. Output: analysis/d009v2/info_gain.txt. Written 2026-10-03 (cloud session).

    python analysis/d009v2/info_gain.py

In-season = a 6-week window starting the 2nd Monday of Jan/Apr/Jul/Oct (Season A: Oct 12 - Nov 20).
Information about the mean per entry session = 1 / (sd_session^2 + sd_stock^2 / k), k = events that session.
"""
import json, datetime as dt, numpy as np, collections
g = json.load(open('analysis/history/graded_events.json'))['events']
ev = [e for e in g if e.get('raw_return') is not None and e.get('entry')]
print("events with return", len(ev), "of", len(g))
def second_monday(y, m):
    d = dt.date(y, m, 1)
    mondays = [d + dt.timedelta(days=i) for i in range(14) if (d + dt.timedelta(days=i)).weekday() == 0]
    return mondays[1]
def in_season(day):
    d = dt.date.fromisoformat(day)
    for y in (d.year - 1, d.year):
        for m in (1, 4, 7, 10):
            lo = second_monday(y, m); hi = lo + dt.timedelta(days=39)
            if lo <= d <= hi: return True
    return False
for e in ev:
    e['net'] = e['raw_return'] - 0.002
    e['ins'] = in_season(e['entry'])
def comps(rows):
    by = collections.defaultdict(list)
    for e in rows: by[e['entry']].append(e['net'])
    groups = list(by.values()); N = sum(map(len, groups)); G = len(groups)
    ybar = np.mean([x for gg in groups for x in gg])
    ssw = sum(((np.array(gg) - np.mean(gg)) ** 2).sum() for gg in groups)
    ssb = sum(len(gg) * (np.mean(gg) - ybar) ** 2 for gg in groups)
    msw = ssw / (N - G); msb = ssb / (G - 1)
    n0 = (N - sum(len(gg) ** 2 for gg in groups) / N) / (G - 1)
    s2s = max(0.0, (msb - msw) / n0)
    ks = [len(gg) for gg in groups]
    return dict(N=N, G=G, mean=float(ybar), sd_session=float(s2s ** .5), sd_stock=float(msw ** .5), k_mean=float(np.mean(ks)), k_median=float(np.median(ks)),
                frac_k_le3=float(np.mean([k <= 3 for k in ks])))
for lab, rows in [("all", ev), ("in-season", [e for e in ev if e['ins']]), ("off-season", [e for e in ev if not e['ins']])]:
    c = comps(rows)
    print(lab, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in c.items()})
# trading days by year with any print, off-season
ys = collections.Counter(); yt = collections.Counter()
import pandas as pd
days = pd.bdate_range('2022-10-01', '2026-09-18')
off = [d.date().isoformat() for d in days if not in_season(d.date().isoformat())]
withp = {e['entry'] for e in ev if not e['ins']}
print("off-season weekdays", len(off), "with >=1 allowlist entry", len(withp & set(off)), round(len(withp & set(off)) / len(off), 3))
print("date range", min(e['entry'] for e in ev), max(e['entry'] for e in ev))

print("\n--- information model ---")
ss, se_ = 0.018, 0.0914   # in-season split (the off-season estimate is unstable: k median 1)
I = lambda k: 0.0 if k <= 0 else 1.0 / (ss**2 + se_**2 / k)
# empirical in-season session-size distribution of the allowlist, scaled to the market-wide ~45/session
ins_k = collections.Counter(e['entry'] for e in ev if e['ins'])
yrs = (dt.date(2026, 9, 1) - dt.date(2022, 9, 21)).days / 365.25
c = 45 / np.mean(list(ins_k.values()))
I_in_season = sum(I(c * k) for k in ins_k.values()) / (yrs * 4)
I_flat45 = 29 * I(45)
print(f"scale c={c:.2f}; info per season: flat 29x45 = {I_flat45:.0f}; empirical shape = {I_in_season:.0f}")
print("per-session info relative to an in-season session (flat 45):", {k: round(I(k) / I(45), 3) for k in (1, 2, 3, 5, 8, 15)})
off_sessions_year = 127   # ~252 sessions - 4 x 29 in-season, less ~9 holidays
print("\nyearly gain (off-season info / in-season info, flat 45 in-season, 4 seasons):")
print("share_with_print  " + "  ".join(f"k={k}" for k in (2, 3, 5, 8)))
for p in (0.4, 0.6, 0.8):
    print(f"{p:<16}  " + "  ".join(f"{p*off_sessions_year*I(k)/(4*I_flat45):+.0%}" for k in (2, 3, 5, 8)))
print("\nsame with the empirical in-season shape:")
for p in (0.4, 0.6, 0.8):
    print(f"{p:<16}  " + "  ".join(f"{p*off_sessions_year*I(k)/(4*I_in_season):+.0%}" for k in (2, 3, 5, 8)))
# the empirical allowlist off-season distribution scaled by the same c
off_k = collections.Counter(e['entry'] for e in ev if not e['ins'])
I_off_emp = sum(I(c * k) for k in off_k.values()) / yrs
print(f"\nempirical off-season (allowlist sessions x c={c:.1f}): {len(off_k)/yrs:.0f} sessions/yr, mean k {c*np.mean(list(off_k.values())):.1f}, "
      f"gain {I_off_emp/(4*I_in_season):+.0%} (empirical in-season) / {I_off_emp/(4*I_flat45):+.0%} (flat)")
# the A+B pooled verdict: with vs without the Nov 23 - Jan 15 off-season (~35 sessions)
mu = 0.0065
for lab, info in [("A+B (v1)", 2 * I_flat45), ("A+B + off-season between, 60% x k=3", 2 * I_flat45 + 0.6 * 35 * I(3)),
                  ("A+B + off-season between, 60% x k=8", 2 * I_flat45 + 0.6 * 35 * I(8))]:
    print(f"{lab}: expected t at +0.65% = {mu*info**.5:.2f}; at +0.30% = {0.003*info**.5:.2f}")

import sys; sys.path.insert(0, 'pipeline'); import report
y = np.array([e['net'] for e in ev]); x = np.array([0.0 if e['ins'] else 1.0 for e in ev]); gg = np.array([e['entry'] for e in ev])
X = np.column_stack([np.ones_like(x), x])
b, s, t = report.ols_k(y, X, gg, 1)
print(f"\noff minus in-season net mean: {b*100:+.2f} pts, clustered se {s*100:.2f}, t {t:.2f}")
for lab, m in [("in", x == 0), ("off", x == 1)]:
    b, s, t = report.ols_k(y[m], np.ones((m.sum(), 1)), gg[m], 0)
    print(f"{lab}: n {m.sum()} sessions {len(set(gg[m]))} mean {b*100:+.2f}% se {s*100:.2f} t {t:.2f} hit {np.mean(y[m] + 0.002 > 0):.3f}")

# would the preceding season's S1 capture (names printing IN that season window) contain the off-season reporters?
def season_of(day):
    d = dt.date.fromisoformat(day)
    for y in (d.year - 1, d.year):
        for m in (1, 4, 7, 10):
            lo = second_monday(y, m); hi = lo + dt.timedelta(days=39)
            if lo <= d <= hi: return (lo, hi)
    return None
seasons = sorted({season_of(e['entry']) for e in ev if e['ins']})
in_by = collections.defaultdict(set)
for e in ev:
    if e['ins']: in_by[season_of(e['entry'])].add(e['ticker'])
hit = tot = 0
for e in ev:
    if e['ins']: continue
    d0 = dt.date.fromisoformat(e['entry'])
    prev = [s for s in seasons if s[1] < d0]
    if not prev: continue
    tot += 1; hit += e['ticker'] in in_by[prev[-1]]
print(f"\noff-season prints whose ticker printed in the PRECEDING season window: {hit}/{tot} = {hit/tot:.0%}")
