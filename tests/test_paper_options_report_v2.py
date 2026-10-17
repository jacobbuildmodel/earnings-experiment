"""D011 report views (registry/D011_report_views_v1.md): three prices, all / v3 only / without DPZ, fill rate as an
outcome (order records only), the open-fill trigger counts, execution, and the real-prints join. Fixtures are the two
real ledgers as committed at c3eb852 (tests/fixtures/paper_ledgers_2026-10-16.json); round trips are completed from
those records and settled by the FROZEN paper_options.settle(), so every result has the live code's shape.
Run: python -m pytest tests/test_paper_options_report_v2.py -q"""
import copy
import datetime
import hashlib
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
import paper_options as po  # noqa: E402
import paper_options_report_v2 as v2  # noqa: E402
from common import ET  # noqa: E402

HERE = os.path.dirname(__file__)
REPO = os.path.join(HERE, "..")
FX = json.load(open(os.path.join(HERE, "fixtures", "paper_ledgers_2026-10-16.json"), encoding="utf-8"))
NOW = datetime.datetime(2026, 10, 16, 20, 45, tzinfo=ET)          # after DPZ's expiry-day close
NOC_SPOT = 514.280029296875
DPZ_SPOT = 307.385009765625


def real(acct, key):
    return copy.deepcopy(FX[acct]["trades"][key])


def ledgers(*extra):
    """Both real ledgers, plus extra trades given as (account, trade)."""
    led = {a: copy.deepcopy(FX[a]) for a in ("PX-F", "PX-L")}
    for a, t in extra:
        led[a]["trades"][t["key"]] = t
    return led


def close_rec(cid, sides, quotes, fill=None, concession=None, dropped=(), simple=False, limit=None, qty=1.0,
              status=None, oid=None):
    """A close record with the fields paper_options.send() writes for a v3 close (and to_rec() after Alpaca)."""
    rec = {"client_order_id": cid, "sent_et": "2026-10-20T14:31:00-04:00", "qty": int(qty),
           "natural": po.natural([{"symbol": s, "side": sd, "position_intent": f"{sd}_to_close"}
                                  for s, sd in sides.items()], quotes),
           "sides": dict(sides), "quotes": quotes, "id": oid or f"id-{cid}"}
    rec["limit_price"] = limit if limit is not None else f"{rec['natural']:.2f}"
    if concession is not None:
        rec.update(exec="v3", concession=concession, dropped_legs=list(dropped), all_sides=dict(sides))
    if simple:
        rec["order_class"] = "simple"
    if fill:
        rec.update(status="filled", filled_qty=qty, filled_at="2026-10-20T18:40:00.123456789Z",
                   legs_filled=[{"symbol": s, "side": sides[s], "qty": qty, "price": p} for s, p in fill.items()])
    else:
        rec.update(status=status or "canceled", filled_qty=0.0, filled_at=None,
                   legs_filled=[{"symbol": s, "side": sides[s], "qty": 0.0, "price": None} for s in sides],
                   cancel_requested="2026-10-20T14:33:05-04:00")
    return rec


C515, P515, C595, P435 = "NOC261120C00515000", "NOC261120P00515000", "NOC261120C00595000", "NOC261120P00435000"


def noc_round_trip():
    """NOC-F (real v3 open, filled at attempt 0) closed on the third attempt at the 10% step; the 595 call wing has a
    zero bid and is dropped (v3 §1)."""
    t = real("PX-F", "seasonA-NOC-2026-10-20-F")
    sides = {C515: "buy", P515: "buy", P435: "sell"}
    q = {C515: {"bid": 10.0, "ask": 11.0, "t": "x"}, P515: {"bid": 12.0, "ask": 13.0, "t": "x"},
         P435: {"bid": 0.10, "ask": 0.30, "t": "x"}}
    dropped = [{"symbol": C595, "bid": 0, "ask": 0.05}]
    k = "seasonA-NOC-2026-10-20-F"
    t["orders"]["close"] = [
        close_rec(f"{k}-close", sides, q, concession=0.0, dropped=dropped),
        close_rec(f"{k}-close-r1", sides, q, concession=0.05, dropped=dropped),
        close_rec(f"{k}-close-r2", sides, q, concession=0.10, dropped=dropped, limit="26.29",
                  fill={C515: 11.2, P515: 13.1, P435: 0.10})]
    t["exit_first_sent_et"], t["exit_late"] = "2026-10-20T14:31:00-04:00", False
    po.settle(t)
    return t


