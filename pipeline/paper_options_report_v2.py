"""D011 paper report views (registry/D011_report_views_v1.md): the views promised on 2026-10-14, beside the frozen
report (pipeline/paper_options_report.py, implementation v3), which is not edited and stays the D011 report.
Descriptive: it adds no test, changes no rule and decides nothing. Code only, no AI.

    python pipeline/paper_options_report_v2.py [SEASON] [--write]

Both paper accounts: options (PX-F, the short iron butterfly, paper/options_ledger.json) and long (PX-L, the long
straddle, paper/long_ledger.json). Every block is shown three times: all trades, v3 only ("exec": "v3"), and all
trades without DPZ (seasonA-DPZ-2026-10-13-F, the v1 trade whose exit failed).
1. Fill rate as an outcome, read from ORDER RECORDS only (no result, P&L or grade is read for it):
   - opens: filled at attempt 0, filled at attempt 1, open_failed: platform, other failures, pending; and the counts
     of registry/D011_open_fill_trigger_v1.md (first 6 trades per account from snapshot 2026-10-16).
   - closes: for v3, the concession step of the order that completed the fill (0% ... 25%), or unfilled by expiry.
2. P&L at three prices next to the actual fill: mid, halfway (half-way from the mid to the far side) and far side
   (natural), each from the quotes the frozen code recorded on the orders that filled, quantity-weighted. Real round
   trips and all trades with a result (simulated legs labelled), each with and without exit_late; the frozen
   report's splits and pairings at each price.
3. Execution: each filled order's fill against its mid, natural and limit, and the share of the half-spread paid.
4. Each order against real OPRA prints (pipeline/paper_fill_recheck.py), where they were fetched.
Rule 7 on every P&L block: under 30 trades or 10 entry dates -> "insufficient".

Pricing (D011 conventions: per unit, debit +, credit -, P&L = -(open net + close net)):
- leg mid = (bid + ask) / 2, needing a bid, a positive ask and ask >= bid; far side = ask to buy, bid to sell (the
  frozen natural()); halfway = (mid + far side) / 2. A missing quote is never priced: that price is missing.
- A v3 close's dropped legs (zero bid) are outside the order and valued at 0 at every price (v3 §1); their mid at
  the close is shown separately.
- Simulated legs: an entry simulated for a platform reason is priced from the first opening record with a natural
  (the record the frozen settle() books). A position held past expiry closes at intrinsic, the same at every price.
  A close simulated because the entry was simulated recorded only its natural: its mid and halfway are missing.
- An adopted order carries the quotes of the run that adopted it, not of its send (flagged).
"""
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, now_et, write_json  # noqa: E402
from paper_options_report import LEDGERS, event_of, is_real, load, mean, median, season_of, shx_rows, status  # noqa: E402
import paper_fill_recheck as recheck  # noqa: E402

LEVELS = ("mid", "halfway", "natural")
PRICES = ("fill",) + LEVELS
DPZ = "seasonA-DPZ-2026-10-13-F"
SUBSETS = {"all": lambda t: True, "v3_only": lambda t: t.get("exec") == "v3",
           "without_DPZ": lambda t: t.get("key") != DPZ}
CONCESSIONS = (0.0, 0.05, 0.10, 0.15, 0.20, 0.25)      # D011 v3 §1 (paper_options.V3_CONCESSIONS)
TRIGGER_FROM, TRIGGER_N, TRIGGER_FAILS = "2026-10-16", 6, 2   # registry/D011_open_fill_trigger_v1.md
SESSION_END = datetime.time(16, 0)


# ---------------------------------------------------------------- prices
def leg_price(q, side, level):
    """One leg's price at mid, halfway or the far side; None if the quote cannot give it."""
    if not isinstance(q, dict):
        return None
    bid, ask = q.get("bid"), q.get("ask")
    if level == "natural":
        if side == "buy":
            return ask if ask else None
        return bid
    if bid is None or not ask or ask < bid:
        return None
    mid = (bid + ask) / 2
    return mid if level == "mid" else (mid + (ask if side == "buy" else bid)) / 2


def order_price(rec, level):
    """Net per unit of one order record at a price level, from its recorded sides and quotes (debit +)."""
    sides, q = (rec or {}).get("sides") or {}, (rec or {}).get("quotes") or {}
    if not sides:
        return None
    net = 0.0
    for sym, side in sides.items():
        p = leg_price(q.get(sym), side, level)
        if p is None:
            return None
        net += p if side == "buy" else -p
    return net


