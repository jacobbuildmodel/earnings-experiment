"""Tests for the D009 shadow statistics (pipeline/shadow.py, pipeline/report.py).

    python -m pytest tests/test_shadow_stats.py -q

Synthetic data only: no network, nothing under outcomes/ is read or written (the report tests run
against a temporary ROOT).
"""
import json
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pipeline"))
import report  # noqa: E402
import shadow  # noqa: E402

SESSION_SD = 0.019   # the part every print on one entry session shares (JOURNAL 2026-10-02: ~1.8-1.9%)
STOCK_SD = 0.095     # the stock-specific part (~9.2-9.6%)


@pytest.fixture
def fast_bootstrap(monkeypatch):
    """Fewer bootstrap draws so hundreds of replications run in seconds. The p-value resolution is
    1/500, ample for checking a 5% test."""
    monkeypatch.setattr(report, "B_WILD", 499)


def panel(rng, sessions, per_session, mean):
    """Returns with a shared session shock plus a stock-specific part, clustered by entry session."""
    g = np.repeat(np.arange(sessions), per_session)
    y = mean + rng.normal(0, SESSION_SD, sessions)[g] + rng.normal(0, STOCK_SD, len(g))
    return y, g


def intercept_p(y, g, rng):
    return report.wild_p_k(y, np.ones((len(y), 1)), g, 0, rng)


def rejection_rate(reps, sessions, per_session, mean, seed):
    rng = np.random.default_rng(seed)
    return float(np.mean([intercept_p(*panel(rng, sessions, per_session, mean), rng) < 0.05 for _ in range(reps)]))


# ------------------------------------------------- the intercept-only restricted wild cluster bootstrap

def test_intercept_only_runs_and_matches_cluster_t():
    rng = np.random.default_rng(1)
    y, g = panel(rng, 30, 10, 0.01)
    b, se, t = report.ols_k(y, np.ones((len(y), 1)), g, 0)
    assert b == pytest.approx(y.mean())
    p = intercept_p(y, g, report.R("H-M"))
    assert 0 < p <= 1
    # one-sided: a strongly negative sample never rejects "mean > 0"
    assert intercept_p(y - 0.05, g, report.R("H-M")) > 0.5


def test_size_under_null_rademacher(fast_bootstrap):
    """30 entry sessions (>= 12 clusters: Rademacher weights), mean 0: rejects at about 5%.
    600 replications: the standard error of the rate is ~0.9 pts, so [2%, 9%] is a 3+ sigma band."""
    rate = rejection_rate(600, 30, 10, 0.0, seed=20261003)
    assert 0.02 <= rate <= 0.09, rate


def test_size_under_null_webb(fast_bootstrap):
    """8 entry sessions (< 12 clusters: Webb six-point weights), mean 0: does not over-reject."""
    rate = rejection_rate(400, 8, 20, 0.0, seed=20261004)
    assert rate <= 0.10, rate


def test_size_under_null_heavy_tails(fast_bootstrap):
    """Earnings moves are fat-tailed. Student-t(3) stock parts, mean 0: still about 5%."""
    rng = np.random.default_rng(20261005)
    hits = []
    for _ in range(400):
        g = np.repeat(np.arange(30), 10)
        y = rng.normal(0, SESSION_SD, 30)[g] + STOCK_SD / np.sqrt(3) * rng.standard_t(3, len(g))
        hits.append(intercept_p(y, g, rng) < 0.05)
    assert 0.015 <= np.mean(hits) <= 0.10, np.mean(hits)


def test_power_under_alternative(fast_bootstrap):
    """A true mean of +2.0% on 30 sessions x 10 events: clustered se ~0.65%, expected t ~3, so the test
    rejects most of the time; at +0.5% it rejects rarely; and power grows with the effect."""
    big = rejection_rate(200, 30, 10, 0.02, seed=7)
    small = rejection_rate(200, 30, 10, 0.005, seed=8)
    assert big >= 0.75, big
    assert small < big


