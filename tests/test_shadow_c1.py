"""D015 C1 live shadow: the pure pieces of pipeline/shadow_c1.py on synthetic data (no network).
Run: python -m pytest tests/test_shadow_c1.py -q"""
import datetime
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "pipeline"))
import shadow_c1 as c  # noqa: E402
from common import ET  # noqa: E402

D = datetime.date


def test_expiry_strictly_after_R():
    # a Friday reaction with a weekly expiring that Friday takes the next week's (D010 §3)
    assert c.pick_expiry(["2026-10-16", "2026-10-23", "2026-11-20"], D(2026, 10, 16)) == "2026-10-23"
    assert c.pick_expiry(["2026-10-23", "2026-10-16"], D(2026, 10, 15)) == "2026-10-16"
    assert c.pick_expiry(["2026-10-16"], D(2026, 10, 16)) is None


def test_monthly_expiry_like_d010():
    exps = ["2026-10-16", "2026-10-23", "2026-10-30", "2026-11-20", "2026-12-18"]
    assert c.pick_expiry(exps, D(2026, 10, 16), monthly=True) == "2026-11-20"   # Oct 16 is a monthly but not after R
    assert c.pick_expiry(exps, D(2026, 10, 14), monthly=True) == "2026-10-16"
    assert c.pick_expiry(["2026-10-23", "2026-10-30"], D(2026, 10, 20), monthly=True) is None
    assert c.is_monthly("2026-11-20") and c.is_monthly("2026-10-16")
    assert not c.is_monthly("2026-10-23") and not c.is_monthly("2026-11-13")
    assert c.is_monthly("2026-06-18")             # Juneteenth 2026 is the third Friday: Thursday's expiry
    assert not c.is_monthly("2026-10-15")         # an ordinary Thursday


def test_strike_nearest_both_sides_tie_lower():
    assert c.pick_strike([95, 100, 105], [95, 100, 105], 101.0) == 100
    assert c.pick_strike([95, 100, 105], [95, 105], 101.0) == 105      # 100 has no put
    assert c.pick_strike([100, 110], [100, 110], 105.0) == 100        # tie -> lower
    assert c.pick_strike([], [100], 100.0) is None
    assert c.pick_strike([100], [100], None) is None


def test_implied_move_needs_two_live_quotes():
    call, put = {"bid": 2.0, "ask": 2.2}, {"bid": 1.8, "ask": 2.0}
    assert abs(c.implied_move(call, put, 100.0) - 0.04) < 1e-12
    assert c.implied_move({"bid": 0.0, "ask": 0.1}, put, 100.0) is None   # zero bid
    assert c.implied_move({"bid": 2.2, "ask": 2.0}, put, 100.0) is None   # crossed
    assert c.implied_move({"bid": None, "ask": 2.0}, put, 100.0) is None
    assert c.implied_move(call, put, 0) is None


def test_capture_window_and_early_close():
    a, b = c.capture_window(D(2026, 10, 15))
    assert (a.hour, a.minute, b.hour, b.minute) == (15, 25, 15, 55)
    a, b = c.capture_window(D(2026, 11, 27))      # NYSE closes 13:00
    assert (a.hour, a.minute, b.hour, b.minute) == (12, 25, 12, 55)


def test_session_list_matches_fetch_indexing():
    R = D(2026, 10, 20)
    xs = c.session_list(R)
    i = xs.index(R)
    assert xs[i - 1] == D(2026, 10, 19)           # r1, the prior close
    assert len(xs[i - 20:i]) == 20 and all(x < R for x in xs[i - 20:i])
    assert xs[i - 20] == min(xs[i - 20:i])


def ev(R="2026-10-20", P="2026-10-19", exists=True):
    return {"ticker": "XYZ", "date": "2026-10-19", "session": "AMC", "industry": "Software", "marketCap": 5e9,
            "exists_before_entry": exists,
            "timing": {"entry": {"session": P}, "exit_A": {"session": R}}}


def prow(pm=105.0, c0=100.0, o=104.0, p30=102.0, pc=101.0, void=""):
    r = {"c0": c0, "o": o, "pm": pm, "pm_t": "2026-10-20T09:20:00-04:00", "o_t": "2026-10-20T09:30:00-04:00",
         "p5": 103.5, "p10": 103.0, "p30": p30, "p60": 101.5, "pc": pc, "void": void, "split_check": "ok",
         "hs0935": 0.001, "hs0940": 0.001, "hs1000": 0.001, "hs1030": 0.001,
         "mid0935": 103.5, "mid0940": 103.0, "mid1000": p30, "mid1030": 101.5,
         "spy_o": 500.0, "spy_p5": 500.0, "spy_p10": 500.0, "spy_p30": 501.0, "spy_p60": 500.0, "spy_pc": 500.0,
         "vw": 104.1, "hs_first": 0.002, "first_bid": 103.9, "first_ask": 104.3, "sec_status_at_fetch": "verified"}
    return r