def recs(t, which):
    return (t.get("orders") or {}).get(which) or []


def filled_qty(rs):
    return sum(r.get("filled_qty") or 0 for r in rs if r.get("id"))


def chain_price(rs, level):
    """Quantity-weighted price of the filled records of one chain; None if a filled record cannot be priced."""
    tot = qty = 0.0
    for r in rs:
        if not r.get("filled_qty") or not r.get("id"):
            continue
        p = order_price(r, level)
        if p is None:
            return None
        tot += p * r["filled_qty"]
        qty += r["filled_qty"]
    return tot / qty if qty else None


def record_fill_net(r):
    """Per-unit net of ONE filled record from its legs (the frozen paper_options.fill_net convention)."""
    if not r.get("filled_qty"):
        return None
    total = 0.0
    for lg in r.get("legs_filled") or []:
        if lg.get("price") is None or lg.get("side") is None or abs((lg.get("qty") or 0) - r["filled_qty"]) > 1e-9:
            return None
        total += lg["price"] * lg["qty"] * (1 if lg["side"] == "buy" else -1)
    return total / r["filled_qty"]


def dropped_mid(rs):
    """Quantity-weighted mid of the legs a filled v3 close left out (sold legs: a credit, so negative)."""
    tot = qty = 0.0
    syms = set()
    for r in rs:
        if not r.get("filled_qty") or not r.get("id"):
            continue
        part = 0.0
        for d in r.get("dropped_legs") or []:
            syms.add(d["symbol"])
            m = leg_price(d, "sell", "mid")
            if m is None:
                return sorted(syms), None
            part -= m
        tot += part * r["filled_qty"]
        qty += r["filled_qty"]
    return sorted(syms), (tot / qty if qty else None)


def three_prices(t):
    """The trade's P&L at the fill and at the three prices. Only for trades with a result (the frozen settle())."""
    res = t["result"]
    o, c = recs(t, "open"), recs(t, "close")
    o_f, c_f = filled_qty(o), filled_qty(c)
    spot, qty = t.get("spot_at_gate"), res.get("qty") or 0
    out = {"fill": {"open": res.get("open_net"), "close": res.get("close_net"), "unit": res.get("pnl_per_unit"),
                    "pnl_on_spot": res.get("pnl_on_spot"), "pnl_usd": res.get("pnl")}}
    why = []
    for lv in LEVELS:
        op = cp = miss = None
        if o_f:
            op = chain_price(o, lv)
        elif t.get("open_failed") == "platform":         # the record settle() books: the first with a natural
            op = order_price(next((r for r in o if r.get("natural") is not None), None), lv)
        if op is None:
            miss = "an opening quote is missing"
        if o_f and c_f >= o_f:
            cp = chain_price(c, lv)
        elif t.get("close_sim"):
            sim = t["close_sim"].get("net")
            if o_f:                                      # held past expiry: intrinsic, the same at every price
                real = chain_price(c, lv) if c_f else 0.0
                cp = None if real is None or sim is None else (real * c_f + sim * (o_f - c_f)) / o_f
            elif lv == "natural":                        # entry simulated: the close recorded only its natural
                cp = sim
            else:
                miss = miss or "the simulated close recorded only its natural"
        if cp is None:
            miss = miss or "a closing quote is missing"
        if op is None or cp is None:
            out[lv] = None
            why.append(f"{lv}: {miss}")
            continue
        unit = -(op + cp)
        out[lv] = {"open": op, "close": cp, "unit": unit, "pnl_on_spot": unit / spot if spot else None,
                   "pnl_usd": round(unit * 100 * qty, 2)}
    if why:
        out["missing_why"] = sorted(set(why))
    syms, dm = dropped_mid(c)
    if syms:
        out["dropped_legs"] = {"symbols": syms, "mid_at_close_left_out": dm}
    return out


# ---------------------------------------------------------------- fill rate (order records only)
def orders_view(t):
    """The fields the fill-rate views may read: never result, P&L or grade."""
    keep = ("key", "ticker", "exec", "snapshot_session", "reaction_session", "expiry", "n", "skipped", "open_failed",
            "open_blocked", "close_rejected", "close_sim", "flag", "exit_late", "orders")
    v = {k: t[k] for k in keep if k in t}
    if "close_sim" in v:
        v["close_sim"] = True                          # only whether one exists, never its price
    return v


