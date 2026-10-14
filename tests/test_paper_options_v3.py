"""D011 v3 (registry/D011_paper_options_v3.md): the version gate, the close that drops no-bid long legs, the
concession walk, the 3-minute cancel with the resend on a later run, the expiry-day cut-off, and all-worthless
closes. The v1 paths are proven unchanged by tests/test_paper_options.py, which is not edited.
Run: python -m pytest tests/test_paper_options_v3.py -q"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
import paper_options as po  # noqa: E402
import test_paper_options as t1  # noqa: E402

KEY = "seasonA-XYZ-2026-10-19-F"


class Broker(t1.Broker):
    """v1's fake, plus simple (one-leg) orders."""

    def view(self, o):
        if "legs" in o["body"]:
            return super().view(o)
        sym, side = o["body"]["symbol"], o["body"]["side"]
        done = float(o.get("filled_qty") or 0)
        return {"id": o["id"], "status": o["status"], "filled_qty": o.get("filled_qty", "0"), "filled_at": "t",
                "symbol": sym, "filled_avg_price": str(t1.Q[sym]["ask" if side == "buy" else "bid"]) if done else None}


@pytest.fixture
def env(monkeypatch, tmp_path):
    b = Broker()
    state = {"gates": [t1.gate(snapshot="2026-10-15", reaction="2026-10-19", expiry="2026-10-23")]}
    monkeypatch.setattr(po, "call", b.call)
    monkeypatch.setattr(po, "chain", lambda t, e: t1.CH)
    monkeypatch.setattr(po, "quotes", lambda syms: {s: t1.Q[s] for s in syms})
    monkeypatch.setattr(po, "LEDGER", str(tmp_path / "ledger.json"))
    monkeypatch.setattr(po, "live_gates", lambda: [("seasonA", g, None, True) for g in state["gates"]])
    monkeypatch.setattr(po, "expiry_close", lambda t, e: 112.0)

    def run(when, **kw):
        monkeypatch.setattr(po, "now_et", lambda: when)
        po.sync(False, **kw)
        return json.load(open(tmp_path / "ledger.json"))
    return b, state, run


def opened(b, run):
    run(t1.at(15, 15, 0))
    led = run(t1.at(15, 15, 10))
    assert po.chain_state(led["trades"][KEY], "open")[0] == 1
    return led


def test_version_gate(env):
    b, state, run = env
    state["gates"].append(t1.gate())                                 # snapshot 2026-10-13: a v1 trade
    led = run(t1.at(13, 15, 0))
    assert "exec" not in led["trades"]["seasonA-XYZ-2026-10-15-F"]
    led = run(t1.at(15, 15, 0))
    assert led["trades"][KEY]["exec"] == "v3"


def test_close_drops_no_bid_long_legs_and_pays_the_first_concession(env):
    b, _, run = env
    opened(b, run)
    led = run(t1.at(19, 14, 35))
    rec = led["trades"][KEY]["orders"]["close"][0]
    body = b.by_cid[f"{KEY}-close"]["body"]
    assert [lg["side"] for lg in body["legs"]] == ["buy", "buy"]        # the two shorts only
    assert {d["symbol"] for d in rec["dropped_legs"]} == {t1.CH[120.0]["call"], t1.CH[80.0]["put"]}
    nat = 4.1 + 4.1
    assert abs(rec["natural"] - nat) < 1e-9 and rec["concession"] == 0.0     # attempt 0: the natural itself
    assert float(body["limit_price"]) == po.limit_of(nat)
    led = run(t1.at(19, 14, 38))                                       # filled on the next read
    r = led["trades"][KEY]["result"]
    open_net = -(3.9 + 3.9) + (0.15 + 0.15)                           # the fake fills wings at their 0.15 ask
    assert abs(r["pnl_per_unit"] - (-(open_net + nat))) < 1e-9 and r["simulated_legs"] == []


def test_two_minute_cancel_then_a_bigger_concession_on_a_later_run(env):
    b, _, run = env
    opened(b, run)
    b.fill_mode = "hold"
    run(t1.at(19, 14, 35))
    run(t1.at(19, 14, 36))
    assert b.orders["o1"]["status"] == "accepted"                     # 1 minute: left alone
    run(t1.at(19, 14, 37))
    assert b.orders["o1"]["status"] == "pending_cancel" and b.posts == 2   # cancel; no resend in the same run
    led = run(t1.at(19, 14, 39))
    recs = led["trades"][KEY]["orders"]["close"]
    assert b.posts == 3 and recs[1]["client_order_id"] == f"{KEY}-close-r1" and recs[1]["concession"] == 0.05
    assert float(b.by_cid[f"{KEY}-close-r1"]["body"]["limit_price"]) > float(b.by_cid[f"{KEY}-close"]["body"]["limit_price"])
    for m in range(41, 60, 2):
        run(t1.at(19, 14, m))
    cs = [r["concession"] for r in json.load(open(po.LEDGER))["trades"][KEY]["orders"]["close"]]
    assert max(cs) == 0.25 and cs == sorted(cs)                       # capped at 25%