def test_seed_is_per_test_name():
    """Same name -> the same stream (so a season and the pool use the same seed per test); different
    names -> different streams."""
    a, b, c = report.R("H-M").random(5), report.R("H-M").random(5), report.R("H-X").random(5)
    assert np.array_equal(a, b)
    assert not np.array_equal(a, c)


# ------------------------------------------------------------------------------- the Holm family

def test_holm_m3():
    adj = report.holm({"H-M": 0.01, "H-X": 0.04, "H-VOL": 1.0})
    assert adj == pytest.approx({"H-M": 0.03, "H-X": 0.08, "H-VOL": 1.0})


def make_rows(rng, season_sessions, per_session, mean, tracks=("SH-W", "SH-M", "SH-X"), flag_every=0):
    rows = []
    for tr in tracks:
        for si, sess in enumerate(season_sessions):
            for k in range(per_session):
                r = float(mean + rng.normal(0, STOCK_SD))
                flags = ["timing_unverified"] if flag_every and k % flag_every == 0 else []
                e = {"track": tr, "ticker": f"T{si:02d}{k:02d}", "date": sess, "session": "AMC",
                     "graded": True, "void": None, "flags": flags,
                     "timing": {"entry": {"price": "open", "session": sess}},
                     "exit_A": {"net_return": r, "raw_return": r + shadow.COST, "WIN_raw": r + shadow.COST > 0,
                                "excess_spy": r},
                     "vol60": float(rng.uniform(0.2, 0.8))}
                if tr == "SH-X":
                    e["straddle"] = {"pnl_on_spot": r / 4, "realised_move": abs(r)}
                    e["implied_move"] = 0.08
                rows.append(e)
    return rows


def sessions(start, n):
    d, out = np.datetime64(start), []
    while len(out) < n:
        if np.is_busday(d):
            out.append(str(d))
        d += 1
    return out


def test_family_is_always_m3_and_missing_test_is_p1(fast_bootstrap):
    """No SH-X events: H-X cannot run, counts as p = 1, and H-M is still adjusted with m = 3."""
    rng = np.random.default_rng(11)
    rows = make_rows(rng, sessions("2026-10-12", 30), 10, 0.02, tracks=("SH-M",))
    res, _, _ = shadow.stats_(rows)
    assert res["H-X"].get("p_one_sided") is None and res["H-X"]["p_holm"] == 1.0
    ps = {k: (res[k]["p_one_sided"] if res[k].get("p_one_sided") is not None else 1.0) for k in shadow.FAMILY}
    assert ps["H-X"] == 1.0
    assert {k: res[k]["p_holm"] for k in shadow.FAMILY} == pytest.approx(report.holm(ps))
    smallest = min(ps, key=ps.get)
    assert res[smallest]["p_holm"] == pytest.approx(min(1.0, 3 * ps[smallest]))
    assert set(res) == set(shadow.FAMILY)


def test_nan_p_counts_as_one(monkeypatch, fast_bootstrap):
    rng = np.random.default_rng(12)
    rows = make_rows(rng, sessions("2026-10-12", 30), 10, 0.02, tracks=("SH-M", "SH-X"))
    real = report.wild_p_k
    monkeypatch.setattr(report, "wild_p_k", lambda y, X, g, j, r, **kw: float("nan") if X.shape[1] == 1 and
                        np.allclose(y, [e["straddle"]["pnl_on_spot"] for e in rows if e["track"] == "SH-X"])
                        else real(y, X, g, j, r, **kw))
    res, _, _ = shadow.stats_(rows)
    assert res["H-X"]["p_one_sided"] != res["H-X"]["p_one_sided"]   # the test ran and gave NaN
    assert res["H-X"]["p_holm"] == 1.0


def test_insufficient_below_rule7_minimum(fast_bootstrap):
    rng = np.random.default_rng(13)
    res, _, _ = shadow.stats_(make_rows(rng, sessions("2026-10-12", 9), 10, 0.05))
    assert all(res[k]["status"] == "insufficient" for k in shadow.FAMILY)


