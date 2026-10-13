"""D014 code on synthetic data: auction and bar prices, delayed opens, the pre-market signal, the split check, a fake
API for build_date, the 42-test family, CR1, BH, Holm, costs, survivors and voids.
Run: python -m pytest tests/test_d014.py -q"""
import csv
import datetime
import gzip
import json
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "analysis", "d014"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
import fetch  # noqa: E402
import run_d014 as rd  # noqa: E402

D = datetime.date(2025, 3, 4)
R1 = datetime.date(2025, 3, 3)
UTC = datetime.timezone.utc


def ts(day, hhmm):
    return fetch.at(day, hhmm).astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def bar(hhmm, o, c, v=100, day=D):
    return {"t": ts(day, hhmm), "o": o, "c": c, "v": v}


def test_prices_auction_first_then_bars():
    minute = {"X": [bar("08:00", 9, 9.5), bar("09:30", 10.1, 10.2), bar("09:33", 10.3, 10.4), bar("09:59", 11, 11.1),
                    bar("15:59", 12, 12.5)]}
    auc = {"X": [{"d": "2025-03-03", "c": [{"p": 9.0, "s": 5}, {"p": 9.9, "s": 1000}]},
                 {"d": "2025-03-04", "o": [{"p": 9.7, "s": 5000, "t": ts(D, "04:00")},     # early-open print: dropped
                                           {"p": 10.0, "s": 800, "t": ts(D, "09:30")}, {"p": 10.05, "s": 2, "t": ts(D, "09:30")}],
                  "c": []}]}
    p = fetch.prices("X", D, R1, minute, {}, auc)
    assert p["c0"] == 9.9 and p["c0_src"] == "auction"
    assert p["o"] == 10.0 and p["o_src"] == "auction"
    assert p["p5"] == 10.4 and p["p10"] == 10.4 and p["p30"] == 11.1 and p["p60"] == 11.1
    assert p["pc"] == 12.5 and p["pc_src"] == "close_from_bar"
    p = fetch.prices("X", D, R1, minute, {}, {})
    assert p["o"] == 10.1 and p["o_src"] == "open_from_bar" and p["c0"] is None


def test_delayed_open_blanks_early_horizons():
    minute = {"X": [bar("09:30", 10, 10), bar("09:41", 10.5, 10.6), bar("09:50", 10.7, 10.8)]}
    auc = {"X": [{"d": "2025-03-04", "o": [{"p": 10.5, "s": 900, "t": ts(D, "09:41")}]}]}
    p = fetch.prices("X", D, R1, minute, {}, auc)
    assert p["p5"] is None and p["p10"] is None and p["p30"] == 10.8


def test_premarket_signal_respects_release_and_cut():
    minute = {"X": [bar("07:00", 10, 10.0), bar("09:20", 11, 11.2), bar("09:27", 12, 12.0)]}
    after = {"X": [bar("16:30", 10, 10.9, day=R1)]}
    acc = fetch.at(D, "08:00")
    assert fetch.premarket("X", D, minute, {}, acc)[0] == 11.2          # 09:27 bar excluded, 07:00 is pre-release
    assert fetch.premarket("X", D, {"X": minute["X"][:1]}, {}, acc) == (None, None)
    acc_amc = fetch.at(R1, "16:05")
    assert fetch.premarket("X", D, {"X": []}, after, acc_amc)[0] == 10.9