# ---------------------------------------------------------------- prices
def test_leg_prices_follow_the_frozen_natural():
    q = {"bid": 1.0, "ask": 1.4}
    assert v2.leg_price(q, "buy", "natural") == 1.4 and v2.leg_price(q, "sell", "natural") == 1.0
    assert v2.leg_price(q, "buy", "mid") == pytest.approx(1.2)
    assert v2.leg_price(q, "buy", "halfway") == pytest.approx(1.3)
    assert v2.leg_price(q, "sell", "halfway") == pytest.approx(1.1)
    assert v2.leg_price({"bid": 0, "ask": 0.05}, "sell", "natural") == 0      # a sold zero-bid leg: 0, as natural()
    assert v2.leg_price({"bid": None, "ask": 1}, "buy", "mid") is None          # missing is never priced
    assert v2.leg_price({"bid": 1, "ask": 0}, "buy", "natural") is None
    assert v2.leg_price({"bid": 2, "ask": 1}, "buy", "mid") is None              # crossed
    assert v2.leg_price(None, "buy", "mid") is None


def test_every_recorded_natural_recomputes_exactly():
    """The far-side price is the frozen code's own natural on every real order record (both ledgers)."""
    n = 0
    for a in ("PX-F", "PX-L"):
        for t in FX[a]["trades"].values():
            for w in ("open", "close"):
                for r in v2.recs(t, w):
                    assert v2.order_price(r, "natural") == pytest.approx(r["natural"], abs=1e-9)
                    n += 1
    assert n == 36


def test_real_open_execution_noc():
    r = FX["PX-F"]["trades"]["seasonA-NOC-2026-10-20-F"]["orders"]["open"][0]
    e = v2.order_execution(r, "open")
    assert e["fill_net"] == pytest.approx(-30.7)            # sold 18.50 + 18.50, bought 3.00 + 3.30
    assert e["mid"] == pytest.approx(-36.345) and e["natural"] == pytest.approx(-30.14)
    assert e["fill_minus_natural (+ = worse)"] == pytest.approx(-0.56)   # 56 cents better than the far side
    assert e["share_of_half_spread_paid"] == pytest.approx(5.645 / 6.205)
    assert not e.get("natural_mismatch")


def test_v3_round_trip_at_three_prices():
    t = noc_round_trip()
    assert t["result"]["simulated_legs"] == [] and t["result"]["close_net"] == pytest.approx(24.2)
    p = v2.three_prices(t)
    assert p["fill"]["unit"] == pytest.approx(6.5)
    # open: mid -36.345, halfway -33.2425, natural -30.14; close (3 legs, the dropped wing at 0): 22.80 / 23.35 / 23.90
    assert p["mid"]["unit"] == pytest.approx(36.345 - 22.80)
    assert p["halfway"]["unit"] == pytest.approx(33.2425 - 23.35)
    assert p["natural"]["unit"] == pytest.approx(30.14 - 23.90)
    assert p["halfway"]["unit"] == pytest.approx((p["mid"]["unit"] + p["natural"]["unit"]) / 2)
    assert p["natural"]["pnl_on_spot"] == pytest.approx(6.24 / NOC_SPOT)
    assert p["mid"]["pnl_usd"] == pytest.approx(round(13.545 * 100, 2))
    assert p["dropped_legs"] == {"symbols": [C595], "mid_at_close_left_out": pytest.approx(-0.025)}
    assert "missing_why" not in p


