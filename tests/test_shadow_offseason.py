"""Tests for the D009 v2 DRAFT off-season shadow (pipeline/shadow_offseason.py). No network: the Nasdaq
captures, the screen, prices, the SEC and git are all faked under a temporary ROOT.

    python -m pytest tests/test_shadow_offseason.py -q
"""
import datetime
import json
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "pipeline"))
import report  # noqa: E402
import shadow  # noqa: E402
import shadow_offseason as so  # noqa: E402
from common import ET  # noqa: E402

DRAFT = json.load(open(os.path.join(HERE, "reviews", "proposals", "D009_v2_yearround_DRAFT.json"), encoding="utf-8"))
RULE = {**DRAFT, "clock_start_entry_session": "2026-10-12"}
LONG_AGO = datetime.datetime(2026, 11, 18, 18, 0, tzinfo=ET)   # every file "committed" on the screen date evening


class FakeSec:
    """Share classes: GOOG and GOOGL are one issuer."""
    def cik(self, t):
        return {"GOOG": 1652044, "GOOGL": 1652044}.get(t)


def test_refuses_until_frozen():
    if os.path.exists(os.path.join(HERE, "registry", so.RULE_FILE)):
        pytest.skip("v2 is frozen")
    with pytest.raises(SystemExit, match="DRAFT"):
        so.load_rule()


def test_window_and_overlap_guard():
    w = so.window(RULE, "off_seasonA", seasons={"seasonA": ("2026-10-12", "2026-11-20")})
    assert (w["lo"], w["hi"], w["after_season"]) == ("2026-11-23", "2027-01-08", "seasonA")
    with pytest.raises(SystemExit, match="overlaps"):
        so.window(RULE, "off_seasonA", seasons={"seasonB": ("2027-01-04", "2027-02-26")})
    with pytest.raises(SystemExit, match="not a registered"):
        so.window(RULE, "off_nothing", seasons={})
    # against the real registry: no frozen season window overlaps the draft's window
    so.window(RULE, "off_seasonA")


def write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f)


def capture(root, day, days):
    p = os.path.join(root, "shadow", "calendar", f"{day}.json")
    write(p, {"session_day": day, "days": {d: {"rows": rows} for d, rows in days.items()}})
    return p


def row(sym, session):
    return {"symbol": sym, "session": session, "session_source": "nasdaq", "marketCap": "$5,000,000,000"}


@pytest.fixture
def env(tmp_path, monkeypatch):
    root = str(tmp_path)
    monkeypatch.setattr(so, "ROOT", root)
    monkeypatch.setattr(shadow, "ROOT", root)
    monkeypatch.setattr(shadow, "CAL_DIR", os.path.join(root, "shadow", "calendar"))
    monkeypatch.setattr(so, "load_rule", lambda: RULE)
    monkeypatch.setattr(so, "Sec", lambda *a, **k: FakeSec())
    monkeypatch.setattr(shadow, "committed_at", lambda p: LONG_AGO)
    monkeypatch.setattr(shadow, "settled", lambda s: True)
    return root


def test_events_follow_the_sh_m_dating_rule(env):
    # Thu 2026-12-10 BMO: snapshot = D-2 sessions = Tue 12-08. AMC 12-10: snapshot = D-1 = Wed 12-09.
    capture(env, "2026-12-08", {"2026-12-10": [row("AAA", "BMO"), row("BBB", "AMC"), row("ZZZ", "BMO")]})
    capture(env, "2026-12-09", {"2026-12-10": [row("BBB", "AMC"), row("AAA", "BMO"), row("GOOG", "AMC"),
                                               row("GOOGL", "AMC"), row("NOSESS", None)]})
    capture(env, "2026-11-19", {"2026-11-20": [row("AAA", "AMC")]})          # inside Season A: v1's, not v2's
    univ = {t: {"universe_committed": LONG_AGO.isoformat(), "marketCap": 5e9} for t in ("AAA", "BBB", "GOOG", "GOOGL", "NOSESS")}
    w = so.window(RULE, "off_seasonA", seasons={})
    evs, stat = so.events(w, univ, sec=FakeSec())
    got = {(e["ticker"], e["date"], e["session"], e["snapshot"]) for e in evs}
    assert got == {("AAA", "2026-12-10", "BMO", "2026-12-08"), ("BBB", "2026-12-10", "AMC", "2026-12-09"),
                   ("GOOG", "2026-12-10", "AMC", "2026-12-09")}   # ZZZ not in universe; GOOGL = GOOG's issuer
    assert stat["rows_without_session"] == 1
    assert all(e["exists_before_entry"] for e in evs)


