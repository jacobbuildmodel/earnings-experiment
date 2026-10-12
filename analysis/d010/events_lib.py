"""D010 §3 event construction (shared by the extractor and run_d010.py). Reads only raw/ files."""
import pandas as pd, bisect

PERIOD = ('2019-01-01', '2026-09-18')


def load_sessions(raw):
    return sorted(pd.read_csv(f'{raw}/sessions.csv')['date'])


def build_events(raw):
    """Return (events_df, excluded) where excluded is a dict of counts for rows that are not events."""
    sess = load_sessions(raw)
    cal = pd.read_csv(f'{raw}/calendar.csv', keep_default_na=False)
    cal = cal[(cal['date'] >= PERIOD[0]) & (cal['date'] <= PERIOD[1])]
    excl = {'when_other_or_missing': int((~cal['when'].isin(['Before market open', 'After market close'])).sum())}
    c = cal[cal['when'].isin(['Before market open', 'After market close'])].copy()
    sset = set(sess)
    out = []; nonsess = 0; nodata = 0
    for sym, d, w in zip(c['act_symbol'], c['date'], c['when']):
        if w.startswith('Before'):
            if d not in sset:
                nonsess += 1; continue
            R = d
        else:
            i = bisect.bisect_right(sess, d)  # next session strictly after D
            if i >= len(sess):
                nodata += 1; continue
            R = sess[i]
        j = bisect.bisect_left(sess, R)
        if j == 0:
            nodata += 1; continue
        out.append((sym, d, w, R, sess[j - 1]))
    excl['bmo_D_not_a_session'] = nonsess
    excl['no_session_data'] = nodata
    ev = pd.DataFrame(out, columns=['symbol', 'D', 'when', 'R', 'P'])
    n0 = len(ev)
    ev = ev.drop_duplicates(['symbol', 'R']).reset_index(drop=True)  # two calendar rows -> same reaction session
    excl['duplicate_symbol_R'] = n0 - len(ev)
    return ev, excl


def select_contract(chain, R):
    """chain: rows of P's chain for one symbol (columns expiration, strike, call_put, delta, numeric/str dates).
    Returns (expiration, strike) or (None, None) -> VOID no_expiry (or no call delta)."""
    exps = sorted({e for e in chain['expiration'] if e > R})
    if not exps:
        return None, None
    ex = exps[0]
    c = chain[(chain['expiration'] == ex) & (chain['call_put'] == 'Call') & chain['delta'].notna()].copy()
    if c.empty:
        return None, None
    c['dist'] = (c['delta'] - 0.5).abs()
    c = c.sort_values(['dist', 'strike'])  # ties -> lower strike
    return ex, float(c.iloc[0]['strike'])
