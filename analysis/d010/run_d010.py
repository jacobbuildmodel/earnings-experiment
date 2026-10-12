"""D010 v1 (registry/D010_exploration_options_v1.md) sections 3-5. Reads ONLY raw/. Deterministic. EXPLORATION ONLY.
Choices the spec leaves open (stated in REPORT.md): CR0 cluster-robust SE by R date; one-sided p from t with G-1 df;
'insufficient' = fewer than 30 events OR fewer than 10 R dates; worst 1% = 1st percentile (linear interpolation);
CVaR5 = mean of values <= 5th percentile; 'without 1% largest' drops ceil(1% of n) events with the largest |statistic|."""
import json, math, numpy as np, pandas as pd
from scipy import stats
import events_lib as E
RAW = 'raw'
ev, excl = E.build_events(RAW)
px = pd.read_csv(f'{RAW}/prices.csv.gz')
close = {(s, d): c for s, d, c in zip(px.symbol, px.date, px.close)}
splits = px[px.split > 0]
p1 = pd.read_csv(f'{RAW}/opt_p1.csv.gz'); p2 = pd.read_csv(f'{RAW}/opt_p2.csv.gz'); q = pd.read_csv(f'{RAW}/opt_q.csv.gz')
U = json.load(open('../history/universe.json')); clusters = U['clusters']


def idx(df):
    return {(r.act_symbol, r.date, r.expiration, round(r.strike, 2), r.call_put): (r.bid, r.ask) for r in df.itertuples()}
I2 = idx(p2); IQ = idx(q)
chains = {k: g for k, g in p1.groupby(['act_symbol', 'date'])}
rows = []; voids = []; nq_detail = {}
for e in ev.itertuples():
    def void(reason, detail=None):
        voids.append((e.symbol, e.R, e.R[:4], reason))
        if detail: nq_detail[detail] = nq_detail.get(detail, 0) + 1
    ch = chains.get((e.symbol, e.P))
    if ch is None:
        void('no_quote', 'no_P_chain_rows'); continue
    ex, k = E.select_contract(ch, e.R)
    if ex is None:
        void('no_expiry'); continue
    k = round(k, 2)
    qs = [I2.get((e.symbol, e.P, ex, k, cp)) for cp in ('Call', 'Put')] + [IQ.get((e.symbol, e.R, ex, k, cp)) for cp in ('Call', 'Put')]
    if any(x is None for x in qs[:2]):
        void('no_quote', 'P_leg_missing'); continue
    if any(x is None for x in qs[2:]):
        void('no_quote', 'Q_leg_missing'); continue
    if any(pd.isna(a) or pd.isna(b) for a, b in qs):
        void('no_quote', 'null_bid_or_ask'); continue
    (cbP, caP), (pbP, paP), (cbQ, caQ), (pbQ, paQ) = qs
    if cbP <= 0 or pbP <= 0:
        void('no_quote', 'P_bid_nonpositive'); continue
    if caP < cbP or paP < pbP or caQ < cbQ or paQ < pbQ:
        void('crossed'); continue
    sp = close.get((e.symbol, e.P)); sq = close.get((e.symbol, e.R))
    if sp is None or sq is None:
        void('no_quote', 'spot_missing'); continue
    if len(splits[(splits.symbol == e.symbol) & (splits.date > e.P) & (splits.date <= e.R)]):
        void('split'); continue
    midP = (cbP + caP + pbP + paP) / 2; midQ = (cbQ + caQ + pbQ + paQ) / 2
    rows.append(dict(symbol=e.symbol, R=e.R, P=e.P, year=int(e.R[:4]), expiration=ex, strike=k, spot_P=sp, spot_Q=sq,
                     short_exec=(cbP + pbP - caQ - paQ) / sp, long_exec=(cbQ + pbQ - caP - paP) / sp,
                     short_mid=(midP - midQ) / sp, implied=midP / sp, realized=abs(sq - sp) / sp,
                     cluster=clusters[e.symbol]['cluster']))
