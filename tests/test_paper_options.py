"""D011 paper options: the iron butterfly's legs, prices, wings, and one full open -> close cycle against a fake
Alpaca (no network). Run: python -m pytest tests/test_paper_options.py -q"""
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
import paper_options as po  # noqa: E402
from common import ET  # noqa: E402

CH = {float(k): {"call": f"XYZ261016C{k * 1000:08d}", "put": f"XYZ261016P{k * 1000:08d}"} for k in range(80, 121, 5)}
Q = {}
for k, v in CH.items():
    Q[v["call"]] = {"bid": max(0.05, 100 - k + 4.0) - 0.1, "ask": max(0.05, 100 - k + 4.0) + 0.1, "t": "x"}
    Q[v["put"]] = {"bid": max(0.05, k - 100 + 4.0) - 0.1, "ask": max(0.05, k - 100 + 4.0) + 0.1, "t": "x"}


def test_wings_two_straddle_prices_out():
    assert po.pick_wings(CH, 100.0, 8.0) == (80.0, 120.0)   # +-16 -> the first listed strikes beyond
    assert po.pick_wings(CH, 100.0, 4.0) == (90.0, 110.0)   # +-8
    assert po.pick_wings(CH, 100.0, 15.0) is None            # +-30 is off the chain


def test_open_legs_natural_and_limit():
    legs = po.legs_for("F", CH, 100.0, (90.0, 110.0), True)
    assert [(lg["side"], lg["position_intent"]) for lg in legs] == [
        ("sell", "sell_to_open"), ("sell", "sell_to_open"), ("buy", "buy_to_open"), ("buy", "buy_to_open")]
    net = po.natural(legs, Q)
    # sell 4.0-0.1 twice, buy the 110 call and 90 put (intrinsic 0, so 0.05 floor... 4-10 -> 0.05) at ask
    assert round(net, 4) == round(-(3.9 + 3.9) + (0.05 + 0.1) * 2, 4)
    assert po.limit_of(net) < 0                    # a credit is a negative limit
    assert po.limit_of(net) == -po.cents_down(-net)
    close = po.close_legs({"legs": legs})
    assert [(lg["side"], lg["position_intent"]) for lg in close] == [
        ("buy", "buy_to_close"), ("buy", "buy_to_close"), ("sell", "sell_to_close"), ("sell", "sell_to_close")]


def test_natural_refuses_a_sold_leg_without_a_bid():
    legs = po.legs_for("F", CH, 100.0, (90.0, 110.0), True)
    q = dict(Q)
    q[CH[100.0]["call"]] = {"bid": 0, "ask": 0.1}
    assert po.natural(legs, q) is None


class FakeAlpaca:
    """Accepts mleg orders, fills them on the next status read at their natural, and keeps a clock."""

    def __init__(self):
        self.orders, self.open = {}, True

    def api(self, method, path, **kw):
        if path == "/clock":
            return {"is_open": self.open}
        if path == "/account":
            return {"equity": "100000"}
        if method == "POST" and path == "/orders":
            b = kw["json"]
            oid = f"o{len(self.orders)}"
            self.orders[oid] = {"id": oid, "status": "accepted", "body": b}
            return {"id": oid, "status": "accepted"}
        if method == "GET" and path.startswith("/orders/"):
            o = self.orders[path.split("/")[-1]]
            o["status"] = "filled"
            return {"status": "filled", "filled_at": "t", "legs": [
                {"symbol": lg["symbol"], "side": lg["side"], "filled_qty": o["body"]["qty"],
                 "filled_avg_price": str(Q[lg["symbol"]]["ask" if lg["side"] == "buy" else "bid"])}
                for lg in o["body"]["legs"]]}
        if method == "DELETE":
            return {}
        raise AssertionError(path)


def gate(snapshot, reaction, expiry):
    return {"ticker": "XYZ", "report_date": reaction, "session": "AMC", "snapshot_session": snapshot,
            "captured_et": f"{snapshot}T14:31:00-04:00", "dry": False, "status": "PASS",
            "timing": {"reaction_day": reaction},
            "options": {"spot": 100.0, "expiry": expiry, "strike": 100.0,
                        "call": {"bid": 3.9, "ask": 4.1}, "put": {"bid": 3.9, "ask": 4.1}}}


