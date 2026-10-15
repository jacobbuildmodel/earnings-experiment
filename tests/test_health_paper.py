"""Health checks added 2026-10-15: paper window coverage (Actions API) and Alpaca positions vs the paper ledgers.
No network: the Actions answers are recorded fixtures (tests/fixtures/health_actions_*.json, real runs of 10-14 and
10-15 mid-day) and the Alpaca accounts are built from the real DPZ trade record (tests/fixtures/health_dpz_trade.json).
Run: python -m pytest tests/test_health_paper.py -q"""
import copy
import datetime
import json
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
import health  # noqa: E402
import paper_options  # noqa: E402
from common import ET  # noqa: E402

FIX = os.path.join(os.path.dirname(__file__), "fixtures")
OCT14, OCT15, OCT16, OCT19 = (datetime.date(2026, 10, d) for d in (14, 15, 16, 19))
C310, P310, C360, P260 = "DPZ261016C00310000", "DPZ261016P00310000", "DPZ261016C00360000", "DPZ261016P00260000"


def at(d, h, m):
    return datetime.datetime.combine(d, datetime.time(h, m), ET)


T15, T16, T19 = at(OCT15, 15, 20), at(OCT16, 15, 20), at(OCT19, 10, 0)     # reconcile() looks at these


def recorded(name):
    rec = json.load(open(os.path.join(FIX, name), encoding="utf-8"))

    def get(path, params=None):
        m = re.fullmatch(r"actions/workflows/(.+)/runs", path)
        if m:
            return {"workflow_runs": rec["runs"][m[1]]}
        m = re.fullmatch(r"actions/runs/(\d+)/jobs", path)
        if m:
            return {"jobs": rec["jobs"][m[1]]}
        raise AssertionError(path)
    return get


def step(acct, start, end=None, status=None, wf="paper-window-push.yml", job="completed"):
    return {"account": acct, "workflow": wf, "url": "u", "job_status": job if end else "in_progress",
            "status": status or ("completed" if end else "in_progress"), "started": start, "completed": end}


# ---------------------------------------------------------------- paper window coverage
def test_window_jobs_reads_the_recorded_api(monkeypatch):
    monkeypatch.setattr(health, "gh_get", recorded("health_actions_2026-10-15_midday.json"))
    steps, frozen = health.window_jobs(at(OCT15, 11, 5))
    by = {(s["workflow"], s["account"]): s for s in steps}
    assert by[("paper-window-push.yml", "options")]["status"] is None          # waiting for the paper-options group
    assert by[("paper-window-push.yml", "options")]["job_status"] == "pending"
    assert by[("paper-window-push.yml", "long")]["status"] == "in_progress"
    assert by[("paper-window-push.yml", "long")]["started"] == datetime.datetime(2026, 10, 15, 10, 48, 53, tzinfo=ET)
    assert by[("paper-window.yml", "options")]["started"].strftime("%H:%M") == "10:24"
    assert [a for a, _ in frozen] == ["long", "long"]          # both paper-options runs were cancelled while pending


def test_oct14_replay_is_amber_only_frozen_runs(monkeypatch):
    """10-14: the four afternoon cron starts of the window runner began 17:00-18:18 ET; the frozen paper-options runs
    landed 14:46, 14:52, 15:16, 15:46. The brief: only frozen coverage is AMBER, not RED."""
    monkeypatch.setattr(health, "gh_get", recorded("health_actions_2026-10-14.json"))
    red, amber, info = health.paper_window(at(OCT14, 14, 46))       # the push-started health run: nothing yet
    assert any(x.startswith("PAPER WINDOW NOT COVERED (options): window steps today ran 11:04-12:00 ET") for x in red)
    for h, m, last in ((15, 20, "15:16"), (16, 20, "15:46")):
        red, amber, info = health.paper_window(at(OCT14, h, m))
        assert not red
        mine = [x for x in amber if "(options)" in x]
        assert len(mine) == 1 and mine[0].startswith("PAPER WINDOW NOT RUNNING (options)")
        assert f"last {last} ET" in mine[0] and "window steps today ran 11:04-12:00 ET" in mine[0]
    # the 17:00 ET cron start, replayed at 17:30: the window is over and the frozen runs stopped at 15:46
    red, amber, info = health.paper_window(at(OCT14, 17, 30))
    assert any("NOT RUNNING (options)" in x and "the window is over" in x for x in amber)