D = pd.DataFrame(rows)
D['ratio'] = D['realized'] / D['implied']
D = D.sort_values(['R', 'symbol']).reset_index(drop=True)
vd = pd.DataFrame(voids, columns=['symbol', 'R', 'year', 'reason'])
reasons = ['no_expiry', 'no_quote', 'crossed', 'split']
void_tab = {r: {'total': int((vd.reason == r).sum()), 'by_year': {str(y): int(n) for y, n in vd[vd.reason == r].groupby('year').size().items()}} for r in reasons}

CUTS = [float(D.implied.quantile(1 / 3)), float(D.implied.quantile(2 / 3))]
D['tercile'] = np.where(D.implied <= CUTS[0], 1, np.where(D.implied <= CUTS[1], 2, 3))


def mean_t(x, dates):
    """mean and CR0 cluster-robust t by R date; returns (mean, se, t, G)."""
    n = len(x)
    if n == 0: return None, None, None, 0
    x = np.asarray(x, float); m = x.mean()
    s = pd.Series(x - m).groupby(np.asarray(dates)).sum()
    G = len(s); se = math.sqrt(float((s ** 2).sum())) / n
    t = m / se if se > 0 else None
    return float(m), float(se), (float(t) if t is not None else None), G


def p_from_t(t, G, side):
    if t is None or G < 2: return 1.0
    return float(1 - stats.t.cdf(t, G - 1)) if side == 'gt' else float(2 * (1 - stats.t.cdf(abs(t), G - 1)))


def describe(x):
    x = np.asarray(x, float)
    if len(x) == 0: return None
    p1_ = np.percentile(x, 1); p5 = np.percentile(x, 5)
    return dict(median=float(np.median(x)), hit_rate=float((x > 0).mean()), worst_1pct=float(p1_),
                cvar_5=float(x[x <= p5].mean()), largest_loss=float(x.min()), mean=float(x.mean()))


def trimmed(df, col):
    k = int(math.ceil(0.01 * len(df)))
    d = df.reindex(df[col].abs().sort_values(ascending=False, kind='mergesort').index[k:])
    m, se, t, G = mean_t(d[col], d.R)
    return dict(n_dropped=k, mean=m, t=t)


def block(df, col='short_exec'):
    m, se, t, G = mean_t(df[col], df.R)
    out = dict(n=int(len(df)), r_dates=int(df.R.nunique()), mean=m, se=se, t=t, stat=col,
               insufficient=bool(len(df) < 30 or df.R.nunique() < 10))
    if len(df):
        out.update(describe(df[col]))
        out['short_mid_mean'] = float(df.short_mid.mean()); out['implied_mean'] = float(df.implied.mean())
        out['realized_mean'] = float(df.realized.mean()); out['ratio_mean'] = float(df.ratio.mean())
        out['ratio_of_means'] = float(df.realized.mean() / df.implied.mean())
        out['without_top1pct_abs'] = trimmed(df, col)
    return out


def half_signs(df, col):
    res = []
    for lo, hi in ((2019, 2022), (2023, 2026)):
        h = df[(df.year >= lo) & (df.year <= hi)]
        res.append(float(h[col].mean()) if len(h) else None)
    return res


tests = []
def add(tid, desc, df, col, side):
    b = block(df, col); b['id'] = tid; b['description'] = desc; b['direction'] = side
    b['p'] = p_from_t(b['t'], b['r_dates'], side) if not b['insufficient'] or b['n'] > 0 else 1.0
    hs = half_signs(df, col); b['half_means'] = hs
    b['_df'] = df; b['_col'] = col
    tests.append(b)

add('X1', 'all events, mean short_exec > 0', D, 'short_exec', 'gt')
add('X2', 'all events, mean long_exec > 0 (expected < 0)', D, 'long_exec', 'gt')
for i, c in enumerate(sorted(set(v['cluster'] for v in clusters.values()))):
    add(f'X3{"abcdefgh"[i]}', f'cluster {c}, mean short_exec > 0', D[D.cluster == c], 'short_exec', 'gt')
for i, tr in enumerate((1, 2, 3)):
    add(f'X4{"abc"[i]}', f'implied tercile {tr}, mean short_exec > 0', D[D.tercile == tr], 'short_exec', 'gt')