def run_at(fake, monkeypatch, tmp_path, when, gates):
    monkeypatch.setattr(po, "api", fake.api)
    monkeypatch.setattr(po, "chain", lambda t, e: CH)
    monkeypatch.setattr(po, "quotes", lambda syms: {s: Q[s] for s in syms})
    monkeypatch.setattr(po, "now_et", lambda: when)
    monkeypatch.setattr(po, "LEDGER", str(tmp_path / "ledger.json"))
    monkeypatch.setattr(po, "live_gates", lambda today: [("A", g) for g in gates if g["snapshot_session"] == today])
    po.sync(False)
    return json.load(open(tmp_path / "ledger.json"))


def test_full_cycle(monkeypatch, tmp_path):
    fake = FakeAlpaca()
    g = gate("2026-10-13", "2026-10-15", "2026-10-16")
    # snapshot session 15:00 ET: one butterfly opened
    led = run_at(fake, monkeypatch, tmp_path, datetime.datetime(2026, 10, 13, 15, 0, tzinfo=ET), [g])
    tr = led["trades"]["A-XYZ-2026-10-15-F"]
    assert tr["n"] == 1 and tr["wings"] == [80.0, 120.0]   # 100000*0.005/(100*8.0) = 0.625 -> floor 0 -> min 1
    assert len(fake.orders) == 1
    body = fake.orders["o0"]["body"]
    assert body["order_class"] == "mleg" and float(body["limit_price"]) < 0
    # the morning of the reaction session: filled, not yet due to close
    led = run_at(fake, monkeypatch, tmp_path, datetime.datetime(2026, 10, 15, 10, 0, tzinfo=ET), [g])
    assert led["trades"]["A-XYZ-2026-10-15-F"]["orders"]["open"][-1]["status"] == "filled"
    assert len(fake.orders) == 1
    # 14:35 ET on the reaction session: closed
    led = run_at(fake, monkeypatch, tmp_path, datetime.datetime(2026, 10, 15, 14, 35, tzinfo=ET), [g])
    assert len(fake.orders) == 2
    led = run_at(fake, monkeypatch, tmp_path, datetime.datetime(2026, 10, 15, 14, 50, tzinfo=ET), [g])
    r = led["trades"]["A-XYZ-2026-10-15-F"]["result"]
    # same quotes at entry and exit: the loss is exactly the four spreads paid (0.2 a leg)
    assert abs(r["pnl_per_unit"] - (-0.8)) < 1e-9
    assert r["simulated_legs"] == []
    assert abs(r["entry_vs_alpaca_natural"]) < 1e-9


def test_unfilled_entry_is_simulated_and_exit_too(monkeypatch, tmp_path):
    fake = FakeAlpaca()
    g = gate("2026-10-13", "2026-10-15", "2026-10-16")
    run_at(fake, monkeypatch, tmp_path, datetime.datetime(2026, 10, 13, 15, 0, tzinfo=ET), [g])
    fake.orders["o0"]["status"] = "expired"
    real_api = fake.api

    def expired_api(method, path, **kw):
        if method == "GET" and path.startswith("/orders/"):
            return {"status": "expired", "legs": []}
        return real_api(method, path, **kw)
    fake.api = expired_api
    led = run_at(fake, monkeypatch, tmp_path, datetime.datetime(2026, 10, 15, 14, 35, tzinfo=ET), [g])
    tr = led["trades"]["A-XYZ-2026-10-15-F"]
    assert tr["orders"]["close"][0]["status"] == "simulated"
    assert tr["result"]["simulated_legs"] == ["close", "open"]
    assert "entry_vs_alpaca_natural" not in tr["result"]       # never in the execution comparison


def test_nothing_sent_while_closed_or_after_cutoff(monkeypatch, tmp_path):
    fake = FakeAlpaca()
    g = gate("2026-10-13", "2026-10-15", "2026-10-16")
    fake.open = False
    run_at(fake, monkeypatch, tmp_path, datetime.datetime(2026, 10, 13, 15, 0, tzinfo=ET), [g])
    assert not fake.orders
    fake.open = True
    run_at(fake, monkeypatch, tmp_path, datetime.datetime(2026, 10, 13, 15, 56, tzinfo=ET), [g])
    assert not fake.orders


def test_expiry_before_reaction_is_skipped(monkeypatch, tmp_path):
    fake = FakeAlpaca()
    g = gate("2026-10-13", "2026-10-19", "2026-10-16")
    led = run_at(fake, monkeypatch, tmp_path, datetime.datetime(2026, 10, 13, 15, 0, tzinfo=ET), [g])
    assert led["trades"]["A-XYZ-2026-10-19-F"]["skipped"] == "expiry_before_reaction"
    assert not fake.orders
