"""
PRE error-ledger self-test — pre_errors.py.
Run: PYTHONPATH=. python tests/errors_selftest.py

The contract being pinned, in one line: A WRONG CALL MUST COST SOMETHING, AND A SINGLE
CLUSTERED NIGHT MUST NOT BE ALLOWED TO LOOK LIKE THREE.

Every assertion here is pinned to a NAMED historical failure, the same discipline the
calc-risk suite uses:
  * the guide-freshness gate — shipped on n=1, failed both Abstraction limbs, reverted
    the next day  -> SHIPPED is refused without both limbs recorded and passing.
  * AMKR's forward guide called unobservable  -> legitimate ONCE. Limb 4 makes the second
    one a Type A blind spot instead of a second free pass.
  * "same-night same-sector correlation exposure raised once and declined" (pre_edgescore
    §48) -> the independence rule.
"""
import tempfile
from pathlib import Path

import pre_errors as E
from pre_errors import (observe, pending, ripe, dispose, SurpriseClaim, surprise_rate,
                        CONFIRMATIONS_REQUIRED, render)

PASS, FAIL = 0, 0


def check(name, got, want):
    global PASS, FAIL
    ok = got == want
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: got {got!r}, want {want!r}")
    PASS += ok
    FAIL += (not ok)


def tmp():
    return Path(tempfile.mkdtemp()) / "errors.jsonl"


def _refused(fn):
    """True if the call raised. Every guard in this module is meant to REFUSE loudly."""
    try:
        fn()
        return False
    except Exception:
        return True


# ---------------------------------------------------------------------------
print("1) THE INDEPENDENCE RULE — three names, one sector, one night = ONE confirmation")
p = tmp()
for t in ("LRCX", "KLAC", "AMAT"):
    observe(t, "2026-08-09", "SEMIS", "washout-term-fires-on-cheap-for-a-reason",
            axis="DIRECTION", failure_type="A", subtype="JUDGMENT",
            deciding_variable="forward guide", path=p)
c = {x["error_class"]: x for x in pending(p)}["washout-term-fires-on-cheap-for-a-reason"]
check("1a three raw hits recorded", c["raw_hits"], 3)
check("1b but only ONE independent confirmation", c["confirmations"], 1)
check("1c so it is NOT ripe", c["state"], "OPEN")
check("1d and nothing is demanding a response yet", len(ripe(p)), 0)

print("\n   ...the same class on three DIFFERENT nights DOES ripen")
observe("ON", "2026-08-12", "SEMIS", "washout-term-fires-on-cheap-for-a-reason",
        axis="DIRECTION", failure_type="A", subtype="JUDGMENT", path=p)
observe("MU", "2026-09-24", "SEMIS", "washout-term-fires-on-cheap-for-a-reason",
        axis="DIRECTION", failure_type="A", subtype="JUDGMENT", path=p)
r = {x["error_class"]: x for x in ripe(p)}
check("1e now 3 independent keys", r["washout-term-fires-on-cheap-for-a-reason"]["confirmations"], 3)
check("1f state is RIPE", r["washout-term-fires-on-cheap-for-a-reason"]["state"], "RIPE")
check("1g raw hits still honestly reported as 5",
      r["washout-term-fires-on-cheap-for-a-reason"]["raw_hits"], 5)
check("1h the threshold is the owner's 3, not a fitted number", CONFIRMATIONS_REQUIRED, 3)

# ---------------------------------------------------------------------------
print("\n2) A MECHANICAL BUG DOES NOT WAIT FOR THREE")
p = tmp()
observe("GLW", "2026-08-09", "INDUSTRIAL", "vel-reads-trailing-revenue-on-order-driven-name",
        axis="PROCESS", failure_type="A", subtype="MECHANICAL",
        note="basis field ignored", path=p)
r = ripe(p)
check("2a one hit is enough for a mechanical error", len(r), 1)
check("2b its disposition is FIX_NOW", r[0]["disposition"], "FIX_NOW")
check("2c required count is 1", r[0]["required"], 1)
check("2d and the demanded response is a fix", "FIX the input" in r[0]["required_response"], True)