# X5: top minus bottom tercile, clustered by R date
top = D[D.tercile == 3]; bot = D[D.tercile == 1]
dates = sorted(set(top.R) | set(bot.R))
mt, mb = top.short_exec.mean(), bot.short_exec.mean()
sc = {d: 0.0 for d in dates}
for d, v in top.groupby('R').short_exec: sc[d] += (v - mt).sum() / len(top)
for d, v in bot.groupby('R').short_exec: sc[d] -= (v - mb).sum() / len(bot)
se5 = math.sqrt(sum(v * v for v in sc.values())); diff = float(mt - mb); t5 = diff / se5 if se5 > 0 else None
x5 = dict(id='X5', description='top minus bottom implied tercile, short_exec, two-sided', direction='two', stat='short_exec',
          n_top=int(len(top)), n_bottom=int(len(bot)), r_dates=len(dates), mean=diff, se=se5, t=t5,
          insufficient=bool(min(len(top), len(bot)) < 30 or len(dates) < 10), p=p_from_t(t5, len(dates), 'two'),
          top=block(top), bottom=block(bot))
hm = []
for lo, hi in ((2019, 2022), (2023, 2026)):
    a = top[(top.year >= lo) & (top.year <= hi)].short_exec; b = bot[(bot.year >= lo) & (bot.year <= hi)].short_exec
    hm.append(float(a.mean() - b.mean()) if len(a) and len(b) else None)
x5['half_means'] = hm; x5['n'] = int(len(top) + len(bot))
tests.append(x5)
for y in range(2019, 2027):
    add(f'X6{"abcdefgh"[y - 2019]}', f'year {y}, mean short_exec > 0', D[D.year == y], 'short_exec', 'gt')
assert len(tests) == 22, len(tests)

# BH-FDR over all 22 (untestable = p 1.0)
ps = np.array([t['p'] for t in tests]); order = np.argsort(ps, kind='mergesort'); m = len(ps)
q_ = np.empty(m); run = 1.0
for rank in range(m, 0, -1):
    i = order[rank - 1]; run = min(run, ps[i] * m / rank); q_[i] = run
for t, qv in zip(tests, q_):
    t['q_bh'] = float(qv)
    h = t['half_means']; s0 = np.sign(t['mean']) if t['mean'] is not None else 0
    t['same_sign_both_halves'] = bool(h[0] is not None and h[1] is not None and np.sign(h[0]) == np.sign(h[1]) == s0 and s0 != 0)
    t['finding'] = bool(t['q_bh'] < 0.10 and t['t'] is not None and abs(t['t']) > 3 and t['same_sign_both_halves'] and not t['insufficient'])
    t.pop('_df', None); t.pop('_col', None)

sym_cov = D.groupby('symbol').size()
res = dict(label='EXPLORATION ONLY (rule 6): cannot confirm; confirmation is D009 H-X live',
           spec='registry/D010_exploration_options_v1.md',
           calendar_coverage=dict(first_calendar_date_in_source='2020-01-22', note='earnings_calendar has no rows before 2020-01-22, so 2019 has no events'),
           events_total=int(len(ev)), events_by_year={str(k): int(v) for k, v in ev.groupby(ev.R.str[:4]).size().items()},
           excluded_calendar_rows=excl, valid_events=int(len(D)), valid_by_year={str(k): int(v) for k, v in D.groupby('year').size().items()},
           voids=void_tab, no_quote_detail=nq_detail, void_total=int(len(vd)),
           implied_tercile_cuts=CUTS, symbols_with_valid_events=int(len(sym_cov)),
           method_notes=dict(se='CR0 cluster-robust by R date', p='t with G-1 df (one-sided for gt, two-sided X5); untestable = 1.0',
                             bh='Benjamini-Hochberg over all 22', finding_rule='q<0.10 and |t|>3 and same sign (as overall) in R 2019-2022 and 2023-2026 and not insufficient',
                             insufficient='n<30 or R dates<10'),
           tests=tests, findings=[t['id'] for t in tests if t['finding']])
json.dump(res, open('results.json', 'w'), indent=1, sort_keys=True, default=lambda o: None if o is None else float(o))
D.to_csv('events_valid.csv', index=False)
print('valid', len(D), 'voids', void_tab, 'findings', res['findings'])