def test_v3_close_fill_rate_and_execution():
    t = noc_round_trip()
    c = v2.close_outcome(v2.orders_view(t), NOW)
    assert c["outcome"] == "filled at 10%" and c["attempt_at_fill"] == 2 and c["attempts_sent"] == 3
    counts = v2.close_counts([c])
    assert counts["10%"] == 1 and sum(counts.values()) == 1
    e = v2.order_execution(t["orders"]["close"][2], "close")
    assert e["limit"] == pytest.approx(26.29) and e["fill_minus_limit (+ = worse)"] == pytest.approx(-2.09)
    assert e["share_of_half_spread_paid"] == pytest.approx(1.4 / 1.1)    # 24.20 against mid 22.80, natural 23.90


def test_simulated_entry_prices_only_at_the_natural():
    """The long NOC open failed for a platform reason (real record). Its close is simulated at the natural of the run,
    which records no quotes: mid and halfway are missing, never invented."""
    t = real("PX-L", "seasonA-NOC-2026-10-20-L")
    t["close_sim"] = {"net": -35.0, "at": "2026-10-20T14:31:00-04:00",
                      "why": "no real position (the entry was simulated); natural at this run"}
    po.settle(t)
    assert t["result"]["simulated_legs"] == ["close", "open"]
    p = v2.three_prices(t)
    assert p["natural"]["unit"] == pytest.approx(p["fill"]["unit"]) == pytest.approx(-(42.57 - 35.0))
    assert p["mid"] is None and p["halfway"] is None
    assert p["missing_why"] == ["halfway: the simulated close recorded only its natural",
                                "mid: the simulated close recorded only its natural"]
    assert v2.close_outcome(v2.orders_view(t), NOW)["outcome"] == "no real position (close simulated)"


def test_held_past_expiry_closes_at_intrinsic_at_every_price():
    t = real("PX-F", "seasonA-DPZ-2026-10-13-F")
    t["flag"] = "held_past_expiry - see the account's exercise and assignment activity"
    t["close_sim"] = {"net": po.fly_payoff(303.09, 310.0, 260.0, 360.0), "at": "2026-10-19T10:40:00-04:00",
                      "why": "held past expiry; settled at intrinsic on the expiry close 303.09"}
    po.settle(t)
    assert t["result"]["simulated_legs"] == ["close"]
    p = v2.three_prices(t)
    for lv in v2.LEVELS:
        assert p[lv]["close"] == pytest.approx(6.91)
    assert p["mid"]["unit"] == pytest.approx(20.18 - 6.91)
    assert p["natural"]["unit"] == pytest.approx(17.56 - 6.91)
    assert p["fill"]["unit"] == pytest.approx(17.60 - 6.91)
    assert v2.close_outcome(v2.orders_view(t), NOW)["outcome"] == "unfilled by expiry (v1)"


def test_partial_fills_are_quantity_weighted():
    t = real("PX-L", "seasonA-RTX-2026-10-20-L")
    o = t["orders"]["open"][0]
    t["n"], o["filled_qty"] = 2, 2.0
    for lg in o["legs_filled"]:
        lg["qty"] = 2.0
    call, put = sorted(o["sides"])
    sides = {call: "sell", put: "sell"}
    q1 = {call: {"bid": 6.0, "ask": 6.4}, put: {"bid": 4.0, "ask": 4.4}}
    q2 = {call: {"bid": 7.0, "ask": 7.4}, put: {"bid": 5.0, "ask": 5.4}}
    k = t["key"]
    t["orders"]["close"] = [close_rec(f"{k}-close", sides, q1, concession=0.0, fill={call: 6.0, put: 4.0}),
                            close_rec(f"{k}-close-r1", sides, q2, concession=0.0, fill={call: 7.0, put: 5.0})]
    po.settle(t)
    p = v2.three_prices(t)
    assert p["natural"]["close"] == pytest.approx(-(10.0 + 12.0) / 2)
    assert p["mid"]["close"] == pytest.approx(-(10.4 + 12.4) / 2)
    assert p["fill"]["close"] == pytest.approx(-11.0)
    assert p["mid"]["pnl_usd"] == pytest.approx(round(p["mid"]["unit"] * 100 * 2, 2))