def attempt_of(rec, i, which):
    m = re.search(rf"-{which}(?:-r(\d+))?$", rec.get("client_order_id") or "")
    return int(m.group(1) or 0) if m else i


def minutes(a, b):
    try:
        return round((recheck.utc(b) - recheck.utc(a)).total_seconds() / 60, 1)
    except (TypeError, ValueError, AttributeError):
        return None


def attempts(rs, which):
    out = []
    for i, r in enumerate(rs):
        end = r.get("filled_at") if r.get("filled_qty") else r.get("cancel_requested")
        out.append({"attempt": attempt_of(r, i, which), "client_order_id": r.get("client_order_id"),
                    "status": r.get("status"), "filled_qty": r.get("filled_qty"), "concession": r.get("concession"),
                    "minutes_live": minutes(r.get("sent_et"), end) if end else None,
                    "adopted": bool(r.get("adopted")), "reject_kind": r.get("reject_kind")})
    return out


def open_outcome(v):
    """One trade's opening outcome from its order records (v = orders_view(trade))."""
    if v.get("skipped"):
        return {"outcome": f"skipped: {v['skipped']}", "sent": False}
    rs = recs(v, "open")
    filled = [(i, r) for i, r in enumerate(rs) if r.get("filled_qty") and r.get("id")]
    row = {"sent": bool(rs), "attempts": attempts(rs, "open")}
    if filled:
        i, r = filled[0]
        row["outcome"] = f"filled_attempt_{attempt_of(r, i, 'open')}"
        q = filled_qty(rs)
        if v.get("n") and q < v["n"]:
            row["partial"] = f"{q:g} of {v['n']}"
        row["minutes_to_fill"] = minutes(rs[0].get("sent_et"), r.get("filled_at"))
    elif v.get("open_failed"):
        row["outcome"] = f"open_failed: {v['open_failed']}"
    elif not rs:
        row["outcome"] = "pending: no opening order yet"
    else:
        row["outcome"] = "pending: an opening order is live"
    return row


def expired(v, now):
    e = v.get("expiry")
    if not e:
        return False
    d = now.date().isoformat()
    return e < d or (e == d and now.time() >= SESSION_END)


def close_outcome(v, now):
    """One trade's closing outcome from its order records. Only trades with a real opening fill have a close."""
    o, c = recs(v, "open"), recs(v, "close")
    o_f, c_f = filled_qty(o), filled_qty(c)
    if not o_f:
        return {"outcome": "no real position" + (" (close simulated)" if v.get("close_sim") else ""), "real": False}
    v3 = v.get("exec") == "v3"
    with_id = [r for r in c if r.get("id")]
    row = {"real": True, "v3": v3, "attempts": attempts(c, "close"), "attempts_sent": len(with_id)}
    if c_f >= o_f:
        done = [(k, r) for k, r in enumerate(with_id) if r.get("filled_qty")]
        k, r = done[-1]
        row["attempt_at_fill"] = k
        row["minutes_first_send_to_fill"] = minutes(c[0].get("sent_et"), r.get("filled_at"))
        if v3:
            cc = r.get("concession")
            row["concession_at_fill"] = cc
            row["outcome"] = f"filled at {round(cc * 100):d}%" if cc is not None else "filled (concession not recorded)"
            if len(done) > 1:
                row["concessions_of_partial_fills"] = [x.get("concession") for _, x in done]
        else:
            row["outcome"] = "filled (v1, no ladder)"
    elif v.get("close_rejected"):
        row["outcome"] = "close_rejected"
    elif expired(v, now) or v.get("close_sim"):
        row["outcome"] = "unfilled by expiry" + ("" if v3 else " (v1)")
        if c_f:
            row["partial"] = f"{c_f:g} of {o_f:g} closed"
    elif not c:
        row["outcome"] = "pending: no close sent yet"
    else:
        row["outcome"] = "pending: closing"
    return row


def open_counts(rows):
    out = {"trades_with_an_open_order": 0, "filled_attempt_0": 0, "filled_attempt_1": 0, "filled_other_attempt": 0,
           "open_failed: platform": 0, "open_failed: other": 0, "pending": 0}
    for r in rows:
        if not r.get("sent") and not r["outcome"].startswith("open_failed"):
            continue
        out["trades_with_an_open_order"] += 1 if r.get("sent") else 0
        o = r["outcome"]
        if o in ("filled_attempt_0", "filled_attempt_1"):
            out[o] += 1
        elif o.startswith("filled_attempt_"):
            out["filled_other_attempt"] += 1
        elif o == "open_failed: platform":
            out[o] += 1
        elif o.startswith("open_failed"):
            out["open_failed: other"] += 1
        else:
            out["pending"] += 1
    return out