def fake_api(monkeypatch, split_close=None):
    calls = []
    sessions = [R1 - datetime.timedelta(days=i) for i in range(40, 0, -1)] + [R1, D]
    daily_x = [{"t": f"{d.isoformat()}T05:00:00Z", "o": 1, "c": 10.0, "v": 1000} for d in sessions]

    def get(path, params):
        calls.append((path, dict(params)))
        if path == "bars" and params["timeframe"] == "1Min" and params["start"] == ts(D, "04:00"):
            return {"bars": {"X": [bar("08:30", 10.5, 10.6), bar("09:30", 10.6, 10.7), bar("09:34", 10.7, 10.8)],
                             "SPY": [bar("09:00", 500, 501), bar("09:30", 501, 502)]}}
        if path == "bars" and params["timeframe"] == "1Min":
            return {"bars": {"X": [bar("16:10", 10, 10.4, v=500, day=R1)]}}
        if path == "bars" and params["adjustment"] == "split":
            return {"bars": {"X": [{"t": f"{R1}T05:00:00Z", "c": split_close or 10.0},
                                   {"t": f"{D}T05:00:00Z", "c": 10.0}]}}
        if path == "bars":
            return {"bars": {"X": daily_x, "SPY": daily_x}}
        if path == "auctions":
            return {"auctions": {"X": [{"d": str(R1), "c": [{"p": 10.0, "s": 99}]},
                                       {"d": str(D), "o": [{"p": 10.6, "s": 99, "t": ts(D, "09:30")}], "c": [{"p": 11, "s": 9}]}],
                                 "SPY": [{"d": str(R1), "c": [{"p": 500, "s": 9}]},
                                         {"d": str(D), "o": [{"p": 501, "s": 9, "t": ts(D, "09:30")}]}]}}
        if path.endswith("/quotes"):
            return {"quotes": [{"bp": 10.7, "ap": 10.9}]}
        raise AssertionError(path)
    monkeypatch.setattr(fetch, "get", get)
    monkeypatch.setattr(fetch.time, "sleep", lambda s: None)
    return calls, sessions


def test_build_date_on_a_fake_api(monkeypatch):
    calls, sessions = fake_api(monkeypatch)
    ev = {"ticker": "X", "date": str(R1), "session": "AMC", "cluster": "c", "exit_A": str(D),
          "accepted_et": "2025-03-03T16:05:00-05:00", "factors": {"market_cap_pit": 5e9}}
    row, = fetch.build_date(D, [ev], sessions, {"X": [[str(R1), 7.5]]})
    assert row["void"] == "" and row["c0"] == 10.0 and row["o"] == 10.6 and row["pm"] == 10.6
    assert row["p5"] == 10.8 and row["pc"] == 11 and row["split_check"] == "ok" and row["surprise"] == 7.5
    assert abs(row["pmv"] - (100 + 500) / 1000) < 1e-12                 # R pre-market (08:30) + R-1 after hours
    assert abs(row["hs0935"] - 0.2 / 21.6) < 1e-12 and row["mid0935"] == 10.8
    assert row["spy_pm"] == 501 and row["spy_o"] == 501
    for path, p in calls:                                                # every end is a timestamp, never a bare date
        if "end" in p:
            assert "T" in p["end"]


def test_split_tolerance(monkeypatch):
    ev = {"ticker": "X", "date": str(R1), "session": "BMO", "cluster": "c", "exit_A": str(D), "accepted_et": None}
    calls, sessions = fake_api(monkeypatch, split_close=10.00001 * 1.0)  # rounding noise: not a split
    assert fetch.build_date(D, [ev], sessions, {})[0]["split_check"] == "ok"
    calls, sessions = fake_api(monkeypatch, split_close=10.0 / 3)        # 3:1 between R-1 and R
    assert fetch.build_date(D, [ev], sessions, {})[0]["void"] == "split"


