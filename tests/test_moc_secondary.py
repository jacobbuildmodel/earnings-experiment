"""Tests for the D019 MOC secondary (pipeline/moc_secondary.py; registry/D019_moc_secondary_v1.md).

    python -m pytest tests/test_moc_secondary.py -q

Synthetic data only: no network, and nothing under the real outcomes/ is read or written (the grade test runs
against a temporary ROOT).
"""
import datetime
import json
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pipeline"))
import moc_secondary as ms  # noqa: E402
import report  # noqa: E402
from common import registry  # noqa: E402
from sessions import timing  # noqa: E402

D001 = registry("D001_outcome_v1.json")


@pytest.fixture(autouse=True)
def fast_bootstrap(monkeypatch):
    monkeypatch.setattr(report, "B_WILD", 199)


class Store:
    """The get() side of a price store, from a dict."""

    def __init__(self, rows):
        self.rows = rows

    def get(self, sym, session, field):
        return self.rows.get((sym, session, field))


def event(ticker="AAA", date="2026-10-14", session="AMC", track="SH-M", graded=True, flags=()):
    return {"track": track, "ticker": ticker, "date": date, "session": session, "graded": graded,
            "flags": list(flags), "timing": timing(datetime.date.fromisoformat(date), session, D001)}


def priced(ev, entry, exit_, div=0.0, splits=None):
    e_s, x_s = ms.sessions_of(ev)
    t = ev["ticker"]
    return {(t, e_s, "close"): entry, (t, x_s, "close"): exit_, (t, x_s, f"div:{e_s}"): div,
            (t, x_s, f"split:{e_s}"): splits or []}


def test_sessions_are_the_close_before_the_print_and_the_reaction_day_close():
    amc = event(date="2026-10-14", session="AMC")      # Wed after the close: Wed close -> Thu close
    assert ms.sessions_of(amc) == ("2026-10-14", "2026-10-15")
    bmo = event(date="2026-10-14", session="BMO")      # Wed before the open: Tue close -> Wed close
    assert ms.sessions_of(bmo) == ("2026-10-13", "2026-10-14")
    mon = event(date="2026-10-19", session="BMO")      # Monday before the open: Friday's close
    assert ms.sessions_of(mon) == ("2026-10-16", "2026-10-19")
    assert ms.sessions_of(bmo)[1] == bmo["timing"]["reaction_day"]


def test_leg_arithmetic_and_fees():
    ev = event()
    lg = ms.leg(Store(priced(ev, 100.0, 103.0, div=0.5)), ev)
    assert lg["raw_return"] == pytest.approx(0.035)
    assert lg["net_return"] == pytest.approx(0.035 - 0.00198)
    assert ms.FEES == pytest.approx(0.00198)
    assert lg["WIN_raw"] is True


def test_missing_price_or_dividend_field_leaves_the_event_ungraded():
    ev = event()
    rows = priced(ev, 100.0, 103.0)
    for k in list(rows):
        if k[2] == "split:" + ms.sessions_of(ev)[0]:
            continue
        broken = {kk: v for kk, v in rows.items() if kk != k}
        assert ms.leg(Store(broken), ev) is None, k
    built = ms.build([ev], Store({}))
    assert built[0]["graded"] is False and built[0]["moc"] is None


def test_split_in_window_is_void():
    ev = event()
    built = ms.build([ev], Store(priced(ev, 100.0, 50.0, splits=[2.0])))
    assert built[0]["void"] == "split_in_window" and built[0]["graded"] is False


def test_only_d009_graded_sh_m_and_sh_w_events_enter():
    evs = [event("A"), event("B", graded=False), event("C", track="SH-X"), event("D", track="SH-W")]
    rows = {}
    for ev in evs:
        rows.update(priced(ev, 10.0, 11.0))
    built = ms.build(evs, Store(rows))
    assert [r["ticker"] for r in built] == ["A", "D"]


def test_t_quantile_matches_tables():
    assert ms.t_quantile(0.975, 1) == pytest.approx(12.706, abs=1e-3)
    assert ms.t_quantile(0.975, 10) == pytest.approx(2.228, abs=1e-3)
    assert ms.t_quantile(0.975, 30) == pytest.approx(2.042, abs=1e-3)