def test_oct14_without_the_frozen_runs_is_red(monkeypatch):
    rec = recorded("health_actions_2026-10-14.json")
    monkeypatch.setattr(health, "gh_get", lambda p, q=None: {"workflow_runs": []} if "paper-options" in p
                        or "paper-long" in p else rec(p, q))
    red, amber, info = health.paper_window(at(OCT14, 15, 20))
    assert any(x.startswith("PAPER WINDOW NOT COVERED (options)") and "dispatch paper-window-push.yml" in x
               for x in red)


def test_on_time_window_is_green_through_the_end():
    s = [step("options", at(OCT16, 12, 0)), step("long", at(OCT16, 10, 48))]
    for h, m in ((14, 40), (15, 20), (15, 55)):
        assert health.window_coverage(at(OCT16, h, m), s, [])[:2] == ([], [])
    done = [step("options", at(OCT16, 12, 0), at(OCT16, 15, 56)), step("long", at(OCT16, 10, 48), at(OCT16, 15, 57))]
    red, amber, info = health.window_coverage(at(OCT16, 16, 20), done, [])
    assert not red and not amber and all("(done)" in x for x in info)


def test_late_start_is_amber_and_an_early_end_is_red():
    late = [step("options", at(OCT16, 14, 49)), step("long", at(OCT16, 10, 48))]
    red, amber, info = health.window_coverage(at(OCT16, 15, 20), late, [])
    assert not red and len(amber) == 1 and amber[0].startswith("PAPER WINDOW LATE (options)") and "14:49" in amber[0]
    crashed = [step("options", at(OCT16, 12, 0), at(OCT16, 15, 0), "completed"), step("long", at(OCT16, 10, 48))]
    red, amber, info = health.window_coverage(at(OCT16, 15, 20), crashed, [])
    assert len(red) == 1 and "NOT COVERED (options)" in red[0] and "ran 12:00-15:00 ET" in red[0]


def test_morning_step_and_a_waiting_job_do_not_cover():
    s = [step("options", at(OCT16, 10, 24), at(OCT16, 12, 0), wf="paper-window.yml"),
         {"account": "options", "workflow": "paper-window-push.yml", "url": "u", "job_status": "pending",
          "status": None, "started": None, "completed": None}, step("long", at(OCT16, 10, 48))]
    red, amber, info = health.window_coverage(at(OCT16, 14, 46), s, [])
    assert len(red) == 1 and "ran 10:24-12:00 ET" in red[0] and "1 window job(s) not yet in their afternoon step" in red[0]


def test_frozen_runs_count_only_if_recent_and_in_the_window():
    s = [step("long", at(OCT16, 10, 48))]
    old = [("options", at(OCT16, 14, 50))]                        # 30 min before 15:20: two fires missed
    assert health.window_coverage(at(OCT16, 15, 20), s, old)[0]
    fresh = [("options", at(OCT16, 15, 2))]
    red, amber, info = health.window_coverage(at(OCT16, 15, 20), s, fresh)
    assert not red and "only the frozen paper-options.yml runs" in amber[0]
    morning = [("options", at(OCT16, 11, 40))]                    # before 14:27: not the window
    assert health.window_coverage(at(OCT16, 14, 50), s, morning)[0]


def test_silent_before_1440_on_weekends_and_early_closes(monkeypatch):
    monkeypatch.setattr(health, "window_jobs", lambda now: pytest.fail("no API call expected"))
    for now in (at(OCT16, 14, 39), at(datetime.date(2026, 10, 17), 15, 20), at(datetime.date(2026, 11, 27), 15, 20)):
        assert health.paper_window(now) == ([], [], [])


