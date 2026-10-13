"""D010 v2 (registry/D010_exploration_options_v2.md). Reads raw/ and events_valid.csv; fetches SPY once into
raw/spy_v2.csv. Deterministic. EXPLORATION ONLY. Same CR0-by-R-date statistics as run_d010.py (v1)."""
import json, math, os, sys, datetime
import numpy as np, pandas as pd
from scipy import stats
from scipy.optimize import brentq

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, 'raw')
HALF = '2025-10-15'


# ---------------------------------------------------------------- data
def spy():
    p = os.path.join(RAW, 'spy_v2.csv')
    if not os.path.exists(p):
        import yfinance as yf
        h = yf.Ticker('SPY').history(start='2019-12-01', end='2026-10-01', auto_adjust=False)
        df = pd.DataFrame({'date': [i.strftime('%Y-%m-%d') for i in h.index], 'close': h['Close'].values})
        df.to_csv(p, index=False, lineterminator='\n')
        json.dump({'source': 'yfinance SPY daily Close auto_adjust=False', 'start': '2019-12-01', 'end': '2026-10-01',
                   'fetched_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'), 'rows': len(df)},
                  open(os.path.join(RAW, 'spy_v2.manifest.json'), 'w'), indent=1)
    return dict(pd.read_csv(p).itertuples(index=False, name=None))


ev = pd.read_csv(os.path.join(HERE, 'events_valid.csv'))
p2 = pd.read_csv(os.path.join(RAW, 'opt_p2.csv.gz'))
px = pd.read_csv(os.path.join(RAW, 'prices.csv.gz'))
close = {(s, d): c for s, d, c in zip(px.symbol, px.date, px.close)}
splits = px[px.split != 0][['symbol', 'date']]
SPY = spy()
Q = {(r.act_symbol, r.date, r.expiration, round(r.strike, 2), r.call_put): (r.bid, r.ask) for r in p2.itertuples()}


def bs(S, K, T, s, call):
    if s <= 0 or T <= 0:
        return max(0.0, (S - K) if call else (K - S))
    d1 = (math.log(S / K) + 0.5 * s * s * T) / (s * math.sqrt(T))
    d2 = d1 - s * math.sqrt(T)
    N = stats.norm.cdf
    return S * N(d1) - K * N(d2) if call else K * N(-d2) - S * N(-d1)


def iv(price, S, K, T, call):
    lo = max(0.0, (S - K) if call else (K - S))
    hi = S if call else K
    if not (lo < price < hi):
        return None
    f = lambda s: bs(S, K, T, s, call) - price
    try:
        if f(0.001) > 0 or f(20.0) < 0:
            return None
        return brentq(f, 0.001, 20.0, xtol=1e-10, maxiter=200)
    except ValueError:
        return None


def split_between(sym, a, b):
    return bool(len(splits[(splits.symbol == sym) & (splits.date > a) & (splits.date <= b)]))


Y, Z, voids = [], [], {'Y': {}, 'Z': {}}
def void(fam, why):
    voids[fam][why] = voids[fam].get(why, 0) + 1

for e in ev.itertuples():
    k = round(e.strike, 2)
    c, p = Q.get((e.symbol, e.P, e.expiration, k, 'Call')), Q.get((e.symbol, e.P, e.expiration, k, 'Put'))
    (cb, ca), (pb, pa) = c, p                        # v1 guaranteed both legs exist, bids > 0, not crossed
    S = e.spot_P
    cm, pm = (cb + ca) / 2, (pb + pa) / 2
    liquid = (ca - cb) / cm <= 0.10 and (pa - pb) / pm <= 0.10
    near = (pd.Timestamp(e.expiration) - pd.Timestamp(e.R)).days <= 7
    base = dict(symbol=e.symbol, R=e.R, P=e.P, expiration=e.expiration, strike=k, liquid=liquid, near=near)
    # ---- family Y: hold to expiry
    sx = close.get((e.symbol, e.expiration))
    if sx is None:
        void('Y', 'no_expiry_close')
    elif split_between(e.symbol, e.P, e.expiration):
        void('Y', 'split')
    else:
        pay = abs(sx - k)
        Y.append(dict(base, short_hte=(cb + pb - pay) / S, short_hte_mid=(cm + pm - pay) / S, long_hte=(pay - ca - pa) / S))
    # ---- family Z: call-put IV spread vs the reaction
    if split_between(e.symbol, e.P, e.R):
        void('Z', 'split'); continue
    if SPY.get(e.P) is None or SPY.get(e.R) is None:
        void('Z', 'no_spy'); continue
    T = (pd.Timestamp(e.expiration) - pd.Timestamp(e.P)).days / 365
    ic, ip = iv(cm, S, k, T, True), iv(pm, S, k, T, False)
    if ic is None or ip is None:
        void('Z', 'no_iv'); continue
    rx = (close[(e.symbol, e.R)] / S - 1) - (SPY[e.R] / SPY[e.P] - 1)
    Z.append(dict(base, ivs=ic - ip, iv_call=ic, iv_put=ip, rx=rx))

