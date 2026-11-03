"""pipeline/stage1.py on synthetic data only (D017 §2: tested before its first run). No real outcome is read."""
import json
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pipeline"))
import report  # noqa: E402
import stage1  # noqa: E402

SESS = [f"2026-10-{d:02d}" for d in (1, 2, 5, 6, 7, 8, 9, 12, 13, 14, 15, 16, 19, 20, 21, 22)]


@pytest.fixture(autouse=True)
def fast_bootstrap(monkeypatch):
    monkeypatch.setattr(report, "B_WILD", 199)   # speed only; stage1 reads no p-value


def spy(step=1.0):
    return {s: 600.0 + step * i for i, s in enumerate(SESS)}, {}


def out_row(i, ret, k, t1="BUY", t2="BUY"):
    entry, exit_ = SESS[k], SESS[k + 1]
    return {"event": f"X{i}_{exit_}", "ticker": f"X{i}", "gate_status": "PASS", "graded": True, "void": None,
            "entry_session": entry, "cluster": "c", "flags": [], "t2_confidence": 0.55,
            "exits": {"exit_A": {"entry": 100.0, "entry_session": entry, "exit": 100.0 * (1 + ret),
                                 "exit_session": exit_, "raw_return": ret, "WIN_raw": ret > 0,
                                 "WIN_net": ret > 0.002, "flags": []}},
            "decisions": {"T0": "BUY", "T1": t1, "T2": t2, "T2G": t2}}


def sh_row(tr, i, ret, k):
    return {"track": tr, "ticker": f"{tr}{i}", "graded": True, "void": None, "flags": [], "vol60": 0.3 + i / 1000,
            "timing": {"entry": {"session": SESS[k]}, "exit_A": {"session": SESS[k + 1]}},
            "exit_A": {"raw_return": ret, "net_return": ret - 0.002, "WIN_raw": ret > 0}}


def make(n, mu, sd, sessions=12, seed=1):
    rng = np.random.default_rng(seed)
    rets = mu + sd * rng.standard_normal(n)
    rets = rets - rets.mean() + mu          # the sample mean is exactly mu
    return [(float(r), i % sessions) for i, r in enumerate(rets)]


def src(rows, sh, voids=None, check="PASS - 0 warning(s)", spy_=None):
    return {"outcomes": (rows, voids or {}, 0, 0), "shadow": sh, "spy": spy_ or spy(),
            "options_ledgers": {"PX-F": None, "PX-L": None}, "shx": [], "recheck": lambda se, cid: None,
            "shares_ledger": {"trades": {}}, "official_open": lambda t, s: None, "decisions": {},
            "health": {"missed_windows": 0, "t2_missing": 0, "frozen_pass": len(rows), "t2_missing_rate": 0.0,
                       "single_source": 0, "fence_breaches": 0},
            "check": {"result": check, "timestamps_line": "[ok]   timestamps: 9 token(s) cover their manifests"},
            "banked": {d: [] for d in stage1.BANKED}, "code": "test"}


def case(mu_w, sd=0.03, n_w=50, n_s0=40, **kw):
    rows = [out_row(i, r, k, t1="BUY" if i % 2 else "NO_BUY") for i, (r, k) in enumerate(make(n_s0, 0.02, sd))]
    sh = [sh_row("SH-W", i, r, k) for i, (r, k) in enumerate(make(n_w, mu_w, sd, seed=2))]
    sh += [sh_row("SH-M", i, r, k) for i, (r, k) in enumerate(make(60, 0.004, sd, seed=3))]
    return stage1.compute("synthetic", "2026-10-30", src(rows, sh, **kw))


def test_alive_and_consistency():
    r = case(0.015)
    w = r["P2"]["SH-W"]
    assert w["n"] == 50 and w["sessions"] == 12
    assert w["net_mean"] == pytest.approx(0.013)
    assert w["word"] == "ALIVE"
    assert r["P1"]["word"] == "PASS"
    assert r["supports"].startswith("fund to Gate 1")
    c = r["P2"]["consistency"]
    a, b = c["S0 net mean: stage1 / report.run H_S0"]
    assert a == pytest.approx(b) and a == pytest.approx(0.018)
    a, b = c["SH-W net mean: stage1 / shadow.report_"]
    assert a == pytest.approx(b)
    assert c["S0 n: stage1 / report.run H_S0"] == [40, 40]
    lo, hi = w["ci95_net"]
    assert lo < w["net_mean"] < hi and hi - lo == pytest.approx(4 * 1.96 * w["se_cluster_session"] / 2)


def test_contradicts_history():
    r = case(-0.01, sd=0.005)
    assert r["P2"]["SH-W"]["ci95_net"][1] < stage1.HIST_NET
    assert r["P2"]["SH-W"]["word"] == "CONTRADICTS HISTORY"
    assert r["supports"].startswith("no new money")


def test_insufficient_small_n_or_few_sessions():
    assert case(0.015, n_w=20)["P2"]["SH-W"]["word"] == "INSUFFICIENT"
    rows = [out_row(i, 0.01, i % 9) for i in range(40)]
    sh = [sh_row("SH-W", i, 0.02, i % 9) for i in range(40)]
    r = stage1.compute("synthetic", "2026-10-30", src(rows, sh))
    assert r["P2"]["SH-W"]["sessions"] == 9 and r["P2"]["SH-W"]["word"] == "INSUFFICIENT"
    assert r["supports"].startswith("fund to Gate 1")      # D017 §5: INSUFFICIENT with a clean record


