"""SH-RU (D009 v3) against the golden fixture (tests/fixtures/runup_*.json): a synthetic calendar and prices whose
E, D_exp, D_act, X and returns were derived by hand, plus the write-once grading loop and the statistics.
Run: python -m pytest tests/test_shadow_runup.py -q"""
import datetime
import json
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
import shadow_runup as ru  # noqa: E402
from common import ET  # noqa: E402

FX = os.path.join(os.path.dirname(__file__), "fixtures")
CAL = json.load(open(os.path.join(FX, "runup_calendar.json")))
PX = json.load(open(os.path.join(FX, "runup_prices.json")))
D = datetime.date.fromisoformat


@pytest.fixture
def root(tmp_path, monkeypatch):
    u = tmp_path / "universe" / "seasonZ"
    (u / "raw").mkdir(parents=True)
    (u / "candidates.json").write_text(json.dumps(CAL["candidates"]))
    (u / "raw" / "nasdaq_calendar.json").write_text(json.dumps(CAL["nasdaq"]))
    (u / "raw" / "av_calendar.csv").write_text(CAL["av_csv"])
    status = {"events": {t: {"status": "CONFIRMED", "calendar_date": d} for t, d in CAL["company_dates"].items()}}
    (u / "event_status.json").write_text(json.dumps(status))
    monkeypatch.setattr(ru, "ROOT", str(tmp_path))
    monkeypatch.setattr(ru, "git_date_et", lambda *p, **k: D(CAL["freeze_date"]) if "registry" in p[0]
                        else D(CAL["capture_date"]))
    return tmp_path


def test_events_dexp_E_and_voids(root):
    evs = {e["ticker"]: e for e in ru.events("seasonZ")}
    assert len(evs) == 6                                    # GOLD listed twice: one event per issuer
    for t, want in CAL["expected"].items():
        e = evs[t]
        assert e["D_exp"] == want["D_exp"], t
        # listing applies only the voids known before any print; print_before_window comes with D_act
        assert e["void"] == (None if want["void"] == "print_before_window" else want["void"]), t
        if want.get("E"):
            assert e["E"] == want["E"], t
    assert evs["GOLD"]["D_exp_sources"] == {"nasdaq": "2026-11-12", "alphavantage": "2026-11-13"}
    assert evs["GOLD"]["aih"] and not evs["TRUNC"]["aih"]


def test_window_resolution(root):
    evs = {e["ticker"]: e for e in ru.events("seasonZ")}
    today = D("2026-12-31")
    for t in ("GOLD", "EARLY", "TRUNC"):
        e = evs[t]
        X = ru.resolve_window(e, D(CAL["company_dates"][t]), today)
        want = CAL["expected"][t]
        assert e["void"] == want["void"], t
        assert (X.isoformat() if X else None) == want.get("X"), t
    e = dict(evs["AVONLY"], flags=[])
    assert ru.resolve_window(e, None, D("2026-11-20")) is None          # not yet known: wait
    X = ru.resolve_window(e, None, D("2027-01-05"))                      # past shift(D_exp, 30)
    assert X == ru.shift(D(e["E"]), 20) and "print_date_unknown" in e["flags"]


def test_returns_match_hand_derivation():
    ev = PX["event"]
    out = ru.compute(ev, PX["prices"])
    want = PX["expected"]
    for k in ("beta_raw", "beta", "R", "R_spy", "R_etf", "excess_beta", "excess_beta1", "excess_etf", "net"):
        assert abs(out[k] - want[k]) < 1e-9, k
    assert out["sessions"] == want["sessions"] and out["flags"] == []
    for d in out["daily"]:
        assert abs(d["ba"] - want["daily_ba"]) < 1e-9 and abs(d["b1"] - want["daily_b1"]) < 1e-9
        assert abs(d["etf"] - want["daily_etf"]) < 1e-9


def test_short_history_beta_and_missing_prices():
    ev = PX["event"]
    px = json.loads(json.dumps(PX["prices"]))
    keep = sorted(px["stock"])[-60:]                     # only 60 closes: < 120 returns for beta
    px["stock"] = {d: px["stock"][d] for d in keep}
    out = ru.compute(ev, px)
    assert out["beta"] == 1.0 and "beta_short" in out["flags"]
    px["stock"].pop("2026-10-20")
    assert ru.compute(ev, px) == {"void": "price_missing"}


