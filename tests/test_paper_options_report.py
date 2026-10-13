"""D011 §8 report (implementation v3): real / simulated / adopted classes, execution from settle()'s field,
exit_late cuts, SH-X pairing with the right sign per side, PX-L/PX-F pairing, season from the key, labels and
flags. Run: python -m pytest tests/test_paper_options_report.py -q"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
import paper_options_report as rep  # noqa: E402


def trade(t, date, pnl, sim=(), late=False, status="PASS", session="AMC", adopted=False, natural=-10.0,
          gap=-0.05, execution=True, structure="F"):
    res = {"pnl_on_spot": pnl, "pnl": round(pnl * 10000, 2), "simulated_legs": list(sim)}
    if execution and "open" not in sim and not adopted:
        res["entry_vs_alpaca_natural"] = gap
        if structure == "F":
            res["entry_credit_vs_gate_bid_sum"] = -1.0
    return {"season": "seasonA", "ticker": t, "report_date": date, "session": session, "gate_status": status,
            "snapshot_session": date, "exit_late": late, "result": res,
            "orders": {"open": [{"natural": natural, "adopted": adopted, "filled_qty": 1.0}]}}


@pytest.fixture
def root(tmp_path, monkeypatch):
    monkeypatch.setattr(rep, "ROOT", str(tmp_path))
    (tmp_path / "paper").mkdir()

    def ledger(name, trades):
        (tmp_path / "paper" / name).write_text(json.dumps(
            {"trades": {(k or f"seasonA-{t['ticker']}-{t['report_date']}-x"): t for k, t in trades}}))
    g = tmp_path / "outcomes" / "shadow" / "seasonA"
    g.mkdir(parents=True)
    (g / "graded.json").write_text(json.dumps({"events": [
        {"track": "SH-X", "ticker": "A", "date": "2026-10-20", "graded": True, "void": None, "straddle": {"pnl_on_spot": 0.012}},
        {"track": "SH-X", "ticker": "B", "date": "2026-10-21", "graded": True, "void": "print_late", "straddle": {"pnl_on_spot": 0.5}}]}))
    return tmp_path, ledger


def test_classes_execution_and_cuts(root):
    tmp, ledger = root
    f = [trade("A", "2026-10-20", 0.01),
         trade("B", "2026-10-21", -0.02, late=True),
         trade("C", "2026-10-22", 0.03, sim=["open", "close"]),
         trade("D", "2026-10-23", 0.02, adopted=True),                       # adopted: real P&L, no execution
         trade("E", "2026-10-23", 0.0, status="INELIGIBLE", session="BMO"),
         trade("H", "2026-10-24", -0.04, sim=["close"])]                     # held past expiry: real open fill
    keyed = [(None, t) for t in f] + [
        ("seasonA-F-2026-10-24-F", {"key": "seasonA-F-2026-10-24-F", "ticker": "F", "report_date": "2026-10-24",
                                    "skipped": "no_wing_strike"}),          # no season field: taken from the key
        ("seasonB-Z-2027-01-20-F", {"key": "seasonB-Z-2027-01-20-F", "ticker": "Z", "report_date": "2027-01-20",
                                    "skipped": "missed_entry_window"}),     # another season: excluded
        ("seasonA-O-2026-10-24-F", {"key": "seasonA-O-2026-10-24-F", "ticker": "O", "report_date": "2026-10-24",
                                    "orphan_order": {"id": "x"}}),
        (None, {"season": "seasonA", "ticker": "G", "report_date": "2026-10-24", "open_failed": "capacity",
                "orders": {"open": [{"reject_kind": "capacity", "sent_et": "2026-10-23T15:00:00-04:00"}]}})]
    ledger("options_ledger.json", keyed)
    ledger("long_ledger.json", [(None, trade("A", "2026-10-20", -0.015, gap=0.04, natural=8.0, structure="L"))])
    out = rep.report("seasonA")
    F = out["PX-F"]
    assert F["records"] == 9 and F["real_round_trips"] == 4 and F["simulated"] == 2 and F["adopted"] == 1
    assert abs(F["pnl_real"]["all"]["mean_pnl_on_spot"] - (0.01 - 0.02 + 0.02 + 0.0) / 4) < 1e-12
    assert F["pnl_real"]["without_exit_late"]["n"] == 3
    assert F["pnl_all_simulated_labelled"]["all"]["n"] == 6
    ex = F["execution"]
    assert ex["n"] == 4                                                     # A, B, E, H (not C simulated, not D adopted)
    assert abs(ex["mean_fill_minus_natural_share_of_premium"] + 0.005) < 1e-12
    assert "mean_credit_minus_gate_bid_sum (wings included, NOT pure execution)" in ex
    assert F["pnl_real"]["splits"]["by_gate_status"]["PASS"]["n"] == 3
    assert F["pnl_real"]["splits_without_exit_late"]["by_session"]["BMO"]["n"] == 1
    assert F["paired_with_SH_X"]["all"]["n"] == 1                          # B's SH-X is void
    assert abs(F["paired_with_SH_X"]["all"]["mean_paper_minus_SH_X"] - (0.01 - 0.012)) < 1e-12
    assert F["capacity_refusals_by_date"] == {"2026-10-23": 1}
    assert F["labels"]["no_wing_strike"] == 1 and F["labels"]["orphan_order"] == 1 and "missed_entry_window" not in F["labels"]
    assert F["flags"]["orphan_order"] == 1 and F["flags"]["exit_late"] == 1
    assert F["pnl_real"]["all"]["status"] == "insufficient" and ex["status"] == "insufficient"
    assert F["pnl_real"]["all"]["median_pnl_on_spot"] == (0.0 + 0.01) / 2   # even n: mean of the middle two
    L = out["PX-L"]
    assert "mean_credit_minus_gate_bid_sum (wings included, NOT pure execution)" not in L["execution"]
    assert abs(L["paired_with_SH_X"]["all"]["mean_paper_plus_SH_X (opposite sides)"] - (-0.015 + 0.012)) < 1e-12
    P = out["PX-L_and_PX-F_paired"]["all"]
    assert P["n"] == 1 and abs(P["mean_sum (~ minus the shared body's round-trip cost, plus the wings' P&L)"] - (0.01 - 0.015)) < 1e-12


def test_missing_ledger_is_reported_not_fatal(root):
    tmp, ledger = root
    ledger("options_ledger.json", [])
    out = rep.report("seasonA")
    assert "note" in out["PX-L"] and out["PX-F"]["records"] == 0
    assert out["PX-L_and_PX-F_paired"]["all"]["n"] == 0