def test_not_yet_visible_when_spy_beats_it():
    r = case(0.006, sd=0.05, spy_=spy(step=8.0))           # SPY rises ~1.3% per window
    w = r["P2"]["SH-W"]
    assert w["net_mean"] > 0 and w["excess_spy_mean"] < 0 and w["ci95_net"][1] >= stage1.HIST_NET
    assert w["word"] == "NOT YET VISIBLE"


def test_p1_fail_on_check_or_void_rate():
    r = case(0.015, check="FAIL - 1 problem(s)")
    assert r["P1"]["word"] == "FAIL" and r["supports"].startswith("repair first")
    r = case(0.015, voids={"no_open": 3})                  # 3 of 43 = 7% >= 5%
    assert r["P1"]["void_rate"] == pytest.approx(3 / 43) and r["P1"]["word"] == "FAIL"


def test_excess_over_spy_with_dividend():
    opens = {"2026-10-01": 100.0, "2026-10-02": 101.0, "2026-10-05": 102.0}
    divs = {"2026-10-02": 1.0, "2026-09-30": 5.0}
    assert stage1.spy_return(opens, divs, "2026-10-01", "2026-10-05") == pytest.approx(0.03)
    assert stage1.spy_return(opens, divs, "2026-10-02", "2026-10-05") == pytest.approx(1 / 101)
    assert stage1.spy_return(opens, divs, "2026-10-01", "2026-10-06") is None
    w = case(0.015)["P2"]["SH-W"]
    # every synthetic window is one session long: SPY's return is (601 + i) / (600 + i) - 1, under 0.17%
    assert 0.015 - 0.0017 < w["excess_spy_mean"] < 0.015 and w["excess_spy_n"] == 50


def test_cut_by_exit_a(tmp_path, monkeypatch):
    d = tmp_path / "outcomes" / "s"
    d.mkdir(parents=True)
    rows = {"in": out_row(1, 0.01, 3), "out": out_row(2, 0.01, 3)}
    rows["out"]["exits"]["exit_A"]["exit_session"] = "2026-11-02"
    rows["void_in"] = {"gate_status": "PASS", "void": "no_open", "entry_session": "2026-10-29", "exits": {}}
    rows["void_out"] = {"gate_status": "PASS", "void": "no_open", "entry_session": "2026-10-31", "exits": {}}
    rows["inel"] = {"gate_status": "INELIGIBLE", "entry_session": "2026-10-20"}
    for k, v in rows.items():
        (d / f"{k}.json").write_text(json.dumps(v), encoding="utf-8")
    monkeypatch.setattr(stage1, "ROOT", str(tmp_path))
    got, voids, pending, inel = stage1.load_rows_cut("s", "2026-10-30")
    assert [r["ticker"] for r in got] == ["X1"] and voids == {"no_open": 1} and inel == 1 and pending == 0
    assert stage1.shadow_in_cut(sh_row("SH-W", 1, 0.0, 3), "2026-10-30")
    assert not stage1.shadow_in_cut({"timing": {"exit_A": {"session": "2026-11-02"}}}, "2026-10-30")


def test_never_shown():
    r = case(0.015)
    stage1.guard(r)
    text = json.dumps(r).lower() + stage1.markdown(r).lower()
    for banned in ("brier", "auc", "slope", "calibration", "h-t2c"):
        assert banned not in text
    assert "t2_confidence" not in text
    with pytest.raises(SystemExit):
        stage1.guard({"P3": {"T2": {"probability": {}}}})
    with pytest.raises(SystemExit):
        stage1.guard({"C1": 1})


def test_p3_and_markdown():
    r = case(0.015)
    t1 = r["P3"]["T1"]
    assert t1["buys"] == 20 and t1["word"] == "INSUFFICIENT"
    assert r["P3"]["T2"]["buys"] == 40 and r["P3"]["T2"]["word"] == "EXPLORATORY"
    assert r["P3"]["decision_agreement_with_T2"]["T2G"] == {"n": 40, "agreement_with_T2": 1.0}
    md = stage1.markdown(r)
    assert "INTERIM" in md and "fund to Gate 1" in md and "| SH-W |" in md


def test_pending_in_cut_is_counted_and_blocks_write():
    r = case(0.015)
    assert r["P2"]["pending_in_cut"] == {"SH-W": 0, "S0 gated": 0, "SH-M": 0} and r["P2"]["cut_complete"]
    assert "the cut is complete" in stage1.markdown(r)
    rows = [out_row(i, r_, k) for i, (r_, k) in enumerate(make(40, 0.02, 0.03))]
    sh = [sh_row("SH-W", i, r_, k) for i, (r_, k) in enumerate(make(50, 0.01, 0.03, seed=2))]
    late = sh_row("SH-W", 99, 0.0, 3)
    late.update(graded=False, exit_A={})                                 # inside the cut, prices not settled yet
    void = sh_row("SH-M", 98, 0.0, 3)
    void.update(graded=False, void="not_domestic_foreign", exit_A={})    # VOID: never pending
    s = src(rows, sh + [late, void])
    s["outcomes"] = (rows, {}, 2, 0)
    r = stage1.compute("synthetic", "2026-10-30", s)
    assert r["P2"]["pending_in_cut"] == {"SH-W": 1, "S0 gated": 2, "SH-M": 0} and not r["P2"]["cut_complete"]
    assert r["P2"]["SH-W"]["n"] == 50 and "INCOMPLETE" in stage1.markdown(r)


def test_out_base_never_replaces(tmp_path, monkeypatch):
    monkeypatch.setattr(stage1, "ROOT", str(tmp_path))
    (tmp_path / "outcomes" / "reports").mkdir(parents=True)
    b = stage1.out_base("2026-10-30")
    assert b.endswith("stage1_2026-10-30")
    open(b + ".md", "w").close()
    assert stage1.out_base("2026-10-30").endswith("stage1_2026-10-30_r2")
