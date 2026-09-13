"""
DEFECT-TIER RE-SCORE — every ledger entry under OLD vs NEW normalisation.
================================================================================
The DEFECT tier (governance, added 2026-08-09) waives the 2-holdout requirement for a
change whose ONLY claim is "behaviour now matches documentation" — but it makes a full
ledger re-score MANDATORY and the flip set must be disclosed. This is that re-score.

    python rescore_units.py

Read-only. It replays each frozen entry through both arithmetics and prints every
verdict that changes. No edge is asserted anywhere in this file.
"""
from __future__ import annotations
import json
from pathlib import Path

from pre_engine import Judgment, Market, EngineConfig, evaluate
import pre_edgescore as ES

ROOT = Path(__file__).parent


def old_expectations(r, W):
    """The pre-1.5.7 arithmetic: divide by the CONSTANT full-population range."""
    c = r.components
    weighted = (W["REV"] * c["REV"] + W["GG"] * c["GG"] + W["VEL"] * c["VEL"] + c["FLAG"])
    norm = 4.0 * (ES._fund_weight_sum(W) / 3.0)
    return max(-1.0, min(1.0, weighted / norm))


def new_expectations(r, W):
    """v1.5.7: divide by the summed range of the legs actually VERIFIED."""
    c = r.components
    weighted = (W["REV"] * c["REV"] + W["GG"] * c["GG"] + W["VEL"] * c["VEL"] + c["FLAG"])
    fund = sum(ES.LEG_RANGE[l] for l in ("REV", "GG", "VEL") if l in (r.verified or []))
    if fund <= 0:
        return 0.0
    return max(-1.0, min(1.0, weighted / (fund * (ES._fund_weight_sum(W) / 3.0))))


def verdict_from(expectations, positioning, confidence):
    """Replicate the stance/tier cascade on a given expectations value."""
    raw = ES.W_EXPECTATIONS * expectations + ES.W_POSITIONING * positioning
    score = raw * confidence
    if abs(score) < ES.EDGE_MIN:
        stance = "NO_TRADE"
    elif score >= ES.EDGE_MIN:
        stance = "BUY"
    elif score > -ES.SHORT_EDGE_MIN:
        stance = "NO_TRADE"
    elif expectations < 0 and positioning <= 0:
        stance = "SHORT"
    else:
        stance = "NO_TRADE"
    conv = "NONE"
    if stance in ("BUY", "SHORT"):
        for lo, name, _ in ES.TIERS:
            if abs(score) >= lo:
                conv = name
                break
    return stance, conv, score


