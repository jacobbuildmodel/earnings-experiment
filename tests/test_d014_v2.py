"""D014 v2: ret5 / rel5 build on a fake price layer, the 18-test family, the CR1 difference test, survivors,
validation, small-ticket costs. Run: python -m pytest tests/test_d014_v2.py -q"""
import csv
import datetime
import gzip
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "analysis", "d014"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
import fetch  # noqa: E402
import fetch_v2  # noqa: E402
import run_d014 as rd  # noqa: E402
import run_d014_v2 as r2  # noqa: E402


def test_build_ret5_rel5():
    sessions = [datetime.date(2025, 3, 1) + datetime.timedelta(days=i) for i in range(10)]
    px = {"X": {d: 100.0 + i for i, d in enumerate(sessions)}, "SOXX": {d: 50.0 for d in sessions},
          "SPY": {d: 500.0 * (1 + 0.01 * i) for i, d in enumerate(sessions)}, "IBIT": None}
    evs = [{"ticker": "X", "exit_A": sessions[8].isoformat()}, {"ticker": "M", "exit_A": sessions[8].isoformat()}]
    rows, failed = fetch_v2.build(evs, sessions, {"X": "SOXX", "M": "IBIT"}, lambda s: px.get(s))
    x, m = rows
    assert abs(x["ret5"] - ((100 + 7) / (100 + 2) - 1)) < 1e-12               # close R-1 / close R-6
    assert abs(x["rel5"] - (0 - (1.07 / 1.02 - 1))) < 1e-12
    assert m["ret5"] is None and m["rel5"] is None and "IBIT" in failed


def test_diff_cell_matches_means_and_cluster_formula():
    rng = random.Random(3)
    a = [{"y": {"5": rng.gauss(0.01, 0.02)}, "R": f"d{i % 20}"} for i in range(200)]
    b = [{"y": {"5": rng.gauss(0.0, 0.02)}, "R": f"d{i % 20}"} for i in range(300)]
    c = r2.diff_cell(a, b, "5")
    ma = sum(e["y"]["5"] for e in a) / 200
    mb = sum(e["y"]["5"] for e in b) / 300
    assert abs(c["diff"] - (ma - mb)) < 1e-12 and c["se"] > 0
    # cross-check against the textbook CR1 sandwich with numpy
    import numpy as np
    X = np.array([[1, 1]] * 200 + [[1, 0]] * 300, float)
    y = np.array([e["y"]["5"] for e in a + b])
    g = [e["R"] for e in a + b]
    beta = np.linalg.solve(X.T @ X, X.T @ y)
    u = y - X @ beta
    meat = sum(np.outer(X[[i for i, k in enumerate(g) if k == c_]].T @ u[[i for i, k in enumerate(g) if k == c_]],
                        X[[i for i, k in enumerate(g) if k == c_]].T @ u[[i for i, k in enumerate(g) if k == c_]])
               for c_ in set(g))
    inv = np.linalg.inv(X.T @ X)
    V = inv @ meat @ inv * (20 / 19) * (499 / 498)
    assert abs(c["se"] - math.sqrt(V[1, 1])) < 1e-12


def synthetic(tmp_path, monkeypatch, effect, seed=2):
    rng = random.Random(seed)
    (tmp_path / "raw").mkdir()
    rows, v2 = [], []
    days = [datetime.date(2022, 9, 5) + datetime.timedelta(days=i) for i in range(0, 1470, 2)]
    for d in days:
        if d > datetime.date(2026, 9, 18):
            continue
        seg = "TRAIN" if d <= datetime.date(2025, 8, 31) else "VALIDATION"
        for j in range(8):
            g = rng.choice([-1, 1]) * rng.uniform(0.012, 0.1)
            c0 = 100.0
            pm = c0 * (1 + g)
            o = pm
            s = 1 if g > 0 else -1
            ret5 = rng.uniform(-0.2, 0.2)
            drift = effect if (s == 1 and ret5 <= -0.08) else 0.0
            path, x = {}, o
            for h in (5, 10, 30, 60):
                x *= 1 + drift + rng.gauss(0, 0.004)
                path[h] = x
            rows.append({"ticker": f"T{j}", "date": d.isoformat(), "session": ("BMO", "AMC")[j % 2], "cluster": "c", "R": d.isoformat(),
                         "segment": seg, "mcap": 5e9, "c0": c0, "c0_src": "auction", "pm": pm, "o": o,
                         "o_src": "auction", **{f"p{h}": path[h] for h in path}, "pc": x, "pc_src": "auction",
                         "hs0935": 0.0004, "hs0940": 0.0004, "hs1000": 0.0004, "hs1030": 0.0004,
                         "mid0935": path[5], "mid0940": path[10], "mid1000": path[30], "mid1030": path[60],
                         "pmv": rng.random(), "split_check": "ok", "void": "", "spy_c0": 500, "spy_pm": 501,
                         "spy_o": 500, **{f"spy_p{h}": 500 for h in (5, 10, 30, 60)}, "spy_pc": 500, "surprise": 1.0})
            v2.append({"ticker": f"T{j}", "R": d.isoformat(), "etf": "SOXX", "ret5": ret5, "etf_ret5": 0, "spy_ret5": 0,
                       "rel5": rng.uniform(-0.05, 0.05)})
    with gzip.open(tmp_path / "raw" / "events_intraday.csv.gz", "wt", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fetch.FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    with open(tmp_path / "raw" / "events_v2.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fetch_v2.FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(v2)
    (tmp_path / "analysis" / "d010").mkdir(parents=True)
    (tmp_path / "analysis" / "d010" / "events_valid.csv").write_text("symbol,R,strike,spot_P,implied\n")
    monkeypatch.setattr(rd, "HERE", str(tmp_path))
    monkeypatch.setattr(rd, "ROOT", str(tmp_path))


def test_null_and_planted_washout(tmp_path, monkeypatch):
    synthetic(tmp_path, monkeypatch, effect=0.0)
    r2.main()
    res = json.load(open(tmp_path / "results_v2.json"))
    assert len(res["train_family"]) == 18 and res["survivors"] == []
    assert "v1 all|d" in res["secondary_small_ticket"]                     # reported whatever v1 said
    d = res["secondary_small_ticket"]["v1 all|d"]
    assert set(d) == {"follow", "fade"}
    f = d["follow"]["train"]
    assert abs((f["net_2bp"] - f["net_13bp"]) - 0.0011) < 1e-12


def test_planted_washout_continuation_is_a_candidate(tmp_path, monkeypatch):
    synthetic(tmp_path, monkeypatch, effect=0.003)
    r2.main()
    res = json.load(open(tmp_path / "results_v2.json"))
    assert "C7_washed_out|30" in res["survivors"] and "C7_minus_C8|30" in res["survivors"]
    assert res["survivors_validation"]["C7_washed_out|30"]["verdict"] == "CANDIDATE"
    assert res["survivors_validation"]["C7_minus_C8|30"]["verdict"] == "CANDIDATE"
    assert not any(k.startswith("C9_minus_C10") for k in res["survivors"])   # washouts sit in both sector groups
