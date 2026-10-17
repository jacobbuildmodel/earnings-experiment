"""D011 report views: paper orders against real OPRA prints (pipeline/paper_fill_recheck.py). Offline: the API is a
fake whose answers have the shapes recorded by the live probe (ops/probes/alpaca_options_history_2026-10-16.json);
the orders are real records from tests/fixtures/paper_ledgers_2026-10-16.json.
Run: python -m pytest tests/test_paper_fill_recheck.py -q"""
import copy
import datetime
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
import paper_fill_recheck as rc  # noqa: E402
from common import ET  # noqa: E402

HERE = os.path.dirname(__file__)
FX = json.load(open(os.path.join(HERE, "fixtures", "paper_ledgers_2026-10-16.json"), encoding="utf-8"))
NOC_F_OPEN = FX["PX-F"]["trades"]["seasonA-NOC-2026-10-20-F"]["orders"]["open"][0]     # filled 18:33:10.38Z
NOC_L_R1 = FX["PX-L"]["trades"]["seasonA-NOC-2026-10-20-L"]["orders"]["open"][1]       # unfilled, cancel 15:37 ET
C515, P515, C595, P435 = "NOC261120C00515000", "NOC261120P00515000", "NOC261120C00595000", "NOC261120P00435000"


@pytest.fixture(autouse=True)
def fast(monkeypatch):
    monkeypatch.setattr(rc, "PAUSE_S", 0)


def write_ledgers(root, led=None):
    led = led or FX
    (root / "paper").mkdir(exist_ok=True)
    for acct, name in (("PX-F", "options_ledger.json"), ("PX-L", "long_ledger.json")):
        (root / "paper" / name).write_text(json.dumps(led[acct]), encoding="utf-8")


class Fake:
    """Alpaca market data with the probe's shapes; fail = {symbol} answers `code`; pages = split answers in two."""
    def __init__(self, fail=(), pages=False, code=500):
        self.calls, self.fail, self.pages, self.code = [], set(fail), pages, code

    def __call__(self, url, params):
        self.calls.append((url, dict(params)))
        sym = params["symbols"]
        if sym in self.fail:
            return self.code, {"message": "refused"}, '{"message":"refused"}'
        field = "bars" if url.endswith("/bars") else "trades"
        row = ({"c": 1.0, "h": 1.2, "l": 0.9, "n": 1, "o": 1.0, "t": params["start"][:17] + "00Z", "v": 1, "vw": 1.0}
               if field == "bars" else {"c": "a", "p": 1.0, "s": 1, "t": params["start"], "x": "C"})
        if self.pages and "page_token" not in params:
            return 200, {field: {sym: [row]}, "next_page_token": "p2"}, ""
        return 200, {field: {sym: [row] if sym != C595 else []}, "next_page_token": None}, ""


# ---------------------------------------------------------------- windows
def test_windows_of_a_filled_order():
    w = rc.windows(NOC_F_OPEN)
    assert rc.z(w["bars"][0]) == "2026-10-16T18:03:10Z" and rc.z(w["bars"][1]) == "2026-10-16T19:03:10Z"
    assert rc.z(w["trades"][0]) == "2026-10-16T18:18:10Z" and rc.z(w["trades"][1]) == "2026-10-16T18:48:10Z"


def test_live_window_of_an_unfilled_order():
    s, e = rc.live_window(NOC_L_R1)
    assert rc.z(s) == "2026-10-16T18:51:37Z" and rc.z(e) == "2026-10-16T19:39:28Z"      # cancel 15:37:28 + 2 min
    r = dict(NOC_L_R1, status="expired")
    r.pop("cancel_requested")
    assert rc.z(rc.live_window(r)[1]) == "2026-10-16T20:00:00Z"                         # the 16:00 ET close (EDT)
    est = dict(r, sent_et="2026-11-05T15:50:00-05:00")
    assert rc.z(rc.live_window(est)[1]) == "2026-11-05T21:00:00Z"                       # 16:00 EST
    late = dict(NOC_L_R1, cancel_requested="2026-10-19T10:00:00-04:00")                 # cancelled next day
    assert rc.z(rc.live_window(late)[1]) == "2026-10-16T20:00:00Z"


def test_nanosecond_timestamps_parse():
    assert rc.z(rc.utc("2026-10-16T18:48:05.614670775Z")) == "2026-10-16T18:48:05Z"


# ---------------------------------------------------------------- fetch
FRI_EVE = datetime.datetime(2026, 10, 16, 20, 45, tzinfo=ET)
SAT_AM = datetime.datetime(2026, 10, 17, 9, 0, tzinfo=ET)


def stored(root):
    return sorted(p.name for p in (root / "paper" / "fill_recheck" / "seasonA").glob("*.json"))