print("\n   ...but a JUDGMENT error on the same axis still waits")
p = tmp()
observe("GLW", "2026-08-09", "INDUSTRIAL", "washout-bar-set-too-wide",
        axis="DIRECTION", failure_type="A", subtype="JUDGMENT", path=p)
check("2e judgment errors PEND", pending(p)[0]["disposition"], "PEND")
check("2f and are not ripe at n=1", len(ripe(p)), 0)
check("2g Type A with no subtype is REFUSED (the split decides ship-now vs wait)",
      _refused(lambda: observe("X", "2026-01-01", "SEMIS", "c", axis="DIRECTION",
                               failure_type="A", subtype="NA", path=p)), True)

# ---------------------------------------------------------------------------
print("\n3) TYPES B AND D STILL MAY NOT BE PATCHED — but they STOP BEING SILENT at 3")
p = tmp()
for i, (t, d) in enumerate([("AMKR", "2026-07-28"), ("ON", "2026-08-12"), ("MCHP", "2026-09-04")]):
    observe(t, d, "SEMIS", "deciding-variable-is-the-forward-guide",
            axis="DIRECTION", failure_type="B", subtype="NA",
            deciding_variable="Q3 revenue guided ~4% below consensus", path=p)
r = ripe(p)[0]
check("3a a Type B class ripens", r["state"], "RIPE")
check("3b its disposition is BOUNDARY, not PEND", r["disposition"], "BOUNDARY")
check("3c and the demanded response FORBIDS a patch",
      "DO NOT PATCH" in r["required_response"], True)
check("3d it asks the bet-SELECTION question instead",
      "bet-selection" in r["required_response"], True)

p = tmp()
for t, d in [("A", "2026-01-01"), ("B", "2026-02-01"), ("C", "2026-03-01")]:
    observe(t, d, "SOFTWARE", "gap-inside-normal-distribution", axis="MAGNITUDE",
            failure_type="D", subtype="NA", deciding_variable="nothing identifiable", path=p)
r = ripe(p)[0]
check("3e a Type D class ripens to VARIANCE", r["disposition"], "VARIANCE")
check("3f which also forbids patching", "DO NOT PATCH" in r["required_response"], True)
check("3g but asks whether the expected-move model is wrong",
      "expected-move" in r["required_response"], True)
check("3h Type B/D with no named deciding variable is REFUSED",
      _refused(lambda: observe("X", "2026-01-01", "SEMIS", "c", axis="DIRECTION",
                               failure_type="B", subtype="NA", path=p)), True)

# ---------------------------------------------------------------------------
print("\n4) CONVICTION IS ITS OWN AXIS — owner asked for this explicitly")
p = tmp()
observe("FSLR", "2026-07-30", "ENERGY", "high-conviction-on-thin-evidence",
        axis="CONVICTION", failure_type="A", subtype="JUDGMENT",
        note="stated HIGH, was wrong; EVIDENCED basis scored 42.9%", path=p)
check("4a CONVICTION is a first-class axis", pending(p)[0]["axis"], "CONVICTION")
check("4b all five axes exist",
      E.AXES, ("DIRECTION", "CONVICTION", "MAGNITUDE", "EXPRESSION", "PROCESS"))

# ---------------------------------------------------------------------------
print("\n5) THE SURPRISE GATE — four limbs, all must pass")
base = dict(ticker="AMKR", event_date="2026-07-28",
            deciding_variable="Q3 revenue guided ~4% below consensus on comms decline",
            first_public_at="2026-07-28 AMC press release", idio_pct=-10.15,
            name_worst_gap=-6.0, was_a_model_input=False,
            sourceable_pre_print=False, prior_claims=0)
v = SurpriseClaim(**base).evaluate()
check("5a a genuine first-time guide-down IS a surprise", v["verdict"], "SURPRISE")
check("5b all four limbs recorded", sorted(v["limbs"]), sorted(E.SURPRISE_LIMBS))

