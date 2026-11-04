"""Health check under the D019 stop (registry/D019_reframe_v1.md §1): the registered stop of paper options F and L
reads as information, not RED; the gates it blocked are not alerts; a paper run that failed only on it is not an
Actions failure. Anything else still alarms. Run: python -m pytest tests/test_health_d019.py -q"""
import datetime
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
import health  # noqa: E402
from common import ET  # noqa: E402

SINCE = "2026-11-04T08:39:25.284907-05:00"
STOP = {"since": SINCE, "stop": "D019", "why": "D019 §1 ... do not clear.", "set_by": "the D019 implementation chat"}
OLD = "seasonA-CIFR-2026-11-02-F"        # blocked by the D011 §5 fill halt of 10-28, before the stop
NEW = "seasonA-NET-2026-11-05-F"         # a gate after the stop
URL = "https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41800000001"
NOW = datetime.datetime(2026, 11, 4, 16, 30, tzinfo=ET)


def trade(created, failed="halt"):
    return {"created_et": created, "open_failed": failed, "open_blocked": failed, "reaction_session": "2026-11-05"}


def ledger(halt=STOP, alerts=(OLD, NEW)):
    return {"halt": halt, "alerts": list(alerts) or None,
            "trades": {OLD: trade("2026-10-29T14:34:06.904686-04:00"), NEW: trade("2026-11-04T14:33:00-05:00")}}


@pytest.fixture
def root(tmp_path, monkeypatch):
    monkeypatch.setattr(health, "ROOT", str(tmp_path))
    (tmp_path / "paper").mkdir()
    return tmp_path


def put(root, name, led):
    (root / "paper" / name).write_text(json.dumps(led))


def log(summary=f"errors 0; alerts ['{OLD}', '{NEW}']; halt True", runs=1, extra=()):
    lines = [f"2026-11-04T19:3{i}:00Z  options ledger: 90 record(s), 40 with a result; {summary}" for i in range(runs)]
    return "\n".join(lines + list(extra) + ["2026-11-04T19:40:00Z ##[error]Process completed with exit code 1."])


# ---------------------------------------------------------------- the ledgers
def test_the_d019_stop_is_information_and_its_gates_are_not_alerts(root):
    put(root, "options_ledger.json", ledger())
    red, amber, info = health.ledgers(NOW)
    assert red == []
    assert amber == [f"paper/options_ledger.json: alerts ['{OLD}']"]           # the older halt's gate still alarms
    assert any("stopped by D019 since 2026-11-04T08:39" in x for x in info)
    assert f"paper/options_ledger.json: 1 gate(s) not opened under the D019 stop ['{NEW}']" in info


def test_any_other_halt_is_still_red(root):
    put(root, "options_ledger.json", ledger(halt={"since": SINCE, "why": "fill anomaly"}))
    red, amber, _ = health.ledgers(NOW)
    assert red == ["paper/options_ledger.json: HALT - fill anomaly"]
    assert amber == [f"paper/options_ledger.json: alerts ['{OLD}', '{NEW}']"]   # nothing is excused without the stop


def test_the_stop_needs_every_ledger(root):
    put(root, "options_ledger.json", ledger())
    put(root, "long_ledger.json", ledger(halt=None, alerts=()))
    assert health.d019_stop() is None
    put(root, "long_ledger.json", ledger(alerts=()))
    s = health.d019_stop()
    assert s["since"] == health.iso(SINCE) and s["blocked"] == {NEW}


# ---------------------------------------------------------------- a failed paper run, read from its own logs
def stop():
    return {"since": health.iso(SINCE), "blocked": {NEW}}


def test_a_run_red_only_on_the_stop_is_information():
    assert health.d019_failure(URL, "2026-11-04T19:30:00Z", stop(), {OLD: {}}, logs=lambda r: [log(runs=3)])
    # a window run's matrix: one job failed only on the stop, the other passed
    assert health.d019_failure(URL, "2026-11-04T19:30:00Z", stop(), {OLD: {}}, logs=lambda r: [log(), "all fine"])


@pytest.mark.parametrize("summary", [
    f"errors 0; alerts ['{OLD}', '{NEW}']; halt False",                     # no halt: the stop is not why it failed
    f"errors 1; alerts ['{OLD}', '{NEW}']; halt True",                      # an order error
    f"errors 0; alerts ['{OLD}', '{NEW}', 'seasonA-X-2026-11-05-F']; halt True",   # a new alert
])
def test_anything_beyond_the_stop_still_alarms(summary):
    assert not health.d019_failure(URL, "2026-11-04T19:30:00Z", stop(), {OLD: {}}, logs=lambda r: [log(summary)])


def test_an_unacknowledged_old_alert_still_alarms():
    assert not health.d019_failure(URL, "2026-11-04T19:30:00Z", stop(), {}, logs=lambda r: [log()])


@pytest.mark.parametrize("extra", [["x PUSH FAILED - the ledger is not on GitHub"], ["x Traceback (most recent call last):"],
                                   ["x ##[error]Process completed with exit code 2."]])
def test_a_push_failure_traceback_or_second_error_still_alarms(extra):
    assert not health.d019_failure(URL, "2026-11-04T19:30:00Z", stop(), {OLD: {}}, logs=lambda r: [log(extra=extra)])


def test_a_run_before_the_stop_or_an_unreadable_log_still_alarms():
    good = lambda r: [log()]
    assert not health.d019_failure(URL, "2026-11-04T13:00:00Z", stop(), {OLD: {}}, logs=good)   # 08:00 ET
    assert not health.d019_failure("no run id", "2026-11-04T19:30:00Z", stop(), {OLD: {}}, logs=good)
    assert not health.d019_failure(URL, "2026-11-04T19:30:00Z", None, {OLD: {}}, logs=good)
    assert not health.d019_failure(URL, "2026-11-04T19:30:00Z", stop(), {OLD: {}}, logs=lambda r: ["all fine"])

    def boom(run_id):
        raise OSError("job log 1: HTTP 403")
    assert not health.d019_failure(URL, "2026-11-04T19:30:00Z", stop(), {OLD: {}}, logs=boom)


def test_the_workflow_names_are_the_paper_workflows():
    wf = os.path.join(os.path.dirname(__file__), "..", ".github", "workflows")
    names = set()
    for f in ("paper-options.yml", "paper-long.yml", "paper-window.yml", "paper-window-push.yml"):
        first = next(x for x in open(os.path.join(wf, f), encoding="utf-8") if x.startswith("name:"))
        names.add(first.split(":", 1)[1].strip())
    assert names == set(health.PAPER_RUNS)