def test_fetch_waits_twelve_hours_and_writes_once(tmp_path):
    write_ledgers(tmp_path)
    fake = Fake()
    assert rc.fetch("seasonA", get=fake, now=FRI_EVE, root=tmp_path) == 0
    done = stored(tmp_path)
    # Fri 20:45 ET: only windows that ended 12+ hours earlier (DPZ's open and its closes up to 10-15)
    assert "seasonA-DPZ-2026-10-13-F-open.json" in done and "seasonA-DPZ-2026-10-13-F-close-r18.json" in done
    assert "seasonA-DPZ-2026-10-13-F-close-r19.json" not in done and "seasonA-NOC-2026-10-20-F-open.json" not in done
    n = len(fake.calls)
    assert rc.fetch("seasonA", get=fake, now=SAT_AM, root=tmp_path) == 0
    after = stored(tmp_path)
    assert len(after) == 36 and set(done) < set(after)
    d = tmp_path / "paper" / "fill_recheck" / "seasonA"
    new = [json.loads((d / f).read_text()) for f in set(after) - set(done)]
    # nothing already stored is fetched again: the second run's calls are exactly the new files' legs
    assert len(fake.calls) - n == sum(len(x["legs"]) * (2 if x["kind"] == "filled" else 1) for x in new)
    got = json.loads((d / "seasonA-NOC-2026-10-20-F-open.json").read_text())
    assert got["kind"] == "filled" and sorted(got["legs"]) == sorted([C515, P515, C595, P435])
    assert got["legs"][C595] == {"bars": [], "trades": []}            # no print: stored empty, never filled in
    un = json.loads((d / "seasonA-NOC-2026-10-20-L-open-r1.json").read_text())
    assert un["kind"] == "unfilled" and "trades" not in un["legs"][C515]
    assert un["window_utc"] == {"bars": ["2026-10-16T18:51:37Z", "2026-10-16T19:39:28Z"], "trades": None}
    assert rc.fetch("seasonA", get=fake, now=SAT_AM, root=tmp_path) == 0 and len(stored(tmp_path)) == 36


def test_a_failed_request_writes_nothing(tmp_path):
    write_ledgers(tmp_path)
    assert rc.fetch("seasonA", get=Fake(fail={P515}), now=SAT_AM, root=tmp_path) == 1
    d = tmp_path / "paper" / "fill_recheck" / "seasonA"
    assert not (d / "seasonA-NOC-2026-10-20-F-open.json").exists()        # retried by a later run
    assert (d / "seasonA-RTX-2026-10-20-F-open.json").exists()


def test_a_bad_request_is_stored_only_once_the_window_is_old(tmp_path):
    write_ledgers(tmp_path)
    refused = Fake(fail={P515}, code=400)
    assert rc.fetch("seasonA", get=refused, now=SAT_AM, root=tmp_path) == 1          # 1 day old: retried
    assert "seasonA-NOC-2026-10-20-F-open.json" not in stored(tmp_path)
    later = datetime.datetime(2026, 10, 20, 9, 0, tzinfo=ET)
    assert rc.fetch("seasonA", get=refused, now=later, root=tmp_path) == 0           # 3+ days: stored with its reason
    got = json.loads((tmp_path / "paper" / "fill_recheck" / "seasonA" / "seasonA-NOC-2026-10-20-F-open.json")
                     .read_text())
    assert got["legs"][P515]["bars"] is None and got["legs"][P515]["error"].startswith("HTTP 400")
    r = rc.compare_filled(NOC_F_OPEN, got)
    assert r["legs"][P515]["missing"].startswith("data refused: HTTP 400") and r["net_at_nearest_trades"] is None


@pytest.mark.parametrize("code", [401, 403, 408, 429, 500])
def test_account_and_transient_refusals_are_never_stored(tmp_path, code):
    """A 403 ("OPRA agreement is not signed") is about the account, not the contract: however old the window, nothing
    is written and the run stays red (second review, finding 1)."""
    write_ledgers(tmp_path)
    later = datetime.datetime(2026, 10, 25, 9, 0, tzinfo=ET)
    assert rc.fetch("seasonA", get=Fake(fail={P515}, code=code), now=later, root=tmp_path) == 1
    assert "seasonA-NOC-2026-10-20-F-open.json" not in stored(tmp_path)


