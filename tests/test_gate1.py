"""Tests for the Gate 1 report builder (pipeline/gate1.py).

    python -m pytest tests/test_gate1.py -q

One test builds the report from the real pilot outputs (read-only; written to a temporary path, never to
outcomes/). The rest use synthetic inputs under a temporary ROOT.
"""
import json
import os
import subprocess
import sys


HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "pipeline"))
import gate1  # noqa: E402


def git_status():
    return subprocess.run(["git", "status", "--porcelain", "--", "outcomes", "events", "universe", "shadow"],
                          cwd=HERE, capture_output=True, text=True).stdout


def test_pilot_builds_and_writes_only_the_out_path(tmp_path):
    before = git_status()
    out = tmp_path / "gate1_pilot.md"
    gate1.main("pilot", out=str(out))
    md = out.read_text(encoding="utf-8")
    for head in ("# Gate 1 report — pilot", "## 1. D005", "### T2 probabilities", "## 2. D008 — H-S0",
                 "## 3. D009", "## 4. Health numbers", "## 5. Decisions Gate 1 must make"):
        assert head in md
    assert "PILOT: bugs, not findings" in md
    assert "CHARTER I12" in md and "Promote a D009 hypothesis" in md
    assert git_status() == before          # nothing under outcomes/ (or any fenced dir) changed


def full_d005():
    def track(n, lift, p):
        return {"n": n, "event_dates": 29, "buy_share": 0.5, "T0_hit_rate": 0.54, "BUY_hit_rate": 0.54 + lift,
                "lift": lift, "p_one_sided": p, "return_lift": 0.002, "verdict": "no evidence (p=0.300)"}
    t2 = track(150, 0.03, 0.3)
    t2["t2_confidence_missing"] = 2
    t2["probability"] = {"n": 148, "brier": 0.246, "brier_reference_in_sample_base_rate": 0.248, "brier_skill": 0.008,
                         "log_loss": 0.686, "auc": 0.53, "auc_ci90_cluster": [0.47, 0.6], "share_conf_0.45_0.55": 0.62,
                         "calibration": [{"bin": "0.00-0.40", "n": 10, "mean_conf": 0.35, "hit_rate": 0.4},
                                         {"bin": "0.40-0.50", "n": 50, "mean_conf": 0.47, "hit_rate": 0.5}],
                         "confidence_test": {"slope": 0.41, "se_cr1": 0.3, "t_cr1": 1.37, "p_one_sided": 0.09}}
    return {"label": "exploratory (not confirmatory)", "implementation": "registered",
            "counts": {"graded": 150, "event_dates": 29, "void": {"split": 1}, "pending": 0, "ineligible_never_graded": 40},
            "tracks": {"T1": {"all": track(150, -0.01, 0.6)}, "T2": {"all": t2}},
            "T2_vs_T1": {"n_events": 150, "event_dates": 29, "delta": 0.04, "p_one_sided": 0.2, "verdict": "no evidence T2 beats T1 (p=0.200)"},
            "confirmatory": {"registered": False, "note": "none registered"},
            "H_S0": {"n": 150, "dates": 29, "net_mean": 0.0061, "se": 0.0048, "t": 1.27, "p_one_sided": 0.11, "verdict": "no evidence (p=0.110)"}}


def full_d009():
    return {"label": "SHADOW - secondary; never a scored track; INTERIM - no verdict",
            "tests": {"H-M": {"n": 1300, "dates": 29, "mean": 0.004, "t": 1.4, "p_one_sided": 0.08, "p_holm": 0.24, "mde": 0.0071,
                              "status": "interim (monitoring only)"},
                      "H-X": {"n": 120, "dates": 25, "mean": 0.003, "t": 0.9, "p_one_sided": 0.2, "p_holm": 0.4, "mde": 0.008,
                              "status": "interim (monitoring only)"},
                      "H-VOL": {"n": 1250, "dates": 29, "diff": 0.006, "t": 1.1, "p_one_sided": 0.14, "p_holm": 0.28, "mde": 0.013,
                                "status": "interim (monitoring only)"}},
            "sensitivity": {"H-M without unverified/late timing": {"n": 1100, "mean": 0.0045, "p_one_sided": 0.07}},
            "descriptive": {"SH-W net mean (descriptive, D009 §5)": {"n": 250, "dates": 29, "mean": 0.005, "t": 1.0},
                            "SH-W hit": 0.53, "events": {"SH-M": {"total": 1400, "graded": 1300, "void": {"not_domestic_foreign": 50}}}}}


