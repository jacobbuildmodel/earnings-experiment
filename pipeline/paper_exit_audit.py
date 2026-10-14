"""D011 exit audit (registry/D011_exit_audit_v1.md): descriptive, decides nothing. For every paper options trade
whose opening order filled and whose close was sent, the P&L had the FIRST close filled at the moment it was sent.
That is the on-time counterfactual, priced from the quotes the frozen code recorded with that order:
  at the natural (the limit actually sent) and at the mid.
It sits next to what really happened: when the close filled, how many attempts it took, and the result.
delay_cost = actual P&L - counterfactual at the natural (negative = the late or failed exit cost money).

    python pipeline/paper_exit_audit.py [SEASON] [--write]
"""
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ET, ROOT, now_et, write_json  # noqa: E402

LEDGERS = {"PX-F": os.path.join("paper", "options_ledger.json"), "PX-L": os.path.join("paper", "long_ledger.json")}


def net_of_fill(recs):
    """Per-unit net of filled orders, debit positive (the frozen paper_options.fill_net convention)."""
    total = qty = 0.0
    for r in recs:
        if not r.get("filled_qty"):
            continue
        legs = r.get("legs_filled") or []
        if not legs or any(lg.get("price") is None for lg in legs):
            return None
        for lg in legs:
            total += lg["price"] * lg["qty"] * (1 if lg["side"] == "buy" else -1)
        qty += r["filled_qty"]
    return total / qty if qty else None


def mid_of(rec):
    q, sides = rec.get("quotes") or {}, rec.get("sides") or {}
    if not q or set(q) != set(sides) or any(q[s].get("bid") is None or q[s].get("ask") is None for s in q):
        return None
    return sum((q[s]["bid"] + q[s]["ask"]) / 2 * (1 if sd == "buy" else -1) for s, sd in sides.items())


def audit_trade(t):
    o = (t.get("orders") or {}).get("open", [])
    c = (t.get("orders") or {}).get("close", [])
    if not any(r.get("filled_qty") for r in o) or not c:
        return None
    open_net = net_of_fill(o)
    first = c[0]
    spot = t.get("spot_at_gate")
    cf_nat = -(open_net + first["natural"]) if open_net is not None and first.get("natural") is not None else None
    m = mid_of(first)
    cf_mid = -(open_net + m) if open_net is not None and m is not None else None
    filled = [r for r in c if r.get("filled_qty")]
    fill_at = None
    if filled and filled[-1].get("filled_at"):
        fill_at = datetime.datetime.fromisoformat(filled[-1]["filled_at"].replace("Z", "+00:00")).astimezone(ET)
    rs = t.get("reaction_session")
    actual = (t.get("result") or {}).get("pnl_per_unit")
    out = {"key": t.get("key"), "ticker": t.get("ticker"), "reaction_session": rs,
           "first_close_sent_et": first.get("sent_et"), "close_attempts": len(c),
           "counterfactual_on_time_natural": cf_nat, "counterfactual_on_time_mid": cf_mid,
           "exit_spread_cost": (cf_mid - cf_nat) if cf_nat is not None and cf_mid is not None else None,
           "close_filled_et": fill_at.isoformat() if fill_at else None,
           "filled_same_day": bool(fill_at and fill_at.date().isoformat() == rs),
           "filled_by_1500": bool(fill_at and fill_at.date().isoformat() == rs and fill_at.time() <= datetime.time(15, 0)),
           "actual_pnl_per_unit": actual, "simulated_legs": (t.get("result") or {}).get("simulated_legs"),
           "delay_cost": (actual - cf_nat) if actual is not None and cf_nat is not None else None,
           "state": "settled" if actual is not None else "open"}
    if spot:
        for k in ("counterfactual_on_time_natural", "counterfactual_on_time_mid", "actual_pnl_per_unit", "delay_cost"):
            out[k + "_on_spot"] = out[k] / spot if out[k] is not None else None
    return out


def audit(season="seasonA", write=False):
    res = {"rule": "D011_exit_audit_v1 (descriptive, decides nothing)", "season": season,
           "run_et": now_et().isoformat(timespec="seconds")}
    for s, rel in LEDGERS.items():
        p = os.path.join(ROOT, rel)
        led = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {"trades": {}}
        rows = [a for k, t in led.get("trades", {}).items()
                if (t.get("season") or k.split("-")[0]) == season and (a := audit_trade(t))]
        res[s] = {"trades": rows, "n": len(rows),
                  "not_filled_same_day": sum(1 for r in rows if not r["filled_same_day"]),
                  "mean_delay_cost": (sum(r["delay_cost"] for r in rows if r["delay_cost"] is not None)
                                      / max(1, sum(1 for r in rows if r["delay_cost"] is not None)))
                  if any(r["delay_cost"] is not None for r in rows) else None}
        for r in rows:
            print(f"{s} {r['key']}: on-time natural {r['counterfactual_on_time_natural']} / mid "
                  f"{r['counterfactual_on_time_mid']}; attempts {r['close_attempts']}; filled {r['close_filled_et']}; "
                  f"actual {r['actual_pnl_per_unit']}; delay cost {r['delay_cost']}")
    if write:
        write_json(os.path.join(ROOT, "outcomes", "paper", f"exit_audit_{season}_{now_et():%Y-%m-%d}.json"), res)
    return res


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    audit(a[0] if a else "seasonA", "--write" in sys.argv)
