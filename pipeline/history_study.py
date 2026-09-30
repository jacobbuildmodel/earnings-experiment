"""D006 §5 steps 2-8: outcomes, scores, the univariate screen, the two candidate rules, validation, and
the choice of T1 rule v0. Run only through `python pipeline/history.py study`, which refuses unless
D006 is frozen. Every computation is appended to analysis/history/search_log.json (D006 §6).

Statistics are the D005 implementation (pipeline/report.py): OLS of WIN_raw on BUY with standard errors
clustered by entry session, and the one-sided restricted wild cluster bootstrap-t.
"""
import bisect
import datetime
import hashlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ET, ROOT, now_et, write_json  # noqa: E402
import report  # noqa: E402  (D005 statistics, read-only use)

OUT = os.path.join(ROOT, "analysis", "history")
FACTORS = ["H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8", "H9", "H10"]
SIGN = {"H1": -1, "H2": -1, "H3": -1, "H4": -1, "H5": 1, "H6": 1, "H7": 1, "H8": 1, "H9": -1, "H10": 1}
TRAIN = ("2023-09-01", "2025-08-31")
VALID = ("2025-09-01", "2026-09-18")
MAX_MISSING = 5
SEED = 20260928


def quarter(d):
    d = datetime.date.fromisoformat(d)
    return d.year * 4 + (d.month - 1) // 3


def outcomes(events):
    """WIN_raw and raw return at exit A (D001), yfinance daily Open, auto_adjust=False. Fetched once per
    ticker; a missing bar excludes the event (`no_price`)."""
    import yfinance as yf
    by_t = {}
    for e in events:
        by_t.setdefault(e["ticker"], []).append(e)
    kept, dropped = [], []
    for t, evs in sorted(by_t.items()):
        h = yf.Ticker(t).history(start="2022-08-01", end="2026-09-30", auto_adjust=False).tz_convert(ET)
        opens = {x.date().isoformat(): float(o) for x, o in zip(h.index, h["Open"]) if o == o and o > 0}
        for e in evs:
            o_in, o_out = opens.get(e["entry"]), opens.get(e["exit_A"])
            if not o_in or not o_out:
                dropped.append({"ticker": t, "date": e["date"], "why": "no_price"})
                continue
            e = dict(e, raw_return=o_out / o_in - 1)
            e["win"] = 1 if e["raw_return"] > 0 else 0
            kept.append(e)
    return kept, dropped


def pct_rank(ref_sorted, v):
    """Share of the reference strictly below v, plus half the ties: a percentile in [0, 1]."""
    lo = bisect.bisect_left(ref_sorted, v)
    hi = bisect.bisect_right(ref_sorted, v)
    return (lo + 0.5 * (hi - lo)) / len(ref_sorted)


def score(events):
    """D006 §5 step 2: each event's factors ranked against the four calendar quarters before its own."""
    byq = {}
    for e in events:
        byq.setdefault(quarter(e["snapshot"]), []).append(e)
    refs = {}
    for q in byq:
        pool = [e for k in range(q - 4, q) for e in byq.get(k, [])]
        refs[q] = {f: sorted(e["factors"][f] for e in pool if e["factors"].get(f) is not None) for f in FACTORS}
    for e in events:
        q = quarter(e["snapshot"])
        s, missing = {}, 0
        for f in FACTORS:
            v, ref = e["factors"].get(f), refs[q][f]
            if v is None or len(ref) < 20:
                s[f] = 0.5
                missing += 1
            else:
                p = pct_rank(ref, v)
                s[f] = p if SIGN[f] > 0 else 1 - p
        e["scores"], e["n_missing"] = s, missing
    return refs


def test(rows, buy):
    """lift, return lift, BUY share, t and one-sided wild bootstrap p (D005) for a BUY vector."""
    y = np.array([r["win"] for r in rows], float)
    x = np.array(buy, float)
    g = np.array([r["entry"] for r in rows])
    ret = np.array([r["raw_return"] for r in rows])
    f = float(x.mean()) if len(x) else float("nan")
    out = {"n": len(rows), "dates": len(set(g)), "buy_share": f, "t0_hit": float(y.mean()) if len(y) else None}
    if len(rows) < 3 or f in (0.0, 1.0):
        out.update(lift=0.0, note="no selection")
        return out
    b, se, t = report.ols_cluster(y, x, g)
    rng = np.random.default_rng(SEED + int(hashlib.sha256(json.dumps([len(rows), float(x.sum())]).encode()).hexdigest()[:6], 16))
    p = report.wild_cluster_p(y, x, g, rng)
    out.update(hit_buy=float(y[x == 1].mean()), lift=float(y[x == 1].mean() - y.mean()), beta=float(b), t=float(t),
               p_one_sided=float(p), return_lift=float(ret[x == 1].mean() - ret.mean()),
               mean_return_all=float(ret.mean()), sufficient=report.sufficient(len(rows), len(set(g))))
    return out


def composite(e, factors):
    return sum(e["scores"][f] for f in factors) / len(factors)


