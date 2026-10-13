"""D014 v2 sections 3-4: the pre-print state and the sector's week, inside the first hour after the print.
Imports v1's frozen run_d014 (events, signal, returns, CR1, BH, Holm, costs) so nothing can drift; adds the 18-test
family, the difference tests and the small-ticket costs. Writes results_v2.json and REPORT_v2.md. Deterministic.

    python analysis/d014/run_d014_v2.py
"""
import csv
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_d014 as rd  # noqa: E402

HV2 = ("5", "30", "60")
SMALL_FEE = 0.0013
GROUPS = {"C7_washed_out": lambda e: e["ret5"] is not None and e["ret5"] <= -0.08,
          "C8_ran_up": lambda e: e["ret5"] is not None and e["ret5"] >= 0.08,
          "C9_sector_sold": lambda e: e["rel5"] is not None and e["rel5"] < 0,
          "C10_sector_bought": lambda e: e["rel5"] is not None and e["rel5"] > 0}
DIFFS = {"C7_minus_C8": ("C7_washed_out", "C8_ran_up"), "C9_minus_C10": ("C9_sector_sold", "C10_sector_bought")}


def join(events):
    v2 = {(r["ticker"], r["R"]): r for r in csv.DictReader(open(os.path.join(rd.HERE, "raw", "events_v2.csv"),
                                                                  encoding="utf-8"))}
    for e in events:
        r = v2.get((e["ticker"], e["R"]), {})
        e["ret5"], e["rel5"] = rd.num(r.get("ret5")), rd.num(r.get("rel5"))
    return events


def diff_cell(a, b, h):
    """y = c + d * 1[group a] on the union of a and b; d and its CR1 standard error, clustered by R."""
    xs = [(e["y"][h], 1.0, e["R"]) for e in a if e["y"][h] is not None] + \
         [(e["y"][h], 0.0, e["R"]) for e in b if e["y"][h] is not None]
    na, nb = sum(1 for _, x, _ in xs if x), sum(1 for _, x, _ in xs if not x)
    da, db = len({r for _, x, r in xs if x}), len({r for _, x, r in xs if not x})
    out = {"n_a": na, "n_b": nb, "dates_a": da, "dates_b": db}
    if min(na, nb) < 30 or min(da, db) < 10:
        out["status"] = "insufficient"
        return out
    ma = sum(y for y, x, _ in xs if x) / na
    mb = sum(y for y, x, _ in xs if not x) / nb
    n, k = len(xs), 2
    # (X'X)^-1 for X = [1, x] with x binary: [[1/nb, -1/nb], [-1/nb, 1/na + 1/nb]]
    inv = ((1 / nb, -1 / nb), (-1 / nb, 1 / na + 1 / nb))
    by = {}
    for y, x, r in xs:
        u = y - (mb + (ma - mb) * x)
        s0, s1 = by.get(r, (0.0, 0.0))
        by[r] = (s0 + u, s1 + u * x)
    G = len(by)
    meat = [[0.0, 0.0], [0.0, 0.0]]
    for s0, s1 in by.values():
        v = (s0, s1)
        for i in range(2):
            for j in range(2):
                meat[i][j] += v[i] * v[j]
    row = (inv[1][0], inv[1][1])
    var = sum(row[i] * meat[i][j] * row[j] for i in range(2) for j in range(2))
    var *= G / (G - 1) * (n - 1) / (n - k)
    se = math.sqrt(var) if var > 0 else None
    d = ma - mb
    out.update({"mean_a": ma, "mean_b": mb, "diff": d, "se": se, "t": d / se if se else None})
    out["p"] = rd.p2(out["t"]) if out["t"] is not None else 1.0
    return out


def family(evs):
    up = [e for e in evs if e["s"] == 1]
    tests = {}
    for g in ("C7_washed_out", "C8_ran_up"):
        for h in HV2:
            tests[f"{g}|{h}"] = rd.cell([e for e in up if GROUPS[g](e)], "y", h)
    for h in HV2:
        a, b = DIFFS["C7_minus_C8"]
        tests[f"C7_minus_C8|{h}"] = diff_cell([e for e in up if GROUPS[a](e)], [e for e in up if GROUPS[b](e)], h)
    for g in ("C9_sector_sold", "C10_sector_bought"):
        for h in HV2:
            tests[f"{g}|{h}"] = rd.cell([e for e in up if GROUPS[g](e)], "y", h)
    for h in HV2:
        a, b = DIFFS["C9_minus_C10"]
        tests[f"C9_minus_C10|{h}"] = diff_cell([e for e in up if GROUPS[a](e)], [e for e in up if GROUPS[b](e)], h)
    return tests


def group_events(evs, name):
    up = [e for e in evs if e["s"] == 1]
    return [e for e in up if GROUPS[name](e)]


def nets(evs, h, side):
    """v1's net (2 bp) and the small-ticket net (13 bp) of the traded side."""
    a = rd.net_cell(evs, h, side)
    xs = [(rd.net(e, h, side) + rd.FEE - SMALL_FEE, e["R"]) for e in evs if rd.net(e, h, side) is not None]
    m, se = rd.cr1([y for y, _ in xs], [r for _, r in xs])
    return {"side": a["side"], "n": a["n"], "net_2bp": a["net_mean"], "t_2bp": a["t"], "net_13bp": m,
            "t_13bp": m / se if m is not None and se else None}


