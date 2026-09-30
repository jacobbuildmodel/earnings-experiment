"""D007 exploration batch 1 (registry/D007_exploration_batch1_v1.md): collect the 10 signals, then test.

    python pipeline/explore_d007.py collect <source>   # finra | market | wiki | dolthub_iv | dolthub_chain  (cached)
    python pipeline/explore_d007.py test               # D007 §2 - refuses unless D007 is frozen

Every value is point in time (dated on or before the event's snapshot session). A failed fetch is
recorded as missing, never filled. Candidates only - nothing here is a result (rules 6-7).
"""
import bisect
import datetime
import json
import os
import sys
import time

import numpy as np
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ET, REGISTRY, ROOT, now_et, write_json  # noqa: E402

OUT = os.path.join(ROOT, "analysis", "d007")
CACHE = os.path.join(ROOT, "cache", "d007")
UA = {"User-Agent": "EarningsExperiment research jacobong999@gmail.com"}
DOLT = "https://www.dolthub.com/api/v1alpha1/post-no-preference/options/master"
SIGNS = {"E1": -1, "E2": -1, "E3": 0, "E4": 0, "E5": 1, "E6": -1, "E7": 0, "E8": 0, "E9": 1, "E10": -1}
TRAIN, VALID = ("2023-09-01", "2025-08-31"), ("2025-09-01", "2026-09-18")


def events():
    g = json.load(open(os.path.join(ROOT, "analysis", "history", "graded_events.json"), encoding="utf-8"))["events"]
    return [e for e in g if TRAIN[0] <= e["date"] <= VALID[1]]


def all_built_events():
    """Every built event incl. the 2022-23 reference year (for the backward-looking ranks)."""
    return json.load(open(os.path.join(ROOT, "analysis", "history", "graded_events.json"), encoding="utf-8"))["events"]


def cpath(*p):
    path = os.path.join(CACHE, *p)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def sessions():
    import yfinance as yf
    h = yf.Ticker("SPY").history(start="2022-06-01", end="2026-09-30", auto_adjust=False).tz_convert(ET)
    return [x.date() for x in h.index]


# ------------------------------------------------------------------ collectors (cached, resumable)
def collect_finra():
    """FINRA Reg SHO daily short-sale volume, consolidated NMS file, one per session."""
    days = [d for d in sessions() if datetime.date(2022, 6, 1) <= d <= datetime.date(2026, 9, 18)]
    universe = {e["ticker"] for e in all_built_events()}
    got = 0
    for d in days:
        p = cpath("finra", f"{d:%Y%m%d}.json")
        if os.path.exists(p):
            continue
        r = requests.get(f"https://cdn.finra.org/equity/regsho/daily/CNMSshvol{d:%Y%m%d}.txt", headers=UA, timeout=60)
        rows = {}
        if r.status_code == 200:
            for line in r.text.splitlines()[1:]:
                f = line.split("|")
                if len(f) >= 5 and f[1] in universe and f[4].isdigit() and int(f[4]) > 0:
                    rows[f[1]] = [int(f[2]), int(f[4])]
        json.dump({"status": r.status_code, "rows": rows}, open(p, "w"))
        got += 1
        time.sleep(0.25)
    print(f"finra: {len(days)} sessions, {got} fetched now")


def collect_market():
    import yfinance as yf
    out = {}
    for t in ("^VIX", "SPY"):
        h = yf.Ticker(t).history(start="2022-06-01", end="2026-09-30", auto_adjust=False).tz_convert(ET)
        out[t] = {x.date().isoformat(): float(c) for x, c in zip(h.index, h["Close"]) if c == c}
    json.dump(out, open(cpath("market.json"), "w"))
    print("market: VIX and SPY closes saved")