def test_no_committing_fetch_inside_the_paper_window(tmp_path, monkeypatch):
    write_ledgers(tmp_path)
    fake = Fake()
    mon = datetime.datetime(2026, 10, 19, 15, 0, tzinfo=ET)
    assert rc.fetch("seasonA", commit=True, get=fake, now=mon, root=tmp_path) == 0 and not fake.calls
    assert rc.in_quiet(datetime.datetime(2026, 10, 19, 14, 0, tzinfo=ET))
    assert not rc.in_quiet(datetime.datetime(2026, 10, 19, 16, 5, tzinfo=ET))
    assert not rc.in_quiet(datetime.datetime(2026, 10, 17, 15, 0, tzinfo=ET))                 # Saturday
    assert rc.probe(commit=True, get=fake, now=mon) is None and not fake.calls


def test_commit_and_a_failed_push(tmp_path, monkeypatch):
    import freeze
    write_ledgers(tmp_path)
    seen = []
    monkeypatch.setattr(freeze, "git", lambda *a, **k: seen.append(a) or "")
    monkeypatch.setattr(freeze, "push_all", lambda: {"origin": False})
    assert rc.fetch("seasonA", commit=True, get=Fake(), now=SAT_AM, root=tmp_path) == 1     # a failed push is red
    assert seen[0][0] == "add" and len(seen[0]) == 37 and seen[1][0] == "commit"
    monkeypatch.setattr(freeze, "push_all", lambda: {"origin": True})
    assert rc.fetch("seasonA", commit=True, get=Fake(), now=SAT_AM, root=tmp_path) == 0     # nothing new: no commit


def test_pages_are_followed():
    rows, err, code = rc.paged(Fake(pages=True), rc.TRADES, {"start": "2026-10-16T18:00:00Z", "end": "x"}, "trades",
                               C515)
    assert err is None and code == 200 and len(rows) == 2


def test_a_fill_without_a_fill_time_is_not_fetched(tmp_path):
    led = copy.deepcopy(FX)
    led["PX-L"]["trades"]["seasonA-RTX-2026-10-20-L"]["orders"]["open"][0]["filled_at"] = None
    write_ledgers(tmp_path, led)
    cids = [r["client_order_id"] for _, _, _, r in rc.order_records("seasonA", tmp_path)]
    assert "seasonA-RTX-2026-10-20-L-open" not in cids and len(cids) == 35


def test_only_final_orders_with_an_id_are_fetched(tmp_path):
    led = copy.deepcopy(FX)
    t = led["PX-F"]["trades"]["seasonA-RTX-2026-10-20-F"]
    t["orders"]["close"] = [dict(copy.deepcopy(t["orders"]["open"][0]), client_order_id="x-close", status="new",
                                 filled_qty=0.0, filled_at=None),                       # live: not final
                            dict(copy.deepcopy(t["orders"]["open"][0]), client_order_id="x-close-r1", id=None,
                                 status="rejected", filled_qty=0.0, filled_at=None)]    # refused: never reached Alpaca
    write_ledgers(tmp_path, led)
    cids = [r["client_order_id"] for _, _, _, r in rc.order_records("seasonA", tmp_path)]
    assert "x-close" not in cids and "x-close-r1" not in cids and len(cids) == 36


# ---------------------------------------------------------------- compare
def test_compare_filled():
    cached = {"legs": {
        C515: {"bars": [{"t": "2026-10-16T18:33:00Z", "o": 18.9, "h": 19.2, "l": 18.6, "c": 19.0, "v": 3, "vw": 18.9}],
               "trades": [{"t": "2026-10-16T18:20:00Z", "p": 20.0, "x": "C", "c": "a"},
                          {"t": "2026-10-16T18:33:40.5Z", "p": 18.9, "x": "A", "c": "f"}]},
        P515: {"bars": [{"t": "2026-10-16T18:40:00Z", "o": 18.2, "h": 18.4, "l": 18.1, "c": 18.1, "v": 1, "vw": 18.2}],
               "trades": [{"t": "2026-10-16T18:40:00Z", "p": 18.1, "x": "C", "c": "a"}]},
        C595: {"bars": [], "trades": [{"t": "2026-10-16T18:34:00Z", "p": 2.8, "x": "C", "c": "a"}]},
        P435: {"bars": [], "trades": [{"t": "2026-10-16T18:33:10Z", "p": 3.3, "x": "C", "c": "a"}]}}}
    r = rc.compare_filled(NOC_F_OPEN, cached)
    a = r["legs"][C515]                                    # sold at 18.50; nearest print 18.90 (30.1 s later)
    assert a["nearest_trade"] == 18.9 and a["nearest_trade_dt_s"] == pytest.approx(30.1, abs=0.1)
    assert a["worse_by_vs_nearest_trade"] == pytest.approx(0.4) and a["nearest_trade_condition"] == "f"
    assert a["fill_minute_bar"]["l"] == 18.6 and a["paper_inside_range"] is False
    assert r["legs"][P515]["worse_by_vs_nearest_trade"] == pytest.approx(-0.4)   # sold at 18.50 above the 18.10 print
    assert r["legs"][P515]["paper_inside_range"] is False and r["legs"][P515]["fill_minute_bar"] is None
    assert r["legs"][C595]["worse_by_vs_nearest_trade"] == pytest.approx(0.2)    # bought at 3.00 over a 2.80 print
    assert r["legs"][C595]["range_bars"] is None and "paper_inside_range" not in r["legs"][C595]
    assert r["paper_net"] == pytest.approx(-30.7)
    assert r["net_at_nearest_trades"] == pytest.approx(-18.9 - 18.1 + 2.8 + 3.3)
    assert r["worse_by_vs_nearest_trades (not simultaneous)"] == pytest.approx(-30.7 + 30.9)
    assert r["max_leg_dt_s"] == pytest.approx(409.6, abs=0.1)        # the 515 put printed 6.8 min after the fill
    assert r["net_at_trades_within_60s"] is None and "worse_by_vs_trades_within_60s" not in r


