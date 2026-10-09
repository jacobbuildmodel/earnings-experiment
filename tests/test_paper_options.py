"""D011 paper options against a fake Alpaca (no network): legs, prices, wings, and every order-state path the
pre-freeze review named (cancel racing a fill, a lost ledger, failed exits, duplicates, rejections, late gates).
Run: python -m pytest tests/test_paper_options.py -q"""
import datetime
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
import paper_options as po  # noqa: E402
from common import ET  # noqa: E402

CH = {float(k): {"call": f"XYZ261016C{k * 1000:08d}", "put": f"XYZ261016P{k * 1000:08d}"} for k in range(80, 121, 5)}
Q = {}
for _k, _v in CH.items():
    Q[_v["call"]] = {"bid": max(0.05, 100 - _k + 4.0) - 0.1, "ask": max(0.05, 100 - _k + 4.0) + 0.1, "t": "x"}
    Q[_v["put"]] = {"bid": max(0.05, _k - 100 + 4.0) - 0.1, "ask": max(0.05, _k - 100 + 4.0) + 0.1, "t": "x"}
KEY = "seasonA-XYZ-2026-10-15-F"


def at(day, hh, mm):
    return datetime.datetime(2026, 10, day, hh, mm, tzinfo=ET)


# ---------------------------------------------------------------- pure functions
def test_wings_two_straddle_prices_out():
    assert po.pick_wings(CH, 100.0, 8.0) == (80.0, 120.0)
    assert po.pick_wings(CH, 100.0, 4.0) == (90.0, 110.0)
    assert po.pick_wings(CH, 100.0, 15.0) is None


def test_legs_natural_limit():
    legs = po.legs_for("F", CH, 100.0, (90.0, 110.0), True)
    assert [(lg["side"], lg["position_intent"]) for lg in legs] == [
        ("sell", "sell_to_open"), ("sell", "sell_to_open"), ("buy", "buy_to_open"), ("buy", "buy_to_open")]
    net = po.natural(legs, Q)
    assert abs(net - (-(3.9 + 3.9) + 0.15 * 2)) < 1e-9
    assert po.limit_of(net) == -7.5
    assert po.limit_of(1.234) == 1.24 and po.limit_of(-1.239) == -1.23
    assert [(lg["side"], lg["position_intent"]) for lg in po.close_legs(legs)] == [
        ("buy", "buy_to_close"), ("buy", "buy_to_close"), ("sell", "sell_to_close"), ("sell", "sell_to_close")]
    q = dict(Q)
    q[CH[100.0]["call"]] = {"bid": 0, "ask": 0.1}
    assert po.natural(legs, q) is None


def test_fly_payoff():
    assert po.fly_payoff(100, 100, 90, 110) == 0
    assert po.fly_payoff(105, 100, 90, 110) == 5
    assert po.fly_payoff(130, 100, 90, 110) == 10      # capped by the wing
    assert po.fly_payoff(70, 100, 90, 110) == 10