def test_grade_is_write_once(root):
    calls = []

    class FakeSec:
        def submission(self, cik):
            return {"filings": {"recent": {"form": [], "items": [], "acceptanceDateTime": []}}}

    def fetch(ev):
        calls.append(ev["ticker"])
        if ev["ticker"] != "GOLD":
            raise ru.FetchFailed("empty stock or SPY series")
        return PX["prices"]
    now = datetime.datetime(2026, 11, 12, 7, 0, tzinfo=ET)   # 07:00 ET on shift(X, 1) for GOLD
    ru.grade("seasonZ", now=now, sec=FakeSec(), fetch=fetch)
    recs = ru.jsonl(str(root / "outcomes" / "shadow" / "seasonZ" / "runup.jsonl"))
    g = recs["seasonZ-GOLD"]
    assert g["X"] == "2026-11-11" and g["D_act"] == "2026-11-12" and abs(g["excess_beta"] - PX["expected"]["excess_beta"]) < 1e-9
    assert recs["seasonZ-EARLY"]["void"] == "print_before_window"
    assert recs["seasonZ-OLD"]["void"] == "window_not_open"
    assert "seasonZ-NONE" not in recs                       # no expected date: not an SH-RU event
    assert "seasonZ-TRUNC" not in recs                      # its fetch failed: nothing stored, retried later
    prices = ru.jsonl(str(root / "outcomes" / "shadow" / "seasonZ" / "runup_prices.jsonl"))
    assert list(prices) == ["seasonZ-GOLD"]
    ru.grade("seasonZ", now=now + datetime.timedelta(days=1), sec=FakeSec(), fetch=fetch)
    assert calls.count("GOLD") == 1                         # graded once, never refetched
    assert calls.count("TRUNC") == 2                        # a failed fetch is retried
    for k in range(2, 12):                                  # 10 distinct failed dates -> VOID price_unavailable
        ru.grade("seasonZ", now=now + datetime.timedelta(days=k), sec=FakeSec(), fetch=fetch)
    recs = ru.jsonl(str(root / "outcomes" / "shadow" / "seasonZ" / "runup.jsonl"))
    assert recs["seasonZ-TRUNC"]["void"] == "price_unavailable"


def test_cbb_and_nw():
    rng = np.random.default_rng(0)
    pos = rng.normal(0.004, 0.01, 80)
    p, se, obs = ru.cbb_p(pos, "H-RU")
    assert p < 0.01 and se > 0 and abs(obs - pos.mean()) < 1e-15
    assert ru.cbb_p(pos, "H-RU") == (p, se, obs)            # deterministic seed by name
    zero = rng.normal(0, 0.01, 80)
    zero -= zero.mean()
    assert 0.3 < ru.cbb_p(zero + 1e-12, "H-RU")[0] < 0.7
    assert ru.nw_t(pos, 5) > 2


def test_kv_fixed_b_null_and_primary(root):
    null = ru.kv_null(0.3)
    assert 2.2 < float(np.quantile(null, 0.95)) < 2.4         # KV (2005) Bartlett: 2.32 at b = 0.3
    rng = np.random.default_rng(3)
    assert ru.kv_p(rng.normal(0.01, 0.01, 60), 20)[0] < 0.05
    with pytest.raises(SystemExit):
        ru.primary_test()                                      # no registered size gate -> no report
    register_gate(root, {"passed": False})
    assert ru.primary_test() == "kv"
    (root / "registry" / "D009_v3_size_gate.json").write_text(json.dumps({"passed": True}))
    with pytest.raises(SystemExit):
        ru.primary_test()                                      # edited after registration -> refused


def test_report_uses_the_registered_primary(root):
    register_gate(root, {"passed": False})
    out = ru.compute(PX["event"], PX["prices"])
    rec = {"key": "seasonZ-GOLD", "season": "seasonZ", "ticker": "GOLD", "aih": True, "E": "2026-10-14",
           "cluster": "semis", "void": None, "flags": [], **out}
    p = root / "outcomes" / "shadow" / "seasonZ"
    p.mkdir(parents=True)
    (p / "runup.jsonl").write_text(json.dumps(rec) + "\n")
    res = ru.report_(["seasonZ"])["tests"]
    assert res["H-RU"]["primary"] == "kv" and res["H-RU"]["status"] == "insufficient"


def register_gate(root, obj):
    import hashlib
    (root / "registry").mkdir(exist_ok=True)
    body = json.dumps(obj).encode()
    (root / "registry" / "D009_v3_size_gate.json").write_bytes(body)
    (root / "registry" / "D009_implementation_v3.sha256").write_text(
        "# test\n" + f"{hashlib.sha256(body).hexdigest()} registry/D009_v3_size_gate.json\n")


def test_sec_date_parse():
    class Sec:
        def submission(self, cik):
            return {"filings": {"recent": {
                "form": ["8-K", "8-K/A", "8-K", "8-K", "10-Q"],
                "items": ["2.02,9.01", "2.02", "7.01", "2.02", ""],
                "acceptanceDateTime": ["2026-11-12T21:05:00.000Z", "2026-11-03T12:00:00.000Z",
                                       "2026-11-01T12:00:00.000Z", "2026-10-15T12:00:00.000Z",
                                       "2026-11-01T12:00:00.000Z"]}}}
    # 21:05 UTC = 16:05 ET Nov 12; the 8-K/A and the 7.01 are ignored; the Oct 15 one is before `after`
    assert ru.sec_date(Sec(), 1, D("2026-10-16")) == D("2026-11-12")
    assert ru.sec_date(Sec(), 1, D("2026-10-01")) == D("2026-10-15")
    assert ru.sec_date(Sec(), None, D("2026-10-01")) is None


def test_one_event_per_issuer_by_cik(root):
    cand = json.loads(json.dumps(CAL["candidates"]))
    cand["candidates"].append({"ticker": "GOLDB", "cluster": "semis", "etf": "SMH", "cik": 1})   # same issuer
    (root / "universe" / "seasonZ" / "candidates.json").write_text(json.dumps(cand))
    assert "GOLDB" not in {e["ticker"] for e in ru.events("seasonZ")}
