"""D014 sections 4-7: the first hour after the print. Reads raw/events_intraday.csv.gz (fetch.py) and the D010 implied
move, runs the frozen procedure, writes results.json and REPORT.md. Deterministic, no randomness.

    python analysis/d014/run_d014.py
"""
import csv
import gzip
import json
import math
import os
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
HS = ("5", "10", "30", "60", "c")
EXIT_Q = {"5": "0935", "10": "0940", "30": "1000", "60": "1030", "c": None}
FEE = 0.0002
FLOOR = 0.01
CONDS = ("C1_big_gap", "C2_surprise_disagrees", "C3_market_against", "C4_bad_news", "C5_mid_cap", "C6_high_attention")


def num(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def implied():
    out = {}
    p = os.path.join(ROOT, "analysis", "d010", "events_valid.csv")
    for r in csv.DictReader(open(p, encoding="utf-8")):
        k, sp, im = num(r["strike"]), num(r["spot_P"]), num(r["implied"])
        if k and sp and im is not None and 0.8 <= k / sp <= 1.25:
            out[(r["symbol"], r["R"])] = im
    return out


def ret(a, b):
    return a / b - 1 if a is not None and b else None


def sign(x):
    return None if x in (None, 0.0) else 1 if x > 0 else -1


def build():
    rows = list(csv.DictReader(gzip.open(os.path.join(HERE, "raw", "events_intraday.csv.gz"), "rt", encoding="utf-8")))
    im = implied()
    voids, below, events = {}, 0, []
    unchecked = sum(1 for r in rows if r.get("split_check") == "unchecked")
    for r in rows:
        if r.get("void"):
            k = (r["void"], r["R"][:4])
            voids[k] = voids.get(k, 0) + 1
            continue
        c0, o, pm = num(r["c0"]), num(r["o"]), num(r["pm"])
        g = pm / c0 - 1
        if abs(g) < FLOOR:
            below += 1
            continue
        s = sign(g)
        p = {h: num(r[f"p{h}"]) for h in ("5", "10", "30", "60")}
        p["c"] = num(r["pc"])
        so, sp = num(r["spy_o"]), {h: num(r[f"spy_p{h}"]) for h in ("5", "10", "30", "60")}
        sp["c"] = num(r["spy_pc"])
        e = {"ticker": r["ticker"], "R": r["R"], "segment": r["segment"], "cluster": r["cluster"],
             "session": r["session"], "g": g, "s": s, "open_gap": o / c0 - 1, "im": im.get((r["ticker"], r["R"])),
             "surprise": num(r["surprise"]), "mcap": num(r["mcap"]), "pmv": num(r["pmv"]),
             "spy_g": ret(num(r["spy_pm"]), num(r["spy_c0"])), "p": p, "c0": c0, "o": o,
             "hs": {k: num(r[f"hs{k}"]) for k in ("0935", "0940", "1000", "1030")},
             "mid": {k: num(r[f"mid{k}"]) for k in ("0935", "0940", "1000", "1030")},
             "srcs": (r["o_src"], r["pc_src"])}
        e["y"] = {h: (s * ret(p[h], o) if p[h] is not None else None) for h in HS}
        e["y"]["d"] = s * ret(p["30"], p["5"]) if p["30"] is not None and p["5"] else None
        spy_r = {h: ret(sp[h], so) for h in HS}
        spy_r["d"] = ret(sp["30"], sp["5"])
        e["y_adj"] = {h: (e["y"][h] - s * spy_r[h] if e["y"][h] is not None and spy_r[h] is not None else None)
                      for h in e["y"]}
        events.append(e)
    return rows, events, voids, below, unchecked


def cr1(ys, clusters):
    """Mean and its CR1 standard error, clustered by reaction date."""
    n = len(ys)
    if n < 2:
        return None, None
    m = sum(ys) / n
    by = {}
    for y, c in zip(ys, clusters):
        by[c] = by.get(c, 0.0) + (y - m)
    G = len(by)
    if G < 2:
        return m, None
    return m, math.sqrt(G / (G - 1) * sum(u * u for u in by.values())) / n


def p2(t):
    return math.erfc(abs(t) / math.sqrt(2))


def cell(evs, key, h):
    xs = [(e[key][h], e["R"]) for e in evs if e[key][h] is not None]
    n, dates = len(xs), len({d for _, d in xs})
    out = {"n": n, "dates": dates}
    if n < 30 or dates < 10:
        out["status"] = "insufficient"
        return out
    m, se = cr1([y for y, _ in xs], [d for _, d in xs])
    out.update({"mean": m, "se": se, "t": m / se if se else None})
    out["p"] = p2(out["t"]) if out["t"] is not None else 1.0
    return out


def flags(train):
    """C6's threshold is the TRAIN median of PMV taken separately for BMO and AMC reporters."""
    pm = {s: statistics.median([e["pmv"] for e in train if e["pmv"] is not None and e["session"] == s])
          for s in ("BMO", "AMC")}
    return pm, {
        "C1_big_gap": lambda e: e["im"] is not None and abs(e["g"]) > e["im"],
        "C2_surprise_disagrees": lambda e: sign(e["surprise"]) is not None and sign(e["surprise"]) != e["s"],
        "C3_market_against": lambda e: sign(e["spy_g"]) is not None and sign(e["spy_g"]) != e["s"],
        "C4_bad_news": lambda e: e["s"] == -1,
        "C5_mid_cap": lambda e: e["mcap"] is not None and e["mcap"] < 10e9,
        "C6_high_attention": lambda e: e["pmv"] is not None and e["pmv"] > pm[e["session"]]}


def family(evs, fl, key="y"):
    tests = {}
    for h in HS:
        tests[f"all|{h}"] = cell(evs, key, h)
    for c in CONDS:
        for h in HS:
            tests[f"{c}|{h}"] = cell([e for e in evs if fl[c](e)], key, h)
            tests[f"{c}|{h}"]["complement"] = cell([e for e in evs if not fl[c](e)], key, h)
    tests["all|d"] = cell(evs, key, "d")
    for c in CONDS:
        tests[f"{c}|d"] = cell([e for e in evs if fl[c](e)], key, "d")
        tests[f"{c}|d"]["complement"] = cell([e for e in evs if not fl[c](e)], key, "d")
    return tests


def bh(ps):
    """Benjamini-Hochberg q-values for a dict of p-values."""
    keys = sorted(ps, key=lambda k: ps[k])
    m, q, prev = len(keys), {}, 1.0
    for i in range(m - 1, -1, -1):
        k = keys[i]
        prev = min(prev, ps[k] * m / (i + 1))
        q[k] = prev
    return q


def holm(ps):
    """Holm-adjusted p-values for a dict of p-values."""
    keys = sorted(ps, key=lambda k: ps[k])
    m, out, run = len(keys), {}, 0.0
    for i, k in enumerate(keys):
        run = max(run, min(1.0, (m - i) * ps[k]))
        out[k] = run
    return out


def net(e, h, side):
    """The traded side's return after costs. Exits at minute h sell at the quote's mid less the half spread;
    the close is an auction. The delayed variant buys at 09:35's mid plus its half spread."""
    s = side * e["s"]
    if h == "d":
        a, b = e["mid"]["0935"], e["mid"]["1000"]
        if a is None or b is None or e["hs"]["0935"] is None or e["hs"]["1000"] is None:
            return None
        return s * (b / a - 1) - e["hs"]["0935"] - e["hs"]["1000"] - FEE
    if h == "c":
        return s * (e["p"]["c"] / e["o"] - 1) - FEE if e["p"]["c"] is not None else None
    k = EXIT_Q[h]
    if e["mid"][k] is None or e["hs"][k] is None:
        return None
    return s * (e["mid"][k] / e["o"] - 1) - e["hs"][k] - FEE


def net_cell(evs, h, side):
    xs = [(net(e, h, side), e["R"]) for e in evs if net(e, h, side) is not None]
    m, se = cr1([y for y, _ in xs], [d for _, d in xs])
    return {"side": "follow" if side == 1 else "fade", "n": len(xs), "net_mean": m,
            "t": m / se if m is not None and se else None}


def quantiles(xs, qs):
    xs = sorted(xs)
    return {str(q): xs[int(q * (len(xs) - 1))] for q in qs} if xs else {}


def descriptive(events):
    out = {"abs_premarket_gap_quantiles": quantiles([abs(e["g"]) for e in events], (0.1, 0.25, 0.5, 0.75, 0.9)),
           "abs_gap_over_implied": {"n": sum(1 for e in events if e["im"]),
                                    **quantiles([abs(e["g"]) / e["im"] for e in events if e["im"]], (0.25, 0.5, 0.75))},
           "open_gap_same_sign_as_premarket": sum(1 for e in events if sign(e["open_gap"]) == e["s"]) / len(events)}
    share = {}
    for h in ("5", "10", "30", "60"):
        xs = [abs(e["p"][h] / e["c0"] - 1) / abs(e["p"]["c"] / e["c0"] - 1) for e in events
              if e["p"][h] and e["p"]["c"] and abs(e["p"]["c"] / e["c0"] - 1) >= 0.01]
        share[h] = {"n": len(xs), "median": statistics.median(xs) if xs else None}
    out["share_of_day_move_reached_by_minute"] = share
    for name, keyf in (("by_year", lambda e: e["R"][:4]), ("by_cluster", lambda e: e["cluster"])):
        grp = {}
        for e in events:
            grp.setdefault(keyf(e), []).append(e)
        out[name] = {k: {h: (lambda xs: {"n": len(xs), "mean": sum(xs) / len(xs) if xs else None})(
            [e["y"][h] for e in v if e["y"][h] is not None]) for h in ("5", "30", "c")} for k, v in sorted(grp.items())}
    out["sources"] = {"open_from_bar": sum(1 for e in events if e["srcs"][0] == "open_from_bar"),
                      "close_from_bar": sum(1 for e in events if e["srcs"][1] == "close_from_bar")}
    return out


def main():
    rows, events, voids, below, unchecked = build()
    train = [e for e in events if e["segment"] == "TRAIN"]
    valid = [e for e in events if e["segment"] == "VALIDATION"]
    pm, fl = flags(train)
    res = {"rule": "D014_exploration_postprint_v1", "label": "EXPLORATION - a survivor is a candidate, never a finding",
           "step1": {"rows": len(rows), "below_1pct_gap_floor": below, "split_unchecked": unchecked,
                     "events": len(events), "train": len(train), "validation": len(valid),
                     "train_dates": len({e["R"] for e in train}), "validation_dates": len({e["R"] for e in valid}),
                     "voids_by_reason_year": {f"{k[0]}|{k[1]}": v for k, v in sorted(voids.items())},
                     "coverage": {k: sum(1 for e in events if e[k] is not None) for k in ("im", "surprise", "pmv", "spy_g")},
                     "quote_coverage": {k: sum(1 for e in events if e["hs"][k] is not None) for k in
                                        ("0935", "0940", "1000", "1030")},
                     "pmv_train_median_by_session": pm},
           "step2_descriptive": descriptive(events)}
    tests = family(train, fl)
    assert len(tests) == 42, len(tests)
    q = bh({k: (v.get("p") if v.get("p") is not None else 1.0) for k, v in tests.items()})
    for k in tests:
        tests[k]["q"] = q[k]
        tests[k]["survivor"] = bool(tests[k].get("t") is not None and abs(tests[k]["t"]) > 3 and q[k] < 0.10)
    res["step3_train_family"] = tests
    res["step3_train_secondary_market_adjusted"] = family(train, fl, "y_adj")
    surv = [k for k, v in tests.items() if v["survivor"]]
    res["survivors"] = surv
    val, one = {}, {}
    for k in surv:
        c, h = k.split("|")
        side = 1 if tests[k]["t"] > 0 else -1
        tr = [e for e in train if c == "all" or fl[c](e)]
        va = [e for e in valid if c == "all" or fl[c](e)]
        v = cell(va, "y", h)
        one[k] = (0.5 * v["p"] if (v.get("t") or 0) * side > 0 else 1 - 0.5 * v["p"]) if v.get("p") is not None else 1.0
        val[k] = {"train_net": net_cell(tr, h, side), "validation": v, "validation_one_sided_p": one[k],
                  "validation_net": net_cell(va, h, side), "validation_adjusted": cell(va, "y_adj", h)}
    adj = holm(one) if one else {}
    for k in surv:
        val[k]["validation_holm_p"] = adj[k]
        nm = val[k]["validation_net"]["net_mean"]
        val[k]["verdict"] = "CANDIDATE" if adj[k] < 0.05 and nm is not None and nm > 0 else "failed validation"
    res["step5_6_survivors"] = val
    res["verdict"] = ([f"{k}: {v['verdict']}" for k, v in val.items()] if surv
                      else ["no first-hour pattern clears the bar (|t| > 3 and BH q < 0.10 on TRAIN)"])
    if not surv:
        res["validation_descriptive_untested"] = {
            k: cell([e for e in valid if k.split("|")[0] == "all" or fl[k.split("|")[0]](e)], "y", k.split("|")[1])
            for k in tests}
    json.dump(res, open(os.path.join(HERE, "results.json"), "w", encoding="utf-8", newline="\n"), indent=1,
              sort_keys=True, default=str)
    report(res)


def f(x, pct=True, d=3):
    return "-" if x is None else f"{x * 100:+.{d}f}%" if pct else f"{x:+.2f}"


def report(res):
    s1 = res["step1"]
    L = ["# D014 - the first hour after the print (EXPLORATION)", "",
         "Frozen procedure `registry/D014_exploration_postprint_v1.md`. The gap's sign is read before 09:27 from "
         "pre-market trades; entry at the official opening auction. Positive y = the stock kept going the gap's way; "
         "negative = it reversed.", "",
         f"Events {s1['events']} with a pre-market gap of at least 1% (TRAIN {s1['train']} on {s1['train_dates']} "
         f"dates, VALIDATION {s1['validation']} on {s1['validation_dates']} dates); {s1['below_1pct_gap_floor']} below "
         f"the floor. Coverage: {s1['coverage']}. Quotes: {s1['quote_coverage']}.", "",
         "## Verdict", ""] + [f"- {v}" for v in res["verdict"]] + [
         "", "## TRAIN family (42 tests)", "",
         "| test | n | dates | mean y | t | q | survivor | complement mean |", "|---|---|---|---|---|---|---|---|"]
    for k, v in res["step3_train_family"].items():
        L.append(f"| {k} | {v['n']} | {v['dates']} | {f(v.get('mean'))} | {f(v.get('t'), False)} | "
                 f"{'-' if v.get('q') is None else round(v['q'], 3)} | {'**yes**' if v['survivor'] else ''} | "
                 f"{f((v.get('complement') or {}).get('mean'))} |")
    if res["step5_6_survivors"]:
        L += ["", "## Survivors: costs and VALIDATION", "",
              "| test | side | TRAIN net | VALIDATION mean y | Holm p | VALIDATION net | verdict |",
              "|---|---|---|---|---|---|---|"]
        for k, v in res["step5_6_survivors"].items():
            L.append(f"| {k} | {v['train_net']['side']} | {f(v['train_net']['net_mean'])} | "
                     f"{f(v['validation'].get('mean'))} | {round(v['validation_holm_p'], 4)} | "
                     f"{f(v['validation_net']['net_mean'])} | {v['verdict']} |")
    d = res["step2_descriptive"]
    L += ["", "## Descriptive (no tests)", "",
          f"- |pre-market gap| quantiles: {d['abs_premarket_gap_quantiles']}",
          f"- |gap| / implied move: {d['abs_gap_over_implied']}",
          f"- the open gap has the pre-market gap's sign in {d['open_gap_same_sign_as_premarket']:.1%} of events",
          f"- share of the reaction day's move reached by minute h (median): "
          f"{ {h: (None if v['median'] is None else round(v['median'], 2)) for h, v in d['share_of_day_move_reached_by_minute'].items()} }",
          f"- sources: {d['sources']}", ""]
    open(os.path.join(HERE, "REPORT.md"), "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
    print("\n".join(L[:10 + len(res["verdict"])]))


if __name__ == "__main__":
    main()