def test_unreadable_api_is_amber(monkeypatch):
    monkeypatch.setattr(health, "window_jobs", lambda now: None)
    assert health.paper_window(at(OCT16, 15, 20)) == ([], ["paper window coverage unreadable (GitHub Actions API)"], [])


def test_api_failure_reads_as_unreadable(monkeypatch):
    def boom(path, params=None):
        raise OSError("HTTP 403")
    monkeypatch.setattr(health, "gh_get", boom)
    assert health.window_jobs(at(OCT16, 15, 20)) is None


# ---------------------------------------------------------------- positions vs ledgers
def dpz():
    return copy.deepcopy(json.load(open(os.path.join(FIX, "health_dpz_trade.json"), encoding="utf-8"))["trade"])


def ledger(*trades):
    return {"trades": {t["key"]: t for t in trades}}


def pos(symbol, qty, side=None):
    return {"symbol": symbol, "qty": str(qty), "side": side or ("short" if qty < 0 else "long")}


FLY = [pos(C310, -1), pos(P310, -1), pos(C360, 1), pos(P260, 1)]
R8 = {"id": "d973db48-f552-4e09-ae3a-29b8c026734c", "client_order_id": "seasonA-DPZ-2026-10-13-F-close-r8",
      "status": "new", "order_class": "mleg", "symbol": "", "legs": [{"symbol": s} for s in (C310, P310, C360, P260)]}


def options_only(led):
    return {"options_ledger.json": led, "ledger.json": None}


def test_terminal_matches_the_frozen_code():
    assert set(health.TERMINAL) == set(paper_options.TERMINAL)


def test_dpz_as_recorded_matches():
    red, amber, info = health.reconcile("options", (FLY, [R8]), options_only(ledger(dpz())), T15)
    assert not red and not amber and any("4 position(s), 1 open order(s) - they match" in x for x in info)


def test_short_quantity_sign_either_convention():
    signed = [pos(C310, -1, "short"), pos(P310, 1, "short"), pos(C360, 1), pos(P260, 1)]
    assert not health.reconcile("options", (signed, [R8]), options_only(ledger(dpz())), T15)[0]


def test_assigned_shares_are_red():
    red, _, _ = health.reconcile("options", (FLY + [pos("DPZ", 100)], [R8]), options_only(ledger(dpz())), T15)
    assert list(red.values()) == ["POSITION NOT IN LEDGER: paper/options DPZ: the account holds +100, the ledgers "
                                  "show +0"]


def test_ledger_position_missing_from_the_account_is_red():
    t = dpz()
    t["orders"]["close"][-1]["status"] = "canceled"            # nothing live, so no lag excuse
    red, _, _ = health.reconcile("options", ([], []), options_only(ledger(t)), T15)
    assert len(red) == 4 and all(m.startswith("LEDGER POSITION NOT IN ACCOUNT") for m in red.values())


def test_a_live_ledger_order_excuses_a_mismatch_only_while_young():
    """The close r8 (sent 10-15 10:24) filled at Alpaca after the last paper run: the account is flat, the ledger still
    shows r8 new. Lag for 30 minutes (info); then the ledger is not being refreshed (AMBER); after 24 h, RED."""
    red, amber, info = health.reconcile("options", ([], []), options_only(ledger(dpz())), at(OCT15, 10, 40))
    assert not red and not amber and sum("ledger lags the broker" in x for x in info) == 4
    assert any("seasonA-DPZ-2026-10-13-F-close-r8" in x and "no longer open at Alpaca" in x for x in info)
    red, amber, info = health.reconcile("options", ([], []), options_only(ledger(dpz())), T15)
    assert not red and len(amber) == 4 and all("sent Thu 10:24 ET" in x and "not refreshed" in x for x in amber)
    red, amber, info = health.reconcile("options", ([], []), options_only(ledger(dpz())), at(OCT16, 10, 30))
    assert len(red) == 4 and all(m.startswith("LEDGER STALE: paper/options DPZ261016") for m in red.values())


