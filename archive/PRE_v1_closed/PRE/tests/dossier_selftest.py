"""
PRE dossier self-test — pre_dossier.py.
Run: PYTHONPATH=. python tests/dossier_selftest.py

Two contracts:
  1. THE 5-EVENT CAP IS ABSOLUTE. Owner-set, permanent, enforced on every write, no
     configuration knob that can quietly grow it back.
  2. A PURGED EVENT LOSES ITS DETAIL BUT NOT ITS EXISTENCE. The file exists to catch a
     mechanism that keeps recurring; a hard delete would make the sixth occurrence read
     as the first, which is the amnesia the file was built to end.
"""
import tempfile
from pathlib import Path

from pre_dossier import record, load, brief, add_standing_note, MAX_EVENTS

PASS, FAIL = 0, 0


def check(name, got, want):
    global PASS, FAIL
    ok = got == want
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: got {got!r}, want {want!r}")
    PASS += ok
    FAIL += (not ok)


def tmp():
    return Path(tempfile.mkdtemp())


# ---------------------------------------------------------------------------
print("1) THE RETENTION RULE — last five, then automatic and permanent deletion")
r = tmp()
check("1a the cap is the owner's five", MAX_EVENTS, 5)
for i in range(1, 8):
    record("NVDA", f"2026-0{i}-01", sector="SEMIS", forecast_direction="UP",
           forecast_conviction="MEDIUM", idio_pct=float(i), forecast_correct=(i % 2 == 0),
           deciding_variable=f"variable {i}", root=r)
d = load("NVDA", r)
check("1b exactly five events kept", len(d["events"]), 5)
check("1c and they are the LAST five",
      [e["event_date"] for e in d["events"]],
      ["2026-03-01", "2026-04-01", "2026-05-01", "2026-06-01", "2026-07-01"])
check("1d the two oldest are gone from detail", d["rollup"]["purged_events"], 2)
check("1e their hit-count survives as a counter", d["rollup"]["purged_correct"], 1)
check("1f and their gap magnitudes survive as a sum", d["rollup"]["purged_abs_gap_sum"], 3.0)

print("\n2) IDEMPOTENT — re-running /post does not duplicate a quarter")
before = len(load("NVDA", r)["events"])
record("NVDA", "2026-07-01", sector="SEMIS", forecast_direction="DOWN", root=r)
d = load("NVDA", r)
check("2a event count unchanged", len(d["events"]), before)
check("2b and the row was REPLACED, not appended",
      d["events"][-1]["forecast"]["direction"], "DOWN")

print("\n3) A RECURRING DECIDING VARIABLE SURVIVES THE PURGE — this is the whole point")
r = tmp()
for i in range(1, 9):
    record("AMKR", f"2026-0{i}-01", sector="SEMIS",
           deciding_variable="forward guide below consensus", root=r)
d = load("AMKR", r)
check("3a only five events kept", len(d["events"]), 5)
check("3b but the recurring variable is counted across the purged ones",
      d["rollup"]["recurring_variables"]["forward guide below consensus"], 3)
check("3c and the brief SURFACES it at T-1",
      "RECURRING deciding variables" in brief("AMKR", r), True)

print("\n4) STANDING NOTES OUTLIVE THE CAP")
r = tmp()
add_standing_note("AEHR", "guides FY with Q4, not Q3 — no fresh guide exists at T-1", root=r)
for i in range(1, 9):
    record("AEHR", f"2026-0{i}-01", sector="SEMIS", root=r)
d = load("AEHR", r)
check("4a the note survives eight events", len(d["standing_notes"]), 1)
check("4b and appears in the brief", "STANDING:" in brief("AEHR", r), True)
add_standing_note("AEHR", "guides FY with Q4, not Q3 — no fresh guide exists at T-1", root=r)
check("4c notes de-duplicate", len(load("AEHR", r)["standing_notes"]), 1)

print("\n5) THE T-1 BRIEF")
r = tmp()
check("5a a name with no history says so, plainly",
      "FIRST LOOK" in brief("ZZZZ", r), True)
record("RDDT", "2026-07-30", sector="COMMS", forecast_direction="DOWN",
       forecast_conviction="MEDIUM", forecast_basis="EVIDENCED", regime="EXTENDED/HIGH_MOVE",
       idio_pct=-17.62, forecast_correct=True, lesson="extension into the print was real", root=r)
b = brief("RDDT", r)
check("5b the brief states the record on the name", "1/1 kept" in b, True)
check("5c it shows the call and what happened", "said DOWN" in b and "-17.62%" in b, True)
check("5d it carries the lesson forward", "lesson:" in b, True)
check("5e it does NOT recommend anything — it is prior context, not a second opinion",
      any(w in b.lower() for w in ("buy", "short", "should", "recommend")), False)

print("\n6) SURPRISES AND FAILURE TYPES ARE VISIBLE ON THE NAME")
r = tmp()
record("AMKR", "2026-07-28", sector="SEMIS", forecast_direction="UP",
       idio_pct=-10.15, forecast_correct=False, failure_type="B", surprise=True,
       deciding_variable="Q3 guide 4% below consensus", root=r)
b = brief("AMKR", r)
check("6a the failure type shows", "[B]" in b, True)
check("6b the surprise flag shows", "SURPRISE" in b, True)
check("6c the deciding variable shows", "moved on:" in b, True)

print(f"\n=== {PASS} passed, {FAIL} failed ===")
raise SystemExit(1 if FAIL else 0)
