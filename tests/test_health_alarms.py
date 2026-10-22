"""Health alarms (designed 2026-10-21 13:40 ET, STATE.md Log): AI step refused, dates stale, runner not acting.
Run: python -m pytest tests/test_health_alarms.py -q"""
import datetime
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
import health  # noqa: E402
import paper_options  # noqa: E402
from common import ET  # noqa: E402

WED = datetime.date(2026, 10, 21)


def at(d, h, m=0):
    return datetime.datetime.combine(d, datetime.time(h, m), ET)


# ---------------------------------------------------------------- AI step refused
REFUSAL = "Your organization has disabled Claude subscription access for Claude Code"


@pytest.fixture
def logs(tmp_path, monkeypatch):
    monkeypatch.setattr(health, "ROOT", str(tmp_path))
    (tmp_path / "logs" / "actions").mkdir(parents=True)
    (tmp_path / "logs" / "t2").mkdir(parents=True)
    return tmp_path


def actions_log(root, stamp, is_error, text, suffix="housekeeping"):
    (root / "logs" / "actions" / f"{stamp}_123_{suffix}.json").write_text(json.dumps(
        {"result": {"is_error": is_error, "text": text}}))


def t2_log(root, backend, stamp, error):
    (root / "logs" / "t2" / f"WDC_2026-10-22_{backend}_{stamp}.json").write_text(json.dumps({"error": error}))


def test_standing_refusal_is_amber_with_its_start(logs):
    for s in ("2026-10-15T0207Z", "2026-10-16T0156Z", "2026-10-20T0210Z"):
        actions_log(logs, s, True, REFUSAL)
    actions_log(logs, "2026-10-14T0235Z", False, "done")
    red, amber = health.ai_refusals(at(WED, 20))
    assert not red and len(amber) == 1
    assert "3 refusal(s) in a row since Wed 14 Oct 22:07 ET" in amber[0] and "standing" in amber[0]


def test_new_refusal_is_red(logs):
    actions_log(logs, "2026-10-20T0210Z", False, "done")
    actions_log(logs, "2026-10-21T0210Z", True, REFUSAL)
    red, amber = health.ai_refusals(at(WED, 20))
    assert len(red) == 1 and "1 refusal(s)" in red[0] and REFUSAL in red[0] and not amber


def test_a_success_after_refusals_clears_it(logs):
    actions_log(logs, "2026-10-20T0210Z", True, REFUSAL)
    actions_log(logs, "2026-10-21T0210Z", False, "done")
    assert health.ai_refusals(at(WED, 20)) == ([], [])


def test_t2_network_error_is_not_a_refusal_but_a_cli_refusal_is(logs):
    t2_log(logs, "gemini", "20261021T163226", "ConnectionError: ('Connection aborted.')")
    t2_log(logs, "sonnet_r", "20261021T163226", REFUSAL)
    red, amber = health.ai_refusals(at(WED, 20))
    assert len(red) == 1 and "T2 backend sonnet_r" in red[0] and not amber


def test_old_steps_are_left_alone(logs):
    actions_log(logs, "2026-10-07T0155Z", True, REFUSAL, suffix="APLD")     # newest log over 5 days old
    assert health.ai_refusals(at(WED, 20)) == ([], [])


# ---------------------------------------------------------------- dates stale
@pytest.fixture
def season(tmp_path, monkeypatch):
    monkeypatch.setattr(health, "ROOT", str(tmp_path))
    u = tmp_path / "universe" / "seasonA"
    u.mkdir(parents=True)

    def write(events):
        (u / "event_status.json").write_text(json.dumps({"events": events}))
    return write


def pending(dates, *checks):
    return {"status": "PENDING", "calendar_dates": dates, "rechecks": list(checks)}


CONFIRMED_LINE = "2026-10-20T08:00:00-04:00: housekeeping - company statement (u); CONFIRMED 2026-11-03 AMC, snapshot x"
NOTHING_LINE = "2026-10-21T08:45:00-04:00: find_dates v3 (2026-10-07) - no_date_announced; feed u"


def test_recent_change_is_quiet(season):
    season({"A": {"status": "CONFIRMED", "rechecks": [CONFIRMED_LINE]}, "B": pending(["2026-10-23"])})
    assert health.dates_stale(at(WED, 10)) == ([], [])          # 26 h after the change