Y = pd.DataFrame(Y).sort_values(['R', 'symbol']).reset_index(drop=True)
Z = pd.DataFrame(Z).sort_values(['R', 'symbol']).reset_index(drop=True)
CUTS = [float(Z.ivs.quantile(1 / 3)), float(Z.ivs.quantile(2 / 3))]
Z['tercile'] = np.where(Z.ivs <= CUTS[0], 1, np.where(Z.ivs <= CUTS[1], 2, 3))


# ---------------------------------------------------------------- statistics (v1's, plus a clustered slope)
def mean_t(x, dates):
    n = len(x)
    if n == 0: return None, None, None, 0
    x = np.asarray(x, float); m = x.mean()
    s = pd.Series(x - m).groupby(np.asarray(dates)).sum()
    G = len(s); se = math.sqrt(float((s ** 2).sum())) / n
    return float(m), float(se), (float(m / se) if se > 0 else None), G


def slope_t(y, x, dates):
    """OLS y = a + b x; CR0 cluster-robust se of b by R date. Returns (b, se, t, G)."""
    y, x = np.asarray(y, float), np.asarray(x, float)
    if len(y) < 3: return None, None, None, 0
    X = np.column_stack([np.ones_like(x), x])
    XtXi = np.linalg.inv(X.T @ X)
    b = XtXi @ X.T @ y
    u = y - X @ b
    g = pd.Series(range(len(y))).groupby(np.asarray(dates)).apply(list)
    M = sum(np.outer(X[i].T @ u[i], X[i].T @ u[i]) for i in (np.array(ix) for ix in g))
    V = XtXi @ M @ XtXi
    se = math.sqrt(V[1, 1])
    return float(b[1]), float(se), (float(b[1] / se) if se > 0 else None), len(g)


def p_from_t(t, G, side='gt'):
    if t is None or G < 2: return 1.0
    return float(1 - stats.t.cdf(t, G - 1)) if side == 'gt' else float(2 * (1 - stats.t.cdf(abs(t), G - 1)))


def describe(x):
    x = np.asarray(x, float)
    if len(x) == 0: return {}
    p5 = np.percentile(x, 5)
    k = math.ceil(0.01 * len(x))
    keep = np.argsort(-np.abs(x))[k:]
    return dict(median=float(np.median(x)), hit_rate=float((x > 0).mean()), worst_1pct=float(np.percentile(x, 1)),
                cvar_5=float(x[x <= p5].mean()), largest_loss=float(x.min()), mean_without_top1pct=float(x[keep].mean()))