print("\n   LIMB 4 IS THE ANTI-EXCUSE LIMB — the second one is a blind spot, not luck")
v = SurpriseClaim(**{**base, "prior_claims": 1}).evaluate()
check("5c a repeat claim is NOT a surprise", v["verdict"], "NOT_SURPRISE")
check("5d it names the failed limb", v["failed_limbs"], ["not_recurrent"])
check("5e and reclassifies to a workable Type A", v["reclassify_to"][0], "A")

print("\n   the other three limbs")
v = SurpriseClaim(**{**base, "sourceable_pre_print": True}).evaluate()
check("5f obtainable at T-1 => not a surprise, it is a sourcing miss", v["verdict"], "NOT_SURPRISE")
v = SurpriseClaim(**{**base, "idio_pct": -4.0}).evaluate()
check("5g a move inside the name's own gap history is not a surprise", v["verdict"], "NOT_SURPRISE")
v = SurpriseClaim(**{**base, "deciding_variable": "sentiment"}).evaluate()
check("5h a vague deciding variable fails limb 1", v["limbs"]["unobservable"], False)
v = SurpriseClaim(**{**base, "name_worst_gap": None}).evaluate()
check("5i unknown distribution cannot support a surprise claim",
      v["limbs"]["outside_distribution"], False)
v = SurpriseClaim(**{**base, "was_a_model_input": True}).evaluate()
check("5j a variable already on our input list is never unobservable",
      v["limbs"]["unobservable"], False)

print("\n   the surprise BUDGET — above it, this is bet selection, not luck")
p = tmp()
for i in range(10):
    observe(f"T{i}", f"2026-0{i%9+1}-01", "SEMIS", f"class-{i}", axis="DIRECTION",
            failure_type="B", subtype="NA", deciding_variable="named variable here",
            surprise={"verdict": "SURPRISE" if i < 5 else "NOT_SURPRISE"}, path=p)
s = surprise_rate(p)
check("5k 5 of 10 = 50%", s["rate"], 0.5)
check("5l which is over the 30% budget", s["over_budget"], True)

# ---------------------------------------------------------------------------
print("\n6) SHIPPING — Abstraction Limb 2 now targets CONFIRMED THESES, not P&L wins")
# RE-AIMED 2026-08-09. The old limb vetoed any fix that broke a previously WINNING trade,
# which is incoherent inside this system's own epistemology: "a winning trade can be a
# wrong thesis... P&L is not truth; attribution is." Limb 2 then sanctified P&L wins.
# Breaking a winner that was right for the WRONG REASON costs nothing — you are removing
# a coincidence, not an edge. So the limb is re-aimed, not loosened.
p = tmp()
ok_kw = dict(rationale="r", mechanism="the norm used the range of legs we do not have",
             abstraction_limb1=True, path=p)
check("6a SHIPPED with no MECHANISM is REFUSED (a net count is never the reason)",
      _refused(lambda: dispose("c", "SHIPPED", rationale="the numbers look better",
                               abstraction_limb1=True, repairs_confirmed=["X"], path=p)), True)
check("6b SHIPPED failing limb 1 is REFUSED",
      _refused(lambda: dispose("c", "SHIPPED", rationale="r", mechanism="m",
                               abstraction_limb1=False, repairs_confirmed=["X"], path=p)), True)
check("6c an EMPTY flip set is REFUSED — 'none checked' != 'none broken'",
      _refused(lambda: dispose("c", "SHIPPED", **ok_kw)), True)

print("\n   the re-aimed limb: P&L wins no longer veto; CONFIRMED THESES do")
check("6d breaking a CONFIRMED thesis and repairing nothing is REFUSED",
      _refused(lambda: dispose("c", "SHIPPED", breaks_confirmed=["AEHR"], **ok_kw)), True)
d = dispose("c", "SHIPPED", breaks_confirmed=["AEHR"],
            repairs_confirmed=["NFLX", "AMKR"], **ok_kw)
check("6e breaking one confirmed thesis but REPAIRING others ships", d["state"], "SHIPPED")
check("6e and the flip set is recorded BOTH ways — the missing symmetry",
      (d["abstraction_test"]["breaks_confirmed"],
       d["abstraction_test"]["repairs_confirmed"]), (["AEHR"], ["NFLX", "AMKR"]))