def test_one_leg_simple_close_restores_the_credit_sign():
    """A long straddle whose call has no bid: the put goes alone as a simple order, its limit_price positive."""
    t = real("PX-L", "seasonA-RTX-2026-10-20-L")
    call, put = sorted(t["orders"]["open"][0]["sides"])
    q = {put: {"bid": 4.5, "ask": 4.9}}
    rec = close_rec(f"{t['key']}-close", {put: "sell"}, q, concession=0.0, dropped=[{"symbol": call, "bid": 0,
                                                                                       "ask": 0.05}],
                    simple=True, limit="4.50", fill={put: 4.6})
    t["orders"]["close"] = [rec]
    assert v2.recheck.limit_net(rec) == -4.50
    e = v2.order_execution(rec, "close")
    assert e["fill_net"] == pytest.approx(-4.6) and e["fill_minus_limit (+ = worse)"] == pytest.approx(-0.1)
    po.settle(t)
    p = v2.three_prices(t)
    assert p["natural"]["close"] == pytest.approx(-4.5) and p["mid"]["close"] == pytest.approx(-4.7)


# ---------------------------------------------------------------- fill rate and the trigger
def test_fill_rate_on_the_real_ledgers():
    r = v2.build(ledgers(), {}, "seasonA", NOW, lambda s, c: None)
    f, lg = r["PX-F"]["by_subset"], r["PX-L"]["by_subset"]
    assert f["all"]["fill_rate"]["opens"]["filled_attempt_0"] == 4
    assert f["v3_only"]["fill_rate"]["opens"]["filled_attempt_0"] == 3
    assert f["without_DPZ"]["trades"] == 3 and f["all"]["trades"] == 4
    assert lg["all"]["fill_rate"]["opens"] == {"trades_with_an_open_order": 3, "filled_attempt_0": 2,
                                               "filled_attempt_1": 0, "filled_other_attempt": 0,
                                               "open_failed: platform": 1, "open_failed: other": 0, "pending": 0}
    assert f["all"]["fill_rate"]["closes"]["v1: unfilled by expiry"] == 1     # DPZ, 28 closes, none filled
    assert f["v3_only"]["fill_rate"]["closes"]["pending"] == 3
    dpz = next(x for x in r["PX-F"]["per_trade"] if x["key"] == v2.DPZ)
    assert dpz["close"]["attempts_sent"] == 28 and dpz["exec"] == "v1"
    noc_l = next(x for x in r["PX-L"]["per_trade"] if x["key"] == "seasonA-NOC-2026-10-20-L")
    assert [a["minutes_live"] for a in noc_l["open"]["attempts"]] == [16.4, 45.8]
    g = r["PX-L"]["open_fill_trigger_v1"]
    assert g["counted"] == 3 and g["counts"]["open_failed: platform"] == 1 and g["state"] == "open: 3 of 6 decided"
    assert [x["key"] for x in g["trades"]] == ["seasonA-NOC-2026-10-20-L", "seasonA-RTX-2026-10-20-L",
                                               "seasonA-VICR-2026-10-20-L"]          # same send time: by key
    assert r["PX-F"]["open_fill_trigger_v1"]["counts"]["filled_attempt_0"] == 3      # DPZ predates 10-16


def test_dpz_close_is_pending_before_expiry():
    t = real("PX-F", "seasonA-DPZ-2026-10-13-F")
    assert v2.close_outcome(v2.orders_view(t), datetime.datetime(2026, 10, 16, 12, 0, tzinfo=ET))["outcome"] == \
        "pending: closing"


