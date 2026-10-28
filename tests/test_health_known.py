"""Health check: acknowledged alerts (ops/health_known.json) go under KNOWN; anything else about them still alarms.
Run: python -m pytest tests/test_health_known.py -q"""
import datetime
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
import health  # noqa: E402
from common import ET  # noqa: E402

DPZ = "seasonA-DPZ-2026-10-13-F"
URL = "https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/40620011970"
SHARES = "POSITION NOT IN LEDGER: paper/options DPZ: the account holds +100, the ledgers show +0"
ALERTS = f"paper/options_ledger.json: alerts ['{DPZ}']"
ENTRY = {"why": "w", "source": "ops/incidents/2026-10-13_DPZ_exit.md", "acknowledged": "2026-10-28", "until": "2026-11-06"}
NOW = datetime.datetime(2026, 10, 28, 10, 0, tzinfo=ET)


def log(summary=f"errors 0; alerts ['{DPZ}']; halt False", extra=()):
    """The paper-options job log of run 40620011970 (Oct 27 22:17 ET), cut to the lines that matter."""
    return "\n".join([
        "2026-10-28T02:17:25.6377022Z PASS - 0 warning(s)",
        "2026-10-28T02:17:25.7322759Z ##[endgroup]",
        f"2026-10-28T02:17:26.8325755Z options ledger: 84 record(s), 26 with a result; {summary}",
        "2026-10-28T02:17:26.8326213Z nothing changed - no write, no commit",
        *extra,
        "2026-10-28T02:17:26.8499172Z ##[error]Process completed with exit code 1.",
    ])


def one(text):
    return lambda run_id: [text]


# ---------------------------------------------------------------- one run, read from its own log
def test_a_run_red_only_on_the_dpz_flag_is_known():
    assert health.known_failure(URL, {DPZ: ENTRY}, logs=one(log())) == [DPZ]


def test_the_summary_line_matches_the_frozen_code():
    src = open(os.path.join(os.path.dirname(__file__), "..", "pipeline", "paper_options.py"), encoding="utf-8").read()
    assert 'print(f"options ledger: {len(trades)} record(s), {done} with a result; errors {len(errors)}; "' in src
    assert 'f"alerts {alerts}; halt {bool(led.get(\'halt\'))}")' in src
    for s in health.NOT_ONLY_ALERTS:
        assert s in src


@pytest.mark.parametrize("summary", [
    f"errors 0; alerts ['{DPZ}', 'seasonA-XYZ-2026-10-28-F']; halt False",     # a new alert
    f"errors 1; alerts ['{DPZ}']; halt False",                                   # an order error
    f"errors 0; alerts ['{DPZ}']; halt True",                                    # a halt
    "errors 0; alerts []; halt False",                                           # red for another reason
])
def test_anything_beyond_the_acknowledged_alert_is_not_known(summary):
    assert health.known_failure(URL, {DPZ: ENTRY}, logs=one(log(summary))) is None


@pytest.mark.parametrize("extra", [
    ["2026-10-28T02:17:26.84Z PUSH FAILED - the ledger is not on GitHub"],
    ["2026-10-28T02:17:26.84Z Traceback (most recent call last):"],
    ["2026-10-28T02:17:26.84Z ##[error]Process completed with exit code 2."],          # a second failed step
])
def test_a_push_failure_traceback_or_second_error_is_not_known(extra):
    assert health.known_failure(URL, {DPZ: ENTRY}, logs=one(log(extra=extra))) is None


def test_no_summary_line_two_jobs_or_an_unreadable_log_is_not_known():
    outage = "x broker unreachable (timeout) - nothing decided this run\nx ##[error]Process completed with exit code 1."
    assert health.known_failure(URL, {DPZ: ENTRY}, logs=one(outage)) is None
    assert health.known_failure(URL, {DPZ: ENTRY}, logs=lambda r: [log(), log()]) is None

    def boom(run_id):
        raise OSError("job log 1: HTTP 403")
    assert health.known_failure(URL, {DPZ: ENTRY}, logs=boom) is None
    assert health.known_failure("no run id here", {DPZ: ENTRY}, logs=one(log())) is None
    assert health.known_failure(URL, {}, logs=one(log())) is None


# ---------------------------------------------------------------- the file
def write_known(root, **groups):
    (root / "ops").mkdir(exist_ok=True)
    (root / "ops" / "health_known.json").write_text(json.dumps(groups), encoding="utf-8")