def test_interim_has_no_verdict_and_final_wording(fast_bootstrap):
    rng = np.random.default_rng(14)
    rows = make_rows(rng, sessions("2026-10-12", 30), 10, 0.0)
    res, _, _ = shadow.stats_(rows)
    assert res["H-M"]["status"] == "interim (monitoring only)"
    res, _, _ = shadow.stats_(rows, final=True)
    st = res["H-M"]["status"]
    assert st.startswith("p < 0.05 after Holm (shadow, secondary)") or st.startswith("no evidence (shadow)")
    assert "works" not in st and "no effect" not in st
    assert res["H-M"]["mde"] == pytest.approx(2.487 * res["H-M"]["se"])


# ------------------------------------------------------------------------- the pooled report (T1)

def write_season(root, season, rows):
    p = os.path.join(root, "outcomes", "shadow", season)
    os.makedirs(p, exist_ok=True)
    with open(os.path.join(p, "graded.json"), "w", encoding="utf-8") as f:
        json.dump({"season": season, "events": rows}, f)


@pytest.fixture
def two_seasons(tmp_path, monkeypatch, fast_bootstrap):
    monkeypatch.setattr(shadow, "ROOT", str(tmp_path))
    rng = np.random.default_rng(21)
    a = make_rows(rng, sessions("2026-10-12", 20), 6, 0.01, flag_every=3)
    b = make_rows(rng, sessions("2027-01-19", 20), 6, 0.01, flag_every=3)
    write_season(str(tmp_path), "seasonA", a)
    write_season(str(tmp_path), "seasonB", b)
    return tmp_path, a, b


def test_pooled_equals_stats_on_concatenated_rows(two_seasons):
    _, a, b = two_seasons
    out = shadow.report_pooled(["seasonA", "seasonB"])
    res, sens, _ = shadow.stats_(a + b)
    for k in shadow.FAMILY:
        assert out["tests"][k]["n"] == res[k]["n"]
        assert out["tests"][k]["p_one_sided"] == res[k]["p_one_sided"]   # same seed by test name
        assert out["tests"][k]["p_holm"] == res[k]["p_holm"]
    assert out["tests"]["H-M"]["n"] == 240 and out["tests"]["H-M"]["dates"] == 40
    for k in sens:
        assert out["sensitivity"][k]["n"] == sens[k]["n"] < out["tests"]["H-M"]["n"]
    assert out["by_season"]["seasonA"]["SH-M"]["graded"] == 120
    assert out["pooled"] is True and "INTERIM" in out["label"]


def test_pooled_seed_matches_single_season_seed(two_seasons):
    """The pool uses the same per-name seed as one season: pooling a season with an empty one gives
    exactly that season's p-values."""
    root, a, _ = two_seasons
    write_season(str(root), "seasonEmpty", [])
    single = shadow.report_("seasonA")
    pooled = shadow.report_pooled(["seasonA", "seasonEmpty"])
    for k in shadow.FAMILY:
        assert pooled["tests"][k]["p_one_sided"] == single["tests"][k]["p_one_sided"]
        assert pooled["tests"][k]["p_holm"] == single["tests"][k]["p_holm"]


def test_pooled_writes_its_own_report(two_seasons):
    root, _, _ = two_seasons
    shadow.report_pooled(["seasonA", "seasonB"], write=True)
    files = os.listdir(os.path.join(root, "outcomes", "shadow", "reports"))
    assert len(files) == 1 and files[0].startswith("pooled_seasonA+seasonB_")


def test_pooled_refuses_pilot_and_bad_args(two_seasons):
    with pytest.raises(SystemExit):
        shadow.report_pooled(["pilot", "seasonA"])
    with pytest.raises(SystemExit):
        shadow.report_pooled(["seasonA", "seasonA"])
    with pytest.raises(SystemExit):
        shadow.report_pooled(["seasonA"])


def test_pool_drops_duplicates():
    e = {"track": "SH-M", "ticker": "X", "date": "2026-10-20", "session": "AMC"}
    rows, dropped = shadow.pool([("seasonA", [e]), ("seasonB", [dict(e)])])
    assert len(rows) == 1 and rows[0]["season"] == "seasonA"
    assert dropped == [{"season": "seasonB", "track": "SH-M", "ticker": "X", "date": "2026-10-20"}]