# ---------------------------------------------------------------- the fake broker
class Broker:
    """Orders fill on the first status read unless told otherwise. DELETE is asynchronous: pending_cancel first."""

    def __init__(self):
        self.orders, self.by_cid, self.open = {}, {}, True
        self.fill_mode = "fill"        # fill | hold | expire
        self.reject = None             # (code, message) for the next POST
        self.quotes_down = False
        self.posts = 0

    def fill(self, o):
        o["status"] = "filled"
        o["filled_qty"] = o["body"]["qty"]

    def view(self, o):
        legs = [{"symbol": lg["symbol"], "side": lg["side"],
                 "filled_qty": o["filled_qty"] if o["status"] in ("filled", "canceled", "expired") else "0",
                 "filled_avg_price": str(Q[lg["symbol"]]["ask" if lg["side"] == "buy" else "bid"])
                 if float(o.get("filled_qty") or 0) else None} for lg in o["body"]["legs"]]
        return {"id": o["id"], "status": o["status"], "filled_qty": o.get("filled_qty", "0"), "filled_at": "t",
                "legs": legs}

    def call(self, method, path, **kw):
        if path == "/clock":
            return 200, {"is_open": self.open}
        if path == "/account":
            return 200, {"equity": "100000"}
        if path == "/orders:by_client_order_id":
            o = self.by_cid.get(kw["params"]["client_order_id"])
            return (200, self.view(o)) if o else (404, {"message": "not found"})
        if method == "POST" and path == "/orders":
            b = kw["json"]
            if b["client_order_id"] in self.by_cid:
                return 422, {"message": "client_order_id must be unique"}
            if self.reject:
                r, self.reject = self.reject, None
                return r[0], {"message": r[1]}
            self.posts += 1
            oid = f"o{len(self.orders)}"
            o = self.orders[oid] = self.by_cid[b["client_order_id"]] = {"id": oid, "status": "accepted",
                                                                         "body": b, "filled_qty": "0"}
            return 200, self.view(o)
        if method == "GET" and path.startswith("/orders/"):
            o = self.orders[path.split("/")[-1]]
            if o["status"] == "accepted":
                if self.fill_mode == "fill":
                    self.fill(o)
                elif self.fill_mode == "expire":
                    o["status"] = "expired"
            elif o["status"] == "pending_cancel":
                o["status"] = o.pop("after_cancel")
                if o["status"] == "filled":
                    o["filled_qty"] = o["body"]["qty"]
            return 200, self.view(o)
        if method == "DELETE":
            o = self.orders[path.split("/")[-1]]
            o["after_cancel"] = "canceled" if self.fill_mode != "race" else "filled"
            o["status"] = "pending_cancel"
            return 204, {}
        raise AssertionError(path)


def gate(snapshot="2026-10-13", reaction="2026-10-15", expiry="2026-10-16", ask=4.1):
    return {"ticker": "XYZ", "report_date": reaction, "session": "AMC", "snapshot_session": snapshot,
            "captured_et": f"{snapshot}T14:31:00-04:00", "dry": False, "status": "PASS",
            "timing": {"reaction_day": reaction},
            "options": {"spot": 100.0, "expiry": expiry, "strike": 100.0,
                        "call": {"bid": 3.9, "ask": ask}, "put": {"bid": 3.9, "ask": 4.1}}}


@pytest.fixture
def env(monkeypatch, tmp_path):
    b = Broker()
    state = {"gates": [gate()], "committed": True}

    def quotes(syms):
        if b.quotes_down:
            raise po.Transient("quotes: HTTP 503")
        return {s: Q[s] for s in syms}
    monkeypatch.setattr(po, "call", b.call)
    monkeypatch.setattr(po, "chain", lambda t, e: CH)
    monkeypatch.setattr(po, "quotes", quotes)
    monkeypatch.setattr(po, "LEDGER", str(tmp_path / "ledger.json"))
    monkeypatch.setattr(po, "live_gates", lambda: [("seasonA", g, None, state["committed"]) for g in state["gates"]])
    monkeypatch.setattr(po, "expiry_close", lambda t, e: 112.0)

    def run(when, **kw):
        monkeypatch.setattr(po, "now_et", lambda: when)
        rc = po.sync(False, **kw)
        return json.load(open(tmp_path / "ledger.json")), rc
    return b, state, run, tmp_path


# ---------------------------------------------------------------- paths
def test_full_cycle(env):
    b, _, run, _ = env
    led, _ = run(at(13, 15, 0))
    tr = led["trades"][KEY]
    assert tr["n"] == 1 and tr["wings"] == [80.0, 120.0] and b.posts == 1
    assert float(b.orders["o0"]["body"]["limit_price"]) < 0
    led, _ = run(at(13, 15, 10))                       # filled; sanity passes; convention verified
    assert led["convention_verified"]["trade"] == KEY and not led.get("halt")
    run(at(15, 10, 0))                                 # reaction morning: not yet due
    assert b.posts == 1
    led, _ = run(at(15, 14, 35))
    assert b.posts == 2 and led["trades"][KEY]["exit_late"] is False
    led, _ = run(at(15, 14, 45))
    r = led["trades"][KEY]["result"]
    assert abs(r["pnl_per_unit"] - (-0.8)) < 1e-9     # the same quotes both ways: exactly the four spreads
    assert r["simulated_legs"] == [] and abs(r["entry_vs_alpaca_natural"]) < 1e-9