def test_shares_lag_allows_the_twice_a_day_sync():
    shares = {"trades": {"k": {"ticker": "NOC", "buy": {"client_order_id": "b", "status": "accepted",
                                                         "submitted_et": "2026-10-15T20:15:00-04:00",
                                                         "filled_qty": "0"}}}}
    books = {"options_ledger.json": ledger(), "ledger.json": shares}
    filled = [pos("NOC", 10)]                    # filled at the 10-16 open, recorded at 20:15
    red, amber, info = health.reconcile("options", (filled, []), books, at(OCT16, 15, 20))
    assert not red and not amber
    assert health.reconcile("options", (filled, []), books, at(OCT19, 10, 0))[0]       # 62 h: RED


def test_young_unknown_order_is_information():
    o = {"id": "z", "client_order_id": "seasonA-NOC-2026-10-19-F-open", "status": "new", "symbol": "",
         "legs": [{"id": "z1", "symbol": "NOC261023C00500000"}], "submitted_at": "2026-10-16T19:10:00Z"}
    red, amber, info = health.reconcile("options", ([], [o]), options_only(ledger()), at(OCT16, 15, 20))
    assert not red and any("not in a committed ledger yet" in x for x in info)
    assert health.reconcile("options", ([], [o]), options_only(ledger()), at(OCT16, 15, 40))[0]


def test_nested_children_listed_on_their_own_are_skipped():
    child = {"id": "leg-1", "client_order_id": "", "status": "new", "symbol": C310, "legs": None}
    r8 = dict(R8, legs=[{"id": "leg-1", "symbol": C310}] + [{"symbol": s} for s in (P310, C360, P260)])
    red, amber, info = health.reconcile("options", (FLY, [r8, child]), options_only(ledger(dpz())), T15)
    assert not red


def test_unknown_and_ended_open_orders_are_red():
    stray = {"id": "x1", "client_order_id": "manual-1", "status": "new", "symbol": "AAPL", "legs": None}
    t = dpz()
    t["orders"]["close"][-1]["status"] = "canceled"
    red, _, _ = health.reconcile("options", (FLY, [R8, stray]), options_only(ledger(t)), T15)
    msgs = sorted(red.values())
    assert msgs[0].startswith("OPEN ORDER NOT IN LEDGER: paper/options manual-1 (AAPL; new)")
    assert msgs[1].startswith("OPEN ORDER THE LEDGER SHOWS AS ENDED") and "ledger status canceled" in msgs[1]


def test_v3_close_with_a_dropped_leg_leaves_that_leg_held():
    t = dpz()
    t["exec"] = "v3"
    t["orders"]["close"] = [{
        "client_order_id": "seasonA-DPZ-2026-10-13-F-close", "id": "c1", "status": "filled", "filled_qty": 1.0,
        "exec": "v3", "dropped_legs": [{"symbol": P260, "bid": 0, "ask": 0.12}],
        "sides": {C310: "buy", P310: "buy", C360: "sell"}, "all_sides": {C310: "buy", P310: "buy", C360: "sell",
                                                                         P260: "sell"},
        "legs_filled": [{"symbol": C310, "side": "buy", "qty": 1.0, "price": 0.5},
                        {"symbol": P310, "side": "buy", "qty": 1.0, "price": 7.0},
                        {"symbol": C360, "side": "sell", "qty": 1.0, "price": 0.01}]}]
    red, amber, info = health.reconcile("options", ([pos(P260, 1)], []), options_only(ledger(t)), T15)
    assert not red and not amber
    assert health.reconcile("options", ([], []), options_only(ledger(t)), T15)[0]       # P260 missing: RED


def test_expired_options_are_not_expected_and_a_leftover_is_amber():
    red, amber, info = health.reconcile("options", ([], []), options_only(ledger(dpz())), T19)
    assert not red and not amber
    red, amber, info = health.reconcile("options", ([pos(P310, -1)], []), options_only(ledger(dpz())), T19)
    assert not red and len(amber) == 1 and "after its expiry 2026-10-16" in amber[0]