def close_counts(rows):
    out = {f"{round(c * 100):d}%": 0 for c in CONCESSIONS}
    out.update({"unfilled by expiry": 0, "close_rejected": 0, "pending": 0, "v1: filled": 0, "v1: unfilled by expiry": 0})
    for r in rows:
        if not r.get("real"):
            continue
        o = r["outcome"]
        if r.get("v3"):
            if r.get("concession_at_fill") is not None:
                key = f"{round(r['concession_at_fill'] * 100):d}%"
                out[key] = out.get(key, 0) + 1
            elif o.startswith("unfilled"):
                out["unfilled by expiry"] += 1
            elif o == "close_rejected":
                out[o] += 1
            elif o.startswith("pending"):
                out["pending"] += 1
        else:
            if o.startswith("filled"):
                out["v1: filled"] += 1
            elif o.startswith("unfilled"):
                out["v1: unfilled by expiry"] += 1
            elif o.startswith("pending"):
                out["pending"] += 1
    return out


def open_fill_trigger(views):
    """registry/D011_open_fill_trigger_v1.md on one account: its first 6 trades with snapshot_session >= 2026-10-16
    that sent at least one opening order, in the order of their first opening send (ties: by key)."""
    pop = [v for v in views if (v.get("snapshot_session") or "") >= TRIGGER_FROM and recs(v, "open")]
    pop.sort(key=lambda v: (recheck.utc(recs(v, "open")[0]["sent_et"]), v.get("key") or ""))
    first = pop[:TRIGGER_N]
    rows = [{"key": v.get("key"), "outcome": open_outcome(v)["outcome"]} for v in first]
    n = {"filled_attempt_0": 0, "filled_attempt_1": 0, "open_failed: platform": 0, "other (counted, never triggers)": 0,
         "pending": 0}
    for r in rows:
        o = r["outcome"]
        if o in n:
            n[o] += 1
        elif o.startswith("pending"):
            n["pending"] += 1
        else:
            n["other (counted, never triggers)"] += 1
    if n["open_failed: platform"] >= TRIGGER_FAILS:
        state = "FIRED: draft D011 v4 for this account's opens (the v3 close ladder), with an independent review"
    elif len(rows) == TRIGGER_N and not n["pending"]:
        state = "not fired: v1 opens stay; close the note with these counts"
    else:
        state = f"open: {len(rows) - n['pending']} of {TRIGGER_N} decided"
    return {"rule": "registry/D011_open_fill_trigger_v1.md", "counted": len(rows), "counts": n, "state": state,
            "trades": rows, "order": "first opening send (UTC), ties by key"}


# ---------------------------------------------------------------- execution and real prints
def order_execution(r, which):
    fill = record_fill_net(r)
    nat, mid, half = order_price(r, "natural"), order_price(r, "mid"), order_price(r, "halfway")
    lim = recheck.limit_net(r)
    out = {"client_order_id": r.get("client_order_id"), "which": which, "concession": r.get("concession"),
           "adopted": bool(r.get("adopted")), "fill_net": fill, "mid": mid, "halfway": half, "natural": nat,
           "limit": lim, "recorded_natural": r.get("natural")}
    if nat is not None and r.get("natural") is not None and abs(nat - r["natural"]) > 1e-6:
        out["natural_mismatch"] = True
    for k, x in (("mid", mid), ("natural", nat), ("limit", lim)):
        out[f"fill_minus_{k} (+ = worse)"] = None if fill is None or x is None else round(fill - x, 4)
    out["share_of_half_spread_paid"] = (None if fill is None or mid is None or nat is None or nat - mid < 1e-9
                                        else (fill - mid) / (nat - mid))
    return out


def execution_rows(trades):
    rows = []
    for t in trades:
        for which in ("open", "close"):
            for r in recs(t, which):
                if r.get("filled_qty") and r.get("id"):
                    rows.append(dict(order_execution(r, which), key=t.get("key"), exec=t.get("exec")))
    return rows