def opened(key, sent, outcome, snap="2026-10-19"):
    t = real("PX-L", "seasonA-RTX-2026-10-20-L")
    t["key"], t["snapshot_session"] = key, snap
    o = t["orders"]["open"]
    o[0]["client_order_id"], o[0]["sent_et"] = f"{key}-open", sent
    if outcome == "a1":
        o[0].update(status="canceled", filled_qty=0.0, filled_at=None)
        o.append(dict(copy.deepcopy(o[0]), client_order_id=f"{key}-open-r1", status="filled", filled_qty=1.0,
                      id=f"{key}-r1"))
    elif outcome in ("platform", "pending"):
        o[0].update(status="canceled" if outcome == "platform" else "new", filled_qty=0.0, filled_at=None)
        if outcome == "platform":
            t["open_failed"] = "platform"
    elif outcome == "rejected":
        o[0].update(status="rejected", reject_kind="rejected_code", filled_qty=0.0, id=None)
        t["open_failed"] = "rejected_code"
    return t


def test_trigger_fires_at_two_platform_failures_in_the_first_six():
    ts = [opened("k1", "2026-10-19T14:33:00-04:00", "a0"), opened("k2", "2026-10-19T14:33:00-04:00", "platform"),
          opened("k3", "2026-10-19T14:40:00-04:00", "pending"), opened("k4", "2026-10-20T14:33:00-04:00", "platform"),
          opened("k0", "2026-10-15T14:33:00-04:00", "platform", snap="2026-10-15")]     # before 10-16: not counted
    g = v2.open_fill_trigger([v2.orders_view(t) for t in ts])
    assert g["counted"] == 4 and g["counts"]["open_failed: platform"] == 2 and g["state"].startswith("FIRED")


def test_trigger_not_fired_once_six_are_decided():
    ts = [opened(f"k{i}", f"2026-10-2{i}T14:33:00-04:00", o)
          for i, o in enumerate(["a0", "a1", "platform", "rejected", "a0", "a0", "platform"])]   # the 7th is outside
    held = real("PX-L", "seasonA-RTX-2026-10-20-L")
    held.update(key="held", orders={}, open_failed="held_by_cap")                    # no order sent: not counted
    g = v2.open_fill_trigger([v2.orders_view(t) for t in ts + [held]])
    assert g["counted"] == 6
    assert g["counts"] == {"filled_attempt_0": 3, "filled_attempt_1": 1, "open_failed: platform": 1,
                           "other (counted, never triggers)": 1, "pending": 0}
    assert g["state"].startswith("not fired")


def test_trigger_orders_by_utc_across_the_dst_change():
    a = opened("b-later", "2026-11-02T09:31:00-05:00", "a0")      # 14:31 UTC
    b = opened("a-earlier", "2026-11-02T10:30:00-04:00", "a0")    # 14:30 UTC (an offset typed as EDT)
    g = v2.open_fill_trigger([v2.orders_view(a), v2.orders_view(b)])
    assert [x["key"] for x in g["trades"]] == ["a-earlier", "b-later"]


def test_trigger_tie_at_the_cut_goes_by_ledger_order_and_shows_the_range():
    """Five trades from one run (one send time) after two earlier ones: places 3-6 come from the tie in the order the
    frozen sync() sent them, i.e. their ledger order, not their tickers."""
    early = [opened("e1", "2026-10-19T14:33:00-04:00", "a0"), opened("e2", "2026-10-19T14:33:00-04:00", "a0")]
    run = [opened(k, "2026-10-20T14:33:00-04:00", o) for k, o in
           (("z-first", "platform"), ("y", "a0"), ("x", "platform"), ("w", "a0"), ("a-last", "a0"))]
    views = [v2.orders_view(t, i) for i, t in enumerate(early + run)]
    g = v2.open_fill_trigger(views)
    assert [x["key"] for x in g["trades"]] == ["e1", "e2", "z-first", "y", "x", "w"]
    assert g["counts"]["open_failed: platform"] == 2 and g["state"].startswith("FIRED")
    assert g["tie_at_cut"] and g["platform_failures_range"] == [1, 2]
    assert "another choice gives 1-2" in g["state"]
    assert g["trades"][2]["attempts"][0]["status"] == "canceled"


