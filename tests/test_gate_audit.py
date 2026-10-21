"""D016 v1: the gate audit reads gate.json and option_chain.json only, re-runs every D003 v4 check, and scores the
alternatives of registry/D016_gate_audit_v1.md §4 and the decision rule of §5."""
import builtins
import datetime
import io
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pipeline"))
import gate_audit as ga  # noqa: E402


def leg(strike, bid, ask, oi=300):
    return {"strike": strike, "bid": bid, "ask": ask, "openInterest": oi}


def event(root, ticker, spot, strike, calls, puts, status="INELIGIBLE", reason="wide_spread", gap=3, live=True):
    d = os.path.join(root, "events", "seasonA", f"{ticker}_2026-10-20")
    os.makedirs(d, exist_ok=True)
    gate = {"season": "seasonA", "ticker": ticker, "report_date": "2026-10-20", "dry": not live, "in_s2_window": live,
            "status": status, "reason": reason,
            "options": {"spot": spot, "strike": strike, "expiry": "2026-10-23", "expiry_sessions_after_reaction": gap}}
    json.dump(gate, open(os.path.join(d, "gate.json"), "w"))
    json.dump({"expiry": "2026-10-23", "calls": calls, "puts": puts, "all_expiries": ["2026-10-23"]},
              open(os.path.join(d, "option_chain.json"), "w"))
    return d


def rtx_like(root):
    """Call tight, put 12.8% at the gate strike (fails v4), straddle 8.5% (A3 passes); the next strike down has both
    legs under 10% (A1 passes)."""
    return event(root, "RTXX", 192.27, 192.5,
                 calls=[leg(190.0, 6.25, 6.70, 500), leg(192.5, 5.15, 5.40, 515), leg(195.0, 3.80, 4.30, 190)],
                 puts=[leg(190.0, 3.50, 3.85, 400), leg(192.5, 4.40, 5.00, 6), leg(195.0, 4.95, 6.50, 23)])


def clean(root):
    return event(root, "GOOD", 100.0, 100.0, calls=[leg(100.0, 3.0, 3.1, 400)], puts=[leg(100.0, 2.9, 3.0, 400)],
                 status="PASS", reason=None)


def test_never_opens_anything_but_its_two_files(tmp_path, monkeypatch):
    root = str(tmp_path)
    d = rtx_like(root)
    clean(root)
    for name in ("decision.json", "t2g.json", "manifest.json", "factors.json", "dossier.json"):
        json.dump({"poison": name}, open(os.path.join(d, name), "w"))
    for sub in ("outcomes/seasonA/RTXX_2026-10-20.json", "paper/ledger.json", "shadow/c1/x.json"):
        os.makedirs(os.path.dirname(os.path.join(root, sub)), exist_ok=True)
        json.dump({"poison": sub}, open(os.path.join(root, sub), "w"))
    opened = []
    real_open, real_io_open = builtins.open, io.open

    def spy(real):
        def _open(path, *a, **k):
            opened.append(os.path.abspath(str(path)))
            return real(path, *a, **k)
        return _open

    monkeypatch.setattr(builtins, "open", spy(real_open))
    monkeypatch.setattr(io, "open", spy(real_io_open))
    rows, pre, skipped = ga.audit("seasonA", root=root)
    monkeypatch.undo()
    assert len(rows) == 2 and opened  # not vacuous: it read both events
    assert {os.path.basename(p) for p in opened} == {"gate.json", "option_chain.json"}
    assert not [p for p in opened if {"outcomes", "paper", "shadow"} & set(p.split(os.sep))]


def test_the_door_refuses_everything_else(tmp_path):
    for p in ("outcomes/seasonA/gate.json", "paper/option_chain.json", "events/seasonA/X/decision.json",
              "events/seasonA/X/t2g.json"):
        with pytest.raises(PermissionError):
            ga.read_json(os.path.join(str(tmp_path), p))


