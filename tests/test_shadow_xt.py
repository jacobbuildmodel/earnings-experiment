"""D012 H-XT: the filter (both legs <= 0.10, missing = out), the test (D009's mean_test on the subset, own
name), the pilot guard and the descriptive split. Run: python -m pytest tests/test_shadow_xt.py -q"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
import shadow  # noqa: E402
import shadow_xt as xt  # noqa: E402


def row(season, t, date, pnl, session, mid=None, flags=()):
    return {"track": "SH-X", "season": season, "ticker": t, "date": date, "graded": True, "void": None,
            "flags": list(flags), "timing": {"entry": {"session": session}},
            "straddle": {"pnl_on_spot": pnl, "pnl_on_spot_mid": mid if mid is not None else pnl + 0.01}}


@pytest.fixture
def root(tmp_path, monkeypatch):
    monkeypatch.setattr(xt, "ROOT", str(tmp_path))

    def gate(season, t, date, call, put):
        d = tmp_path / "events" / season / f"{t}_{date}"
        d.mkdir(parents=True)
        o = {"options": {"rel_spread": {"call": call, "put": put}}} if call is not None else {"options": {}}
        (d / "gate.json").write_text(json.dumps(o))
    return tmp_path, gate


def test_filter_boundaries(root):
    _, gate = root
    gate("seasonA", "AAA", "2026-10-20", 0.10, 0.10)     # exactly at the rule: in
    gate("seasonA", "BBB", "2026-10-20", 0.05, 0.11)     # one leg over: out
    gate("seasonA", "CCC", "2026-10-21", None, None)     # no rel_spread recorded: out
    rows = [row("seasonA", "AAA", "2026-10-20", 0.01, "2026-10-19"),
            row("seasonA", "BBB", "2026-10-20", -0.02, "2026-10-19"),
            row("seasonA", "CCC", "2026-10-21", 0.03, "2026-10-20"),
            row("seasonA", "DDD", "2026-10-22", 0.03, "2026-10-21")]   # no gate file at all: out
    inn, out = xt.split(rows)
    assert [e["ticker"] for e in inn] == ["AAA"]
    assert sorted(e["ticker"] for e in out) == ["BBB", "CCC", "DDD"]


def test_test_is_d009s_mean_test_on_the_subset(root):
    _, gate = root
    rows = []
    for i in range(12):
        t, date, sess = f"T{i}", f"2026-10-{10 + i}", f"2026-10-{9 + i}"
        gate("seasonA", t, date, 0.04, 0.06 if i % 2 else 0.2)       # odd i in, even i out
        rows.append(row("seasonA", t, date, 0.01 * (i % 3) - 0.005, sess))
    res, sens, desc = xt.stats(rows)
    inn = [r for i, r in enumerate(rows) if i % 2]
    want = shadow.mean_test([r["straddle"]["pnl_on_spot"] for r in inn],
                            [r["timing"]["entry"]["session"] for r in inn], "H-XT")
    assert res["H-XT"]["n"] == 6 and abs(res["H-XT"]["mean"] - want["mean"]) < 1e-12
    assert res["H-XT"]["p_one_sided"] == want["p_one_sided"]
    assert res["H-XT"]["status"] == "insufficient"                  # 6 events < 30
    assert desc["events"] == {"graded SH-X": 12, "in H-XT": 6, "excluded": 6, "excluded for a missing rel_spread": 0}


def test_ungraded_and_other_tracks_are_ignored(root):
    _, gate = root
    gate("seasonA", "AAA", "2026-10-20", 0.05, 0.05)
    rows = [dict(row("seasonA", "AAA", "2026-10-20", 0.01, "2026-10-19"), graded=False),
            dict(row("seasonA", "AAA", "2026-10-20", 0.01, "2026-10-19"), track="SH-M")]
    res, _, desc = xt.stats(rows)
    assert desc["events"]["graded SH-X"] == 0


def test_pilot_is_never_part_of_hxt():
    with pytest.raises(SystemExit):
        xt.run(["pilot"])
