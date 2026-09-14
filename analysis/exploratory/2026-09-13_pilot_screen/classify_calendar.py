import json, glob, csv, io, time, datetime, math
import yfinance as yf
SP=r"C:/Users/jacob/AppData/Local/Temp/claude/C--Users-jacob-OneDrive-Desktop-Jacob-CLAUDE/d1b217a6-158f-4781-943d-b6efea3606c3/scratchpad"
j=json.load(open(glob.glob(r'C:/Users/jacob/.claude/projects/C--Users-jacob-OneDrive-Desktop-Jacob-CLAUDE/d1b217a6-158f-4781-943d-b6efea3606c3/tool-results/*EARNINGS_CALENDAR*')[0],encoding='utf-8'))
rows=[r for r in csv.DictReader(io.StringIO(j['sample_data'])) if '2026-09-14'<=r['reportDate']<='2026-10-09']
out=[]
for i,r in enumerate(rows):
    t=r['symbol']; rec={'symbol':t,'name':r['name'],'reportDate':r['reportDate'],'tod_av':r.get('timeOfTheDay','')}
    try:
        inf=yf.Ticker(t).info
        rec.update(sector=inf.get('sector'), industry=inf.get('industry'), mcap=inf.get('marketCap'),
                   rev_growth=inf.get('revenueGrowth'), quoteType=inf.get('quoteType'))
    except Exception as e:
        rec['err']=str(e)[:60]
    out.append(rec); time.sleep(0.25)
    if i%25==0: print(f"{i}/{len(rows)}", flush=True)
# ATM IV only for names that could plausibly pass the sector + size screen
KEEP={'Technology','Communication Services','Healthcare','Consumer Cyclical','Industrials'}
for rec in out:
    if rec.get('sector') in KEEP and (rec.get('mcap') or 0)>=2e9:
        try:
            tk=yf.Ticker(rec['symbol']); exps=tk.options
            today=datetime.date(2026,9,13)
            exp=next((e for e in exps if (datetime.date.fromisoformat(e)-today).days>=7), None)
            if exp:
                ch=tk.option_chain(exp); px=tk.fast_info['last_price']
                c=ch.calls.iloc[(ch.calls['strike']-px).abs().argsort()[:1]]
                p=ch.puts.iloc[(ch.puts['strike']-px).abs().argsort()[:1]]
                rec['atm_iv']=round(float((c['impliedVolatility'].iloc[0]+p['impliedVolatility'].iloc[0])/2),3)
                rec['iv_exp']=exp
        except Exception as e:
            rec['iv_err']=str(e)[:60]
        time.sleep(0.3)
json.dump(out, open(SP+"/calendar_classified.json","w"), indent=1)
print("DONE", len(out))