def test_compare_filled_headline_needs_every_leg_within_60s():
    t = {"t": "2026-10-16T18:33:10Z", "x": "C", "c": "a"}
    cached = {"legs": {C515: {"bars": [], "trades": [dict(t, p=18.6)]}, P515: {"bars": [], "trades": [dict(t, p=18.4)]},
                       C595: {"bars": [], "trades": [dict(t, p=3.1)]}, P435: {"bars": [], "trades": [dict(t, p=3.3)]}}}
    r = rc.compare_filled(NOC_F_OPEN, cached)
    assert r["max_leg_dt_s"] == pytest.approx(0.4, abs=0.1)
    assert r["net_at_trades_within_60s"] == pytest.approx(-18.6 - 18.4 + 3.1 + 3.3)
    assert r["worse_by_vs_trades_within_60s"] == pytest.approx(-30.7 + 30.6)


def test_compare_filled_missing_prints_stay_missing():
    cached = {"legs": {C515: {"bars": [], "trades": []}}}
    r = rc.compare_filled(NOC_F_OPEN, cached)
    assert r["legs"][C515]["nearest_trade"] is None and r["legs"][P515]["missing"] == "not fetched"
    assert r["net_at_nearest_trades"] is None and "worse_by_vs_nearest_trades" not in r


def test_compare_unfilled():
    cached = {"legs": {C515: {"bars": [{"t": "2026-10-16T19:00:00Z", "l": 22.0, "h": 22.5}]},
                       P515: {"bars": [{"t": "2026-10-16T19:10:00Z", "l": 20.9, "h": 21.0}]}}}
    r = rc.compare_unfilled(NOC_L_R1, cached)               # bought at the indicative asks 22.43 + 20.48 = 42.91
    assert r["legs"][C515]["print_reached_far_side"] is True and r["legs"][P515]["print_reached_far_side"] is False
    assert r["best_net_from_prints"] == pytest.approx(42.9) and r["limit"] == pytest.approx(42.91)
    assert r["prints_reached_limit (not simultaneous)"] is True
    r2 = rc.compare_unfilled(NOC_L_R1, {"legs": {C515: {"bars": []}, P515: {"bars": []}}})
    assert r2["best_net_from_prints"] is None and r2["legs"][C515]["missing"] == "no real trade while the order was live"


def test_limit_net():
    assert rc.limit_net({"limit_price": "-30.14", "sides": {C515: "sell", P515: "sell"}}) == -30.14
    assert rc.limit_net({"limit_price": "4.50", "order_class": "simple", "sides": {P515: "sell"}}) == -4.50
    assert rc.limit_net({"limit_price": "4.50", "order_class": "simple", "sides": {P515: "buy"}}) == 4.50
    assert rc.limit_net({"sides": {}}) is None


# ---------------------------------------------------------------- the workflow
def test_the_workflow_is_safe_on_a_public_repo():
    import yaml
    wf = os.path.join(HERE, "..", ".github", "workflows")
    for name in os.listdir(wf):
        y = yaml.safe_load(open(os.path.join(wf, name), encoding="utf-8"))
        on = y.get(True) or y.get("on") or {}
        assert "pull_request" not in on and "pull_request_target" not in on, name   # no stranger's code gets secrets
    y = yaml.safe_load(open(os.path.join(wf, "paper-fill-recheck.yml"), encoding="utf-8"))
    job = y["jobs"]["recheck"]
    assert "env" not in job                                                          # keys on the data steps only
    for step in job["steps"]:
        if "APCA_API_KEY_ID" in (step.get("env") or {}):
            assert "paper_fill_recheck.py" in step["run"]
    assert any("sha256sum -c registry/D011_report_views_implementation_v1.sha256" in (s.get("run") or "")
               for s in job["steps"])