def collect_wiki():
    """Ticker -> English Wikipedia article via Wikidata (P249 ticker symbol), then daily pageviews."""
    tickers = sorted({e["ticker"] for e in all_built_events()})
    mp = cpath("wiki_map.json")
    if not os.path.exists(mp):
        vals = " ".join(f'"{t}"' for t in tickers)
        q = f"""SELECT ?t ?article WHERE {{ VALUES ?t {{ {vals} }} ?item p:P414 ?st . ?st pq:P249 ?t .
                ?article schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> . }}"""
        r = requests.get("https://query.wikidata.org/sparql", params={"query": q, "format": "json"},
                         headers={**UA, "Accept": "application/sparql-results+json"}, timeout=120)
        m = {}
        for b in r.json()["results"]["bindings"]:
            m.setdefault(b["t"]["value"], set()).add(b["article"]["value"].rsplit("/", 1)[1])
        json.dump({k: sorted(v) for k, v in m.items()}, open(mp, "w"), indent=1)
    m = json.load(open(mp))
    for t, arts in m.items():
        p = cpath("wiki", f"{t}.json")
        if os.path.exists(p):
            continue
        if len(arts) != 1:  # ambiguous mapping: counted, never guessed
            json.dump({"error": f"ambiguous: {arts}"}, open(p, "w"))
            continue
        url = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/"
               f"{arts[0]}/daily/20220601/20260920")
        r = requests.get(url, headers=UA, timeout=60)
        views = {i["timestamp"][:8]: i["views"] for i in r.json().get("items", [])} if r.status_code == 200 else {}
        json.dump({"article": arts[0], "status": r.status_code, "views": views}, open(p, "w"))
        time.sleep(0.2)
    print(f"wiki: {len(m)} of {len(tickers)} tickers mapped to an article")


def dolt(q, tries=3):
    for i in range(tries):
        try:
            r = requests.get(DOLT, params={"q": q}, headers=UA, timeout=90)
            d = r.json()
            if d.get("query_execution_status") == "Success":
                return d.get("rows", [])
            err = d.get("query_execution_message", "")
        except (requests.RequestException, ValueError) as exc:
            err = str(exc)
        time.sleep(3 * (i + 1))
    return {"error": err[:200]}


def collect_dolthub_iv():
    for t in sorted({e["ticker"] for e in all_built_events()}):
        p = cpath("dolt_iv", f"{t}.json")
        if os.path.exists(p):
            continue
        rows = dolt(f"SELECT date, hv_current, iv_current, iv_month_ago FROM volatility_history "
                    f"WHERE act_symbol='{t}' AND date BETWEEN '2022-06-01' AND '2026-09-18'")
        json.dump(rows, open(p, "w"))
    print("dolthub_iv: done")


def collect_dolthub_chain():
    for e in all_built_events():
        p = cpath("dolt_chain", f"{e['ticker']}_{e['snapshot']}.json")
        if os.path.exists(p):
            continue
        rows = dolt(f"SELECT expiration, strike, call_put, vol FROM option_chain WHERE date='{e['snapshot']}' "
                    f"AND act_symbol='{e['ticker']}'")
        json.dump(rows, open(p, "w"))
    print("dolthub_chain: done")


# ------------------------------------------------------------------ signals
def closes(t):
    import yfinance as yf
    h = yf.Ticker(t).history(start="2022-06-01", end="2026-09-30", auto_adjust=False).tz_convert(ET)
    return {x.date().isoformat(): float(c) for x, c in zip(h.index, h["Close"]) if c == c}