def test_no_change_in_30h_with_a_near_name_is_amber_and_says_rechecks_run(season):
    season({"A": {"status": "CONFIRMED", "rechecks": [CONFIRMED_LINE]},
            "B": pending(["2026-10-28"], NOTHING_LINE)})            # 5 sessions away: not within 3
    red, amber = health.dates_stale(at(WED, 20))
    assert not red and len(amber) == 1
    assert "since Tue 20 Oct 08:00 ET" in amber[0] and "run but confirm nothing" in amber[0]


def test_a_name_within_3_sessions_is_red_and_not_running_is_named(season):
    season({"B": pending(["2026-10-23"], "2026-10-19T08:00:00-04:00: find_dates v3 - no_date_announced")})
    red, amber = health.dates_stale(at(WED, 20))
    assert len(red) == 1 and "['B']" in red[0] and "not running" in red[0] and "the season began" in red[0]


def test_far_or_past_dates_do_not_count(season):
    season({"B": pending(["2026-11-20"]), "C": pending(["2026-10-19"]), "D": {"status": "FROZEN"}})
    assert health.dates_stale(at(WED, 20)) == ([], [])


def test_a_retirement_counts_as_a_change(season):
    season({"A": {"status": "INELIGIBLE", "rechecks": [
        "2026-10-21T09:00:00-04:00: housekeeping - INELIGIBLE unconfirmed: no company date"]},
        "B": pending(["2026-10-22"])})
    assert health.dates_stale(at(WED, 20)) == ([], [])


# ---------------------------------------------------------------- runner not acting
def step(acct, started, completed=None, url="https://github.com/o/r/actions/runs/39628692665"):
    return {"account": acct, "workflow": "paper-window-push.yml", "url": url, "job_status": "in_progress",
            "status": "in_progress" if completed is None else "completed", "started": started, "completed": completed}


def order(cid, submitted, status="new"):
    return {"client_order_id": cid, "status": status, "submitted_at": submitted.isoformat()}


LEDGERS = {"options_ledger.json": {"trades": {"seasonA-HXL-2026-10-21-F": {"exec": "v3"},
                                              "seasonA-OLD-2026-10-14-F": {}}},
           "long_ledger.json": {"trades": {}}}


def idle(now, orders, steps=None):
    steps = steps if steps is not None else [step("options", at(WED, 14, 27))]
    return health.runner_idle(now, steps, state=lambda a: ([], orders if a == "options" else []),
                              read=lambda names: {n: LEDGERS.get(n) for n in names})


def test_v3_close_past_2_plus_5_min_is_red_with_the_run_to_cancel():
    red = idle(at(WED, 15, 0), [order("seasonA-HXL-2026-10-21-F-close-r2", at(WED, 14, 52))])
    assert len(red) == 1 and "gh run cancel 39628692665" in red[0] and "2-min cancel limit" in red[0]
    assert "cancel that run FIRST" in red[0]


def test_inside_the_limit_or_pending_cancel_is_quiet():
    assert idle(at(WED, 15, 0), [order("seasonA-HXL-2026-10-21-F-close", at(WED, 14, 54))]) == []
    assert idle(at(WED, 15, 0), [order("seasonA-HXL-2026-10-21-F-close", at(WED, 14, 30), "pending_cancel")]) == []


def test_other_orders_get_15_plus_5_min():
    o = [order("seasonA-OLD-2026-10-14-F-close-r1", at(WED, 14, 41))]
    assert idle(at(WED, 15, 0), o) == []                         # 19 min
    assert len(idle(at(WED, 15, 2), o)) == 1                     # 21 min


def test_no_running_step_unknown_orders_and_outside_the_window_are_quiet():
    old = [order("seasonA-HXL-2026-10-21-F-close", at(WED, 14, 30))]
    assert idle(at(WED, 15, 0), old, steps=[step("options", at(WED, 14, 27), completed=at(WED, 14, 40))]) == []
    assert idle(at(WED, 15, 0), [order("someone-else", at(WED, 14, 0))]) == []
    assert idle(at(WED, 14, 35), old) == []                      # before 14:40
    assert idle(at(WED, 15, 57), old) == []                      # after 15:56


def test_cancel_limits_match_the_frozen_paper_code():
    assert CANCEL_LIMITS == (paper_options.V3_RETRY_AFTER_MIN, paper_options.RETRY_AFTER_MIN)


CANCEL_LIMITS = (health.CANCEL_AFTER["v3_close"], health.CANCEL_AFTER["other"])