def test_expiry_evening_removal_is_not_red():
    """Fri 10-16 after the close: Alpaca may remove DPZ's expiring legs that evening while the ledger still lists
    them and its last close shows expired. Before the close they are still expected."""
    t = dpz()
    t["orders"]["close"][-1]["status"] = "expired"
    assert health.reconcile("options", ([], []), options_only(ledger(t)), at(OCT16, 15, 30))[0]
    for h, m in ((16, 0), (17, 15), (23, 30)):
        red, amber, info = health.reconcile("options", ([], []), options_only(ledger(t)), at(OCT16, h, m))
        assert not red and not amber
        assert not health.reconcile("options", (FLY, []), options_only(ledger(t)), at(OCT16, h, m))[0]


def test_unreadable_leg_fill_is_amber_not_red():
    t = dpz()
    t["orders"]["open"][0]["legs_filled"][0]["qty"] = 0.0     # fill_net's rule: leg qty must equal the order's
    t["orders"]["close"][-1]["status"] = "canceled"
    red, amber, info = health.reconcile("options", (FLY, []), options_only(ledger(t)), T15)
    assert not red and any("cannot be read" in x for x in amber)


def test_shares_ledger_shares_the_options_account():
    """paper.py's T0 shares trade on the APCA_* account too (paper/ledger.json)."""
    shares = {"trades": {"seasonA-NOC-2026-10-20": {
        "ticker": "BRK-B", "buy": {"client_order_id": "b", "status": "filled", "filled_qty": "41"},
        "sell": {"client_order_id": "s", "status": "accepted", "filled_qty": "0"}}}}
    sell = {"id": "o2", "client_order_id": "s", "status": "accepted", "symbol": "BRK.B"}
    red, amber, info = health.reconcile("options", ([pos("BRK.B", 41)], [sell]),
                                        {"options_ledger.json": ledger(), "ledger.json": shares}, T16)
    assert not red and not amber
    shares["trades"]["seasonA-NOC-2026-10-20"]["sell"]["status"] = "expired"
    red, _, _ = health.reconcile("options", ([], []), {"options_ledger.json": ledger(), "ledger.json": shares}, T16)
    assert list(red.values()) == ["LEDGER POSITION NOT IN ACCOUNT: paper/options BRK.B: the account holds +0, the "
                                  "ledgers show +41"]


def test_orphan_order_is_known_but_its_fill_is_red():
    orphan = {"key": "seasonA-RTX-2026-10-20-F", "ticker": "RTX", "orphan_order": {"id": "o9", "status": "filled"}}
    red, _, _ = health.reconcile("options", ([pos("RTX261023C00180000", -2)], []),
                                 options_only(ledger(orphan)), T16)
    assert list(red) == [("options", "position", "RTX261023C00180000")]


def test_red_needs_a_second_look():
    looks = iter([(FLY + [pos("DPZ", 100)], [R8]), (FLY, [R8])])
    slept = []
    red, amber, info = health.positions_check(
        at(OCT15, 15, 20), state=lambda a: next(looks) if a == "options" else ([], []),
        read=lambda names: {n: ledger(dpz()) if n == "options_ledger.json" else None for n in names},
        sleep=slept.append)
    assert not red and slept == [120] and any(x.startswith("cleared on a second look 120 s later") for x in info)
    red, amber, info = health.positions_check(
        at(OCT15, 15, 20), state=lambda a: (FLY + [pos("DPZ", 100)], [R8]) if a == "options" else ([], []),
        read=lambda names: {n: ledger(dpz()) if n == "options_ledger.json" else None for n in names},
        sleep=slept.append)
    assert red == ["POSITION NOT IN LEDGER: paper/options DPZ: the account holds +100, the ledgers show +0"]


