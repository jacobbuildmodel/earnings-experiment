"""
PRE batch-runner self-test — the CLOCK GUARD and the GG handoff.
Run: PYTHONPATH=. python tests/batch_selftest.py

The clock guard is the single most important assertion in this file. The 2026-07-29 batch was
voided because verdicts were produced 3.5h after the print, and the safeguard at the time was
"remember to check". These pin it in code.
"""
import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pre_batch as B

PASS, FAIL = 0, 0
ET = ZoneInfo("America/New_York")


def check(name, got, want):
    global PASS, FAIL
    ok = got == want
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: got {got!r}, want {want!r}")
    PASS += ok
    FAIL += (not ok)


# ---------------------------------------------------------------------------
print("1) cutoff arithmetic — exchange time, not local, not UTC")
amc = B.cutoff_utc("2026-07-29", "amc")
bmo = B.cutoff_utc("2026-07-29", "bmo")
check("1a AMC cutoff is 16:00 ET", amc.astimezone(ET).strftime("%H:%M"), "16:00")
check("1b BMO cutoff is 09:30 ET", bmo.astimezone(ET).strftime("%H:%M"), "09:30")
check("1c AMC is after BMO on the same date", amc > bmo, True)
check("1d July resolves to EDT (UTC-4), so 16:00 ET == 20:00 UTC",
      amc.astimezone(timezone.utc).strftime("%H:%M"), "20:00")
# DST is the classic silent bug: a fixed -4 offset would put January's cutoff an hour wrong.
jan = B.cutoff_utc("2026-01-15", "amc")
check("1e January resolves to EST (UTC-5), so 16:00 ET == 21:00 UTC",
      jan.astimezone(timezone.utc).strftime("%H:%M"), "21:00")

# ---------------------------------------------------------------------------
print("\n2) THE GUARD — registration after the event must be impossible")
past = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")
future = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")

raised = False
try:
    B.clock_guard(past, "amc", registering=True)
except SystemExit as e:
    raised = True
    msg = str(e)
check("2a past event + --register RAISES", raised, True)
check("2b ...and the refusal names it as a counterfactual", "counterfactual" in msg, True)
check("2c ...and cites HANDOFF §14", "§14" in msg, True)

# A dry run on a past event is ALLOWED — that is how a counterfactual is legitimately built.
g = B.clock_guard(past, "amc", registering=False)
check("2d past event WITHOUT --register is allowed (dry counterfactual)", g["past"], True)

# The normal case: a future event may register.
g2 = B.clock_guard(future, "amc", registering=True)
check("2e future event + --register is permitted", g2["past"], False)
check("2f ...and reports time remaining", g2["minutes_left"] > 0, True)

# ---------------------------------------------------------------------------
print("\n3) GG handoff — absent file must DECLARE None, never default to 0")
gg = B.load_gg(["AAA", "BBB"], "2099-01-01")          # no such gg_ file exists
check("3a absent file -> GG None", gg["AAA"]["GG"], None)
check("3b ...status is NOT_SOURCED, not VERIFIED", gg["AAA"]["status"], "NOT_SOURCED")
check("3c ...and it says guidance was not looked at",
      any("not looked at" in r for r in gg["AAA"]["reasons"]), True)
check("3d every requested ticker is represented", sorted(gg), ["AAA", "BBB"])

# ---------------------------------------------------------------------------
print("\n4) GG handoff — a real file is parsed, verified and polarity-corrected")
rows = {"GOOD": [{"metric": "REVENUE", "period": "FY2026",
                  "prior_low": 10.0, "new_low": 11.0,
                  "quote": "now expect revenue of $11.0B",
                  "prior_quote": "expect revenue of $10.0B",
                  "source_url": "https://investor.example.com/q3",
                  "source_date": "2026-07-29"}],
        "COSTUP": [{"metric": "EXPENSES", "period": "FY2026",
                    "prior_low": 10.0, "new_low": 11.0,
                    "quote": "now expect expenses of $11.0B",
                    "prior_quote": "expect expenses of $10.0B",
                    "source_url": "https://investor.example.com/q3",
                    "source_date": "2026-07-29"}],
        "BADSRC": [{"metric": "REVENUE", "period": "FY2026",
                    "prior_low": 10.0, "new_low": 11.0,
                    "quote": "street sees $11.0B", "prior_quote": "street saw $10.0B",
                    "comparison": "CONSENSUS",
                    "source_url": "https://example.com", "source_date": "2026-07-29"}]}
old_root = B.ROOT
tmp = Path(tempfile.mkdtemp())
B.ROOT = tmp
(tmp / "gg_2026-10-27.json").write_text(json.dumps(rows), encoding="utf-8")
try:
    gg2 = B.load_gg(["GOOD", "COSTUP", "BADSRC", "MISSING"], "2026-10-27")
finally:
    B.ROOT = old_root
check("4a revenue raised -> +1", gg2["GOOD"]["GG"], +1)
check("4b EXPENSES raised -> -1 (polarity applied through the runner)",
      gg2["COSTUP"]["GG"], -1)
check("4c consensus comparison refused end-to-end", gg2["BADSRC"]["GG"], None)
check("4d a ticker absent from the file is NOT_SOURCED",
      gg2["MISSING"]["status"], "NOT_SOURCED")
check("4e verified rows carry the basis into the Judgment",
      gg2["GOOD"]["gg_basis"], "COMPANY_GUIDANCE")

# ---------------------------------------------------------------------------
print("\n5) GG actually reaches the engine and lifts completeness")
from pre_engine import Market, Truth, EngineConfig, evaluate
cases = B.build_cases(
    ["GOOD"],
    {"GOOD": {"price": 100.0, "mean": 5.0, "bad": 9.0, "nq": 10, "dv": 5e8, "sv": 5e6,
              "ped": 1.0, "ep": 0.0, "blw": 30.0, "etf": "XLK", "gaps": [], "lastdate": None}},
    {"GOOD": {"u30": 3, "d30": 0, "u7": 1, "d7": 0, "an": 10, "rv": 40.0}},
    gg2, 18_000.0)
t, j, m, tr, sk = cases[0]
check("5a GG landed on the Judgment", j.GG, +1)
check("5b gg_basis travelled with it", j.gg_basis, "COMPANY_GUIDANCE")
r = evaluate(j, m, t=tr, cfg=EngineConfig(fasttrack=True, watch=False, react_in_ds=False))
check("5c engine counts GG as VERIFIED", "GG" in r.verified, True)
check("5d GG is in the component sum", r.components["GG"], +1)

from pre_edgescore import edge_score
v_gg = edge_score("GOOD", j, m, tr, EngineConfig(fasttrack=True, watch=False, react_in_ds=False))
j.GG, j.gg_basis = None, None
v_no = edge_score("GOOD", j, m, tr, EngineConfig(fasttrack=True, watch=False, react_in_ds=False))
check("5e confidence is HIGHER with GG sourced", v_gg.confidence > v_no.confidence, True)
check("5f completeness 3/4 with GG vs 2/4 without", (v_gg.completeness, v_no.completeness),
      (0.75, 0.5))

print(f"\n=== {PASS} passed, {FAIL} failed ===")
raise SystemExit(1 if FAIL else 0)