def panel(mean, sessions=12, per=5, seed=1):
    rng = np.random.default_rng(seed)
    days, day = [], datetime.date(2026, 10, 12)
    while len(days) < sessions:
        if day.weekday() < 5:
            days.append(day)
        day += datetime.timedelta(days=1)
    out = []
    i = 0
    for day in days:
        shock = rng.normal(0, 0.01)
        for _ in range(per):
            r = mean + shock + rng.normal(0, 0.03)
            out.append({"track": "SH-M", "ticker": f"T{i}", "date": day.isoformat(), "session": "AMC",
                        "flags": ["late_8k"] if i % 7 == 0 else [], "void": None, "graded": True,
                        "moc": {"entry_session": day.isoformat(), "raw_return": r, "net_return": r - ms.FEES,
                                "WIN_raw": r > 0}})
            i += 1
    return out


def test_statistic_interval_and_labels():
    rows = panel(0.02)
    res = ms.stats_(rows, "seasonA")
    s = res["tracks"]["SH-M"]["all"]
    assert s["n"] == 60 and s["dates"] == 12
    assert s["mean"] == pytest.approx(np.mean([r["moc"]["net_return"] for r in rows]))
    assert s["raw_mean"] - s["mean"] == pytest.approx(ms.FEES)
    q = ms.t_quantile(0.975, 11)
    assert s["ci95_t"][1] == pytest.approx(s["mean"] + q * s["se"])
    assert s["net_mean_stress"] == pytest.approx(s["mean"] - 0.001)
    assert res["tracks"]["SH-M"]["without_unverified_timing"]["n"] == 60 - sum(1 for r in rows if r["flags"])
    assert res["evidence"] is False and "gate2" not in res
    assert "DESCRIPTIVE" in ms.lines(res)[0]
    assert res["tracks"]["SH-W"]["all"]["n"] == 0


def test_gate2_only_on_season_b():
    hi = ms.stats_(panel(0.02), "seasonB")
    assert hi["evidence"] is True and hi["gate2"]["met"] is True
    lo = ms.stats_(panel(-0.01), "seasonB")
    assert lo["gate2"]["met"] is False
    assert "EVIDENCE" in ms.lines(hi)[0]
    few = ms.stats_(panel(0.02, sessions=5), "seasonB")
    assert few["tracks"]["SH-M"]["all"]["status"] == "insufficient"


def test_price_store_is_its_own_write_once_file(tmp_path, monkeypatch):
    monkeypatch.setattr(ms, "ROOT", str(tmp_path))
    p = ms.MocPrices("seasonX")
    p.add("AAA", "2026-10-14", "close", 10.0)
    p.add("AAA", "2026-10-14", "close", 99.0)          # write-once: the first value stays
    p.save()
    assert os.path.basename(p.path) == "moc_prices.jsonl"
    assert ms.MocPrices("seasonX").get("AAA", "2026-10-14", "close") == 10.0
    assert not (tmp_path / "outcomes" / "shadow" / "seasonX" / "prices.jsonl").exists()


def test_grade_writes_only_its_own_files(tmp_path, monkeypatch):
    monkeypatch.setattr(ms, "ROOT", str(tmp_path))
    d = tmp_path / "outcomes" / "shadow" / "seasonX"
    d.mkdir(parents=True)
    ev = event()
    (d / "graded.json").write_text(json.dumps({"events": [ev]}), encoding="utf-8")
    store = d / "moc_prices.jsonl"
    with open(store, "w", encoding="utf-8") as f:
        for (sym, sess, field), v in priced(ev, 100.0, 101.0).items():
            f.write(json.dumps({"symbol": sym, "session": sess, "field": field, "value": v}) + "\n")
    rows = ms.grade("seasonX", do_fetch=False)
    assert rows[0]["graded"] and rows[0]["moc"]["raw_return"] == pytest.approx(0.01)
    assert sorted(p.name for p in d.iterdir()) == ["graded.json", "moc.json", "moc_prices.jsonl"]
    assert json.loads((d / "moc.json").read_text(encoding="utf-8"))["evidence"] is False