def test_every_check_is_counted_not_only_the_first(tmp_path):
    root = str(tmp_path)
    event(root, "THIN", 50.0, 50.0, calls=[leg(50.0, 1.0, 1.3, 20)], puts=[leg(50.0, 1.0, 1.3, 20)])
    (row,), _, _ = ga.audit("seasonA", root=root)
    assert row["fails"] == ["wide_spread", "thin_oi"]  # gate.json keeps only wide_spread
    assert row["reproduced"]


def test_alternatives(tmp_path):
    root = str(tmp_path)
    rtx_like(root)
    # cheap options: 0.55/0.62 is 12% of mid but 7 cents, inside the dollar floor
    event(root, "CHEAP", 10.0, 10.0, calls=[leg(10.0, 0.55, 0.62, 400)], puts=[leg(10.0, 0.50, 0.57, 400)])
    rows = {r["ticker"]: r for r in ga.audit("seasonA", root=root)[0]}
    rtx, cheap = rows["RTXX"], rows["CHEAP"]
    assert rtx["fails"] == ["wide_spread"] and rtx["reproduced"]
    assert round(rtx["reading"]["straddle_spread"], 3) == 0.085
    assert {k: v["pass"] for k, v in rtx["alt"].items()} == {"A0": False, "A1": True, "A2": False, "A3": True, "A4": True}
    assert rtx["alt"]["A1"]["strike"] == 190.0
    assert {k: v["pass"] for k, v in cheap["alt"].items()} == {"A0": False, "A1": False, "A2": True, "A3": False, "A4": False}
    assert not cheap["sens"]["leg_0.125"] and cheap["sens"]["leg_0.15"]  # its put leg is 13.1% of mid
    assert not rtx["sens"]["leg_0.125"] and rtx["sens"]["leg_0.15"]  # its put leg is 12.8%


def test_pre_chain_and_dry_gates_are_set_aside(tmp_path):
    root = str(tmp_path)
    clean(root)
    d = os.path.join(root, "events", "seasonA", "UNCF_2026-10-21")
    os.makedirs(d)
    json.dump({"ticker": "UNCF", "report_date": "2026-10-21", "dry": False, "in_s2_window": True,
               "status": "INELIGIBLE", "reason": "unconfirmed"}, open(os.path.join(d, "gate.json"), "w"))
    event(root, "DRYY", 100.0, 100.0, calls=[leg(100.0, 3.0, 3.1)], puts=[leg(100.0, 2.9, 3.0)], live=False)
    rows, pre, skipped = ga.audit("seasonA", root=root)
    assert [r["ticker"] for r in rows] == ["GOOD"] and pre[0]["reason"] == "unconfirmed" and skipped == ["DRYY_2026-10-20"]


def test_decision_rule():
    def row(passes):
        r = {"fails": [] if passes["A0"] else ["wide_spread"], "reading": {"straddle_spread": 0.05,
             "leg_spread": {"call": 0.05, "put": 0.05}}, "alt": {k: {"pass": v} for k, v in passes.items()}}
        return r
    base = dict(A0=False, A1=False, A2=False, A3=False, A4=False)
    one = [row({**base, "A3": True, "A4": True})] + [row({k: True for k in base})] * 3
    assert ga.decide(one)["alternative"] is None  # a 1-name gain keeps v4
    two = one + [row({**base, "A1": True, "A3": True, "A4": True})]
    d = ga.decide(two)
    assert d["gain"]["A3"] == 2 and d["gain"]["A4"] == 2 and d["alternative"] == "A3"  # tie -> A3 before A4


def test_decision_run_waits_for_friday(monkeypatch):
    monkeypatch.setattr(ga, "DECISION_FROM", datetime.datetime(2099, 1, 1, tzinfo=ga.ET))
    with pytest.raises(SystemExit):
        ga.main(["seasonA", "--decision"])


def test_reproduces_every_stored_season_a_gate():
    rows, pre, _ = ga.audit("seasonA")
    if not rows:
        pytest.skip("no Season A gate on disk")
    assert [r["ticker"] for r in rows if not r["reproduced"]] == []