def main():
    rows = [json.loads(l) for l in (ROOT / "ledger.jsonl").open(encoding="utf-8") if l.strip()]
    entries = [r for r in rows if r.get("type") == "entry"]
    voids = {r["entry_id"] for r in rows if r.get("type") == "void"}
    outcomes = {r["entry_id"]: r for r in rows if r.get("type") == "outcome"}

    flips, same, skipped = [], 0, 0
    for e in entries:
        ji = (e.get("inputs") or {}).get("judgment") or {}
        mi = (e.get("inputs") or {}).get("market") or {}
        if not ji or not mi:
            skipped += 1
            continue
        try:
            j = Judgment(**{k: v for k, v in ji.items() if k in Judgment.__dataclass_fields__})
            m = Market(**{k: v for k, v in mi.items() if k in Market.__dataclass_fields__})
            cfg = EngineConfig(fasttrack=True, watch=False, react_in_ds=False)
            r = evaluate(j, m, cfg=cfg)
        except Exception:
            skipped += 1
            continue
        # An entry that replays to INPUT_INVALID returns no components at all. It has
        # no expectations term either way, so the fix cannot move it. Counted, not scored.
        if not r.components:
            skipped += 1
            continue

        W = ES.SECTOR_WEIGHTS.get(ES.SECTOR_OF.get(e["ticker"], "DEFAULT"),
                                  ES.SECTOR_WEIGHTS["DEFAULT"])
        excess = None
        if ji.get("stock_pct_since_last_earnings") is not None and \
           ji.get("sector_etf_pct_same_window") is not None:
            excess = ji["stock_pct_since_last_earnings"] - ji["sector_etf_pct_same_window"]
        dd = ji.get("pct_below_52w_high")
        washed = (excess is not None and excess <= -15.0) and (dd is not None and dd >= 20.0)
        extended = (excess is not None and excess >= 15.0)
        pos = 1.0 if washed else (-1.0 if extended else 0.0)

        slots = {"REV": "REV" in (r.verified or []), "GG": "GG" in (r.verified or []),
                 "VEL": "VEL" in (r.verified or []),
                 "WASH": excess is not None and dd is not None}
        conf = ES.CONF_FLOOR + ES.CONF_SPAN * (sum(slots.values()) / len(slots))

        o_exp, n_exp = old_expectations(r, W), new_expectations(r, W)
        o_st, o_cv, o_sc = verdict_from(o_exp, pos, conf)
        n_st, n_cv, n_sc = verdict_from(n_exp, pos, conf)

        rec = {"ticker": e["ticker"], "date": e["event_date"], "id": e["id"],
               "void": e["id"] in voids, "REV": r.components["REV"],
               "verified": [x for x in (r.verified or []) if x in ("REV", "GG", "VEL")],
               "pos": pos, "conf": round(conf, 3),
               "old": (o_st, o_cv, round(o_sc, 4)), "new": (n_st, n_cv, round(n_sc, 4)),
               "idio": (outcomes.get(e["id"]) or {}).get("idio_open_pct")}
        if o_st != n_st or o_cv != n_cv:
            flips.append(rec)
        else:
            same += 1

    print("=" * 84)
    print("DEFECT-TIER RE-SCORE — units normalisation (constant 4 -> summed range of "
          "verified legs)")
    print("=" * 84)
    print(f"entries replayed: {len(entries) - skipped}   unchanged: {same}   "
          f"FLIPPED: {len(flips)}   unreplayable: {skipped}")
    if not flips:
        print("\n  no verdicts change.")
    else:
        print(f"\n{'ticker':7s}{'date':12s}{'REV':>4s} {'pos':>5s} {'legs':12s}"
              f"{'OLD':28s}{'NEW':28s}{'idio':>8s}")
        print("-" * 104)
        for f in sorted(flips, key=lambda x: (x["void"], x["date"])):
            o = f"{f['old'][0]}/{f['old'][1]} {f['old'][2]:+.4f}"
            n = f"{f['new'][0]}/{f['new'][1]} {f['new'][2]:+.4f}"
            idio = f"{f['idio']:+.2f}%" if f["idio"] is not None else "  --"
            print(f"{f['ticker']:7s}{f['date']:12s}{f['REV']:>+4d} {f['pos']:>+5.0f} "
                  f"{','.join(f['verified']) or '-':12s}{o:28s}{n:28s}{idio:>8s}"
                  + ("   [VOID]" if f["void"] else ""))

    # what the flip set does to the graded record — reported as COST, never as evidence
    graded = [f for f in flips if f["idio"] is not None and not f["void"]]
    if graded:
        print("\n  Of the flips, those with a graded outcome in the CLEAN record:")
        opened = [f for f in graded if f["old"][0] in ("BUY", "SHORT")
                  and f["new"][0] == "NO_TRADE"]
        newly = [f for f in graded if f["old"][0] == "NO_TRADE"
                 and f["new"][0] in ("BUY", "SHORT")]
        for f in opened:
            s = f["idio"] if f["old"][0] == "BUY" else -f["idio"]
            print(f"    REMOVED a trade: {f['ticker']:6s} {f['date']}  was "
                  f"{s:+.2f}% {'win' if s > 0 else 'loss'}")
        for f in newly:
            s = f["idio"] if f["new"][0] == "BUY" else -f["idio"]
            print(f"    ADDED a trade:   {f['ticker']:6s} {f['date']}  would have been "
                  f"{s:+.2f}% {'win' if s > 0 else 'loss'}")
        print("\n  >>> THE HARD CONSTRAINT (governance, DEFECT tier):")
        print("      At n=11 the flip set IS the training set. These counts are evidence")
        print("      about the COST of the fix. They are NEVER the reason to ship it.")
        print("      The reason to ship is that the scorer did not do what it said.")
    print("=" * 84)


if __name__ == "__main__":
    main()
