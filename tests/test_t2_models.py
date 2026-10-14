"""D013: the shadow backends reuse t2_stage2 unchanged - routing to their own model, T2 first, the T2M mean, and
the report's reuse of D005's evaluate via the T2G slot. No network, no git. Run: python -m pytest tests/test_t2_models.py -q"""
import datetime
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
import t2_models as tm  # noqa: E402
import t2_stage2 as ts  # noqa: E402

REPLY = {"prior": {"p": 0.54, "from": "base rate"}, "confidence": 0.61, "thesis": "x", "reasons": ["a", "b"],
         "moved_from_prior": "m", "deciding_variable": "d",
         "theses": [{"expected": "e", "mechanism": "m", "wrong_if": "w"}] * 3, "key_observations": ["k"],
         "items_used": ["I1"]}


@pytest.fixture
def calls(monkeypatch):
    seen = []

    def fake_claude(rule, sys_prompt, user):
        seen.append(rule["t2_model"])
        text = json.dumps(REPLY) if sys_prompt == ts.SYSTEM else "I don't know."
        return {"ok": True, "limited": False, "text": text, "model": rule["t2_model"], "isolation": {"tools": []}}
    monkeypatch.setattr(ts, "call_claude", fake_claude)
    monkeypatch.setattr(ts, "call", tm._ORIG_CALL)
    yield seen
    for b in tm.MODELS:
        ts.BACKENDS.pop(b, None)


def event(tmp_path):
    e = tmp_path / "seasonA" / "XYZ_2026-10-20"
    e.mkdir(parents=True)
    gate = {"ticker": "XYZ", "report_date": "2026-10-20", "session": "AMC", "captured_et": "2026-10-19T14:31:00-04:00",
            "timing": {"entry": {"session": "2026-10-20"}, "exit_A": {"session": "2026-10-21"}}}
    (e / "gate.json").write_text(json.dumps(gate))
    (e / "dossier.json").write_text(json.dumps({"items": [{"id": "I1", "kind": "release", "source": "s",
                                                           "published": "2026-10-01"}], "missing": []}))
    return str(e)


def test_shadow_backends_route_to_their_own_model(tmp_path, calls, monkeypatch):
    monkeypatch.setattr(ts, "now_et", lambda: datetime.datetime(2026, 10, 19, 20, 0, tzinfo=ts.ET))
    tm.configure()
    rule = {"id": "D004_decision_protocol_v4", "t2_model": "claude-sonnet-5-5"}
    edir = event(tmp_path)
    out = ts.decide("seasonA", edir, "opus", rule, write=False)
    assert out["track"] == "T2O" and out["t2"]["model"] == "claude-opus-5-5" and out["t2"]["decision"] == "BUY"
    assert calls == ["claude-opus-5-5", "claude-opus-5-5"]           # the probe and the decision
    out = ts.decide("seasonA", edir, "sonnet_r", rule, write=False)
    assert out["track"] == "T2R" and calls[-1] == "claude-sonnet-5-5"
    out = ts.decide("seasonA", edir, "claude", rule, write=False)     # T2 itself is untouched
    assert out["track"] == "T2" and calls[-1] == "claude-sonnet-5-5"
    assert ts.BACKENDS["claude"]["file"] == "t2.json" and ts.BACKENDS["opus"]["file"] == "t2o.json"


def test_t2_first_order_and_budget(monkeypatch, calls, tmp_path):
    ran = []
    monkeypatch.setattr(tm, "drift", lambda: [])
    monkeypatch.setattr(tm, "ROOT", str(tmp_path))
    monkeypatch.setattr(ts, "waiting", lambda b: ["something"] if b == "claude" else [])
    monkeypatch.setattr(ts, "run", lambda bs: ran.append((bs, ts.waiting(bs[0]))))
    tm.run(["opus"])
    assert ran == []                                                  # T2 still waiting: shadows wait
    todo = [("seasonA", f"e{i}", {}) for i in range(20)]
    monkeypatch.setattr(ts, "waiting", lambda b: [] if b == "claude" else todo)
    tm.run(["opus", "sonnet_r"])
    assert [r[0] for r in ran] == [["sonnet_r"], ["opus"]]            # the replicate first
    assert all(len(r[1]) == tm.RUN_CAP for r in ran)                  # per-run cap
    # trailing 7-day cap: 75 decided sonnet_r logs leave room for 5
    logs = tmp_path / "logs" / "t2"
    logs.mkdir(parents=True)
    now = tm.now_et()
    for i in range(75):
        (logs / f"E{i}_sonnet_r_x.json").write_text(json.dumps({"outcome": "decided", "called_et": now.isoformat()}))
    (logs / "old_sonnet_r_x.json").write_text(json.dumps(
        {"outcome": "decided", "called_et": (now - datetime.timedelta(days=8)).isoformat()}))
    ran.clear()
    tm.run(["sonnet_r"])
    assert len(ran[0][1]) == tm.WEEK_CAP - 75
    assert ts.waiting("claude") == []                                 # the real waiting is restored


def test_drift_refuses(monkeypatch):
    monkeypatch.setattr(tm, "drift", lambda: ["pipeline/t2_stage2.py differs"])
    with pytest.raises(SystemExit):
        tm.run(["opus"])


def test_model_check_rejects_a_substituted_model(tmp_path, monkeypatch):
    monkeypatch.setattr(ts, "call", tm._ORIG_CALL)
    monkeypatch.setattr(ts, "call_claude", lambda rule, s, u: {"ok": True, "limited": False, "text": "x",
                                                               "model": "claude-haiku-5-5",
                                                               "isolation": {"model": "claude-haiku-5-5"}})
    tm.configure()
    try:
        res = ts.call("opus", {"t2_model": "claude-sonnet-5-5"}, "s", "u")
        assert not res["ok"] and "model check failed" in res["error"]
        res = ts.call("sonnet_r", {"t2_model": "claude-sonnet-5-5"}, "s", "u")
        assert not res["ok"]
    finally:
        for bk in tm.MODELS:
            ts.BACKENDS.pop(bk, None)