def test_cancel_that_loses_the_race_never_doubles(env):
    b, _, run, _ = env
    b.fill_mode = "hold"
    run(at(13, 15, 0))
    run(at(13, 15, 16))                                # stale -> cancel requested; NO resend in the same run
    assert b.posts == 1 and b.orders["o0"]["status"] == "pending_cancel"
    b.fill_mode = "race"
    b.orders["o0"]["after_cancel"] = "filled"          # the cancel loses: the original fills
    led, _ = run(at(13, 15, 26))
    assert b.posts == 1                                # never resent
    assert po.chain_state(led["trades"][KEY], "open")[0] == 1


def test_cancel_then_resend_once(env):
    b, _, run, _ = env
    b.fill_mode = "hold"
    run(at(13, 15, 0))
    run(at(13, 15, 16))
    led, _ = run(at(13, 15, 26))                       # canceled -> resent as -open-r1
    assert b.posts == 2 and "seasonA-XYZ-2026-10-15-F-open-r1" in b.by_cid
    run(at(13, 15, 42)); run(at(13, 15, 52))
    assert b.posts == 2                                # at most two opening orders


def test_lost_ledger_adopts_the_existing_order(env):
    b, _, run, tmp = env
    run(at(13, 15, 0))
    os.remove(tmp / "ledger.json")                     # the push was lost
    led, _ = run(at(13, 15, 5))
    assert b.posts == 1
    assert led["trades"][KEY]["orders"]["open"][0].get("adopted") is True


def test_duplicate_id_refusal_is_adopted(env):
    b, _, run, _ = env
    b.by_cid["seasonA-XYZ-2026-10-15-F-open"] = {"id": "ox", "status": "filled", "filled_qty": "1",
                                                 "body": {"qty": "1", "legs": po.legs_for("F", CH, 100.0, (80.0, 120.0), True)}}
    b.orders["ox"] = b.by_cid["seasonA-XYZ-2026-10-15-F-open"]
    led, _ = run(at(13, 15, 0))
    rec = led["trades"][KEY]["orders"]["open"][0]
    assert rec["adopted"] and rec["status"] == "filled" and b.posts == 0


def test_failed_exit_retries_until_filled(env):
    b, _, run, _ = env
    run(at(13, 15, 0)); run(at(13, 15, 10))
    b.quotes_down = True
    led, _ = run(at(15, 14, 35))                       # quotes down: nothing sent, an error, no id consumed
    assert b.posts == 1 and led["errors_last_run"]
    b.quotes_down = False
    b.fill_mode = "expire"
    run(at(15, 14, 45))
    led, _ = run(at(15, 14, 55))                       # the close expired -> resent -close-r1
    assert b.posts == 3 and "seasonA-XYZ-2026-10-15-F-close-r1" in b.by_cid
    b.fill_mode = "fill"
    led, _ = run(at(16, 10, 0))
    led, _ = run(at(16, 10, 10))
    assert "result" in led["trades"][KEY] and led["trades"][KEY]["result"]["simulated_legs"] == []


def test_held_past_expiry_is_flagged_and_settled_at_intrinsic(env):
    b, _, run, _ = env
    run(at(13, 15, 0)); run(at(13, 15, 10))
    b.open = False                                     # every exit run finds the market closed
    run(at(15, 14, 35)); run(at(16, 15, 0))
    led, _ = run(at(19, 9, 0))
    tr = led["trades"][KEY]
    assert tr["flag"].startswith("held_past_expiry")
    assert tr["result"]["close_net"] == 12.0 and tr["result"]["simulated_legs"] == ["close"]


def test_unfilled_entry_is_simulated_and_kept_out_of_execution(env):
    b, _, run, _ = env
    b.fill_mode = "expire"
    run(at(13, 15, 0)); run(at(13, 15, 10))            # expired -> resent -r1 -> expires too
    led, _ = run(at(13, 15, 20))
    assert b.posts == 2
    led, _ = run(at(15, 14, 35))
    tr = led["trades"][KEY]
    assert tr["open_failed"] == "platform" and tr["result"]["simulated_legs"] == ["close", "open"]
    assert "entry_vs_alpaca_natural" not in tr["result"]