def main():
    rows, events, voids, below, unchecked = rd.build()
    events = join(events)
    train = [e for e in events if e["segment"] == "TRAIN"]
    valid = [e for e in events if e["segment"] == "VALIDATION"]
    res = {"rule": "D014_exploration_postprint_v2", "label": "EXPLORATION - a survivor is a candidate, never a finding",
           "step1": {"events": len(events), "with_ret5": sum(1 for e in events if e["ret5"] is not None),
                     "with_rel5": sum(1 for e in events if e["rel5"] is not None),
                     "gap_up_train": sum(1 for e in train if e["s"] == 1),
                     "group_sizes_train": {g: len(group_events(train, g)) for g in GROUPS}}}
    tests = family(train)
    assert len(tests) == 18, len(tests)
    q = rd.bh({k: (v.get("p") if v.get("p") is not None else 1.0) for k, v in tests.items()})
    for k in tests:
        tests[k]["q"] = q[k]
        tests[k]["survivor"] = bool(tests[k].get("t") is not None and abs(tests[k]["t"]) > 3 and q[k] < 0.10)
    res["train_family"] = tests
    surv = [k for k, v in tests.items() if v["survivor"]]
    res["survivors"] = surv
    vfam = family(valid)
    one, val = {}, {}
    for k in surv:
        name, h = k.split("|")
        side = 1 if tests[k]["t"] > 0 else -1
        v = vfam[k]
        one[k] = (0.5 * v["p"] if (v.get("t") or 0) * side > 0 else 1 - 0.5 * v["p"]) if v.get("p") is not None else 1.0
        val[k] = {"validation": v, "validation_one_sided_p": one[k]}
        if name in GROUPS:
            val[k]["train_nets"] = nets(group_events(train, name), h, side)
            val[k]["validation_nets"] = nets(group_events(valid, name), h, side)
    adj = rd.holm(one) if one else {}
    for k in surv:
        val[k]["validation_holm_p"] = adj[k]
        ok = adj[k] < 0.05
        if k.split("|")[0] in GROUPS:
            nm = val[k]["validation_nets"]["net_2bp"]
            ok = ok and nm is not None and nm > 0
        val[k]["verdict"] = "CANDIDATE" if ok else "failed validation"
    res["survivors_validation"] = val
    res["verdict"] = ([f"{k}: {v['verdict']}" for k, v in val.items()] if surv
                      else ["no pre-print-state or sector-week pattern clears the bar (|t| > 3 and BH q < 0.10 on TRAIN)"])
    # Section 4, secondary: small-ticket costs for v1's survivors and v1's delayed variant, whatever its verdict.
    sec = {}
    v1p = os.path.join(rd.HERE, "results.json")
    v1 = json.load(open(v1p, encoding="utf-8")) if os.path.exists(v1p) else {}
    pm, fl = rd.flags(train)
    keys = list(dict.fromkeys(v1.get("survivors", []) + ["all|d"]))
    for k in keys:
        c, h = k.split("|")
        t = (v1.get("step3_train_family") or {}).get(k, {}).get("t")
        tr = [e for e in train if c == "all" or fl[c](e)]
        va = [e for e in valid if c == "all" or fl[c](e)]
        sides = [1 if t > 0 else -1] if t else [1, -1]
        sec[f"v1 {k}"] = {("follow" if s == 1 else "fade"): {"train": nets(tr, h, s), "validation": nets(va, h, s)}
                          for s in sides}
    res["secondary_small_ticket"] = sec
    res["descriptive_with_positive_surprise"] = {
        f"{g}|{h}": rd.cell([e for e in group_events(train + valid, g) if (e["surprise"] or 0) > 0], "y", h)
        for g in ("C7_washed_out", "C8_ran_up") for h in HV2}
    json.dump(res, open(os.path.join(rd.HERE, "results_v2.json"), "w", encoding="utf-8", newline="\n"), indent=1,
              sort_keys=True, default=str)
    report(res)


def report(res):
    f = rd.f
    L = ["# D014 v2 - pre-print state and the sector's week, first hour after the print (EXPLORATION)", "",
         "Frozen procedure `registry/D014_exploration_postprint_v2.md`. Gap-up events only (s = +1). Positive y = "
         "the gap kept going after the open.", "", f"Step 1: {res['step1']}", "", "## Verdict", ""]
    L += [f"- {v}" for v in res["verdict"]]
    L += ["", "## TRAIN family (18 tests)", "", "| test | n | mean / diff | t | q | survivor |", "|---|---|---|---|---|---|"]
    for k, v in res["train_family"].items():
        n = v.get("n", f"{v.get('n_a')} vs {v.get('n_b')}")
        L.append(f"| {k} | {n} | {f(v.get('mean', v.get('diff')))} | {f(v.get('t'), False)} | "
                 f"{round(v['q'], 3)} | {'**yes**' if v['survivor'] else ''} |")
    L += ["", "## Secondary: small-ticket costs (13 bp vs 2 bp)", ""]
    for k, sides in res["secondary_small_ticket"].items():
        for side, d in sides.items():
            L.append(f"- {k} {side}: TRAIN net {f(d['train']['net_2bp'])} / {f(d['train']['net_13bp'])}; "
                     f"VALIDATION net {f(d['validation']['net_2bp'])} / {f(d['validation']['net_13bp'])}")
    open(os.path.join(rd.HERE, "REPORT_v2.md"), "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
    print("\n".join(L[:9 + len(res["verdict"])]))


if __name__ == "__main__":
    main()