def signals(evs, sess):
    si = {d.isoformat(): i for i, d in enumerate(sess)}
    mk = json.load(open(cpath("market.json")))
    out = {}
    by_cluster = {}
    for e in evs:
        by_cluster.setdefault(e.get("cluster"), []).append(e)
    finra_cache = {}

    def finra(d):
        if d not in finra_cache:
            p = cpath("finra", f"{d.replace('-', '')}.json")
            finra_cache[d] = json.load(open(p))["rows"] if os.path.exists(p) else None
        return finra_cache[d]

    for e in evs:
        s = {}
        k = si.get(e["snapshot"])
        # E1
        if k is not None and k >= 65:
            def ratio(days):
                v = [finra(sess[j].isoformat()) for j in days]
                r = [x[e["ticker"]][0] / x[e["ticker"]][1] for x in v if x and e["ticker"] in x]
                return (sum(r) / len(r)) if len(r) >= 0.8 * len(days) else None
            a, b = ratio(range(k - 4, k + 1)), ratio(range(k - 64, k - 4))
            s["E1"] = a - b if a is not None and b is not None else None
        # E2 - peers of the same cluster whose exit-A session is within the 10 sessions to the snapshot
        if k is not None and k >= 10:
            lo = sess[k - 9].isoformat()
            peers = [p["raw_return"] for p in by_cluster.get(e.get("cluster"), [])
                     if p["ticker"] != e["ticker"] and lo <= p["exit_A"] <= e["snapshot"] and "raw_return" in p]
            s["E2"] = float(np.mean(peers)) if len(peers) >= 2 else None
        # E3, E4
        s["E3"] = mk["^VIX"].get(e["snapshot"])
        if k is not None and k >= 20:
            a, b = mk["SPY"].get(sess[k - 20].isoformat()), mk["SPY"].get(e["snapshot"])
            s["E4"] = b / a - 1 if a and b else None
        # E5
        wp = cpath("wiki", f"{e['ticker']}.json")
        if os.path.exists(wp):
            v = json.load(open(wp)).get("views") or {}
            snap = datetime.date.fromisoformat(e["snapshot"])
            last5 = [v.get((snap - datetime.timedelta(days=i)).strftime("%Y%m%d")) for i in range(5)]
            prior = [v.get((snap - datetime.timedelta(days=i)).strftime("%Y%m%d")) for i in range(5, 65)]
            last5, prior = [x for x in last5 if x is not None], [x for x in prior if x is not None]
            if len(last5) >= 4 and len(prior) >= 45 and np.mean(prior) >= 30:
                s["E5"] = float(np.mean(last5) / np.mean(prior))
        # E6
        d = datetime.date.fromisoformat(e["date"])
        q_end = datetime.date(d.year, 3 * ((d.month - 1) // 3) + 1, 1) - datetime.timedelta(days=1)
        s["E6"] = (d - q_end).days
        # E7, E8
        ip = cpath("dolt_iv", f"{e['ticker']}.json")
        if os.path.exists(ip):
            rows = json.load(open(ip))
            if isinstance(rows, list):
                row = next((r for r in rows if r["date"] == e["snapshot"]), None)
                if row:
                    iv, hv, im = (float(row[x]) if row.get(x) else None for x in ("iv_current", "hv_current", "iv_month_ago"))
                    s["E7"] = iv / hv if iv and hv else None
                    s["E8"] = iv / im if iv and im else None
        # E9, E10
        cp = cpath("dolt_chain", f"{e['ticker']}_{e['snapshot']}.json")
        if os.path.exists(cp):
            rows = json.load(open(cp))
            spot = e.get("_close")
            if isinstance(rows, list) and rows and spot:
                exp = min(r["expiration"] for r in rows)
                ch = [r for r in rows if r["expiration"] == exp and r.get("vol")]
                calls = {float(r["strike"]): float(r["vol"]) for r in ch if r["call_put"] == "Call"}
                puts = {float(r["strike"]): float(r["vol"]) for r in ch if r["call_put"] == "Put"}
                both = sorted(set(calls) & set(puts))
                if both:
                    atm = min(both, key=lambda x: (abs(x - spot), x))
                    s["E9"] = calls[atm] - puts[atm]
                    if puts:
                        otm = min(puts, key=lambda x: abs(x - 0.9 * spot))
                        s["E10"] = puts[otm] - calls[atm] if abs(otm / spot - 0.9) < 0.05 else None
        out[f"{e['ticker']}_{e['date']}"] = s
    return out


def quarter(d):
    d = datetime.date.fromisoformat(d)
    return d.year * 4 + (d.month - 1) // 3


def test():
    import report  # D005 statistics
    frozen = any("D007_exploration_batch1_v1.md" in line for line in open(os.path.join(REGISTRY, "FROZEN.sha256")))
    if not frozen:
        raise SystemExit("D007 is not frozen - no test may run")
    sess = sessions()
    evs = all_built_events()
    # the snapshot close, for the option strikes (point in time: the snapshot session's own close)
    by_t = {}
    for e in evs:
        by_t.setdefault(e["ticker"], []).append(e)
    for t, es in by_t.items():
        c = closes(t)
        for e in es:
            e["_close"] = c.get(e["snapshot"])
    sig = signals(evs, sess)
    for e in evs:
        e["_sig"] = sig[f"{e['ticker']}_{e['date']}"]
    res, pvals = {}, []
    rng_seed = 20260930
    for j, f in enumerate(SIGNS):
        byq = {}
        for e in evs:
            if e["_sig"].get(f) is not None:
                byq.setdefault(quarter(e["snapshot"]), []).append(e["_sig"][f])
        rows = []
        for e in evs:
            v = e["_sig"].get(f)
            if v is None or not (TRAIN[0] <= e["date"] <= VALID[1]) or "win" not in e:
                continue
            ref = sorted(x for k in range(quarter(e["snapshot"]) - 4, quarter(e["snapshot"])) for x in byq.get(k, []))
            if len(ref) < 20:
                continue
            p = (bisect.bisect_left(ref, v) + 0.5 * (bisect.bisect_right(ref, v) - bisect.bisect_left(ref, v))) / len(ref)
            score = 1 - p if SIGNS[f] < 0 else p
            rows.append((e, 1 if score > 0.5 else 0))
        r = {"n_scored": len(rows), "coverage": round(len(rows) / max(1, len([e for e in evs if TRAIN[0] <= e["date"] <= VALID[1]])), 3)}

        def stats(sub, seed):
            if len(sub) < 3 or len({x for _, x in sub}) < 2:
                return {"n": len(sub), "note": "no split"}
            y = np.array([e["win"] for e, _ in sub], float)
            x = np.array([h for _, h in sub], float)
            g = np.array([e["entry"] for e, _ in sub])
            ret = np.array([e["raw_return"] for e, _ in sub])
            b, se, t = report.ols_cluster(y, x, g)
            if SIGNS[f] != 0:
                p = report.wild_cluster_p(y, x, g, np.random.default_rng(seed))
            else:
                p = min(1.0, 2 * min(report.wild_cluster_p(y, x, g, np.random.default_rng(seed)),
                                     report.wild_cluster_p(y, -x, g, np.random.default_rng(seed + 1))))
            return {"n": len(sub), "dates": len(set(g)), "lift": float(y[x == 1].mean() - y.mean()), "t": float(t),
                    "p": float(p), "return_lift": float(ret[x == 1].mean() - ret.mean())}
        r["full"] = stats(rows, rng_seed + j)
        r["train"] = stats([z for z in rows if z[0]["date"] <= TRAIN[1]], rng_seed + 100 + j)
        r["validation"] = stats([z for z in rows if z[0]["date"] >= VALID[0]], rng_seed + 200 + j)
        res[f] = r
        pvals.append(r["full"].get("p", 1.0))
    q = report.bh(pvals)
    for f, qq in zip(SIGNS, q):
        r = res[f]
        r["bh_q"] = qq
        fu, tr, va = r["full"], r["train"], r["validation"]
        same = (tr.get("lift", 0) > 0) == (va.get("lift", 0) > 0) == (fu.get("lift", 0) > 0)
        r["candidate"] = bool(qq < 0.10 and abs(fu.get("t", 0)) > 3 and same and fu.get("n", 0) >= 300
                              and fu.get("dates", 0) >= 50)
    write_json(os.path.join(OUT, "result.json"), {"run_et": now_et().isoformat(), "rule": "D007 v1 §2", "tests": res})
    for f, r in res.items():
        fu = r["full"]
        print(f"{f:4} n={fu.get('n'):>5} lift={fu.get('lift', 0) * 100:+5.1f}pt t={fu.get('t', 0):+5.2f} "
              f"q={r['bh_q']:.3f} ret_lift={fu.get('return_lift', 0) * 100:+.2f}% "
              f"train={r['train'].get('lift', 0) * 100:+.1f} valid={r['validation'].get('lift', 0) * 100:+.1f} "
              f"cov={r['coverage']} {'CANDIDATE' if r['candidate'] else ''}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["collect"]:
        {"finra": collect_finra, "market": collect_market, "wiki": collect_wiki,
         "dolthub_iv": collect_dolthub_iv, "dolthub_chain": collect_dolthub_chain}[a[1]]()
    elif a[:1] == ["test"]:
        test()
    else:
        raise SystemExit(__doc__)
