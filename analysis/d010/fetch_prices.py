"""Fetch yfinance SPY sessions + unadjusted closes + splits for the D010 universe. Writes raw/*.csv and manifest."""
import json, datetime, time
import yfinance as yf, pandas as pd
u = json.load(open('../history/universe.json')); T = u['tickers']
man = []
def retry(f, n=8):
    for k in range(n):
        try:
            return f()
        except Exception as e:
            time.sleep(15 * (k + 1))
    raise RuntimeError('yfinance failed after retries')
spy = retry(lambda: yf.Ticker('SPY').history(start='2018-12-01', end='2026-10-01', auto_adjust=False))
spy.index = pd.to_datetime(spy.index).tz_localize(None).normalize()
pd.DataFrame({'date': spy.index.strftime('%Y-%m-%d')}).to_csv('raw/sessions.csv', index=False)
man.append(('yfinance SPY history 2018-12-01..2026-09-30', datetime.datetime.utcnow().isoformat(), len(spy)))
rows = []; spl = []; missing = []
for i in range(0, len(T), 20):
    b = T[i:i+20]
    d = retry(lambda: yf.download(b, start='2018-12-01', end='2026-10-01', auto_adjust=False, actions=True, group_by='ticker', progress=False, threads=False))
    for s in b:
        try:
            x = d[s]
        except KeyError:
            missing.append(s); continue
        x = x.dropna(subset=['Close'])
        if x.empty: missing.append(s); continue
        for dt, r in x.iterrows():
            rows.append((s, pd.Timestamp(dt).strftime('%Y-%m-%d'), r['Close'], r.get('Stock Splits', 0)))
    man.append((f'yfinance download batch {b[0]}..{b[-1]}', datetime.datetime.utcnow().isoformat(), len(rows)))
    time.sleep(1)
df = pd.DataFrame(rows, columns=['symbol', 'date', 'close', 'split'])
df['split'] = df['split'].fillna(0)
df.to_csv('raw/prices.csv.gz', index=False)
json.dump({'missing_symbols': missing, 'log': man}, open('raw/manifest_prices.json', 'w'), indent=1)
print(len(df), 'missing', missing)
