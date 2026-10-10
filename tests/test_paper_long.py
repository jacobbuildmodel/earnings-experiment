"""D011 v2: the long straddle runs v1's frozen code against structure L, a second account and its own ledger.
Reuses v1's fake broker. Run: python -m pytest tests/test_paper_long.py -q"""
import datetime
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
sys.path.insert(0, os.path.dirname(__file__))
import paper_long as pl  # noqa: E402
import paper_options as po  # noqa: E402
from test_paper_options import CH, Q, Broker, at, gate  # noqa: E402

KEY = "seasonA-XYZ-2026-10-15-L"


@pytest.fixture
def env(monkeypatch, tmp_path):
    monkeypatch.setattr(pl, "LEDGER", str(tmp_path / "long.json"))
    b = Broker()
    state = {"gates": [gate()]}
    # the raw gate list goes in BEFORE configure, so configure's START filter is what is tested
    monkeypatch.setattr(po, "live_gates", lambda: [("seasonA", g, None, True) for g in state["gates"]])
    pl.configure(monkeypatch.setattr)
    monkeypatch.setattr(po, "call", b.call)
    monkeypatch.setattr(po, "chain", lambda t, e: CH)
    monkeypatch.setattr(po, "quotes", lambda syms: {s: Q[s] for s in syms})
    monkeypatch.setattr(po, "expiry_close", lambda t, e: 112.0)

    def run(when):
        monkeypatch.setattr(po, "now_et", lambda: when)
        rc = po.sync(False)
        return json.load(open(tmp_path / "long.json")), rc
    return b, state, run


def test_configure_points_v1_at_L(env):
    assert po.STRUCTURES == "L" and po.LEDGER.endswith("long.json")
    assert po.load_ledger()["structures"] == {"L": "long straddle"}


def test_long_cycle(env):
    b, _, run = env
    led, _ = run(at(13, 15, 0))
    body = b.orders["o0"]["body"]
    assert [(lg["side"], lg["position_intent"]) for lg in body["legs"]] == [("buy", "buy_to_open")] * 2
    assert float(body["limit_price"]) == 8.2                 # a debit is a positive limit
    led, _ = run(at(13, 15, 10))
    assert led["convention_verified"]["trade"] == KEY
    run(at(15, 14, 35))
    led, _ = run(at(15, 14, 45))
    r = led["trades"][KEY]["result"]
    assert abs(r["pnl_per_unit"] - (-0.4)) < 1e-9          # two spreads of 0.2 at unchanged quotes


def test_long_held_past_expiry_receives_the_move(env):
    b, _, run = env
    run(at(13, 15, 0)); run(at(13, 15, 10))
    b.open = False
    led, _ = run(at(19, 9, 0))
    r = led["trades"][KEY]["result"]
    assert r["close_net"] == -12.0 and abs(r["pnl_per_unit"] - (12.0 - 8.2)) < 1e-9


def test_gates_before_start_are_not_this_tracks(env):
    b, state, run = env
    state["gates"] = [gate(snapshot="2026-10-09", reaction="2026-10-13", expiry="2026-10-16")]
    led, _ = run(at(13, 15, 0))
    assert led["trades"] == {} and b.posts == 0


def test_not_configured_is_inert(monkeypatch, capsys):
    monkeypatch.delenv(pl.KEY_ID, raising=False)
    assert not pl.configured()