def test_trigger_says_when_a_tied_trade_is_still_pending():
    early = [opened(f"e{i}", "2026-10-19T14:33:00-04:00", o) for i, o in enumerate(["a0", "a0", "platform", "a0"])]
    run = [opened(k, "2026-10-20T14:33:00-04:00", o) for k, o in (("p", "a0"), ("q", "a0"), ("r", "pending"))]
    g = v2.open_fill_trigger([v2.orders_view(t, i) for i, t in enumerate(early + run)])
    assert g["counted"] == 6 and g["state"].startswith("not fired") and g["pending_in_tie"] == 1
    assert g["platform_failures_range"] == [1, 1] and "1 trade(s) tied at the cut still pending" in g["state"]


def test_trigger_counts_trades_that_sent_no_order_apart():
    held = real("PX-L", "seasonA-RTX-2026-10-20-L")
    held.update(key="held", snapshot_session="2026-10-19", orders={}, open_failed="held_by_cap")
    g = v2.open_fill_trigger([v2.orders_view(held)])
    assert g["counted"] == 0 and g["not_in_population (sent no opening order)"] == {"held_by_cap": 1}


def test_fill_rate_never_reads_result_or_fill_prices():
    """Change every result and every fill price: the fill-rate views and the trigger do not move."""
    led = ledgers(("PX-F", noc_round_trip()))
    a = v2.build(copy.deepcopy(led), {}, "seasonA", NOW, lambda s, c: None)
    for acct in ("PX-F", "PX-L"):
        for t in led[acct]["trades"].values():
            if "result" in t:
                t["result"] = {k: (v * 3 + 7 if isinstance(v, float) else v) for k, v in t["result"].items()}
            for w in ("open", "close"):
                for r in v2.recs(t, w):
                    for lg in r.get("legs_filled") or []:
                        lg["price"] = None if lg["price"] is None else lg["price"] + 5
    b = v2.build(led, {}, "seasonA", NOW, lambda s, c: None)
    for acct in ("PX-F", "PX-L"):
        assert a[acct]["open_fill_trigger_v1"] == b[acct]["open_fill_trigger_v1"]
        for name in v2.SUBSETS:
            assert a[acct]["by_subset"][name]["fill_rate"] == b[acct]["by_subset"][name]["fill_rate"]
    assert "result" not in v2.orders_view(noc_round_trip())


def test_every_real_close_lands_in_one_bucket():
    t = noc_round_trip()
    t["orders"]["close"][2].pop("concession")                      # a fill whose step was not recorded
    rows = [v2.close_outcome(v2.orders_view(x), NOW) for x in
            (t, noc_round_trip(), real("PX-F", "seasonA-DPZ-2026-10-13-F"), real("PX-F", "seasonA-RTX-2026-10-20-F"),
             real("PX-L", "seasonA-NOC-2026-10-20-L"))]
    c = v2.close_counts(rows)
    assert c["filled, step unknown"] == 1 and c["10%"] == 1 and c["v1: unfilled by expiry"] == 1 and c["pending"] == 1
    assert sum(c.values()) == sum(1 for r in rows if r["real"]) == 4


def test_close_attempt_numbers_survive_a_refused_record():
    t = noc_round_trip()
    c = t["orders"]["close"]
    c[1].update(id=None, status="rejected", reject_kind="rejected_code")     # r1 refused: no Alpaca id
    c[2]["concession"] = 0.05                                                  # so r2 was the 2nd order sent
    o = v2.close_outcome(v2.orders_view(t), NOW)
    assert o["attempt_at_fill"] == 2 and o["sent_before_fill"] == 1 and o["outcome"] == "filled at 5%"