def synthetic(tmp_path, monkeypatch, drift=0.0, seed=1):
    rng = random.Random(seed)
    (tmp_path / "raw").mkdir()
    rows = []
    days = [datetime.date(2023, 1, 2) + datetime.timedelta(days=i) for i in range(0, 1200, 3)]
    for d in days:
        if d > datetime.date(2026, 9, 18):
            continue
        seg = "TRAIN" if d <= datetime.date(2025, 8, 31) else "VALIDATION"
        for j in range(6):
            c0 = 100.0
            g = rng.choice([-1, 1]) * rng.uniform(0.002, 0.1)
            pm = c0 * (1 + g)
            o = pm * (1 + rng.gauss(0, 0.002))
            s = 1 if g > 0 else -1
            path, x = {}, o
            for h in (5, 10, 30, 60):
                x *= 1 + s * drift + rng.gauss(0, 0.004)
                path[h] = x
            pc = x * (1 + rng.gauss(0, 0.01))
            rows.append({"ticker": f"T{j}", "date": d.isoformat(), "session": rng.choice(["AMC", "BMO"]), "cluster": "c",
                         "R": d.isoformat(), "segment": seg, "mcap": rng.choice([5e9, 20e9]), "c0": c0,
                         "c0_src": "auction", "pm": pm, "o": o, "o_src": "auction", **{f"p{h}": path[h] for h in path},
                         "pc": pc, "pc_src": "auction", "hs0935": 0.0005, "hs0940": 0.0005, "hs1000": 0.0004,
                         "hs1030": 0.0004, "mid0935": path[5], "mid0940": path[10], "mid1000": path[30],
                         "mid1030": path[60], "pmv": rng.random(), "split_check": "ok", "void": "", "spy_c0": 500,
                         "spy_pm": 500 * (1 + rng.gauss(0, 0.003)), "spy_o": 500,
                         **{f"spy_p{h}": 500 for h in (5, 10, 30, 60)}, "spy_pc": 501, "surprise": rng.gauss(0, 5)})
    rows.append({**rows[0], "void": "no_open"})
    with gzip.open(tmp_path / "raw" / "events_intraday.csv.gz", "wt", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fetch.FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    d010 = tmp_path / "analysis" / "d010"
    d010.mkdir(parents=True)
    (d010 / "events_valid.csv").write_text("symbol,R,strike,spot_P,implied\nT0,2023-01-02,100,100,0.05\n"
                                           "T1,2023-01-02,300,100,0.05\n")
    monkeypatch.setattr(rd, "HERE", str(tmp_path))
    monkeypatch.setattr(rd, "ROOT", str(tmp_path))
    return rows


def test_null_has_no_survivor(tmp_path, monkeypatch):
    rows = synthetic(tmp_path, monkeypatch, drift=0.0)
    rd.main()
    res = json.load(open(tmp_path / "results.json"))
    assert len(res["step3_train_family"]) == 42
    assert res["step1"]["voids_by_reason_year"] == {"no_open|2023": 1}
    below = sum(1 for r in rows[:-1] if abs(r["pm"] / r["c0"] - 1) < 0.01)
    assert res["step1"]["below_1pct_gap_floor"] == below > 0
    assert res["survivors"] == [] and "no first-hour pattern" in res["verdict"][0]
    assert (tmp_path / "REPORT.md").exists()


def test_strong_continuation_survives_and_validates(tmp_path, monkeypatch):
    synthetic(tmp_path, monkeypatch, drift=0.003)
    rd.main()
    res = json.load(open(tmp_path / "results.json"))
    assert "all|30" in res["survivors"] and res["step3_train_family"]["all|30"]["t"] > 3
    v = res["step5_6_survivors"]["all|30"]
    assert v["train_net"]["side"] == "follow" and v["verdict"] == "CANDIDATE"
    assert v["validation_holm_p"] >= v["validation_one_sided_p"]


def test_cr1_bh_holm():
    m, se = rd.cr1([1.0, 1.0, -1.0, -1.0], ["a", "a", "b", "b"])
    assert m == 0 and abs(se - 1.0) < 1e-12                            # sqrt(G/(G-1) * (2^2 + 2^2)) / n = 4 / 4
    q = rd.bh({"a": 0.01, "b": 0.04, "c": 0.5})
    assert abs(q["a"] - 0.03) < 1e-12 and abs(q["b"] - 0.06) < 1e-12 and q["c"] == 0.5
    h = rd.holm({"a": 0.01, "b": 0.04, "c": 0.5})
    assert abs(h["a"] - 0.03) < 1e-12 and abs(h["b"] - 0.08) < 1e-12 and h["c"] == 0.5
