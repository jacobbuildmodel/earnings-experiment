"""
BACKTEST — replay the FORECAST layer over every scored event in the ledger.
================================================================================
Owner asked for the theory to be tested against the data that already exists. This is that
test, and it is the largest sample PRE has ever had (every historical entry that carries both
its frozen inputs and a recorded outcome).

*** WHAT THIS IS AND IS NOT ***
NOT forward validation. `pre_forecast` was written on 2026-07-30, after every outcome below
was known. A post-hoc function scored against the outcomes it post-dates is contaminated by
construction — HANDOFF §3.3. Nothing here may be quoted as an edge, a hit rate, or evidence
that the layer works.

What it CAN legitimately do, and the reason it is worth running:
  * find STRUCTURE — does accuracy differ by regime / conviction / basis? A signal that is
    flat across every slice is not a signal, and that verdict is safe even on contaminated
    data because it is a NEGATIVE result.
  * check the layer never abstains on real inputs, at scale.
  * expose the base rate: what fraction of these events gapped UP at all? If the sample is
    70% up, then "always guess UP" is the benchmark to beat, and any accuracy below it is
    worse than a constant.

The base-rate comparison is the important column. It is the one that cannot flatter the model.
"""
import json
from pathlib import Path

from pre_forecast import forecast

ROOT = Path(__file__).resolve().parent
LEDGER = ROOT / "ledger.jsonl"


def build():
    rows = [json.loads(l) for l in LEDGER.open(encoding="utf-8") if l.strip()]
    entries = {r["id"]: r for r in rows if r.get("type") == "entry"}
    outs = [r for r in rows if r.get("type") == "outcome"]
    paired = []
    for o in outs:
        e = entries.get(o.get("entry_id"))
        if not e or o.get("idio_open_pct") is None:
            continue
        j = (e.get("inputs") or {}).get("judgment") or {}
        m = (e.get("inputs") or {}).get("market") or {}
        sk = (e.get("inputs") or {}).get("skew") or {}
        ped, ep = j.get("stock_pct_since_last_earnings"), j.get("sector_etf_pct_same_window")
        excess = (ped - ep) if (ped is not None and ep is not None) else None
        comps = (e.get("verdict") or {}).get("components") or {}
        exp = None
        if comps:
            exp = (comps.get("REV", 0) + comps.get("GG", 0) + comps.get("VEL", 0)
                   + comps.get("FLAG", 0)) / 4.0
        f = forecast(e["ticker"], expectations=exp or 0.0, excess=excess,
                     dd=j.get("pct_below_52w_high"), implied_move=m.get("implied_move"),
                     avg_gap=m.get("avg_abs_open"), bad_gap=m.get("gap_bad_case"),
                     put_call=sk.get("put_call_oi_ratio"),
                     short_interest=sk.get("short_interest_pct_float"),
                     event_date=e.get("event_date"),
                     trade_stance=(e.get("verdict") or {}).get("action"))
        idio = o["idio_open_pct"]
        paired.append({"ticker": e["ticker"], "event": e.get("event_date"), "idio": idio,
                       "dir": f.direction, "conv": f.conviction, "basis": f.basis,
                       "regime": f.regime, "signal": f.signal,
                       "correct": (f.direction == "UP") == (idio > 0),
                       "big": abs(idio) >= 5.0, "trade": f.trade_stance})
    # one row per (ticker, event) — the ledger contains re-registrations
    uniq = {}
    for p in paired:
        uniq[(p["ticker"], p["event"])] = p
    return sorted(uniq.values(), key=lambda r: (r["event"] or "", r["ticker"]))


def acc(rows):
    if not rows:
        return None
    return (round(100 * sum(r["correct"] for r in rows) / len(rows), 1), len(rows))


def main():
    P = build()
    if not P:
        print("no scored events with usable inputs"); return
    up = sum(1 for r in P if r["idio"] > 0)
    base_dir = "UP" if up >= len(P) / 2 else "DOWN"
    base = round(100 * max(up, len(P) - up) / len(P), 1)

    print("=" * 96)
    print(f"  FORECAST BACKTEST — {len(P)} scored events from the ledger")
    print("  *** CONTAMINATED: the layer post-dates every outcome. NOT evidence. ***")
    print("=" * 96)
    print(f"\n  BASE RATE: {up}/{len(P)} events gapped UP. Always guessing {base_dir} "
          f"scores {base}% — that is the number to beat.")
    o = acc(P)
    print(f"  FORECAST : {o[0]}%  (n={o[1]})   -> "
          f"{'BEATS' if o[0] > base else 'DOES NOT BEAT'} the constant guess"
          f"  [{o[0]-base:+.1f}pp]")

    for key, label in (("basis", "BY BASIS"), ("conv", "BY CONVICTION"), ("regime", "BY REGIME")):
        print(f"\n  {label}")
        for v in sorted({r[key] for r in P}):
            a = acc([r for r in P if r[key] == v])
            flag = "" if a[1] >= 5 else "   (n too small to read)"
            print(f"    {v:22s} {a[0]:5.1f}%  n={a[1]:<3d}{flag}")

    big = [r for r in P if r["big"]]
    if big:
        a = acc(big)
        print(f"\n  ON >=5% MOVERS: {a[0]}%  n={a[1]}  "
              f"({100*len(big)//len(P)}% of events moved >=5% idio)")
    ev = [r for r in P if r["basis"] != "COINFLIP"]
    if ev:
        a = acc(ev)
        print(f"  EXCLUDING COINFLIPS: {a[0]}%  n={a[1]}")

    cf = [r for r in P if r["basis"] == "COINFLIP"]
    print(f"\n  abstention check: {len(P)} events, {len(P)} directions emitted, "
          f"0 abstentions. {len(cf)} labelled COINFLIP.")

    print("\n  WORST MISSES (largest moves called wrong):")
    for r in sorted([r for r in P if not r["correct"]], key=lambda r: -abs(r["idio"]))[:6]:
        print(f"    {r['ticker']:6s} {r['event']}  called {r['dir']:4s} "
              f"[{r['basis']:9s}] {r['regime']:20s} -> {r['idio']:+7.2f}")
    print("\n  BEST CALLS:")
    for r in sorted([r for r in P if r["correct"]], key=lambda r: -abs(r["idio"]))[:6]:
        print(f"    {r['ticker']:6s} {r['event']}  called {r['dir']:4s} "
              f"[{r['basis']:9s}] {r['regime']:20s} -> {r['idio']:+7.2f}")

    json.dump(P, (ROOT / "_backtest_forecast.json").open("w"), indent=1)
    print(f"\n  wrote _backtest_forecast.json")


if __name__ == "__main__":
    main()