REG = datetime.datetime(2026, 10, 14, 15, 0, tzinfo=ET)
CAP = {"status": "ok", "im": 0.03, "capture_committed": "2026-10-19T15:57:00-04:00", "R": "2026-10-20",
       "expiry": "2026-11-20", "days_after_R": 31, "call": {"bid": 1.0, "ask": 1.05}, "put": {"bid": 1.95, "ask": 2.0},
       "nearest": {"status": "ok", "im": 0.02, "expiry": "2026-10-23", "days_after_R": 3}}


def test_c1_flag_and_reversal_sign():
    r = c.event_row(ev(), CAP, REG, "verified", prow())
    assert r["graded"] and r["void"] is None
    assert abs(r["g"] - 0.05) < 1e-12 and r["s"] == 1
    assert r["c1"] is True                                   # 5% > 3%
    assert abs(r["y"]["30"] - (102.0 / 104.0 - 1)) < 1e-12  # negative: the gap reversed
    assert r["net_auction"]["30"] > 0                        # the fade earned
    assert r["net_retail"]["30"] is not None
    assert abs(r["im_rel_spread_max"] - 0.05 / 1.025) < 1e-12
    assert r["im_nearest"] == 0.02 and r["c1_nearest"] is True and r["im_days_after_R"] == 31


def test_gap_within_im_or_below_floor_is_not_c1():
    r = c.event_row(ev(), dict(CAP, im=0.06), REG, "verified", prow())
    assert r["graded"] and r["c1"] is False
    r = c.event_row(ev(), dict(CAP, im=0.001), REG, "verified", prow(pm=100.5))
    assert r["below_floor"] and r["c1"] is False


def test_gap_down_signs():
    r = c.event_row(ev(), CAP, REG, "verified", prow(pm=94.0, o=95.0, p30=97.0, pc=96.0))
    assert r["s"] == -1 and r["c1"] is True
    assert r["y"]["30"] < 0                                  # it bounced: a reversal is negative y


def test_void_order_and_im_timing():
    late = dict(CAP, capture_committed="2026-10-20T09:28:00-04:00")
    r = c.event_row(ev(), late, REG, "verified", prow())
    assert r["im_status"] == "im_late" and r["im"] is None and r["c1"] is False and r["graded"]
    r = c.event_row(ev(), None, REG, "verified", prow())
    assert r["im_status"] == "no_capture" and r["c1"] is False
    r = c.event_row(ev(), CAP, datetime.datetime(2026, 10, 20, 9, 31, tzinfo=ET), "verified", prow())
    assert r["void"] == "before_registration" and not r["graded"]
    r = c.event_row(ev(), CAP, None, "verified", prow())
    assert r["void"] == "before_registration"
    r = c.event_row(ev(exists=False), CAP, REG, "verified", prow())
    assert r["void"] == "not_committed_before_entry"
    r = c.event_row(ev(), CAP, REG, "contradicted", prow())
    assert r["void"] == "print_contradicted"
    r = c.event_row(ev(), CAP, REG, "foreign", prow())
    assert r["void"] == "not_domestic_foreign"
    r = c.event_row(ev(), CAP, REG, "verified", prow(void="no_premarket"))
    assert r["void"] == "no_premarket" and not r["graded"]
    r = c.event_row(ev(), CAP, REG, "verified", None)
    assert not r["graded"] and r["void"] is None              # not yet priced
    r = c.event_row(ev(), CAP, datetime.datetime(2026, 10, 19, 16, 0, tzinfo=ET), "verified", prow())
    assert r["im_status"] == "pre_registration" and r["im"] is None and r["c1"] is False
    r = c.event_row(ev(), dict(CAP, R="2026-10-21"), REG, "verified", prow())
    assert r["im_status"] == "mismatch" and r["im"] is None
    r = c.event_row(ev(), dict(CAP, expiry="2026-10-20"), REG, "verified", prow())
    assert r["im_status"] == "mismatch"
    r = c.event_row(ev(), CAP, REG, "sec_error HTTPError", prow(), today=D(2026, 10, 30))
    assert r["void"] == "sec_unresolved"                      # still failing after 10 days
    r = c.event_row(ev(), CAP, REG, "sec_error HTTPError", None, today=D(2026, 10, 21))
    assert r["void"] is None                                  # within patience: waits
    r = c.event_row(ev(), CAP, REG, "verified", dict(prow(), sec_status_at_fetch="sec_error X"))
    assert r["void"] == "sec_unresolved"                      # priced with no floor -> void


def rows(n, dates, y):
    return [{"graded": True, "c1": True, "R": f"2026-10-{10 + i % dates:02d}", "y": {"30": y + (0.01 if i % 2 else -0.01)}}
            for i in range(n)]


