"""Pull D010 option data from a local dolt clone of post-no-preference/options (spec §7 path 1).
Phase 1: per P date, universe symbols with an event, 0.25<=|delta|<=0.75 rows. Phase 2: exact contract quotes on P and on R.
Per-date chunks are cached in raw/chunks/, so a stopped run resumes. Manifest records every query."""
import subprocess, io, os, sys, json, datetime, concurrent.futures as cf
import pandas as pd
import events_lib as E
RAW = 'raw'; DOLT = os.environ.get('DOLT_OPTIONS', '/tmp/dolt/options')
os.makedirs(f'{RAW}/chunks', exist_ok=True)
MAN = []


def sql(q):
    for k in range(4):
        r = subprocess.run(['dolt', 'sql', '-r', 'csv', '-q', q], cwd=DOLT, capture_output=True, text=True)
        if r.returncode == 0:
            return pd.read_csv(io.StringIO(r.stdout))
        import time; time.sleep(5 * (k + 1))
    raise RuntimeError(r.stderr[:300])


def inlist(xs):
    return ",".join("'%s'" % x for x in xs)


def phase1(P, syms):
    f = f'{RAW}/chunks/p1_{P}.csv.gz'
    if os.path.exists(f):
        return pd.read_csv(f)
    q = (f"select date,act_symbol,expiration,strike,call_put,bid,ask,delta from option_chain where date='{P}' "
         f"and act_symbol in ({inlist(syms)}) and abs(delta)>=0.25 and abs(delta)<=0.75")
    d = sql(q); d.to_csv(f, index=False)
    MAN.append({'q': q, 'at': datetime.datetime.utcnow().isoformat(), 'rows': len(d)})
    return d


def exact(date, tuples, tag):
    f = f'{RAW}/chunks/{tag}_{date}.csv.gz'
    if os.path.exists(f):
        return pd.read_csv(f)
    if not tuples:
        d = pd.DataFrame(columns=['date', 'act_symbol', 'expiration', 'strike', 'call_put', 'bid', 'ask', 'delta'])
    else:
        tl = ",".join("('%s','%s',%s)" % t for t in tuples)
        q = (f"select date,act_symbol,expiration,strike,call_put,bid,ask,delta from option_chain where date='{date}' "
             f"and (act_symbol,expiration,strike) in ({tl})")
        d = sql(q)
        MAN.append({'q': q[:400] + '...', 'at': datetime.datetime.utcnow().isoformat(), 'rows': len(d)})
    d.to_csv(f, index=False)
    return d


def work(P):
    sub = ev[ev.P == P]
    ch = phase1(P, sorted(sub.symbol.unique()))
    sel = []
    for _, r in sub.iterrows():
        c = ch[ch.act_symbol == r.symbol]
        if c.empty:
            continue
        ex, k = E.select_contract(c, r.R)
        if ex is not None:
            sel.append((r.symbol, ex, k, r.R))
    exact(P, sorted({(s, e, k) for s, e, k, _ in sel}), 'p2')
    return P, sel


ev, _ = E.build_events(RAW)
dates = sorted(ev.P.unique())
if len(sys.argv) > 1:
    dates = dates[:int(sys.argv[1])]
selR = {}
with cf.ThreadPoolExecutor(4) as ex_:
    for n, (P, sel) in enumerate(ex_.map(work, dates)):
        for s, e, k, R in sel:
            selR.setdefault(R, set()).add((s, e, k))
        if n % 50 == 0:
            print('phase1/2 P', n, len(dates), flush=True)
rd = sorted(selR)
list(cf.ThreadPoolExecutor(4).map(lambda R: exact(R, sorted(selR[R]), 'q'), rd))
json.dump(MAN, open(f'{RAW}/manifest_options_{datetime.date.today()}.json', 'w'), indent=1)
for tag, pat in (('p1', 'p1_'), ('p2', 'p2_'), ('q', 'q_')):
    fs = sorted(f for f in os.listdir(f'{RAW}/chunks') if f.startswith(pat))
    df = pd.concat([pd.read_csv(f'{RAW}/chunks/{f}') for f in fs], ignore_index=True)
    df.to_csv(f'{RAW}/opt_{tag}.csv.gz', index=False); print(tag, len(df))