d2 = dispose("c2", "SHIPPED", breaks_unattributed=["CLS", "TEM"], **ok_kw)
check("6f breaking an UNATTRIBUTED winner is DISCLOSED, not vetoed", d2["state"], "SHIPPED")
check("6f  — you cannot claim protection for a thesis you never recorded",
      d2["abstraction_test"]["breaks_unattributed"], ["CLS", "TEM"])
check("6g the limb states what it now targets",
      d["abstraction_test"]["limb2_target"], "CONFIRMED THESES, not P&L winners")
check("6h and the net count is labelled COST, never justification",
      "never the reason" in d["abstraction_test"]["net_note"], True)

print("\n   the guide-freshness gate, replayed: it must STILL be impossible to ship")
check("6i it failed limb 1 (AMKR was Type B, unobservable) -> REFUSED",
      _refused(lambda: dispose("guide-freshness-gate", "SHIPPED", rationale="prevents AMKR",
                               mechanism="assert a fresh guide", abstraction_limb1=False,
                               breaks_confirmed=["AEHR"], path=p)), True)
check("6j and even with limb 1 asserted it breaks AEHR and repairs nothing -> REFUSED",
      _refused(lambda: dispose("guide-freshness-gate", "SHIPPED", rationale="prevents AMKR",
                               mechanism="assert a fresh guide", abstraction_limb1=True,
                               breaks_confirmed=["AEHR"], path=p)), True)

print("\n   thesis_confirmed — the SOP field that has NEVER ONCE been written")
p2 = tmp()
o1 = observe("AEHR", "2026-07-14", "SEMIS", "cls", axis="DIRECTION", failure_type="A",
             subtype="JUDGMENT", correct=True, thesis_confirmed=True, path=p2)
check("6k observations now carry attribution", o1["thesis_confirmed"], True)
o2 = observe("CLS", "2026-07-28", "SEMIS", "cls", axis="DIRECTION", failure_type="A",
             subtype="JUDGMENT", correct=True, path=p2)
check("6l unattributed defaults to None, which is NOT False", o2["thesis_confirmed"], None)

# ---------------------------------------------------------------------------
print("\n7) WINS ARE RECORDED TOO — limb 2 cannot be checked from a log of losses")
p = tmp()
observe("AEHR", "2026-07-14", "SEMIS", "washout-term-fires-on-cheap-for-a-reason",
        axis="DIRECTION", failure_type="A", subtype="JUDGMENT", correct=True,
        idio_pct=35.04, path=p)
observe("NFLX", "2026-07-18", "SOFTWARE", "washout-term-fires-on-cheap-for-a-reason",
        axis="DIRECTION", failure_type="A", subtype="JUDGMENT", correct=False, path=p)
c = pending(p)[0]
check("7a a win does not count as a confirmation", c["confirmations"], 1)
check("7b but it is retained against the class for limb 2",
      [w["ticker"] for w in c["wins_touching_class"]], ["AEHR"])

# ---------------------------------------------------------------------------
print("\n8) HYGIENE")
p = tmp()
observe("A", "2026-01-01", "SEMIS", "  Washout Term Fires!! ", axis="DIRECTION",
        failure_type="A", subtype="JUDGMENT", path=p)
check("8a class names are slugged so two spellings cannot split a count",
      pending(p)[0]["error_class"], "washout-term-fires")
check("8b an empty class name is refused",
      _refused(lambda: observe("A", "2026-01-01", "S", "", axis="DIRECTION",
                               failure_type="A", subtype="JUDGMENT", path=p)), True)
check("8c a bad axis is refused",
      _refused(lambda: observe("A", "2026-01-01", "S", "c", axis="VIBES",
                               failure_type="A", subtype="JUDGMENT", path=p)), True)
check("8d render() runs on a live board", isinstance(render(p), str), True)

print(f"\n=== {PASS} passed, {FAIL} failed ===")
raise SystemExit(1 if FAIL else 0)