def test_tests_and_verdicts():
    assert c.cr1_test(rows(29, 12, -0.01))["status"] == "insufficient"
    assert c.cr1_test(rows(40, 9, -0.01))["status"] == "insufficient"
    t = c.cr1_test(rows(60, 15, -0.02))
    assert t["mean"] < 0 and t["p_one_sided"] < 0.001
    assert c.verdict(t, "season_A") == "CONFIRMED"
    assert c.verdict({"p_one_sided": 0.004}, "season_A") == "CONFIRMED"
    assert c.verdict({"p_one_sided": 0.006}, "season_A").startswith("not yet")
    assert c.verdict({"p_one_sided": 0.044}, "final") == "CONFIRMED"
    assert c.verdict({"p_one_sided": 0.046}, "final") == "NOT CONFIRMED"
    assert c.verdict({"status": "insufficient"}, "final") == "insufficient"
    assert c.verdict({"p_one_sided": 0.0001}, "interim") == "interim - no verdict"
    assert t["df"] == 14
    up = c.cr1_test(rows(60, 15, +0.02))
    assert up["p_one_sided"] > 0.999                          # one-sided: a continuation never confirms


def test_alpha_split():
    assert c.LOOK1_P + c.FINAL_P <= 0.05 + 1e-12


def test_drift_guard(tmp_path, monkeypatch):
    import hashlib
    lst = tmp_path / "list.sha256"
    lines = ["# test"]
    for rel in c.PINNED:
        data = open(os.path.join(ROOT, rel), "rb").read().replace(b"\r\n", b"\n")
        lines.append(f"{hashlib.sha256(data).hexdigest()}  {rel}")
    lst.write_text("\n".join(lines) + "\n", encoding="utf-8")
    monkeypatch.setattr(c, "IMPL_LIST", str(lst))
    c.drift()                                                 # matches: no exit
    lst.write_text("\n".join(lines[:-1] + ["0" * 64 + "  " + c.PINNED[-1]]) + "\n", encoding="utf-8")
    try:
        c.drift()
        assert False, "drift not caught"
    except SystemExit as exc:
        assert c.PINNED[-1] in str(exc)


def test_health_c1_capture_alarm(tmp_path, monkeypatch):
    import health
    (tmp_path / "registry").mkdir()
    monkeypatch.setattr(health, "ROOT", str(tmp_path))
    at = lambda y, m, d, h, mi: datetime.datetime(y, m, d, h, mi, tzinfo=ET)  # noqa: E731
    assert health.c1_capture_check(at(2026, 10, 15, 17, 0)) is None          # not registered yet: silent
    (tmp_path / "registry" / "D015_implementation_v1.sha256").write_text("x\n")
    assert "2026-10-15" in health.c1_capture_check(at(2026, 10, 15, 17, 0))  # after the close: today's
    assert "2026-10-14" in health.c1_capture_check(at(2026, 10, 15, 12, 0))  # before it: the previous session
    assert "2026-10-16" in health.c1_capture_check(at(2026, 10, 18, 9, 0))   # Sunday: Friday's
    (tmp_path / "shadow" / "c1" / "im").mkdir(parents=True)
    (tmp_path / "shadow" / "c1" / "im" / "2026-10-15.json").write_text("{}")
    assert health.c1_capture_check(at(2026, 10, 15, 17, 0)) is None
    assert health.c1_capture_check(at(2026, 10, 13, 17, 0)) is None          # before D015 existed