# ---------------------------------------------------------------- subsets and the whole report
def test_subsets_and_pnl_blocks():
    dpz = real("PX-F", "seasonA-DPZ-2026-10-13-F")
    dpz["close_sim"] = {"net": 6.91, "at": "x", "why": "held past expiry; settled at intrinsic on the expiry close"}
    po.settle(dpz)
    led = ledgers(("PX-F", noc_round_trip()))
    led["PX-F"]["trades"][v2.DPZ] = dpz
    r = v2.build(led, {("NOC", "2026-10-20"): 0.01}, "seasonA", NOW, lambda s, c: None)
    b = r["PX-F"]["by_subset"]
    sim = "all_with_result (simulated legs labelled)"
    assert b["all"]["pnl"]["real"]["all"]["common_set"]["fill"]["n"] == 1          # DPZ's close is simulated
    assert b["all"]["pnl"][sim]["all"]["common_set"]["mid"]["n"] == 2
    assert b["v3_only"]["pnl"][sim]["all"]["common_set"]["mid"]["n"] == 1
    assert b["without_DPZ"]["pnl"][sim]["all"]["each_price"]["natural"]["n"] == 1
    m = b["all"]["pnl"]["real"]["all"]["common_set"]["mid"]
    assert m["mean_pnl_on_spot"] == pytest.approx(13.545 / NOC_SPOT) and m["status"] == "insufficient"
    assert b["all"]["pnl"][sim]["splits"]["by_session"]["BMO"]["common_set"]["fill"]["n"] == 2
    assert b["all"]["pnl"]["real"]["splits"]["by_gate_status"]["other"]["common_set"]["natural"]["n"] == 1
    pair = b["all"]["pnl"]["real"]["paired_with_SH_X"]["all"]["natural"]
    assert pair["mean_paper_minus_SH_X"] == pytest.approx(6.24 / NOC_SPOT - 0.01)
    assert b["all"]["execution"]["close"]["orders"] == 1 and b["all"]["execution"]["open"]["orders"] == 4
    assert r["PX-L_and_PX-F_paired"]["all"]["all"]["fill"]["n"] == 0


def test_common_set_keeps_the_columns_comparable():
    """A simulated-entry trade has no mid: it leaves the common set, stays in each_price at fill and natural."""
    noc_l = real("PX-L", "seasonA-NOC-2026-10-20-L")
    noc_l["close_sim"] = {"net": -35.0, "at": "x", "why": "no real position (the entry was simulated)"}
    po.settle(noc_l)
    r = v2.build(ledgers(("PX-L", noc_l)), {}, "seasonA", NOW, lambda s, c: None)
    blk = r["PX-L"]["by_subset"]["all"]["pnl"]["all_with_result (simulated legs labelled)"]["all"]
    assert blk["not_priced_at_all_four"] == 1 and blk["common_set"]["fill"]["n"] == 0
    assert blk["each_price"]["fill"]["n"] == 1 and blk["each_price"]["mid"]["n"] == 0
    assert blk["each_price"]["mid"]["missing"] == 1


def test_px_f_and_px_l_paired_at_every_price():
    """RTX on both accounts as real round trips: the pairing is computed at each price, like the frozen both_sides."""
    f = real("PX-F", "seasonA-RTX-2026-10-20-F")
    sides_f = {s: ("buy" if sd == "sell" else "sell") for s, sd in f["orders"]["open"][0]["sides"].items()}
    qf = {s: {"bid": 1.0, "ask": 1.2} for s in sides_f}
    f["orders"]["close"] = [close_rec(f"{f['key']}-close", sides_f, qf, concession=0.0,
                                      fill={s: (1.2 if sd == "buy" else 1.0) for s, sd in sides_f.items()})]
    lg = real("PX-L", "seasonA-RTX-2026-10-20-L")
    sides_l = {s: "sell" for s in lg["orders"]["open"][0]["sides"]}
    ql = {s: {"bid": 5.0, "ask": 5.4} for s in sides_l}
    lg["orders"]["close"] = [close_rec(f"{lg['key']}-close", sides_l, ql, concession=0.0,
                                       fill={s: 5.0 for s in sides_l})]
    po.settle(f)
    po.settle(lg)
    r = v2.build(ledgers(("PX-F", f), ("PX-L", lg)), {}, "seasonA", NOW, lambda s, c: None)
    p = r["PX-L_and_PX-F_paired"]["v3_only"]["all"]
    pf, pl = v2.three_prices(f), v2.three_prices(lg)
    for price in v2.PRICES:
        assert p[price]["n"] == 1
        assert p[price]["mean_sum"] == pytest.approx(pf[price]["pnl_on_spot"] + pl[price]["pnl_on_spot"])
    assert p["fill"]["mean_sum"] == pytest.approx((f["result"]["pnl_per_unit"] + lg["result"]["pnl_per_unit"])
                                                  / f["spot_at_gate"])