def execution_summary(rows):
    def blk(rs):
        sh = [r["share_of_half_spread_paid"] for r in rs if r["share_of_half_spread_paid"] is not None]
        return {"orders": len(rs), "mean_share_of_half_spread_paid": mean(sh),
                "median_share_of_half_spread_paid": median(sh),
                "mean_fill_minus_natural": mean([r["fill_minus_natural (+ = worse)"] for r in rs
                                                 if r["fill_minus_natural (+ = worse)"] is not None]),
                "mean_fill_minus_limit": mean([r["fill_minus_limit (+ = worse)"] for r in rs
                                               if r["fill_minus_limit (+ = worse)"] is not None]),
                "unpriced": len(rs) - len(sh), "adopted": sum(1 for r in rs if r["adopted"]),
                "natural_mismatch": sum(1 for r in rs if r.get("natural_mismatch"))}
    return {"open": blk([r for r in rows if r["which"] == "open"]),
            "close": blk([r for r in rows if r["which"] == "close"])}


def recheck_rows(trades, season, cache):
    out = []
    for t in trades:
        for which in ("open", "close"):
            for r in recs(t, which):
                if not r.get("id") or not r.get("client_order_id"):
                    continue
                filled = recheck.is_filled(r)
                if not filled and r.get("status") not in recheck.TERMINAL:
                    continue
                c = cache(season, r["client_order_id"])
                row = {"key": t.get("key"), "exec": t.get("exec"), "which": which,
                       "client_order_id": r["client_order_id"], "fetched": c is not None}
                if c is not None:
                    row.update(recheck.compare_filled(r, c) if filled else recheck.compare_unfilled(r, c))
                else:
                    row["kind"] = "filled" if filled else "unfilled"
                out.append(row)
    return out


def recheck_summary(rows):
    f = [r for r in rows if r["kind"] == "filled"]
    u = [r for r in rows if r["kind"] == "unfilled"]
    legs = [lg for r in f if r["fetched"] for lg in r["legs"].values()]
    worse = [lg["worse_by_vs_nearest_trade"] for lg in legs if lg.get("worse_by_vs_nearest_trade") is not None]
    ulegs = [lg for r in u if r["fetched"] for lg in r["legs"].values()]
    return {"filled_orders": len(f), "filled_fetched": sum(1 for r in f if r["fetched"]),
            "filled_legs": len(legs),
            "legs_with_a_real_trade_nearby": sum(1 for lg in legs if lg.get("nearest_trade") is not None),
            "legs_with_a_trade_within_60s": sum(1 for lg in legs if (lg.get("nearest_trade_dt_s") or 1e9) <= 60),
            "legs_paper_inside_bar_range": sum(1 for lg in legs if lg.get("paper_inside_range") is True),
            "legs_paper_outside_bar_range": sum(1 for lg in legs if lg.get("paper_inside_range") is False),
            "mean_leg_worse_by_vs_nearest_trade": mean(worse),
            "orders_with_every_leg_traded": sum(1 for r in f if r.get("net_at_nearest_trades") is not None),
            "unfilled_orders": len(u), "unfilled_fetched": sum(1 for r in u if r["fetched"]),
            "unfilled_legs_with_prints_while_live": sum(1 for lg in ulegs if lg.get("bars_while_live")),
            "unfilled_legs_whose_print_reached_far_side": sum(1 for lg in ulegs if lg.get("print_reached_far_side")),
            "unfilled_orders_prints_reached_limit (not simultaneous)":
                sum(1 for r in u if r.get("prints_reached_limit (not simultaneous)"))}


# ---------------------------------------------------------------- P&L summaries at every price
def summary_at(rows, price):
    """rows: [(trade, prices)]; the frozen summary's fields at one price, over the trades priced there."""
    got = [(t, p[price]) for t, p in rows if p.get(price) and p[price].get("pnl_on_spot") is not None]
    xs = [v["pnl_on_spot"] for _, v in got]
    dates = len({t.get("snapshot_session") for t, _ in got})
    return {"n": len(xs), "missing": len(rows) - len(xs), "entry_dates": dates, "mean_pnl_on_spot": mean(xs),
            "median_pnl_on_spot": median(xs), "hit_rate": mean([1.0 if x > 0 else 0.0 for x in xs]),
            "pnl_usd": round(sum(v["pnl_usd"] for _, v in got), 2), "status": status(len(xs), dates)}


def at_prices(rows):
    return {p: summary_at(rows, p) for p in PRICES}