def test_no_sleep_when_everything_matches_and_unreadable_accounts(monkeypatch):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    red, amber, info = health.positions_check(
        at(OCT15, 15, 20), state=lambda a: None if a == "long" else "unconfigured",
        read=lambda names: pytest.fail("no ledger read for an unread account"),
        sleep=lambda s: pytest.fail("no second look"))
    assert not red and amber == ["paper/long: Alpaca positions / orders unreadable - not reconciled"]
    assert info == ["paper/options: no Alpaca keys here - positions not reconciled"]
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    red, amber, info = health.positions_check(at(OCT15, 15, 20), state=lambda a: "unconfigured", read=None,
                                              sleep=lambda s: pytest.fail("no second look"))
    assert len(amber) == 2 and not info


def test_alpaca_state_without_keys(monkeypatch):
    for k in ("APCA_API_KEY_ID", "APCA_API_SECRET_KEY"):
        monkeypatch.delenv(k, raising=False)
    assert health.alpaca_state("options") == "unconfigured"


def test_read_ledgers_falls_back_to_the_working_copy(tmp_path, monkeypatch):
    monkeypatch.setattr(health, "ROOT", str(tmp_path))         # not a git repository: git fetch fails
    (tmp_path / "paper").mkdir()
    (tmp_path / "paper" / "options_ledger.json").write_text(json.dumps(ledger(dpz())), encoding="utf-8")
    (tmp_path / "paper" / "long_ledger.json").write_text("{not json", encoding="utf-8")
    got = health.read_ledgers(("options_ledger.json", "long_ledger.json", "ledger.json"))
    assert got["options_ledger.json"]["trades"] and got["long_ledger.json"] == "unreadable" and got["ledger.json"] is None
    red, amber, info = health.reconcile("long", ([], []), {"long_ledger.json": "unreadable"}, T15)
    assert amber == ["paper/long: paper/long_ledger.json is not readable JSON"]


# ---------------------------------------------------------------- review follow-ups (Sonnet, 2026-10-15)
def test_a_step_that_already_ended_inside_the_window_does_not_cover():
    """A late morning-mode paper-window.yml fire whose step ran 14:44:00-14:44:02 is no coverage at 14:45:20."""
    blip = [step("options", at(OCT16, 14, 44), at(OCT16, 14, 44) + datetime.timedelta(seconds=2),
                 wf="paper-window.yml"), step("long", at(OCT16, 10, 48))]
    red, amber, info = health.window_coverage(at(OCT16, 14, 45) + datetime.timedelta(seconds=20), blip, [])
    assert len(red) == 1 and "NOT COVERED (options)" in red[0]


def test_deadline_boundary_and_running_after_the_end():
    s = [step("options", at(OCT16, 14, 45)), step("long", at(OCT16, 14, 45) + datetime.timedelta(seconds=1))]
    red, amber, info = health.window_coverage(at(OCT16, 15, 0), s, [])
    assert not red and len(amber) == 1 and "LATE (long)" in amber[0]
    red, amber, info = health.window_coverage(at(OCT16, 16, 5), [step("options", at(OCT16, 12, 0)),
                                                                 step("long", at(OCT16, 12, 0))], [])
    assert not red and not amber


def test_uncovered_window_is_amber_once_over():
    for h, m in ((16, 20), (17, 15), (23, 30)):
        red, amber, info = health.window_coverage(at(OCT16, h, m), [], [])
        assert not red and len(amber) == 2 and all("the window is over" in x for x in amber)


def test_window_step_patterns_match_the_workflow_files():
    import yaml
    wfdir = os.path.join(os.path.dirname(__file__), "..", ".github", "workflows")
    for wf, pattern in health.WINDOW_STEPS.items():
        doc = yaml.safe_load(open(os.path.join(wfdir, wf), encoding="utf-8"))
        job = doc["jobs"]["window"]                       # GitHub names the matrix jobs "window (options)" / "(long)"
        assert "name" not in job and job["strategy"]["matrix"]["account"] == ["options", "long"]
        names = [st.get("name") or "" for st in job["steps"]]
        assert sum(bool(re.match(pattern, n)) for n in names) == 1, (wf, names)
        assert any("paper_window.py" in (st.get("run") or "") for st in job["steps"]
                   if re.match(pattern, st.get("name") or ""))
    for wf in health.FROZEN_PAPER.values():
        assert os.path.exists(os.path.join(wfdir, wf))