def run(Y, Z, tag):
  tests = []
  def add(tid, desc, df, kind, col=None):
      n, G = len(df), df.R.nunique() if len(df) else 0
      if kind == 'mean':
          est, se, t, G = mean_t(df[col], df.R)
          halves = [mean_t(h[col], h.R)[0] for h in (df[df.R < HALF], df[df.R >= HALF])]
          d = describe(df[col])
      elif kind == 'slope':
          est, se, t, G = slope_t(df.rx, df.ivs, df.R)
          halves = [slope_t(h.rx, h.ivs, h.R)[0] for h in (df[df.R < HALF], df[df.R >= HALF])]
          d = {}
      else:  # tercile 3 - tercile 1
          sub = df[df.tercile.isin([1, 3])]
          est, se, t, G = slope_t(sub.rx, (sub.tercile == 3).astype(float), sub.R)
          def hd(h):
              h = h[h.tercile.isin([1, 3])]
              return slope_t(h.rx, (h.tercile == 3).astype(float), h.R)[0] if h.tercile.nunique() == 2 else None
          halves = [hd(df[df.R < HALF]), hd(df[df.R >= HALF])]
          d = {'mean_t3': float(df[df.tercile == 3].rx.mean()), 'mean_t1': float(df[df.tercile == 1].rx.mean())}
      insuff = n < 30 or G < 10
      tests.append(dict(id=tid, sample=desc, n=n, R_dates=int(G), estimate=est, se=se, t=t, p=p_from_t(t, G),
                        halves=halves, insufficient=bool(insuff), **d))

  add('Y1', 'all', Y, 'mean', 'short_hte')
  add('Y2', 'liquid', Y[Y.liquid], 'mean', 'short_hte')
  add('Y3', 'liquid and near', Y[Y.liquid & Y.near], 'mean', 'short_hte')
  add('Y4', 'all', Y, 'mean', 'long_hte')
  add('Y5', 'liquid', Y[Y.liquid], 'mean', 'long_hte')
  add('Z1', 'all with ivs (slope)', Z, 'slope')
  add('Z2', 'all with ivs (T3 - T1)', Z, 'tdiff')
  add('Z3', 'liquid with ivs (slope)', Z[Z.liquid], 'slope')
  add('Z4', 'all with ivs: tercile 3 mean rx', Z[Z.tercile == 3], 'mean', 'rx')

  # BH over all 9
  ps = np.array([t['p'] for t in tests]); m = len(ps); order = np.argsort(ps)
  q = np.empty(m); prev = 1.0
  for rank, i in reversed(list(enumerate(order, 1))):
      prev = min(prev, ps[i] * m / rank); q[i] = prev
  for t, qi in zip(tests, q):
      t['q'] = float(qi)
      same = all(h is not None and t['estimate'] is not None and np.sign(h) == np.sign(t['estimate']) for h in t['halves'])
      t['finding'] = bool(qi < 0.10 and t['t'] is not None and abs(t['t']) > 3 and same and not t['insufficient'])

  desc = {'Y_short_hte_mid_all': float(Y.short_hte_mid.mean()), 'Y_short_hte_mid_liquid': float(Y[Y.liquid].short_hte_mid.mean()),
          'Y_n': len(Y), 'Y_liquid_n': int(Y.liquid.sum()), 'Y_liquid_near_n': int((Y.liquid & Y.near).sum()),
          'Z_n': len(Z), 'Z_share_missing_ivs': voids['Z'].get('no_iv', 0) / len(ev), 'ivs_tercile_cuts': CUTS,
          'ivs_mean': float(Z.ivs.mean()), 'ivs_median': float(Z.ivs.median())}
  out = {'rule': 'D010_exploration_options_v2', 'events_in': len(ev), 'voids': voids, 'tests': tests, 'descriptive': desc,
         'findings': [t['id'] for t in tests if t['finding']]}
  json.dump(out, open(os.path.join(HERE, f'results_v2{tag}.json'), 'w', newline='\n'), indent=1, sort_keys=True)
  for t in tests:
      print(f"{t['id']} {t['sample']:32s} n={t['n']:4d} G={t['R_dates']:3d} est={t['estimate'] * 100 if t['estimate'] is not None else float('nan'):+.3f}% "
            f"t={t['t'] if t['t'] is not None else float('nan'):+.2f} q={t['q']:.3f} halves={[None if h is None else round(h * 100, 3) for h in t['halves']]} "
            f"{'FINDING' if t['finding'] else ''}{' insufficient' if t['insufficient'] else ''}")
  print(json.dumps(desc), voids)


# As frozen (D010 v2 §2-§4).
run(Y, Z, '')
# Disclosed post-hoc correction (REPORT_v2.md): yfinance's "unadjusted" Close is split- and spin-off-adjusted
# retroactively, so for some events spot and strike sit on different scales. Events whose v1 strike / spot_P is
# outside [0.8, 1.25] are dropped (an outcome-free criterion; 16 events). Same tests, same BH over 9.
_bad = set(zip(ev.symbol[(ev.strike / ev.spot_P > 1.25) | (ev.strike / ev.spot_P < 0.8)],
               ev.P[(ev.strike / ev.spot_P > 1.25) | (ev.strike / ev.spot_P < 0.8)]))
_keep = lambda df: df[[(a, b) not in _bad for a, b in zip(df.symbol, df.P)]].reset_index(drop=True)
Zc = _keep(Z)
run(_keep(Y), Zc, '_scalefix')