def test_full_report_renders_every_number():
    h = {"missed_windows": 0, "t2_missing": 3, "frozen_pass": 150, "t2_missing_rate": 0.02, "void": 9, "graded_or_void": 150,
         "void_rate": 0.06, "single_source": 0, "fence_breaches": 0, "action_logs": 60, "breach_list": []}
    md = gate1.build("seasonA", full_d005(), "outcomes/reports/seasonA_2026-12-01.json", full_d009(), "saved", h, built="2026-12-01T09:00")
    assert "| T2 | 150 | 29 | 50% | 54.0% | 57.0% | +3.0 | 0.300 | +0.20 |" in md
    assert "**Brier skill 0.008**" in md and "slope 0.410" in md and "one-sided p 0.090" in md
    assert "| 0.40-0.50 | 50 | 0.470 | 50.0% |" in md
    assert "| 150 | 29 | 0.61% | 0.48% | 1.27 | 0.110 | 1.19% |" in md      # H-S0, MDE = 2.487 x se
    assert "| H-M | 1300 | 29 | 0.40% | 1.40 | 0.080 | 0.240 | 0.71% | interim (monitoring only) |" in md
    assert "| VOID | 6.0% (9 of 150 settled PASS) | < 5% | **NO** |" in md
    assert "| T2 missing | 2.0% (3 of 150 frozen PASS) | < 5% | yes |" in md
    assert "Season A is exploratory" in md and "PILOT" not in md


def write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh)


def test_health_counts(tmp_path, monkeypatch):
    root = str(tmp_path)
    monkeypatch.setattr(gate1, "ROOT", root)
    write(os.path.join(root, "universe", "s", "event_status.json"),
          {"events": {"A": {"status": "INELIGIBLE", "reason": "missed_window"}, "B": {"status": "FROZEN"}}})
    write(os.path.join(root, "events", "s", "B_1", "manifest.json"), {"status": "PASS", "notes": []})
    write(os.path.join(root, "events", "s", "C_1", "manifest.json"), {"status": "PASS", "notes": ["T2 frozen as MISSING: capacity"]})
    write(os.path.join(root, "events", "s", "D_1", "manifest.json"), {"status": "INELIGIBLE"})
    write(os.path.join(root, "outcomes", "s", "B_1.json"), {"gate_status": "PASS", "graded": True, "void": None,
                                                           "flags": [], "exits": {"exit_A": {"flags": ["single_source"]}}})
    write(os.path.join(root, "outcomes", "s", "C_1.json"), {"gate_status": "PASS", "graded": False, "void": "split_in_window"})
    write(os.path.join(root, "outcomes", "s", "D_1.json"), {"gate_status": "INELIGIBLE"})
    write(os.path.join(root, "logs", "actions", "2026-10-20T0100Z_1.json"), {"fence_breaches": [{"fence": "outcomes/", "tool": "Read"}]})
    write(os.path.join(root, "logs", "actions", "2026-09-01T0100Z_2.json"), {"fence_breaches": [{"fence": "x", "tool": "y"}]})
    h = gate1.health("s", ("2026-10-01", "2026-11-30"))
    assert h["missed_windows"] == 1
    assert (h["t2_missing"], h["frozen_pass"], h["t2_missing_rate"]) == (1, 2, 0.5)
    assert (h["void"], h["graded_or_void"], h["void_rate"]) == (1, 2, 0.5)
    assert h["single_source"] == 1
    assert (h["fence_breaches"], h["action_logs"]) == (1, 1)           # the September log is outside the window
    assert h["breach_list"] == [{"log": "2026-10-20T0100Z_1.json", "fence": "outcomes/", "tool": "Read"}]


def test_newest_saved_report_wins(tmp_path, monkeypatch):
    root = str(tmp_path)
    monkeypatch.setattr(gate1, "ROOT", root)
    write(os.path.join(root, "outcomes", "reports", "s_2026-11-01.json"), {"v": 1})
    write(os.path.join(root, "outcomes", "reports", "s_2026-12-01.json"), {"v": 2})
    rep, src = gate1.load_d005("s")
    assert rep == {"v": 2} and src == "outcomes/reports/s_2026-12-01.json"
    rep, src = gate1.load_d009("s")
    assert rep is None and src == "no shadow grade for this season"


def test_cli_requires_a_season():
    r = subprocess.run([sys.executable, os.path.join(HERE, "pipeline", "gate1.py")], capture_output=True, text=True)
    assert r.returncode != 0 and "gate1.py <season>" in (r.stderr + r.stdout)