def test_fetch_prices_end_to_end_with_fake_alpaca(tmp_path, monkeypatch):
    """The grading wrapper around D014's frozen fetch code, on synthetic Alpaca responses (no network)."""
    import json as _json
    sys.path.insert(0, os.path.join(ROOT, "analysis", "d014"))
    import fetch
    R, r1 = D(2026, 10, 20), D(2026, 10, 19)
    z = lambda day, hh, mm: datetime.datetime(day.year, day.month, day.day, hh, mm, tzinfo=ET).astimezone(  # noqa: E731
        datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sessions = c.session_list(R)

    def minute_bars(sym, day, start, end):
        out = []
        if day == R:                                                  # R: pre-market and the session
            out.append({"t": z(R, 9, 20), "o": 105, "h": 105, "l": 105, "c": 105.0, "v": 5000, "vw": 105})
            px = {0: 104.0, 4: 103.5, 9: 103.0, 29: 102.0, 59: 101.5, 389: 101.0}
            last = 104.0
            for m in range(0, 390):
                last = px.get(m, last)
                t = datetime.datetime(R.year, R.month, R.day, 9, 30, tzinfo=ET) + datetime.timedelta(minutes=m)
                out.append({"t": t.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "o": last,
                            "h": last, "l": last, "c": last, "v": 1000, "vw": last + 0.1})
        if day == r1:                                                 # AMC after-hours, after the release
            out.append({"t": z(r1, 16, 30), "o": 106, "h": 106, "l": 106, "c": 106.0, "v": 3000, "vw": 106})
        return out

    def paged(path, params, key):
        syms = params["symbols"].split(",")
        if path == "auctions":
            return {s: [{"d": r1.isoformat(), "c": [{"p": 100.0, "s": 9000, "t": z(r1, 16, 0)}], "o": []},
                        {"d": R.isoformat(), "o": [{"p": 104.0, "s": 9000, "t": z(R, 9, 30)}],
                         "c": [{"p": 101.0, "s": 9000, "t": z(R, 16, 0)}]}] for s in syms}
        tf = params["timeframe"]
        if tf == "1Day":
            return {s: [{"t": z(x, 0, 0), "o": 100, "h": 100, "l": 100, "c": 100.0, "v": 1e6}
                        for x in sessions if x <= R] for s in syms}
        start = params["start"]
        day = R if start.startswith(R.isoformat()) else r1
        return {s: minute_bars(s, day, start, params["end"]) for s in syms}

    def get(path, params):
        return {"quotes": [{"bp": 99.9, "ap": 100.1}]} if path.endswith("/quotes") else None

    monkeypatch.setattr(fetch, "paged", paged)
    monkeypatch.setattr(fetch, "get", get)
    monkeypatch.setattr(fetch, "PAUSE", 0)
    monkeypatch.setattr(c, "ROOT", str(tmp_path))
    evs = [{"ticker": "XYZ", "date": "2026-10-19", "session": "AMC", "industry": "Software", "marketCap": 5e9}]
    tstore = {"XYZ_2026-10-19_AMC": {"status": "verified",
                                     "hits": [{"accepted_et": "2026-10-19T16:05:00-04:00", "window": "AMC"}]}}
    out = c.fetch_prices("seasonA", R.isoformat(), evs, tstore)
    row = out["rows"][0]
    assert row["void"] == "" and row["c0"] == 100.0 and row["o"] == 104.0 and row["pc"] == 101.0
    assert row["pm"] == 105.0                       # R pre-market beats the R-1 after-hours bar
    assert row["accepted_et"] == "2026-10-19T16:05:00-04:00"
    assert row["p30"] == 102.0 and row["r1"] == "2026-10-19"
    assert row["vw"] is not None and row["status"] == "ok"
    assert os.path.exists(c.price_path("seasonA", R.isoformat()))
    _json.dumps(out)                                 # storable
    r = c.event_row({**evs[0], "exists_before_entry": True,
                     "timing": {"entry": {"session": "2026-10-19"}, "exit_A": {"session": "2026-10-20"}}},
                    CAP, REG, "verified", row)
    assert r["graded"] and r["c1"] and abs(r["g"] - 0.05) < 1e-12
    assert abs(r["y"]["30"] - (102.0 / 104.0 - 1)) < 1e-12
    assert r["net_retail"]["c"] is not None and r["net_auction"]["c"] > 0
    assert c.fetch_prices("seasonA", R.isoformat(), evs, tstore) == out   # write-once: read back, not refetched


def test_student_t_against_tables():
    # textbook one-sided critical values
    assert abs(c.t_cdf(-2.797, 24) - 0.005) < 2e-4
    assert abs(c.t_cdf(-1.711, 24) - 0.05) < 2e-4
    assert abs(c.t_cdf(-2.228, 10) - 0.025) < 2e-4
    assert abs(c.t_cdf(2.228, 10) - 0.975) < 2e-4
    assert abs(c.t_cdf(0.0, 7) - 0.5) < 1e-12
    assert abs(c.t_cdf(-1.6449, 100000) - 0.05) < 2e-4        # -> normal


def test_looks_are_gated_and_written_once(tmp_path, monkeypatch):
    monkeypatch.setattr(c, "ROOT", str(tmp_path))
    try:
        c.look1(today=D(2026, 12, 6))
        assert False, "look 1 before its date"
    except SystemExit as exc:
        assert "2026-12-07" in str(exc)
    rows_ = rows(60, 15, -0.02)
    try:
        c.take_look("x", rows_, "season_A", "t", ready=False)
        assert False, "look taken while not ready"
    except SystemExit as exc:
        assert "not ready" in str(exc)
    paths = c.take_look("x", rows_, "season_A", "t", ready=True)
    assert all(os.path.exists(p) for p in paths)
    try:
        c.take_look("x", rows_, "season_A", "t", ready=True)
        assert False, "second look"
    except SystemExit as exc:
        assert "once" in str(exc)


def test_status_is_blind():
    r = c.event_row(ev(), CAP, REG, "verified", prow())
    txt = c.status_text("seasonA", [r], [])
    assert "mean" not in txt and "y_30" not in txt and '"c1": 1' in txt