def splits_at(rows):
    return {"by_gate_status": {k: at_prices([x for x in rows if (x[0].get("gate_status") == "PASS") == (k == "PASS")])
                               for k in ("PASS", "other")},
            "by_session": {k: at_prices([x for x in rows if x[0].get("session") == k]) for k in ("BMO", "AMC")}}


def paired_shx_at(rows, shx, structure):
    """The frozen report's SH-X pairing at each price (PX-F: paper - SH-X; PX-L: paper + SH-X)."""
    sign = 1 if structure == "PX-F" else -1
    out = {}
    for price in PRICES:
        pairs = [(t, p[price]["pnl_on_spot"], shx[event_of(t)]) for t, p in rows
                 if event_of(t) in shx and p.get(price) and p[price].get("pnl_on_spot") is not None]
        dates = len({t.get("snapshot_session") for t, _, _ in pairs})
        out[price] = {"n": len(pairs), "entry_dates": dates, "mean_paper": mean([a for _, a, _ in pairs]),
                      "mean_SH_X": mean([b for _, _, b in pairs]),
                      ("mean_paper_minus_SH_X" if sign == 1 else "mean_paper_plus_SH_X (opposite sides)"):
                          mean([a - sign * b for _, a, b in pairs]), "status": status(len(pairs), dates)}
    return out


def pnl_block(rows, shx, structure):
    real = [x for x in rows if is_real(x[0])]

    def no_late(rs):
        return [x for x in rs if not x[0].get("exit_late")]
    return {"real": {"all": at_prices(real), "without_exit_late": at_prices(no_late(real)),
                     "splits": splits_at(real), "splits_without_exit_late": splits_at(no_late(real)),
                     "paired_with_SH_X": {"all": paired_shx_at(real, shx, structure),
                                          "without_exit_late": paired_shx_at(no_late(real), shx, structure)}},
            "all_with_result (simulated legs labelled)": {"all": at_prices(rows),
                                                          "without_exit_late": at_prices(no_late(rows))}}


def both_sides_at(F, L, keep, late_cut):
    """The frozen report's PX-L / PX-F pairing at each price: events where both sides are real round trips."""
    out = {}
    keys = [k for k in F if k in L and keep(F[k][0]) and keep(L[k][0]) and is_real(F[k][0]) and is_real(L[k][0])
            and not (late_cut and (F[k][0].get("exit_late") or L[k][0].get("exit_late")))]
    for price in PRICES:
        ks = [k for k in keys if (F[k][1].get(price) or {}).get("pnl_on_spot") is not None
              and (L[k][1].get(price) or {}).get("pnl_on_spot") is not None]
        f = [F[k][1][price]["pnl_on_spot"] for k in ks]
        lv = [L[k][1][price]["pnl_on_spot"] for k in ks]
        dates = len({F[k][0].get("snapshot_session") for k in ks})
        out[price] = {"n": len(ks), "entry_dates": dates, "mean_PX-F": mean(f), "mean_PX-L": mean(lv),
                      "mean_sum": mean([a + b for a, b in zip(f, lv)]), "status": status(len(ks), dates)}
    return out


