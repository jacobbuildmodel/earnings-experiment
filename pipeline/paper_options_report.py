"""D011 §8 (v1) and §3 (v2): the paper-options report. Code only; reads the two ledgers and D009's graded SH-X rows.
It computes §8 and nothing else, and changes nothing in §3-§7.
Registered as D011 implementation v3 (D011 v1 §8 said "implementation v2" and "paper_options.py report"; v2's name
went to the long straddle, and paper_options.py is frozen, so the report is this separate file).

    python pipeline/paper_options_report.py [SEASON] [--write]

Classes of a trade with a result:
  real P&L     no simulated leg (an adopted fill IS a real Alpaca fill and counts here; adopted trades are counted)
  execution    result.entry_vs_alpaca_natural present - settle() sets it only for a real, non-adopted opening fill,
               whatever happened at the close
Per structure (PX-F, the short iron butterfly; PX-L, the long straddle):
1. Execution: fill - natural per unit (negative = the fill beat the far-side quotes) and as a share of the
   natural premium (the natural of the first filled opening attempt, as settle() uses); PX-F only: the credit
   minus the gate's bid sum (wings included - NOT a pure execution gap).
2. P&L per $1 of spot (pnl_on_spot) and dollars, on the real sample and on all trades with a result (simulated
   legs labelled), each with and without exit_late; split by gate status (PASS / other) and session (BMO / AMC).
3. Paired with SH-X (D009) on the same events. PX-F is the same side as SH-X: paper - SH-X. PX-L is the opposite
   side: paper + SH-X (≈ minus what the two sides paid). With and without exit_late.
4. Capacity refusals by date, every outcome label, and the flags.
v2: per event, PX-L next to PX-F where both have a real round trip; with and without exit_late.
Rule 7 on every block: under 30 trades or 10 entry dates -> "insufficient" (numbers shown, no verdict).
Disclosed: a trade whose opening was simulated never carries exit_late, even when its simulated exit ran after
15:00, so it survives the "without exit_late" cut; SH-X voids (print timing) make the paired n smaller than the
P&L n. Median = the middle value, or the mean of the two middle values.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, now_et, write_json  # noqa: E402

LEDGERS = {"PX-F": os.path.join("paper", "options_ledger.json"), "PX-L": os.path.join("paper", "long_ledger.json")}


def load(p):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def mean(xs):
    return sum(xs) / len(xs) if xs else None


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    if not n:
        return None
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def status(n, dates):
    return "insufficient" if n < 30 or dates < 10 else "descriptive (shadow)"


def season_of(key, t):
    return t.get("season") or key.split("-")[0]


def event_of(t):
    return (t.get("ticker"), t.get("report_date"))


def is_real(t):
    return "result" in t and not t["result"].get("simulated_legs")


def has_execution(t):
    return "result" in t and t["result"].get("entry_vs_alpaca_natural") is not None


def no_late(ts):
    return [t for t in ts if not t.get("exit_late")]


def summary(trades):
    xs = [t["result"]["pnl_on_spot"] for t in trades]
    dates = len({t.get("snapshot_session") for t in trades})
    return {"n": len(xs), "entry_dates": dates, "mean_pnl_on_spot": mean(xs), "median_pnl_on_spot": median(xs),
            "hit_rate": mean([1.0 if x > 0 else 0.0 for x in xs]),
            "pnl_usd": round(sum(t["result"]["pnl"] for t in trades), 2), "status": status(len(xs), dates)}


def splits(trades):
    return {"by_gate_status": {k: summary([t for t in trades if (t.get("gate_status") == "PASS") == (k == "PASS")])
                               for k in ("PASS", "other")},
            "by_session": {k: summary([t for t in trades if t.get("session") == k]) for k in ("BMO", "AMC")}}


def first_filled_natural(t):
    return next((r["natural"] for r in (t.get("orders") or {}).get("open", [])
                 if r.get("filled_qty") and r.get("natural") is not None), None)


def execution(trades, structure):
    ex = [t for t in trades if has_execution(t)]
    pct = [t["result"]["entry_vs_alpaca_natural"] / abs(first_filled_natural(t)) for t in ex if first_filled_natural(t)]
    out = {"n": len(ex), "entry_dates": len({t.get("snapshot_session") for t in ex}),
           "mean_fill_minus_natural_per_unit": mean([t["result"]["entry_vs_alpaca_natural"] for t in ex]),
           "mean_fill_minus_natural_share_of_premium": mean(pct)}
    if structure == "PX-F":
        out["mean_credit_minus_gate_bid_sum (wings included, NOT pure execution)"] = mean(
            [t["result"]["entry_credit_vs_gate_bid_sum"] for t in ex if "entry_credit_vs_gate_bid_sum" in t["result"]])
    out["status"] = status(out["n"], out["entry_dates"])
    return out


def paired_shx(trades, shx, structure):
    sign = 1 if structure == "PX-F" else -1
    pairs = [(t, t["result"]["pnl_on_spot"], shx[event_of(t)]) for t in trades if event_of(t) in shx]
    name = "mean_paper_minus_SH_X" if sign == 1 else "mean_paper_plus_SH_X (opposite sides)"
    return {"n": len(pairs), "entry_dates": len({t.get("snapshot_session") for t, _, _ in pairs}),
            "mean_paper": mean([a for _, a, _ in pairs]), "mean_SH_X": mean([b for _, _, b in pairs]),
            name: mean([a - sign * b for _, a, b in pairs]),
            "status": status(len(pairs), len({t.get("snapshot_session") for t, _, _ in pairs}))}


def structure_report(trades, shx, structure):
    done = [t for t in trades if "result" in t]
    rt = [t for t in done if is_real(t)]
    out = {"records": len(trades), "with_result": len(done), "real_round_trips": len(rt),
           "simulated": sum(1 for t in done if not is_real(t)),
           "adopted": sum(1 for t in trades if any(r.get("adopted") for r in (t.get("orders") or {}).get("open", [])))}
    out["execution"] = execution(done, structure)
    out["pnl_real"] = {"all": summary(rt), "without_exit_late": summary(no_late(rt)),
                       "splits": splits(rt), "splits_without_exit_late": splits(no_late(rt))}
    out["pnl_all_simulated_labelled"] = {"all": summary(done), "without_exit_late": summary(no_late(done)),
                                         "splits": splits(done), "splits_without_exit_late": splits(no_late(done))}
    out["paired_with_SH_X"] = {"all": paired_shx(rt, shx, structure),
                               "without_exit_late": paired_shx(no_late(rt), shx, structure)}
    cap = {}
    for t in trades:
        for r in (t.get("orders") or {}).get("open", []) + (t.get("orders") or {}).get("close", []):
            if r.get("reject_kind") == "capacity":
                d = (r.get("sent_et") or "")[:10]
                cap[d] = cap.get(d, 0) + 1
    labels = {}
    for t in trades:
        lab = (t.get("skipped") or t.get("open_failed") or ("orphan_order" if t.get("orphan_order") else None)
               or ("result" if "result" in t else "open/pending"))
        labels[lab] = labels.get(lab, 0) + 1
    out["capacity_refusals_by_date"] = cap
    out["labels"] = labels
    out["flags"] = {k: sum(1 for t in trades if t.get(k)) for k in
                    ("exit_late", "flag", "partial_open", "fill_unreadable", "close_rejected", "orphan_order")}
    return out


def shx_rows(season):
    g = load(os.path.join(ROOT, "outcomes", "shadow", season, "graded.json"))
    if not g:
        return {}
    return {(e["ticker"], e["date"]): e["straddle"]["pnl_on_spot"] for e in g["events"]
            if e["track"] == "SH-X" and e.get("graded") and not e.get("void") and e.get("straddle")}


def both_sides(F, L, late_cut):
    keys = [k for k in F if k in L and is_real(F[k]) and is_real(L[k])
            and not (late_cut and (F[k].get("exit_late") or L[k].get("exit_late")))]
    s = [F[k]["result"]["pnl_on_spot"] + L[k]["result"]["pnl_on_spot"] for k in keys]
    dates = len({F[k].get("snapshot_session") for k in keys})
    return {"n": len(keys), "entry_dates": dates, "mean_PX-F": mean([F[k]["result"]["pnl_on_spot"] for k in keys]),
            "mean_PX-L": mean([L[k]["result"]["pnl_on_spot"] for k in keys]),
            "mean_sum (~ minus the shared body's round-trip cost, plus the wings' P&L)": mean(s),
            "status": status(len(keys), dates),
            "per_event": [{"event": f"{k[0]}_{k[1]}", "PX-F": F[k]["result"]["pnl_on_spot"],
                           "PX-L": L[k]["result"]["pnl_on_spot"]} for k in sorted(keys)]}


def report(season="seasonA", write=False):
    shx = shx_rows(season)
    out = {"season": season, "rule": "D011_paper_options_v1 §8 + v2 §3 (implementation v3)",
           "run_et": now_et().isoformat(timespec="seconds"), "label": "PAPER - descriptive execution track; adds no test"}
    by = {}
    for s, rel in LEDGERS.items():
        led = load(os.path.join(ROOT, rel))
        trades = [t for k, t in (led or {}).get("trades", {}).items() if season_of(k, t) == season]
        by[s] = {event_of(t): t for t in trades if t.get("ticker")}
        out[s] = structure_report(trades, shx, s) if led else {"note": f"no ledger {rel}"}
    out["PX-L_and_PX-F_paired"] = {"all": both_sides(by["PX-F"], by["PX-L"], False),
                                   "without_exit_late": both_sides(by["PX-F"], by["PX-L"], True)}
    for s in LEDGERS:
        r = out[s]
        if "pnl_real" in r:
            p = r["pnl_real"]["all"]
            m = p["mean_pnl_on_spot"]
            print(f"{s}: {r['real_round_trips']} real round trip(s), mean pnl/spot "
                  f"{None if m is None else round(m * 100, 3)}% [{p['status']}]; execution n={r['execution']['n']}; "
                  f"labels {r['labels']}")
    print("paired PX-L/PX-F:", out["PX-L_and_PX-F_paired"]["all"]["n"])
    if write:
        write_json(os.path.join(ROOT, "outcomes", "paper", f"options_report_{season}_{now_et():%Y-%m-%d}.json"), out)
    return out


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    report(a[0] if a else "seasonA", "--write" in sys.argv)