def test_gh_get_retries_once(monkeypatch):
    import requests
    calls = []

    class R:
        def __init__(self, code):
            self.status_code = code

        def json(self):
            return {"ok": 1}
    monkeypatch.setattr(requests, "get", lambda *a, **k: calls.append(1) or R(502 if len(calls) == 1 else 200))
    monkeypatch.setattr(health.time, "sleep", lambda s: None)
    assert health.gh_get("x") == {"ok": 1} and len(calls) == 2
    calls.clear()
    monkeypatch.setattr(requests, "get", lambda *a, **k: calls.append(1) or R(502))
    with pytest.raises(OSError):
        health.gh_get("x")
    assert len(calls) == 2


def test_alpaca_state_unreadable_shapes(monkeypatch):
    import requests
    monkeypatch.setenv("APCA_API_KEY_ID", "k")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "s")

    class R:
        def __init__(self, code, body):
            self.status_code, self.body = code, body

        def json(self):
            return self.body
    for code, body in ((401, {"message": "unauthorized"}), (200, {"code": 1}), (503, None)):
        monkeypatch.setattr(requests, "get", lambda *a, _c=code, _b=body, **k: R(_c, _b))
        assert health.alpaca_state("options") is None
    monkeypatch.setattr(requests, "get", lambda *a, **k: R(200, []))
    assert health.alpaca_state("options") == ([], [])


def test_unreadable_on_the_second_look_is_amber_not_red():
    looks = iter([(FLY + [pos("DPZ", 100)], [R8]), None])
    red, amber, info = health.positions_check(
        T15, state=lambda a: next(looks) if a == "options" else ([], []),
        read=lambda names: {n: ledger(dpz()) if n == "options_ledger.json" else None for n in names},
        sleep=lambda s: None)
    assert not red and any(x.startswith("seen once, the account was unreadable on the second look: POSITION NOT IN")
                           for x in amber)


def test_a_crashing_check_is_amber_and_run_still_reports(tmp_path, monkeypatch):
    monkeypatch.setattr(health, "ROOT", str(tmp_path))
    monkeypatch.setattr(health, "check_py", lambda: ("PASS - 0 warning(s)", [], 0))
    monkeypatch.setattr(health, "actions_failures", lambda now: [])
    monkeypatch.setattr(health, "window_jobs", lambda now: ([], []))
    monkeypatch.setattr(health, "alpaca_state", lambda acct: ([{"symbol": "X", "qty": "abc"}], []))
    monkeypatch.setattr(health, "read_ledgers", lambda names: {n: None for n in names})
    status, red, amber, info = health.run(now=at(OCT16, 15, 20))
    assert status == "RED" and sum("PAPER WINDOW NOT COVERED" in x for x in red) == 2      # window: RED end to end
    assert any(x.startswith("positions_check crashed: ValueError") for x in amber)


def test_recorded_live_shape_matches_the_ledger():
    """The real account at 10-15 11:38 ET (dry dispatch run 38762134094): one rolled-up mleg close, four legs held.
    The DPZ fixture's ledger stops at close r8, so r12 is added as the ledger had it then (live, status new)."""
    live = json.load(open(os.path.join(FIX, "health_alpaca_shapes_2026-10-15.json"), encoding="utf-8"))
    t = dpz()
    t["orders"]["close"][-1]["status"] = "canceled"
    t["orders"]["close"].append({"client_order_id": "seasonA-DPZ-2026-10-13-F-close-r12", "id": "fa4322ae",
                                 "sent_et": "2026-10-15T11:37:09-04:00", "status": "new", "filled_qty": 0.0,
                                 "sides": {C310: "buy", P310: "buy", C360: "sell", P260: "sell"}, "legs_filled": []})
    red, amber, info = health.reconcile("options", (live["positions"], live["open_orders"]),
                                        options_only(ledger(t)), at(OCT15, 11, 38))
    assert not red and not amber and any("4 position(s), 1 open order(s) - they match" in x for x in info)