# ---------------------------------------------------------------- the report
def build(ledgers, shx, season, now, cache):
    """ledgers: {"PX-F": ledger dict or None, "PX-L": ...}; cache(season, client_order_id) -> stored prints or None."""
    out = {"season": season, "rule": "registry/D011_report_views_v1.md (descriptive; the frozen D011 report is "
           "pipeline/paper_options_report.py)", "run_et": now.isoformat(timespec="seconds"),
           "label": "PAPER - descriptive execution views; adds no test, changes no rule",
           "subsets": {"all": "every trade", "v3_only": 'trades with "exec": "v3"',
                       "without_DPZ": f"every trade except {DPZ}"}}
    priced = {}
    for s in LEDGERS:
        led = ledgers.get(s)
        if not led:
            out[s] = {"note": f"no ledger {LEDGERS[s]}"}
            continue
        trades = [t for k, t in sorted((led.get("trades") or {}).items()) if season_of(k, t) == season]
        rows = [(t, three_prices(t)) for t in trades if "result" in t]
        priced[s] = {event_of(t): (t, p) for t, p in rows if t.get("ticker")}
        views = [orders_view(t) for t in trades]
        per_trade = []
        for t, v in zip(trades, views):
            p = next((p for tt, p in rows if tt is t), None)
            per_trade.append({"key": t.get("key"), "exec": t.get("exec") or "v1",
                              "snapshot_session": t.get("snapshot_session"), "open": open_outcome(v),
                              "close": close_outcome(v, now), "simulated_legs": (t.get("result") or {}).get(
                                  "simulated_legs"), "prices": p})
        exec_rows = execution_rows(trades)
        rc_rows = recheck_rows(trades, season, cache)
        acct = {"records": len(trades), "per_trade": per_trade,
                "open_fill_trigger_v1": open_fill_trigger(views), "by_subset": {}}
        for name, keep in SUBSETS.items():
            kt = [t for t in trades if keep(t)]
            kv = [orders_view(t) for t in kt]
            acct["by_subset"][name] = {
                "trades": len(kt),
                "fill_rate": {"opens": open_counts([open_outcome(v) for v in kv]),
                              "closes": close_counts([close_outcome(v, now) for v in kv])},
                "pnl": pnl_block([x for x in rows if keep(x[0])], shx, s),
                "execution": execution_summary([r for r in exec_rows if keep({"key": r["key"], "exec": r["exec"]})]),
                "real_prints": recheck_summary([r for r in rc_rows if keep({"key": r["key"], "exec": r["exec"]})])}
        acct["execution_orders"] = exec_rows
        acct["real_prints_orders"] = rc_rows
        out[s] = acct
    F, L = priced.get("PX-F", {}), priced.get("PX-L", {})
    out["PX-L_and_PX-F_paired"] = {name: {"all": both_sides_at(F, L, keep, False),
                                          "without_exit_late": both_sides_at(F, L, keep, True)}
                                   for name, keep in SUBSETS.items()}
    return out


# ---------------------------------------------------------------- markdown
def pct(x, d=3):
    return "-" if x is None else f"{x * 100:.{d}f}%"


def num(x, d=2):
    return "-" if x is None else f"{x:.{d}f}"