def test_expiry_day_cutoff(env):
    b, state, run = env
    state["gates"][0] = t1.gate(snapshot="2026-10-15", reaction="2026-10-19", expiry="2026-10-19")
    opened(b, run)
    b.open = True
    led = run(t1.at(19, 15, 12))                                       # due, but past 15:10 on the expiry date
    assert b.posts == 1 and not led["trades"][KEY].get("orders", {}).get("close")


def tr_long(monkeypatch, q):
    legs = po.legs_for("L", t1.CH, 100.0, None, True)
    tr = {"key": "k", "exec": "v3", "legs": legs, "n": 1, "spot_at_gate": 100.0}
    sent = []
    monkeypatch.setattr(po, "lookup", lambda cid: None)
    monkeypatch.setattr(po, "quotes", lambda syms: {s: q[s] for s in syms if s in q})
    monkeypatch.setattr(po, "call", lambda m, p, **kw: (sent.append(kw["json"]) or 200,
                                                        {"id": "x", "status": "accepted", "filled_qty": "0"}))
    return tr, legs, sent


def test_missing_quote_is_never_worthless(monkeypatch):
    c, p = t1.CH[100.0]["call"], t1.CH[100.0]["put"]
    tr, legs, sent = tr_long(monkeypatch, {c: {"bid": 6.0, "ask": 6.2, "t": None}})     # the put's quote is missing
    assert po.send(tr, "close", po.close_legs(legs), 1, "k-close", t1.at(19, 14, 35)) is None
    assert sent == [] and "close_sim" not in tr and tr["not_sent"]


def test_one_leg_left_goes_as_a_simple_order(monkeypatch):
    c, p = t1.CH[100.0]["call"], t1.CH[100.0]["put"]
    tr, legs, sent = tr_long(monkeypatch, {c: {"bid": 6.0, "ask": 6.2, "t": None}, p: {"bid": 0, "ask": 0.05, "t": None}})
    rec = po.send(tr, "close", po.close_legs(legs), 1, "k-close", t1.at(19, 14, 35))
    body = sent[0]
    assert "legs" not in body and body["symbol"] == c and body["side"] == "sell" and body["limit_price"] == "6.00"
    assert rec["order_class"] == "simple" and rec["dropped_legs"][0]["symbol"] == p
    filled = po.to_rec({"id": "x", "status": "filled", "filled_qty": "1", "symbol": c, "filled_avg_price": "6.05"},
                       rec["all_sides"])
    assert filled["legs_filled"] == [{"symbol": c, "side": "sell", "qty": 1.0, "price": 6.05}]
    assert po.fill_net([filled]) == -6.05


def test_every_leg_zero_bid_sends_the_full_close(monkeypatch):
    c, p = t1.CH[100.0]["call"], t1.CH[100.0]["put"]
    tr, legs, sent = tr_long(monkeypatch, {c: {"bid": 0, "ask": 0.05, "t": None}, p: {"bid": 0, "ask": 0.05, "t": None}})
    po.send(tr, "close", po.close_legs(legs), 1, "k-close", t1.at(19, 14, 35))
    assert len(sent[0]["legs"]) == 2 and "close_sim" not in tr


def test_dropped_wing_value_at_expiry_is_recorded_and_alerts_when_in_the_money(env, monkeypatch):
    b, _, run = env
    opened(b, run)
    run(t1.at(19, 14, 35)); run(t1.at(19, 14, 37))                   # closed with both wings dropped
    monkeypatch.setattr(po, "expiry_close", lambda t, e: 125.0)       # the 120 call ends 5 in the money
    led = run(t1.at(26, 10, 0))
    tr = led["trades"][KEY]
    assert tr["dropped_at_expiry"]["intrinsic"][t1.CH[120.0]["call"]] == 5.0 and tr["dropped_itm"]
    assert KEY in led["alerts"] and tr["result"]["pnl_per_unit"] is not None   # the result itself is unchanged


def test_v1_trade_keeps_fifteen_minutes_and_all_legs(env):
    b, state, run = env
    state["gates"] = [t1.gate()]                                       # snapshot 2026-10-13: v1
    run(t1.at(13, 15, 0)); run(t1.at(13, 15, 10))
    b.fill_mode = "hold"
    run(t1.at(15, 14, 35))
    run(t1.at(15, 14, 40))
    body = b.by_cid["seasonA-XYZ-2026-10-15-F-close"]["body"]
    assert len(body["legs"]) == 4 and b.orders["o1"]["status"] == "accepted"   # not cancelled at 5 minutes