def test_existence_before_entry_voids_late_files(env, monkeypatch):
    capture(env, "2026-11-23", {"2026-11-24": [row("AAA", "AMC")]})
    late = datetime.datetime(2026, 11, 24, 10, 0, tzinfo=ET)   # after the 11-24 entry open
    univ = {"AAA": {"universe_committed": late.isoformat(), "marketCap": 5e9}}
    evs, _ = so.events(so.window(RULE, "off_seasonA", seasons={}), univ, sec=FakeSec(), committed=lambda p: LONG_AGO)
    assert len(evs) == 1 and evs[0]["exists_before_entry"] is False


def test_universe_applies_v1_s1_filters(env):
    write(os.path.join(env, "shadow", "offseason", "off_seasonA", "market.json"), {"tickers": {
        "GOOD": {"quoteType": "EQUITY", "exchange": "NMS", "currency": "USD", "marketCap": 3e9, "industry": "Software"},
        "SMALL": {"quoteType": "EQUITY", "exchange": "NYQ", "currency": "USD", "marketCap": 1.9e9},
        "ETF": {"quoteType": "ETF", "exchange": "NYQ", "currency": "USD", "marketCap": 9e9},
        "OTC": {"quoteType": "EQUITY", "exchange": "PNK", "currency": "USD", "marketCap": 9e9},
        "SHELL": {"quoteType": "EQUITY", "exchange": "NYQ", "currency": "USD", "marketCap": 9e9, "industry": "Shell Companies"},
        "CAD": {"quoteType": "EQUITY", "exchange": "NYQ", "currency": "CAD", "marketCap": 9e9},
        "PFD-PA": {"quoteType": "EQUITY", "exchange": "NYQ", "currency": "USD", "marketCap": 9e9},
        "ERR": {"error": "HTTPError: 404"}}})
    u = so.universe("off_seasonA", so.window(RULE, "off_seasonA", seasons={}))
    assert set(u) == {"GOOD"}


def test_grade_end_to_end_labels_sh_mo(env):
    write(os.path.join(env, "shadow", "offseason", "off_seasonA", "market.json"), {"tickers": {
        t: {"quoteType": "EQUITY", "exchange": "NYQ", "currency": "USD", "marketCap": 5e9} for t in ("AAA", "BBB", "FGN")}})
    capture(env, "2026-12-08", {"2026-12-10": [row("AAA", "BMO")]})
    capture(env, "2026-12-09", {"2026-12-10": [row("BBB", "AMC"), row("FGN", "AMC")]})
    out = os.path.join(env, "outcomes", "shadow", "off_seasonA")
    os.makedirs(out)
    px = [("AAA", "2026-12-09", "open", 100.0), ("AAA", "2026-12-10", "open", 103.0), ("AAA", "2026-12-10", "div:2026-12-09", 0.0),
          ("AAA", "2026-12-10", "split:2026-12-09", []),
          ("BBB", "2026-12-10", "open", 50.0), ("BBB", "2026-12-11", "open", 49.0), ("BBB", "2026-12-11", "div:2026-12-10", 0.0),
          ("BBB", "2026-12-11", "split:2026-12-10", []),
          ("FGN", "2026-12-10", "open", 10.0), ("FGN", "2026-12-11", "open", 11.0), ("FGN", "2026-12-11", "div:2026-12-10", 0.0),
          ("FGN", "2026-12-11", "split:2026-12-10", [])]
    with open(os.path.join(out, "prices.jsonl"), "w") as f:
        for s, ss, fld, v in px:
            f.write(json.dumps({"symbol": s, "session": ss, "field": fld, "value": v}) + "\n")
    write(os.path.join(out, "timing.json"), {"AAA_2026-12-10_BMO": {"status": "verified", "final": True},
                                             "BBB_2026-12-10_AMC": {"status": "unverified", "final": True},
                                             "FGN_2026-12-10_AMC": {"status": "foreign", "final": True}})
    rows = {r["ticker"]: r for r in so.grade("off_seasonA", do_fetch=False)}
    assert all(r["track"] == "SH-MO" for r in rows.values())
    assert rows["AAA"]["graded"] and rows["AAA"]["exit_A"]["net_return"] == pytest.approx(0.03 - shadow.COST)
    assert rows["BBB"]["graded"] and rows["BBB"]["flags"] == ["timing_unverified"]
    assert rows["FGN"]["void"] == "not_domestic_foreign" and not rows["FGN"]["graded"]
    saved = json.load(open(os.path.join(out, "graded.json")))
    assert saved["rule"] == "D009_shadow_tracks_v2" and len(saved["events"]) == 3