def markdown(r):
    L = [f"# D011 paper report views - {r['season']} - {r['run_et'][:16]} ET", "",
         "Descriptive, from `registry/D011_report_views_v1.md`. It adds no test and changes no rule. The D011 report "
         "of record stays `pipeline/paper_options_report.py`. Every number below is computed by code from the two "
         "paper ledgers and the stored real prints.", "",
         "Subsets: **all** = every trade; **v3 only** = `\"exec\": \"v3\"`; **without DPZ** = every trade except "
         f"`{DPZ}`. Status follows rule 7 (under 30 trades or 10 entry dates = insufficient).", ""]
    accts = [s for s in LEDGERS if "by_subset" in r.get(s, {})]
    L += ["## 1. Fill rate (order records only)", "", "### Opens", "",
          "| account | subset | trades with an open order | filled at attempt 0 | at attempt 1 | open_failed: platform "
          "| other failure | pending |", "|---|---|---|---|---|---|---|---|"]
    for s in accts:
        for name, b in r[s]["by_subset"].items():
            o = b["fill_rate"]["opens"]
            L.append(f"| {s} | {name} | {o['trades_with_an_open_order']} | {o['filled_attempt_0']} | "
                     f"{o['filled_attempt_1']} | {o['open_failed: platform']} | {o['open_failed: other']} | "
                     f"{o['pending']} |")
    L += ["", "### Open-fill trigger v1 (first 6 trades per account from snapshot 2026-10-16)", "",
          "| account | counted | attempt 0 | attempt 1 | platform failures | other | pending | state |",
          "|---|---|---|---|---|---|---|---|"]
    for s in accts:
        g = r[s]["open_fill_trigger_v1"]
        n = g["counts"]
        L.append(f"| {s} | {g['counted']} of 6 | {n['filled_attempt_0']} | {n['filled_attempt_1']} | "
                 f"{n['open_failed: platform']} | {n['other (counted, never triggers)']} | {n['pending']} | "
                 f"{g['state']} |")
    L += ["", "### Closes: the concession step at fill (v3), or unfilled by expiry", "",
          "| account | subset | 0% | 5% | 10% | 15% | 20% | 25% | unfilled by expiry | rejected | pending | "
          "v1 filled | v1 unfilled |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for s in accts:
        for name, b in r[s]["by_subset"].items():
            c = b["fill_rate"]["closes"]
            L.append(f"| {s} | {name} | " + " | ".join(str(c[f"{round(x * 100):d}%"]) for x in CONCESSIONS)
                     + f" | {c['unfilled by expiry']} | {c['close_rejected']} | {c['pending']} | {c['v1: filled']} | "
                       f"{c['v1: unfilled by expiry']} |")
    L += ["", "## 2. P&L per $1 of spot at the fill and at three prices", "",
          "Mean (n). Mid = the middle of each recorded quote; halfway = half-way from the mid to the far side; "
          "natural = the far side.", "",
          "| account | subset | sample | fill | mid | halfway | natural | entry dates | status |",
          "|---|---|---|---|---|---|---|---|---|"]
    for s in accts:
        for name, b in r[s]["by_subset"].items():
            for samp, blk in (("real round trips", b["pnl"]["real"]["all"]),
                              ("real, without exit_late", b["pnl"]["real"]["without_exit_late"]),
                              ("all with a result (simulated labelled)",
                               b["pnl"]["all_with_result (simulated legs labelled)"]["all"])):
                cells = " | ".join(f"{pct(blk[p]['mean_pnl_on_spot'])} ({blk[p]['n']})" for p in PRICES)
                L.append(f"| {s} | {name} | {samp} | {cells} | {blk['fill']['entry_dates']} | "
                         f"{blk['fill']['status']} |")
    L += ["", "## 3. Execution: each filled order against its own quotes", "",
          "Share of the half-spread paid: 0 = filled at the mid, 1 = at the far side, above 1 = worse than the far side.",
          "", "| account | subset | orders | mean share of half-spread paid | median | mean fill - natural | "
              "mean fill - limit |", "|---|---|---|---|---|---|---|"]
    for s in accts:
        for name, b in r[s]["by_subset"].items():
            for which in ("open", "close"):
                e = b["execution"][which]
                L.append(f"| {s} | {name} ({which}) | {e['orders']} | {num(e['mean_share_of_half_spread_paid'])} | "
                         f"{num(e['median_share_of_half_spread_paid'])} | {num(e['mean_fill_minus_natural'], 3)} | "
                         f"{num(e['mean_fill_minus_limit'], 3)} |")
    L += ["", "## 4. Orders against real OPRA prints (Alpaca historical bars and trades)", "",
          "Trades, not quotes: a check, not a fill model. Missing prints stay missing.", "",
          "| account | subset | filled orders (fetched) | legs | real trade nearby | within 60 s | inside bar range "
          "| outside | mean leg fill worse than nearest trade | unfilled orders (fetched) | prints reached the limit "
          "(not simultaneous) |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for s in accts:
        for name, b in r[s]["by_subset"].items():
            x = b["real_prints"]
            L.append(f"| {s} | {name} | {x['filled_orders']} ({x['filled_fetched']}) | {x['filled_legs']} | "
                     f"{x['legs_with_a_real_trade_nearby']} | {x['legs_with_a_trade_within_60s']} | "
                     f"{x['legs_paper_inside_bar_range']} | {x['legs_paper_outside_bar_range']} | "
                     f"{num(x['mean_leg_worse_by_vs_nearest_trade'], 3)} | {x['unfilled_orders']} "
                     f"({x['unfilled_fetched']}) | {x['unfilled_orders_prints_reached_limit (not simultaneous)']} |")
    L += ["", "## 5. Per trade", "",
          "| account | trade | exec | open | close | P&L/spot fill | mid | halfway | natural | simulated |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for s in accts:
        for t in r[s]["per_trade"]:
            p = t["prices"] or {}
            cells = " | ".join(pct((p.get(k) or {}).get("pnl_on_spot")) for k in PRICES)
            L.append(f"| {s} | {t['key']} | {t['exec']} | {t['open']['outcome']} | {t['close']['outcome']} | {cells} | "
                     f"{', '.join(t['simulated_legs'] or []) or '-'} |")
    return "\n".join(L) + "\n"


def report(season="seasonA", write=False, now=None):
    now = now or now_et()
    ledgers = {s: load(os.path.join(ROOT, rel)) for s, rel in LEDGERS.items()}
    r = build(ledgers, shx_rows(season), season, now, lambda se, cid: recheck.load_cached(se, cid))
    md = markdown(r)
    print(md)
    if write:
        base = os.path.join(ROOT, "outcomes", "paper", f"options_report_v2_{season}_{now:%Y-%m-%d}")
        write_json(base + ".json", r)
        with open(base + ".md", "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
    return r


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    report(a[0] if a else "seasonA", "--write" in sys.argv)