def test_markdown_is_ascii_and_complete():
    md = v2.markdown(v2.build(ledgers(("PX-F", noc_round_trip())), {}, "seasonA", NOW, lambda s, c: None))
    md.encode("ascii")
    for s in ("## 1. Fill rate", "Open-fill trigger v1", "## 2. P&L", "### Paired", "## 3. Execution",
              "## 4. Orders against real", "## 5. Per trade", "filled at 10%", "without_DPZ", "v3_only", "PX-F + PX-L"):
        assert s in md


def test_report_joins_cached_prints():
    cache = {"seasonA-NOC-2026-10-20-F-open": {"legs": {
        C515: {"bars": [], "trades": [{"t": "2026-10-16T18:33:20.5Z", "p": 18.9, "s": 1, "x": "C", "c": "a"}]},
        P515: {"bars": [], "trades": [{"t": "2026-10-16T18:33:10.383385407Z", "p": 18.4, "s": 1, "x": "C", "c": "a"}]}}}}
    led = ledgers()
    led["PX-L"]["trades"]["seasonA-VICR-2026-10-20-L"]["orders"]["open"][0]["filled_at"] = None
    r = v2.build(led, {}, "seasonA", NOW, lambda s, c: cache.get(c))
    rows = [x for x in r["PX-F"]["real_prints_orders"] if x["fetched"]]
    assert len(rows) == 1 and rows[0]["legs"][C515]["worse_by_vs_nearest_trade"] == pytest.approx(0.4)
    assert rows[0]["legs"][P515]["nearest_trade_dt_s"] == 0.0
    assert rows[0]["legs"][C595]["missing"] == "not fetched" and rows[0]["net_at_nearest_trades"] is None
    s = r["PX-F"]["by_subset"]["all"]["real_prints"]
    assert s["filled_orders"] == 4 and s["filled_fetched"] == 1 and s["unfilled_orders"] == 28
    assert s["legs_with_a_trade_within_60s"] == 2                 # a print at 0.0 s counts (review finding 2)
    assert s["mean_leg_worse_by_vs_trade_within_60s"] == pytest.approx((0.4 - 0.1) / 2)
    sl = r["PX-L"]["by_subset"]["all"]["real_prints"]
    assert sl["filled_fill_time_unknown"] == 1 and sl["filled_orders"] == 1
    e = next(x for x in r["PX-F"]["execution_orders"] if x["client_order_id"] == v2.DPZ + "-open")
    assert e["minutes_send_to_fill (the quotes are from the send)"] == pytest.approx(31.9)


# ---------------------------------------------------------------- registration
def sha(path):
    return hashlib.sha256(open(os.path.join(REPO, path), "rb").read().replace(b"\r\n", b"\n")).hexdigest()


def hash_lines(name):
    out = []
    for line in open(os.path.join(REPO, "registry", name), encoding="utf-8"):
        if line.strip() and not line.startswith("#"):
            digest, path = line.split(maxsplit=1)
            out.append((digest, path.strip().lstrip("*")))
    return out


def test_the_frozen_report_is_untouched():
    lines = hash_lines("D011_implementation_v3.sha256")
    assert len(lines) == 2
    for digest, path in lines:
        assert sha(path) == digest, path


def test_the_views_match_their_registration():
    """Every line must hold (the workflow checks the same list with sha256sum -c): a change is a new list."""
    lines = hash_lines("D011_report_views_implementation_v1.sha256")
    assert len(lines) == 7
    for digest, path in lines:
        assert sha(path) == digest, path
