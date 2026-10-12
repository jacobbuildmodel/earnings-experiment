"""D012 H-XT: the tradable short straddle. Code only; reads graded SH-X rows, never grades anything itself.

    python pipeline/shadow_xt.py report SEASON [--write] [--final]
    python pipeline/shadow_xt.py report-pooled SEASON SEASON [--write] [--final]

H-XT (registry/D012_tradable_straddle_v1.md §2): mean SH-X P&L on spot (bid) > 0 over the graded SH-X events
whose gate.json records options.rel_spread <= 0.10 on BOTH the call and the put. A gate without rel_spread is
out. SH-X rows, voids and grading are D009's (pipeline/shadow.py, not edited); the test is D009's H-X test
(shadow.mean_test) under the name "H-XT", in its own family (m = 1, alpha 0.05).
Reported beside it, descriptive (§4): SH-X at mid on the subset, D011 PX-F and PX-L on the subset, and SH-X on
the excluded (wider) gates.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, now_et, write_json  # noqa: E402

MAX_REL_SPREAD = 0.10
LEDGERS = {"PX-F": os.path.join("paper", "options_ledger.json"), "PX-L": os.path.join("paper", "long_ledger.json")}


def load(p):
    return json.load(open(p, encoding="utf-8"))


def gate_spread(season, ticker, date):
    """(call, put) rel_spread recorded by the gate, or None if the gate or the field is missing."""
    p = os.path.join(ROOT, "events", season, f"{ticker}_{date}", "gate.json")
    if not os.path.exists(p):
        return None
    rs = (load(p).get("options") or {}).get("rel_spread") or {}
    if rs.get("call") is None or rs.get("put") is None:
        return None
    return float(rs["call"]), float(rs["put"])


def tradable(spread):
    return spread is not None and spread[0] <= MAX_REL_SPREAD and spread[1] <= MAX_REL_SPREAD


def split(rows):
    """SH-X rows of one or more seasons -> (in H-XT, excluded). Each row must carry its season."""
    inn, out = [], []
    for e in rows:
        if e["track"] != "SH-X":
            continue
        sp = gate_spread(e["season"], e["ticker"], e["date"])
        (inn if tradable(sp) else out).append({**e, "rel_spread_gate": sp})
    return inn, out


def paper_pnl(rows, track):
    """D011 ledger results (pnl_on_spot) for the same events, real-fill round trips and all trades."""
    p = os.path.join(ROOT, LEDGERS[track])
    if not os.path.exists(p):
        return {"n": 0}
    trades = load(p).get("trades", {})
    keys = {f"{e['season']}-{e['ticker']}-{e['date']}" for e in rows}
    res = [t["result"] for k, t in trades.items() if k.rsplit("-", 1)[0] in keys and t.get("result")]
    real = [r["pnl_on_spot"] for r in res if not r.get("simulated_legs")]
    allr = [r["pnl_on_spot"] for r in res]
    mean = lambda xs: sum(xs) / len(xs) if xs else None  # noqa: E731
    return {"n_real": len(real), "mean_real": mean(real), "n_all": len(allr), "mean_all": mean(allr)}


def stats(allrows, final=False):
    import shadow
    graded = [e for e in allrows if e.get("graded")]
    X, excl = split(graded)
    g = lambda rs: [e["timing"]["entry"]["session"] for e in rs]  # noqa: E731
    clean = lambda rs: [e for e in rs if not set(e.get("flags", [])) & {"timing_unverified", "late_8k"}]  # noqa: E731
    r = shadow.mean_test([e["straddle"]["pnl_on_spot"] for e in X], g(X), "H-XT")
    r["mde"] = shadow.mde(r)
    import report
    if not report.sufficient(r.get("n", 0), r.get("dates", 0) or 0):
        r["status"] = "insufficient"
    elif not final:
        r["status"] = "interim (monitoring only)"
    else:
        p = r.get("p_one_sided")
        r["status"] = ("p < 0.05 (shadow, confirmatory for H-XT)" if p is not None and p == p and p < 0.05 else
                       f"no evidence (shadow) - an effect smaller than {r['mde'] * 100:.2f} pts would usually be missed"
                       if r.get("mde") else "no evidence (shadow)")
    mids = [e["straddle"]["pnl_on_spot_mid"] for e in X if e["straddle"].get("pnl_on_spot_mid") is not None]
    sens = {"H-XT without timing_unverified / late_8k":
            shadow.mean_test([e["straddle"]["pnl_on_spot"] for e in clean(X)], g(clean(X)), "H-XT-clean")}
    desc = {"SH-X at mid on the H-XT subset": shadow.mean_test(mids, [e["timing"]["entry"]["session"] for e in X
                                                                        if e["straddle"].get("pnl_on_spot_mid") is not None],
                                                                "H-XT-mid"),
            "D011 PX-F on the subset": paper_pnl(X, "PX-F"),
            "D011 PX-L on the subset": paper_pnl(X, "PX-L"),
            "SH-X on the excluded gates (rel_spread > 0.10 or missing)":
                shadow.mean_test([e["straddle"]["pnl_on_spot"] for e in excl], g(excl), "H-XT-excluded"),
            "events": {"graded SH-X": len(X) + len(excl), "in H-XT": len(X), "excluded": len(excl),
                       "excluded for a missing rel_spread": sum(1 for e in excl if e["rel_spread_gate"] is None)}}
    return {"H-XT": r}, sens, desc


def run(seasons, write=False, final=False, pooled=False):
    import shadow
    if any(s.lower().startswith("pilot") for s in seasons):
        raise SystemExit("D009 §6 / D012: pilot numbers are never part of H-XT")
    loaded = [(s, load(os.path.join(ROOT, "outcomes", "shadow", s, "graded.json"))["events"]) for s in seasons]
    allrows, dropped = shadow.pool(loaded)
    res, sens, desc = stats(allrows, final)
    out = {"seasons": list(seasons), "pooled": pooled, "rule": "D012_tradable_straddle_v1 §2-§4",
           "run_et": now_et().isoformat(timespec="seconds"),
           "label": "SHADOW - confirmatory for H-XT only at Season B's end, pooled" + ("" if final else "; INTERIM - no verdict"),
           "tests": res, "sensitivity": sens, "descriptive": desc, "duplicates_dropped": dropped}
    v = res["H-XT"]
    print(f"H-XT {'+'.join(seasons)}: n={v.get('n')} dates={v.get('dates')} "
          + (f"mean={v['mean'] * 100:+.2f}% " if v.get("mean") is not None else "")
          + (f"t={v['t']:.2f} p={v['p_one_sided']:.3f} " if v.get("t") is not None and v["t"] == v["t"] else "")
          + str(v.get("status", v.get("note"))))
    print(json.dumps(desc, default=str))
    if write:
        name = ("pooled_" if pooled else "") + "+".join(seasons)
        write_json(os.path.join(ROOT, "outcomes", "shadow", "reports", f"HXT_{name}_{now_et():%Y-%m-%d}.json"), out)
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    seasons = [x for x in a[1:] if not x.startswith("--")]
    if a[:1] == ["report"] and len(seasons) == 1:
        run(seasons, "--write" in a, "--final" in a)
    elif a[:1] == ["report-pooled"] and len(seasons) >= 2 and len(set(seasons)) == len(seasons):
        run(seasons, "--write" in a, "--final" in a, pooled=True)
    else:
        raise SystemExit(__doc__)
