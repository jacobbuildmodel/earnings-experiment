"""Health exits() after the D011 v3 review: a full close awaiting settlement is not flagged, a partial close is,
and a v3 trade's expiry-day last send is 15:10 ET. Run: python -m pytest tests/test_health_exits.py -q"""
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
import health  # noqa: E402
import test_paper_ops_dpz as t  # noqa: E402
from common import ET  # noqa: E402


def at(d, h, m):
    return datetime.datetime.combine(d, datetime.time(h, m), ET)


def test_full_close_awaiting_settlement_is_not_flagged():
    assert health.exits("x", {"trades": {"k": t.dpz(close_filled=True)}}, at(t.TUE, 15, 20)) == ([], [])


def test_partial_close_is_flagged():
    tr = t.dpz(close_filled=True)
    tr["orders"]["open"][0]["filled_qty"] = 2.0
    red, amber = health.exits("x", {"trades": {"k": tr}}, at(t.TUE, 15, 20))
    assert red and "1 of 2 closed" in red[0]


def test_v3_expiry_day_last_send_is_1510():
    tr = t.dpz()
    tr.update(exec="v3", expiry="2026-10-13")
    red, amber = health.exits("x", {"trades": {"k": tr}}, at(t.TUE, 15, 20))
    assert not red and amber
    tr["expiry"] = "2026-10-16"
    red, amber = health.exits("x", {"trades": {"k": tr}}, at(t.TUE, 15, 20))
    assert red and "15:55" in red[0]


def test_close_sim_is_not_flagged():
    tr = t.dpz()
    tr["close_sim"] = {"net": 0.0}
    assert health.exits("x", {"trades": {"k": tr}}, at(t.TUE, 15, 20)) == ([], [])