def test_capacity_and_code_rejections_are_not_simulated(env):
    b, state, run, _ = env
    b.reject = (403, "insufficient options buying power")
    led, rc = run(at(13, 15, 0))
    run(at(13, 15, 10))
    led, _ = run(at(15, 14, 35))
    assert led["trades"][KEY]["open_failed"] == "capacity" and "result" not in led["trades"][KEY]
    state["gates"] = [gate(reaction="2026-10-16", expiry="2026-10-16")]
    b.reject = (403, "account not eligible to trade uncovered option contracts")
    led, rc = run(at(13, 15, 30))
    k2 = "seasonA-XYZ-2026-10-16-F"
    led, rc = run(at(13, 15, 40))
    assert led["trades"][k2]["open_failed"] == "rejected_code" and rc == 1 and k2 in led["alerts"]


def test_closed_market_cutoff_and_uncommitted_gate(env):
    b, state, run, _ = env
    b.open = False
    run(at(13, 15, 0))
    assert b.posts == 0
    b.open = True
    state["committed"] = False
    run(at(13, 15, 10))
    assert b.posts == 0
    state["committed"] = True
    led, _ = run(at(13, 15, 56))                       # first seen after the cutoff
    assert b.posts == 0 and led["trades"][KEY]["skipped"] == "missed_entry_window"


def test_gate_without_ask_is_recorded(env, monkeypatch):
    b, state, run, _ = env
    monkeypatch.setattr(po, "live_gates", lambda: [("seasonA", gate(ask=None), "not_eligible_vs_shx (no ask)", True)])
    led, _ = run(at(13, 15, 0))
    assert led["trades"][KEY]["skipped"].startswith("not_eligible_vs_shx") and b.posts == 0


def test_expiry_before_reaction_is_skipped(env):
    b, state, run, _ = env
    state["gates"] = [gate(reaction="2026-10-19")]
    led, _ = run(at(13, 15, 0))
    assert led["trades"]["seasonA-XYZ-2026-10-19-F"]["skipped"] == "expiry_before_reaction" and b.posts == 0


def test_unverified_cap_and_fill_anomaly_halt(env, monkeypatch):
    b, state, run, _ = env
    state["gates"] = [dict(gate(reaction=f"2026-10-{d}", expiry="2026-10-30"), ticker=f"T{d}") for d in range(15, 21)]
    b.fill_mode = "hold"
    led, _ = run(at(13, 15, 0))
    assert b.posts == po.UNVERIFIED_OPEN_CAP           # 3 opens until a fill verifies the convention
    # a fill far from the natural halts new opens
    o = b.orders["o0"]
    o["status"] = "filled"
    o["filled_qty"] = "1"
    real_view = b.view

    def bad_view(oo):
        v = real_view(oo)
        if oo is o:
            for lg in v["legs"]:
                lg["filled_avg_price"] = "9.99" if lg["side"] == "buy" else "0.01"
        return v
    b.view = bad_view
    led, rc = run(at(13, 15, 5))
    assert led.get("halt") and rc == 1


def test_exits_only_sends_no_open(env):
    b, _, run, _ = env
    run(at(13, 15, 0), exits_only=True)
    assert b.posts == 0


def test_simulated_exit_waits_for_a_price(env):
    b, _, run, _ = env
    b.fill_mode = "expire"
    run(at(13, 15, 0)); run(at(13, 15, 10)); run(at(13, 15, 20))
    b.quotes_down = True
    led, _ = run(at(15, 14, 35))
    assert "close_sim" not in led["trades"][KEY] and "result" not in led["trades"][KEY]
    b.quotes_down = False
    led, _ = run(at(15, 14, 45))
    assert led["trades"][KEY]["result"]["simulated_legs"] == ["close", "open"]


def test_cap_blocks_are_labelled_and_alerted(env):
    b, state, run, _ = env
    state["gates"] = [dict(gate(reaction=f"2026-10-{d}", expiry="2026-10-30"), ticker=f"T{d}") for d in range(15, 20)]
    b.fill_mode = "hold"
    run(at(13, 15, 0))
    led, rc = run(at(13, 15, 56))
    blocked = [t for t in led["trades"].values() if t.get("open_failed") == "held_by_cap"]
    assert len(blocked) == 2 and rc == 1 and all(t["key"] in led["alerts"] for t in blocked)


def test_lost_ledger_after_cutoff_finds_the_orphan(env):
    b, _, run, tmp = env
    run(at(13, 15, 0))
    os.remove(tmp / "ledger.json")
    led, rc = run(at(13, 15, 58))
    assert led["trades"][KEY]["orphan_order"]["id"] == "o0" and rc == 1
