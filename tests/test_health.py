"""Health check: missed windows, T2 / shadow missing after the deadline, ledger halts, Actions failures, status.
Run: python -m pytest tests/test_health.py -q"""
import datetime
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
import health  # noqa: E402
from common import ET  # noqa: E402


@pytest.fixture
def root(tmp_path, monkeypatch):
    monkeypatch.setattr(health, "ROOT", str(tmp_path))
    monkeypatch.setattr(health, "check_py", lambda: ("PASS - 0 warning(s)", [], 0))
    monkeypatch.setattr(health, "actions_failures", lambda now: [])
    monkeypatch.setattr(health, "v4_rule", lambda season: {"t2_deadline_minutes_before_entry_open": 15})
    u = tmp_path / "universe" / "seasonA"
    u.mkdir(parents=True)
    (u / "event_status.json").write_text(json.dumps({"events": {
        "AAA": {"status": "CONFIRMED", "snapshot_session": "2026-10-16", "calendar_date": "2026-10-19"},
        "BBB": {"status": "CONFIRMED", "snapshot_session": "2026-10-16", "calendar_date": "2026-10-19"},
        "CCC": {"status": "PENDING"}}}))
    (tmp_path / "events" / "seasonA" / "AAA_2026-10-19").mkdir(parents=True)
    (tmp_path / "events" / "seasonA" / "AAA_2026-10-19" / "gate.json").write_text(json.dumps(
        {"status": "PASS", "timing": {"entry": {"session": "2026-10-19"}}}))
    (tmp_path / "events" / "seasonA" / "AAA_2026-10-19" / "manifest.json").write_text(json.dumps(
        {"status": "PASS", "entry_open_et": "2026-10-19T09:30:00-04:00"}))
    (tmp_path / "events" / "seasonA" / "AAA_2026-10-19" / "manifest_t2.json").write_text("{}")
    (tmp_path / "events" / "seasonA" / "AAA_2026-10-19" / "dossier.json").write_text("{}")
    (tmp_path / "shadow" / "calendar").mkdir(parents=True)
    return tmp_path


def test_green_before_anything_is_due(root):
    status, red, amber, info = health.run(now=datetime.datetime(2026, 10, 16, 10, 0, tzinfo=ET))
    assert status in ("GREEN", "AMBER") and not red


def test_missed_window_is_red(root):
    status, red, amber, info = health.run(now=datetime.datetime(2026, 10, 16, 17, 0, tzinfo=ET))
    assert status == "RED" and any("MISSED SNAPSHOT WINDOW" in x and "BBB" in x for x in red)
    assert not any("AAA" in x for x in red if "MISSED" in x)


def test_shadows_missing_after_deadline_are_amber_t2_red(root):
    now = datetime.datetime(2026, 10, 19, 9, 20, tzinfo=ET)                 # past 09:15 deadline
    status, red, amber, info = health.run(now=now)
    assert any("T2R missing: AAA_2026-10-19" in x for x in amber) and any("T2O missing" in x for x in amber)
    assert not any("T2 MISSING" in x for x in red)
    os.remove(root / "events" / "seasonA" / "AAA_2026-10-19" / "manifest_t2.json")
    status, red, amber, info = health.run(now=now)
    assert any("T2 MISSING: AAA_2026-10-19" in x for x in red)


def test_halt_and_critical_actions_failure(root, monkeypatch):
    (root / "paper").mkdir()
    (root / "paper" / "options_ledger.json").write_text(json.dumps({"halt": {"why": "fill anomaly"}, "trades": {}}))
    monkeypatch.setattr(health, "actions_failures", lambda now: [("Earnings experiment - S2 window", "t", "u", "failure"),
                                                                 ("Earnings experiment - grade", "t", "u", "timed_out")])
    status, red, amber, info = health.run(now=datetime.datetime(2026, 10, 15, 10, 0, tzinfo=ET))
    assert any("HALT" in x for x in red) and any("S2 window" in x for x in red) and any("grade" in x for x in amber)


def test_unreadable_actions_api_is_amber(root, monkeypatch):
    monkeypatch.setattr(health, "actions_failures", lambda now: None)
    status, red, amber, info = health.run(now=datetime.datetime(2026, 10, 15, 10, 0, tzinfo=ET))
    assert any("unreadable" in x for x in amber)


def test_t2_at_risk_and_check_crash(root, monkeypatch):
    os.remove(root / "events" / "seasonA" / "AAA_2026-10-19" / "manifest_t2.json")
    status, red, amber, info = health.run(now=datetime.datetime(2026, 10, 19, 0, 0, tzinfo=ET))    # 9 h before
    assert any("T2 AT RISK: AAA_2026-10-19" in x for x in red)
    status, red, amber, info = health.run(now=datetime.datetime(2026, 10, 16, 21, 0, tzinfo=ET))   # 60 h (weekend)
    assert not any("AT RISK" in x for x in red)
    status, red, amber, info = health.run(now=datetime.datetime(2026, 10, 16, 10, 0, tzinfo=ET))   # 3 days before
    assert not any("AAA" in x for x in red)
    monkeypatch.setattr(health, "check_py", lambda: ("Traceback ...", [], 1))
    status, red, amber, info = health.run(now=datetime.datetime(2026, 10, 15, 10, 0, tzinfo=ET))
    assert status == "RED" and any("check.py" in x for x in red)


def test_stage1_not_frozen_is_red(root):
    e = root / "events" / "seasonA" / "BBB_2026-10-19"
    e.mkdir(parents=True)
    (e / "gate.json").write_text(json.dumps({"status": "PASS", "timing": {"entry": {"session": "2026-10-19"}}}))
    status, red, amber, info = health.run(now=datetime.datetime(2026, 10, 19, 9, 31, tzinfo=ET))
    assert any("STAGE 1 NOT FROZEN" in x and "BBB" in x for x in red)
