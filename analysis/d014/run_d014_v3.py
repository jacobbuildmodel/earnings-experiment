"""D014 v3 section 2: v1 and v2 group-mean survivors priced at the retail entry (first-minute VWAP worsened by half the
first post-open quoted spread). Adds no hypothesis test. Imports v1's and v2's frozen code. Writes results_v3.json and
REPORT_v3.md. Deterministic.

    python analysis/d014/run_d014_v3.py
"""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_d014 as rd  # noqa: E402
import run_d014_v2 as r2  # noqa: E402

FEES = {"2bp": 0.0002, "13bp": 0.0013}


def join(events):
    p = os.path.join(rd.HERE, "raw", "events_v3.csv")
    v3 = {(r["ticker"], r["R"]): r for r in csv.DictReader(open(p, encoding="utf-8"))}
    for e in events:
        r = v3.get((e["ticker"], e["R"]), {})
        e["vw"], e["hs_first"] = rd.num(r.get("vw")), rd.num(r.get("hs_first"))
        e["first_bid"], e["first_ask"] = rd.num(r.get("first_bid")), rd.num(r.get("first_ask"))
    return events


def entry(e, d, kind):
    """The entry price for trade direction d (+1 buy, -1 short) under one entry definition."""
    if kind == "auction":
        return e["o"]
    if kind == "primary":
        return e["vw"] * (1 + d * e["hs_first"]) if e["vw"] and e["hs_first"] is not None else None
    if kind == "vwap":
        return e["vw"]
    if kind == "far_side":
        return e["first_ask"] if d == 1 else e["first_bid"]
    raise ValueError(kind)


def retail_net(e, h, side, kind="primary", fee=0.0002):
    d = side * e["s"]
    E = entry(e, d, kind)
    if not E:
        return None
    if h == "c":
        X = e["p"]["c"]
    else:
        k = rd.EXIT_Q[h]
        X = e["mid"][k] * (1 - d * e["hs"][k]) if e["mid"][k] is not None and e["hs"][k] is not None else None
    if X is None:
        return None
    return d * (X / E - 1) - fee


def summary(evs, h, side, kind, fee):
    xs = [(retail_net(e, h, side, kind, fee), e["R"]) for e in evs if retail_net(e, h, side, kind, fee) is not None]
    m, se = rd.cr1([y for y, _ in xs], [r for _, r in xs])
    return {"n": len(xs), "dates": len({r for _, r in xs}), "net_mean": m, "t": m / se if m is not None and se else None}


def label(tr, va, h, side):
    out = {}
    for f, fee in FEES.items():
        out[f] = {"train": summary(tr, h, side, "primary", fee), "validation": summary(va, h, side, "primary", fee)}
    ok = lambda f: all((out[f][s]["net_mean"] or 0) > 0 and out[f][s]["net_mean"] is not None for s in ("train", "validation"))
    out["label"] = ("executable at small tickets" if ok("13bp") else "executable (retail)" if ok("2bp") else "auction-only")
    return out


def main():
    rows, events, voids, below, unchecked = rd.build()
    events = join(r2.join(events))
    train = [e for e in events if e["segment"] == "TRAIN"]
    valid = [e for e in events if e["segment"] == "VALIDATION"]
    pm, fl = rd.flags(train)
    res = {"rule": "D014_exploration_postprint_v3", "label": "EXPLORATION cost addendum - adds no test",
           "coverage": {"events": len(events), "with_retail_entry": sum(1 for e in events if e["vw"] and e["hs_first"] is not None)}}
    lab = {}
    v1 = json.load(open(os.path.join(rd.HERE, "results.json"), encoding="utf-8"))
    for k in v1.get("survivors", []):
        c, h = k.split("|")
        if h == "d":
            continue
        side = 1 if v1["step3_train_family"][k]["t"] > 0 else -1
        lab[f"v1 {k}"] = label([e for e in train if c == "all" or fl[c](e)], [e for e in valid if c == "all" or fl[c](e)],
                               h, side)
        lab[f"v1 {k}"]["v1_verdict"] = (v1.get("step5_6_survivors") or {}).get(k, {}).get("verdict")
    p2 = os.path.join(rd.HERE, "results_v2.json")
    v2 = json.load(open(p2, encoding="utf-8")) if os.path.exists(p2) else {}
    for k in v2.get("survivors", []):
        g, h = k.split("|")
        if g not in r2.GROUPS:
            continue
        side = 1 if v2["train_family"][k]["t"] > 0 else -1
        lab[f"v2 {k}"] = label(r2.group_events(train, g), r2.group_events(valid, g), h, side)
        lab[f"v2 {k}"]["v2_verdict"] = (v2.get("survivors_validation") or {}).get(k, {}).get("verdict")
    res["survivor_labels"] = lab
    desc = {}
    for h in ("5", "10", "30", "60", "c"):
        for side, name in ((1, "follow"), (-1, "fade")):
            desc[f"all|{h} {name}"] = {seg: {kind: summary(evs, h, side, kind, 0.0002)["net_mean"]
                                             for kind in ("auction", "primary", "vwap", "far_side")}
                                       for seg, evs in (("train", train), ("validation", valid))}
    res["descriptive_unconditional_by_entry_2bp"] = desc
    json.dump(res, open(os.path.join(rd.HERE, "results_v3.json"), "w", encoding="utf-8", newline="\n"), indent=1,
              sort_keys=True, default=str)
    f = rd.f
    L = ["# D014 v3 - the retail entry (cost addendum, no new test)", "",
         "Frozen `registry/D014_exploration_postprint_v3.md`. Retail entry = the first regular minute's VWAP worsened "
         "by half the first post-open quoted spread (moomoo SG has no opening-auction order).", "",
         f"Coverage: {res['coverage']}", "", "## Survivors", ""]
    L += [f"- {k}: **{v['label']}** - retail net TRAIN {f(v['2bp']['train']['net_mean'])} / VALIDATION "
          f"{f(v['2bp']['validation']['net_mean'])} at 2 bp; {f(v['13bp']['validation']['net_mean'])} at 13 bp "
          f"(VALIDATION)" for k, v in lab.items()] or ["- no v1 or v2 group-mean survivor to price"]
    L += ["", "## Unconditional, net at 2 bp by entry (descriptive)", "",
          "| cell | segment | auction | retail (primary) | plain VWAP | far side |", "|---|---|---|---|---|---|"]
    for k, segs in desc.items():
        for seg, d in segs.items():
            L.append(f"| {k} | {seg} | {f(d['auction'])} | {f(d['primary'])} | {f(d['vwap'])} | {f(d['far_side'])} |")
    open(os.path.join(rd.HERE, "REPORT_v3.md"), "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
    print("\n".join(L[:8 + len(lab)]))


if __name__ == "__main__":
    main()
