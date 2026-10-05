"""D004 v4 (pipeline/dossier.py, pipeline/t2_stage2.py, freeze.decision_problems): offline tests."""
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pipeline"))
import dossier  # noqa: E402
import t2_stage2  # noqa: E402
from common import ET  # noqa: E402
from freeze import decision_problems  # noqa: E402

FILLER = "Revenue grew in the quarter driven by demand. " * 80


def test_mda_skips_toc_and_cross_reference():
    text = ("Table of Contents Item 2. Management's Discussion and Analysis of Financial Condition 18 Item 3. "
            "Quantitative and Qualitative Disclosures 30 Item 4. Controls 31 "
            "risk is described under Item 2 - Management's Discussion and Analysis of Financial Condition "
            + FILLER[:900] + " Item 2. M anagement's Discussion and Analysis of Financial Condition and Results Overview "
            + FILLER + " see Part II, Item 4 of this report " + FILLER + " Item 3. Quantitative and Qualitative Disclosures X")
    chunk = dossier.mda(text, "10-Q")
    assert chunk and chunk.startswith("Item 2. M anagement") and "Overview" in chunk[:120]


def test_mda_none_when_absent():
    assert dossier.mda("Item 1. Financial Statements " + FILLER, "10-Q") is None


def test_mda_10k_heading():
    text = "Item 7. Management’s Discussion and Analysis 34 Item 7A. Quantitative 40 " \
           + "PART II Item 7 ITEM 7. MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION " + FILLER \
           + " Item 7A. Quantitative and Qualitative"
    assert dossier.mda(text, "10-K").startswith("ITEM 7. MANAGEMENT")


GOOD = {"prior": {"p": 0.54, "from": "AMC base rate"}, "confidence": 0.5, "thesis": "t", "reasons": ["a", "b"],
        "moved_from_prior": "m", "deciding_variable": "d", "key_observations": ["k"],
        "theses": [{"expected": "e", "mechanism": "m", "wrong_if": "w"}] * 3, "items_used": ["I1"]}


def test_shape_problems():
    assert t2_stage2.shape_problems(GOOD) == []
    assert t2_stage2.shape_problems({**GOOD, "prior": "0.54 from AMC"})
    assert t2_stage2.shape_problems({**GOOD, "theses": ["a", "b", "c"]})
    assert t2_stage2.shape_problems({**GOOD, "confidence": "high"})


def dossier_stub():
    return {"items": [{"id": "I1", "kind": "gate", "source": "gate.json", "published": "2026-10-13T14:31:00-04:00"},
                      {"id": "I2", "kind": "release", "form": "8-K", "source": "sec", "published": "2026-07-15T16:00:00-04:00"}],
            "missing": []}


def test_code_sets_the_decision():
    now = datetime.datetime(2026, 10, 13, 20, 0, tzinfo=ET)
    t = t2_stage2.to_t2(GOOD, "I don't know", dossier_stub(), {"model": "m"}, now)
    assert t["decision"] == "NO_BUY" and t["confidence"] == 0.5          # BUY iff > 0.5
    t = t2_stage2.to_t2({**GOOD, "confidence": 0.514}, "I don't know", dossier_stub(), {"model": "m"}, now)
    assert t["decision"] == "BUY" and t["confidence"] == 0.51
    assert t2_stage2.thesis_md({"ticker": "X", "report_date": "2026-10-14", "session": "AMC"}, t, "T2")


def test_snapshot_item_exception_is_narrow():
    gate = {"captured_et": "2026-10-13T14:31:00-04:00", "season": "seasonX"}
    dl = datetime.datetime(2026, 10, 14, 9, 15, tzinfo=ET)
    t = t2_stage2.to_t2({**GOOD, "items_used": ["I1", "I2"]}, "I don't know", dossier_stub(), {"model": "m"},
                        datetime.datetime(2026, 10, 13, 20, 0, tzinfo=ET))
    d = {"t0": {"decision": "BUY"}, "t1": {"decision": None, "note": "test"}, "t2": t}
    assert not [p for p in decision_problems(d, gate, dl) if "published" in p]
    # the same timestamp on a non-snapshot item is refused
    t["inputs_read"][1]["published"] = "2026-10-13T14:31:00-04:00"
    assert [p for p in decision_problems(d, gate, dl) if "after the snapshot" in p]