def test_lapsed_and_incomplete_entries_are_not_in_force(tmp_path, monkeypatch):
    monkeypatch.setattr(health, "ROOT", str(tmp_path))
    assert health.known_alerts(NOW.date()) == ({}, {}, [], [])                       # no file
    write_known(tmp_path, lines={SHARES: dict(ENTRY, until="2026-10-27"), ALERTS: {"why": "w"}},
                paper_options_alerts={DPZ: ENTRY})
    lines, keys, amber, info = health.known_alerts(NOW.date())
    assert lines == {} and keys == {DPZ: ENTRY}
    assert amber == [f"{health.KNOWN_FILE}: {ALERTS} lacks ['source', 'acknowledged', 'until'] - not treated as known"]
    assert info == [f"{health.KNOWN_FILE}: {SHARES} lapsed on 2026-10-27 - it alarms again until re-acknowledged"]


def test_the_committed_file_is_in_force_and_names_its_sources():
    p = os.path.join(os.path.dirname(__file__), "..", health.KNOWN_FILE)
    k = json.load(open(p, encoding="utf-8"))
    for group in ("lines", "paper_options_alerts"):
        for e in k[group].values():
            assert all(e.get(f) for f in health.KNOWN_FIELDS)
            assert os.path.exists(os.path.join(os.path.dirname(__file__), "..", e["source"]))


def test_only_an_exact_line_moves():
    lines = {SHARES: ENTRY}
    other = SHARES.replace("+100", "+200")
    red, amber, known = health.split_known([SHARES, other], [ALERTS], lines)
    assert red == [other] and amber == [ALERTS] and len(known) == 1 and known[0].startswith(SHARES + " - w (")


# ---------------------------------------------------------------- the whole run
@pytest.fixture
def root(tmp_path, monkeypatch):
    monkeypatch.setattr(health, "ROOT", str(tmp_path))
    monkeypatch.setattr(health, "check_py", lambda: ("PASS - 0 warning(s)", [], 0))
    monkeypatch.setattr(health, "v4_rule", lambda season: {"t2_deadline_minutes_before_entry_open": 15})
    monkeypatch.setattr(health, "paper_window", lambda now: ([], [], []))
    monkeypatch.setattr(health, "positions_check", lambda now: ([SHARES], [], []))
    monkeypatch.setattr(health, "job_logs", one(log()))
    for d in ("universe/seasonA", "shadow/calendar", "shadow/c1/im", "paper"):
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    (tmp_path / "universe" / "seasonA" / "event_status.json").write_text(json.dumps({"events": {}}))
    (tmp_path / "paper" / "options_ledger.json").write_text(json.dumps({"trades": {}, "alerts": [DPZ]}))
    monkeypatch.setattr(health, "capture_check", lambda now: None)
    monkeypatch.setattr(health, "c1_capture_check", lambda now: None)
    return tmp_path


def test_today_reads_green_with_three_known(root, monkeypatch, capsys):
    write_known(root, lines={SHARES: ENTRY, ALERTS: ENTRY}, paper_options_alerts={DPZ: ENTRY})
    monkeypatch.setattr(health, "actions_failures", lambda now: [
        (health.PAPER_OPTIONS, "2026-10-28T02:17:04Z", URL, "failure"),
        (health.PAPER_OPTIONS, "2026-10-27T23:35:03Z", URL.replace("40620011970", "40603120598"), "failure")])
    status, red, amber, info = health.run(now=NOW)
    out = capsys.readouterr().out
    assert (status, red, amber) == ("GREEN", [], [])
    assert "**GREEN** (3 known)" in out
    assert f"2 paper-options run(s) in 24 h failed only on the acknowledged alert(s) ['{DPZ}']" in out
    assert "newest 2026-10-28T02:17:04Z " + URL in out


def test_without_the_file_today_reads_red_as_before(root, monkeypatch):
    monkeypatch.setattr(health, "actions_failures", lambda now: [(health.PAPER_OPTIONS, "t", URL, "failure")])
    status, red, amber, info = health.run(now=NOW)
    assert status == "RED" and red == [SHARES]
    assert amber == [f"Actions failure: {health.PAPER_OPTIONS} at t {URL}", ALERTS]


def test_a_new_red_still_shows(root, monkeypatch):
    write_known(root, lines={SHARES: ENTRY, ALERTS: ENTRY}, paper_options_alerts={DPZ: ENTRY})
    monkeypatch.setattr(health, "job_logs", one(log(f"errors 0; alerts ['{DPZ}', 'seasonA-NEW-2026-10-28-F']; "
                                                     "halt False")))
    monkeypatch.setattr(health, "actions_failures", lambda now: [
        (health.PAPER_OPTIONS, "t", URL, "failure"), ("Earnings experiment - S2 window", "t2", "u2", "failure"),
        (health.PAPER_OPTIONS, "t3", URL, "timed_out")])
    status, red, amber, info = health.run(now=NOW)
    assert status == "RED" and red == ["Actions failure: Earnings experiment - S2 window at t2 u2"]
    assert amber == [f"Actions failure: {health.PAPER_OPTIONS} at t {URL}",
                     f"Actions timed_out: {health.PAPER_OPTIONS} at t3 {URL}"]