# ---------------------------------------------------------------------------------- statistics

def synth(rng, track, days, per, mean):
    rows = []
    for di, day in enumerate(days):
        for k in range(per):
            r = float(mean + rng.normal(0, 0.09))
            rows.append({"track": track, "ticker": f"{track}{di}{k}", "date": day, "graded": True, "flags": [],
                         "timing": {"entry": {"session": day}}, "exit_A": {"net_return": r}})
    return rows


def bdays(start, n):
    return [str(x) for x in np.busday_offset(start, np.arange(n), roll="forward")]


def test_year_stats_pools_from_the_clock(monkeypatch):
    monkeypatch.setattr(report, "B_WILD", 499)
    rng = np.random.default_rng(3)
    before = synth(rng, "SH-M", bdays("2026-10-01", 5), 10, 0.0)        # entry before the clock: excluded
    m = synth(rng, "SH-M", bdays("2026-10-12", 25), 10, 0.01)
    w = synth(rng, "SH-W", bdays("2026-10-12", 25), 3, 0.01)           # other v1 tracks never enter
    mo = synth(rng, "SH-MO", bdays("2026-11-23", 20), 3, 0.01)
    res, sens, desc = so.year_stats(mo, before + m + w, "2026-10-12")
    h = res["H-MY"]
    assert h["n"] == len(m) + len(mo) and h["dates"] == 45
    assert h["status"] == "interim (monitoring only)"
    assert h["mde"] == pytest.approx(2.487 * h["se"])
    assert desc["H-MO off-season alone (descriptive)"]["n"] == len(mo)
    assert desc["off minus in-season (descriptive)"]["n"] == len(m) + len(mo)
    assert desc["events"]["SH-M in sample"] == len(m)
    # the same seed by name as the v1 helpers
    ref = shadow.mean_test([e["exit_A"]["net_return"] for e in m + mo], [e["date"] for e in m + mo], "H-MY")
    assert h["p_one_sided"] == ref["p_one_sided"]
    final, _, _ = so.year_stats(mo, m, "2026-10-12", final=True)
    st = final["H-MY"]["status"]
    assert st.startswith("p < 0.05 (shadow") or st.startswith("no evidence (shadow)")


def test_year_stats_insufficient(monkeypatch):
    monkeypatch.setattr(report, "B_WILD", 499)
    rng = np.random.default_rng(4)
    res, _, _ = so.year_stats(synth(rng, "SH-MO", bdays("2026-11-23", 9), 5, 0.02), [], "2026-10-12")
    assert res["H-MY"]["status"] == "insufficient"


def test_report_needs_the_clock_and_refuses_pilot(env, monkeypatch):
    monkeypatch.setattr(so, "load_rule", lambda: DRAFT)
    with pytest.raises(SystemExit, match="clock_start"):
        so.report_(["off_seasonA"], ["seasonA"])
    monkeypatch.setattr(so, "load_rule", lambda: RULE)
    with pytest.raises(SystemExit, match="pilot"):
        so.report_(["off_seasonA"], ["pilot"])
