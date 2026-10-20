"""pipeline/hk.py (2026-10-20): the AI reads company pages; code writes the records and refuses what D003 §6 refuses."""
import datetime
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
import hk  # noqa: E402
import find_dates as fd  # noqa: E402
from common import ET, rule_for  # noqa: E402

RULE = rule_for("D003_universe_screen", "seasonA")
NOW = datetime.datetime(2026, 10, 20, 8, 30, tzinfo=ET)


def st(**events):
    return {"season": "seasonA", "events": {k: {"status": "PENDING", "calendar_dates": v} for k, v in events.items()}}


def test_confirm_writes_the_record_when_a_second_source_agrees(tmp_path, monkeypatch):
    monkeypatch.setattr(hk, "ROOT", str(tmp_path))
    monkeypatch.setattr(fd, "second_source_agrees", lambda *a: (True, [{"source": "nasdaq calendar", "session": "AMC"}]))
    s = st(LOGI=["2026-10-27"])
    msg = hk.confirm(s, "LOGI", "2026-10-27", "AMC", "u", "p", "t", "q", False, RULE, NOW)
    assert "CONFIRMED" in msg and s["events"]["LOGI"]["snapshot_session"] == "2026-10-26"
    assert json.loads((tmp_path / "events" / "seasonA" / "LOGI_2026-10-27" / "confirm.json").read_text())["session"] == "AMC"


def test_confirm_refuses_without_an_agreeing_second_source(tmp_path, monkeypatch):
    monkeypatch.setattr(hk, "ROOT", str(tmp_path))
    monkeypatch.setattr(fd, "second_source_agrees", lambda *a: (False, []))
    s = st(LOGI=["2026-10-27"])
    assert "left PENDING" in hk.confirm(s, "LOGI", "2026-10-27", "AMC", "u", "p", "t", "q", False, RULE, NOW)
    assert s["events"]["LOGI"]["status"] == "PENDING" and not (tmp_path / "events").exists()


def test_confirm_refuses_a_passed_snapshot_and_a_date_outside_the_window(tmp_path, monkeypatch):
    monkeypatch.setattr(hk, "ROOT", str(tmp_path))
    monkeypatch.setattr(fd, "second_source_agrees", lambda *a: (True, []))
    with pytest.raises(SystemExit):
        hk.confirm(st(GE=["2026-10-20"]), "GE", "2026-10-20", "BMO", "u", "p", "t", "q", False, RULE, NOW)
    with pytest.raises(SystemExit):
        hk.confirm(st(X=["2027-01-05"]), "X", "2027-01-05", "AMC", "u", "p", "t", "q", False, RULE, NOW)


def test_retire_unconfirmed_only_after_every_snapshot_has_passed():
    s = st(SMMT=["2026-10-19"], GLW=["2026-10-27"])
    assert "INELIGIBLE" in hk.retire(s, "SMMT", "unconfirmed", "why", RULE, NOW)
    with pytest.raises(SystemExit):
        hk.retire(s, "GLW", "unconfirmed", "why", RULE, NOW)
    assert s["events"]["GLW"]["status"] == "PENDING"


def test_log_line_appends_to_the_cloud_run_log(tmp_path):
    p = tmp_path / "STATE.md"
    p.write_text("# STATE\n\n## Cloud run log\n\nintro\n", encoding="utf-8")
    hk.log_line("3 re-checked, 1 confirmed", NOW, str(p))
    assert p.read_text(encoding="utf-8").endswith("housekeeping 08:30 ET:** 3 re-checked, 1 confirmed\n")
