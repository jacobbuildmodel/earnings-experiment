"""After the DPZ incident (ops/incidents/2026-10-13_DPZ_exit.md): the window runner's cadence, the health check's
exit alarms, and the exit audit's on-time counterfactual. Run: python -m pytest tests/test_paper_ops_dpz.py -q"""
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
import health  # noqa: E402
import paper_exit_audit as pea  # noqa: E402
import paper_window as pw  # noqa: E402
from common import ET  # noqa: E402

TUE = datetime.date(2026, 10, 13)


def dpz(close_filled=False, result=None):
    o = {"filled_qty": 1.0, "legs_filled": [
        {"symbol": "C310", "side": "sell", "qty": 1.0, "price": 9.5}, {"symbol": "P310", "side": "sell", "qty": 1.0, "price": 11.2},
        {"symbol": "C360", "side": "buy", "qty": 1.0, "price": 2.45}, {"symbol": "P260", "side": "buy", "qty": 1.0, "price": 0.65}]}
    c = {"sent_et": "2026-10-13T14:46:51-04:00", "natural": 17.28,
         "sides": {"C310": "buy", "P310": "buy", "C360": "sell", "P260": "sell"},
         "quotes": {"C310": {"bid": 0.98, "ask": 2.23}, "P310": {"bid": 10.52, "ask": 15.05},
                    "C360": {"bid": 0, "ask": 0.03}, "P260": {"bid": 0, "ask": 0.12}},
         "filled_qty": 1.0 if close_filled else 0.0,
         "filled_at": "2026-10-14T15:01:02.123456789Z" if close_filled else None}
    t = {"key": "seasonA-DPZ-2026-10-13-F", "season": "seasonA", "ticker": "DPZ", "reaction_session": "2026-10-13",
         "expiry": "2026-10-16", "spot_at_gate": 307.385, "orders": {"open": [o], "close": [c]}}
    if result is not None:
        t["result"] = {"pnl_per_unit": result, "simulated_legs": []}
    return t


def test_audit_counterfactual_matches_the_incident_numbers():
    a = pea.audit_trade(dpz())
    assert abs(a["counterfactual_on_time_natural"] - 0.32) < 1e-9
    assert abs(a["counterfactual_on_time_mid"] - 3.285) < 1e-9
    assert a["state"] == "open" and not a["filled_same_day"] and a["delay_cost"] is None
    b = pea.audit_trade(dpz(close_filled=True, result=-7.71))
    assert b["close_filled_et"].startswith("2026-10-14T11:01") and not b["filled_by_1500"]
    assert abs(b["delay_cost"] - (-7.71 - 0.32)) < 1e-9


def test_health_exit_alarms():
    led = {"trades": {"k": dpz()}}
    at = lambda d, h, m: datetime.datetime.combine(d, datetime.time(h, m), ET)
    assert health.exits("x", led, at(TUE, 14, 50)) == ([], [])                      # inside the window, not yet
    red, amber = health.exits("x", led, at(TUE, 15, 20))
    assert red and "EXIT NOT FILLED" in red[0] and not amber
    red, amber = health.exits("x", led, at(TUE, 16, 30))
    assert not red and "EXIT MISSED" in amber[0]
    red, amber = health.exits("x", led, at(TUE + datetime.timedelta(days=1), 10, 0))
    assert not red and amber
    done = {"trades": {"k": dpz(close_filled=True, result=1.0)}}
    assert health.exits("x", done, at(TUE, 15, 20)) == ([], [])


def test_window_runner_cadence(tmp_path, monkeypatch):
    calls, slept = [], []
    t = [datetime.datetime.combine(TUE, datetime.time(14, 0), ET)]
    clock = lambda: t[0]

    def sleep(s):
        slept.append(s)
        t[0] += datetime.timedelta(seconds=s)

    monkeypatch.setattr(pw, "run", lambda cmd: calls.append(cmd[1]) or 0)
    monkeypatch.setattr(pw.subprocess, "run", lambda *a, **k: None)
    monkeypatch.setattr(pw, "now_et", clock)
    pw.main("options", "14:27", "15:56", 3, False, sleep, clock)
    syncs = [c for c in calls if c.endswith("paper_options.py")]
    assert slept[0] == 27 * 60 and len(syncs) == 30                                # 14:27, 14:30 ... 15:54
    calls.clear()
    t[0] = datetime.datetime.combine(TUE, datetime.time(16, 0), ET)
    assert pw.main("options", "14:27", "15:56", 3, False, sleep, clock) == 0 and not calls


def test_window_runner_morning_only_if_active(tmp_path, monkeypatch):
    monkeypatch.setattr(pw, "ROOT", str(tmp_path))
    (tmp_path / "paper").mkdir()
    (tmp_path / "paper" / "options_ledger.json").write_text(json.dumps({"trades": {}}))
    calls = []
    monkeypatch.setattr(pw, "run", lambda cmd: calls.append(cmd) or 0)
    monkeypatch.setattr(pw.subprocess, "run", lambda *a, **k: None)
    t = [datetime.datetime.combine(TUE, datetime.time(9, 40), ET)]
    pw.main("options", "09:35", "12:00", 3, True, lambda s: None, lambda: t[0])
    assert calls == []
    (tmp_path / "paper" / "options_ledger.json").write_text(json.dumps({"trades": {"k": dpz()}}))
    assert pw.active("paper/options_ledger.json")
