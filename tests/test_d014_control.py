"""D014 control days: the control-day rule and the summary block. Run: python -m pytest tests/test_d014_control.py -q"""
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "analysis", "d014"))
import control_days as cd  # noqa: E402


def test_control_day_is_10_sessions_back_and_avoids_prints():
    sessions = [datetime.date(2025, 1, 1) + datetime.timedelta(days=i) for i in range(40)]
    rows = [{"ticker": "A", "R": sessions[30].isoformat(), "mcap": "5e9"},
            {"ticker": "B", "R": sessions[30].isoformat(), "mcap": "2e10"}]
    prints = {"A": [sessions[30]], "B": [sessions[30], sessions[22]]}          # B printed 2 sessions after C
    out = cd.control_rows(rows, sessions, prints)
    assert [(r["ticker"], r["C"]) for r in out] == [("A", sessions[20])]


def test_block_two_sided_penalty():
    rs = [{"hs_first": 0.004, "hs0935": 0.002, "vw": 101.0, "o": 100.0},
          {"hs_first": None, "hs0935": 0.001, "vw": 99.0, "o": 100.0}]
    b = cd.block(rs)
    assert b["market_order_penalty_two_sided"]["n"] == 1
    assert abs(b["market_order_penalty_two_sided"]["mean"] - 0.004 * 1.01) < 1e-12
    assert abs(b["abs_vwap_vs_open"]["mean"] - 0.01) < 1e-12 and b["hs0935"]["n"] == 2