def median_ref(events, factors):
    """For each event, the median composite of the four calendar quarters before its own (§5 step 5)."""
    byq = {}
    for e in events:
        byq.setdefault(quarter(e["snapshot"]), []).append(composite(e, factors))
    med = {}
    for q in byq:
        pool = [c for k in range(q - 4, q) for c in byq.get(k, [])]
        med[q] = float(np.median(pool)) if len(pool) >= 20 else None
    return med


def rule_buys(rows, events, factors):
    med = median_ref(events, factors)
    return [1 if med[quarter(r["snapshot"])] is not None and composite(r, factors) > med[quarter(r["snapshot"])] else 0
            for r in rows]


def log(entry):
    p = os.path.join(OUT, "search_log.json")
    logd = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {"entries": []}
    logd["entries"].append({"at_et": now_et().isoformat(), **entry})
    write_json(p, logd)


def run():
    built = json.load(open(os.path.join(OUT, "events.json"), encoding="utf-8"))
    events, dropped = outcomes(built["events"])
    score(events)
    scored = [e for e in events if e["n_missing"] <= MAX_MISSING]
    unscored = [e for e in events if e["n_missing"] > MAX_MISSING]
    train = [e for e in scored if TRAIN[0] <= e["date"] <= TRAIN[1]]
    valid = [e for e in scored if VALID[0] <= e["date"] <= VALID[1]]
    res = {"counts": {"built": built["n_events"], "with_prices": len(events), "no_price": len(dropped),
                      "unscored_missing_gt5": len(unscored), "train": len(train), "validation": len(valid)}}

    # step 4 - univariate screen on TRAIN (10 tests)
    uni = {f: test(train, [1 if e["scores"][f] > 0.5 else 0 for e in train]) for f in FACTORS}
    q = report.bh([uni[f].get("p_one_sided", 1.0) for f in FACTORS])
    for f, qq in zip(FACTORS, q):
        uni[f]["bh_q"] = qq
    res["univariate_train"] = uni
    log({"step": 4, "tests": len(FACTORS), "result": uni})

    # step 5 - candidate rules
    sel = [f for f in FACTORS if uni[f].get("lift", 0) > 0 and uni[f].get("t", 0) > 3 and uni[f]["bh_q"] < 0.10]
    rules = {"R-LIT": FACTORS}
    if sel:
        rules["R-SEL"] = sel
    res["r_sel_factors"] = sel
    for name, fs in rules.items():
        res[f"{name}_train"] = test(train, rule_buys(train, events, fs))

    # step 6 - validation (the only look)
    for name, fs in rules.items():
        res[f"{name}_validation"] = test(valid, rule_buys(valid, events, fs))
    log({"step": 6, "tests": len(rules), "result": {n: res[f"{n}_validation"] for n in rules}})

    # step 7 - choose
    lit = res["R-LIT_validation"].get("lift", 0)
    chosen = "R-SEL" if "R-SEL" in rules and res["R-SEL_validation"].get("lift", 0) > lit else "R-LIT"
    res["rule_v0"] = {"name": chosen, "factors": rules[chosen],
                      "failed_validation": res[f"{chosen}_validation"].get("lift", 0) <= 0,
                      "selected_winner_of_two": "R-SEL" in rules}
    for k in ("train", "validation"):
        for n in rules:
            s = res[f"{n}_{k}"].get("buy_share")
            if s is not None and not 0.3 <= s <= 0.7:
                res.setdefault("tripwires", []).append(f"{n} {k} BUY share {s:.2f} outside 30-70%")

    # step 8 - descriptive splits (not tests), on the chosen rule
    fs = rules[chosen]
    desc = {}
    for label, key in (("cluster", lambda e: e.get("cluster") or "unknown"), ("session", lambda e: e["session"])):
        for grp in sorted({key(e) for e in scored}):
            rows = [e for e in scored if key(e) == grp and e["date"] >= TRAIN[0]]
            buys = rule_buys(rows, events, fs)
            desc[f"{label}={grp}"] = {"n": len(rows), "t0_hit": float(np.mean([r["win"] for r in rows])) if rows else None,
                                      "rule_hit_buy": float(np.mean([r["win"] for r, b in zip(rows, buys) if b])) if any(buys) else None,
                                      "sufficient": report.sufficient(len(rows), len({r["entry"] for r in rows}))}
    res["descriptive"] = desc
    res["missing_by_cluster"] = {}
    for e in events:
        c = e.get("cluster") or "unknown"
        m = res["missing_by_cluster"].setdefault(c, {"events": 0, "unscored": 0, **{f: 0 for f in FACTORS}})
        m["events"] += 1
        m["unscored"] += e["n_missing"] > MAX_MISSING
        for f in FACTORS:
            m[f] += e["factors"].get(f) is None
    write_json(os.path.join(OUT, "study_result.json"), res)
    write_json(os.path.join(OUT, "graded_events.json"), {"note": "history outcomes (pre-pilot) - D006", "events": events,
                                                         "dropped": dropped})
    print(json.dumps({k: res[k] for k in ("counts", "r_sel_factors", "rule_v0")}, indent=1))
    return res