def test_write_path_stages_only_shadow_files(tmp_path, calls, monkeypatch):
    """The real decide(write=True) + freeze_stage2 for a shadow: only t2o files, its manifest, tokens and opus logs."""
    import hashlib
    monkeypatch.setattr(ts, "ROOT", str(tmp_path))
    monkeypatch.setattr(ts, "now_et", lambda: datetime.datetime(2026, 10, 19, 20, 0, tzinfo=ts.ET))
    edir = event(tmp_path)
    d = open(os.path.join(edir, "dossier.json"), "rb").read().replace(b"\r\n", b"\n")
    (tmp_path / "seasonA" / "XYZ_2026-10-20" / "manifest.json").write_text(json.dumps(
        {"sha256": {"dossier.json": hashlib.sha256(d).hexdigest()}, "entry_open_et": "2026-10-20T09:30:00-04:00"}))
    added = []
    monkeypatch.setattr(ts, "timestamp", lambda digest, edir, stem: ([f"{stem}.tsr_x"], []))
    monkeypatch.setattr(ts, "push_all", lambda: {"origin": True})

    def git(*a, **k):
        if a[0] == "add":
            added.extend(a[1:])
        return "2026-10-19T20:00:01-04:00" if a[0] == "log" else ""
    monkeypatch.setattr(ts, "git", git)
    tm.configure()
    rule = {"id": "D004_decision_protocol_v4", "t2_model": "claude-sonnet-5-5"}
    out = ts.decide("seasonA", edir, "opus", rule, write=True)
    assert out.startswith("done: BUY 0.61") and "BLIND" in out
    names = [os.path.basename(x) for x in added]
    shadow = {"manifest_t2o.json", "manifest_t2o.tsr_x", "t2o.json", "t2o_thesis.md"}
    assert shadow <= set(names) and len(names) == 5
    assert all("_opus_" in n for n in names if n not in shadow)
    assert not os.path.exists(os.path.join(edir, "t2.json"))


def graded_row(t2c, win):
    return {"ticker": "XYZ", "report_date": "2026-10-20", "entry_session": "2026-10-20", "graded": True,
            "decisions": {"T0": "BUY", "T2": "BUY" if t2c > 0.5 else "NO_BUY"}, "t2_confidence": t2c,
            "stage2": {"T2": "frozen before the entry open"}, "exits": {"exit_A": {"WIN_raw": win, "raw_return": 0.01}}}


def test_t2m_is_the_mean_of_three_frozen_tracks(tmp_path, monkeypatch):
    monkeypatch.setattr(tm, "ROOT", str(tmp_path))
    e = tmp_path / "events" / "seasonA" / "XYZ_2026-10-20"
    e.mkdir(parents=True)
    (e / "manifest.json").write_text(json.dumps({"entry_open_et": "2026-10-20T09:30:00-04:00"}))
    (tmp_path / "registry").mkdir()
    (tmp_path / "registry" / "D004_decision_protocol_v4.json").write_text(json.dumps({"t2_model": "claude-sonnet-5-5"}))
    (e / "t2o.json").write_text(json.dumps({"t2": {"decision": "BUY", "confidence": 0.70, "model": "claude-opus-5-5",
                                                   "leak_probe": "I don't know."}}))
    (e / "t2r.json").write_text(json.dumps({"t2": {"decision": "NO_BUY", "confidence": 0.40, "model": "claude-sonnet-5-5"}}))
    monkeypatch.setattr(tm, "frozen_before_entry", lambda edir, m, eo: True)
    r = tm.shadow_row(graded_row(0.55, True), "seasonA")
    assert r["d013_confidence"] == {"T2O": 0.70, "T2R": 0.40, "T2": 0.55, "T2M": round((0.55 + 0.40 + 0.70) / 3, 4)}
    assert r["decisions"]["T2M"] == "BUY" and r["correct"]["T2R"] is False and r["correct"]["T2O"] is True
    # a shadow frozen too late (or not at all) is absent, and T2M then does not exist
    monkeypatch.setattr(tm, "frozen_before_entry", lambda edir, m, eo: m != "manifest_t2r.json")
    r = tm.shadow_row(graded_row(0.55, True), "seasonA")
    assert "T2R" not in r["decisions"] and "T2M" not in r["decisions"]
    # a frozen file from another model never counts
    monkeypatch.setattr(tm, "frozen_before_entry", lambda edir, m, eo: True)
    (e / "t2o.json").write_text(json.dumps({"t2": {"decision": "BUY", "confidence": 0.70, "model": "claude-haiku-5-5"}}))
    r = tm.shadow_row(graded_row(0.55, True), "seasonA")
    assert "T2O" not in r["decisions"] and r["d013_excluded"] == ["T2O: model claude-haiku-5-5"]


def test_as_slot_reuses_the_t2g_slot():
    r = graded_row(0.55, True)
    r["decisions"]["T2O"] = "NO_BUY"
    r["d013_confidence"] = {"T2O": 0.3}
    out = tm.as_slot([r, graded_row(0.6, False)], "T2O")
    assert len(out) == 1 and out[0]["decisions"]["T2G"] == "NO_BUY" and out[0]["t2g_confidence"] == 0.3
    assert r["decisions"].get("T2G") is None                          # the original row is not modified
