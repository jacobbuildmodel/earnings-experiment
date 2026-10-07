"""find_dates v2 (2026-10-06): the snapshot-day morning pass. A date confirmed before the S2 window opens
counts for today's gate; one found later, or by the evening run, is left for the AI step as before."""
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
import find_dates as fd  # noqa: E402
from common import ET  # noqa: E402

EVENTS = {"AAA": ("2026-10-13", "BMO"),   # snapshot Fri 2026-10-09
          "BBB": ("2026-10-12", "AMC"),   # snapshot Fri 2026-10-09
          "CCC": ("2026-10-20", "AMC")}   # not urgent on 10-09


def run(tmp_path, monkeypatch, clock, urgent):
    d = tmp_path / "universe" / "seasonA"
    d.mkdir(parents=True, exist_ok=True)
    sp = d / "event_status.json"
    sp.write_text(json.dumps({"season": "seasonA", "events": {
        k: {"status": "PENDING", "calendar_dates": [v[0]]} for k, v in EVENTS.items()}}))
    probed = []

    def probe(t, window):
        probed.append(t)
        return {"checked_et": "t", "outcome": "found", "date": EVENTS[t][0], "session": EVENTS[t][1], "feed": "f",
                "source": {"url": "u", "published_et": "p", "sentence": "s", "title": "t",
                           "session_from_call_time": False}}
    monkeypatch.setattr(fd, "ROOT", str(tmp_path))
    monkeypatch.setattr(fd, "probe", probe)
    monkeypatch.setattr(fd, "second_source_agrees", lambda *a: (True, []))
    monkeypatch.setattr(fd.time, "sleep", lambda s: None)
    monkeypatch.setattr(fd, "now_et", lambda: clock)
    fd.apply("seasonA", urgent=urgent)
    st = json.loads(sp.read_text())["events"]
    return sorted(probed), {k: v["status"] for k, v in st.items()}


def test_morning_confirms_todays_snapshot(tmp_path, monkeypatch):
    probed, st = run(tmp_path, monkeypatch, datetime.datetime(2026, 10, 9, 10, 45, tzinfo=ET), True)
    assert probed == ["AAA", "BBB"]
    assert st == {"AAA": "CONFIRMED", "BBB": "CONFIRMED", "CCC": "PENDING"}


def test_too_close_to_the_window_does_nothing(tmp_path, monkeypatch):
    probed, st = run(tmp_path, monkeypatch, datetime.datetime(2026, 10, 9, 14, 27, tzinfo=ET), True)
    assert probed == [] and set(st.values()) == {"PENDING"}


def test_not_a_session_does_nothing(tmp_path, monkeypatch):
    probed, st = run(tmp_path, monkeypatch, datetime.datetime(2026, 10, 10, 10, 45, tzinfo=ET), True)
    assert probed == [] and set(st.values()) == {"PENDING"}


def test_evening_run_unchanged(tmp_path, monkeypatch):
    probed, st = run(tmp_path, monkeypatch, datetime.datetime(2026, 10, 9, 21, 0, tzinfo=ET), False)
    assert st == {"AAA": "PENDING", "BBB": "PENDING", "CCC": "CONFIRMED"}
