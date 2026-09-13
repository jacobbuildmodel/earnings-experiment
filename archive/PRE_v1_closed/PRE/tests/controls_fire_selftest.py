"""
DO THE CONTROLS ACTUALLY FIRE?  —  the standing rule, made executable.
================================================================================
Run: PYTHONPATH=. python tests/controls_fire_selftest.py

WHY THIS SUITE EXISTS. Three separate defects surfaced on 2026-08-09, and they were
not three bugs — they were ONE process defect, three times:

  1. VOID STATUS was recorded in prose and had no field in ledger.jsonl, so every
     statistic — including the 5/15 the model quoted about itself, and the
     kill-switch dashboard — silently counted rows the documentation called void.
  2. THE TRADE PAUSE was installed on `pre_ledger.pre_register()`, which is not the
     function `pre_batch.py` calls. The guard existed and did not cover the live path.
  3. `thesis_confirmed` has been a MANDATORY field in the POSTMORTEM SOP since
     2026-07-29 and has been written on ZERO of 60 outcome rows. Not "recorded and
     never consulted" — never recorded.

**This system reliably builds the control and does not wire it.**

THE STANDING RULE, generalised from the end-to-end CLI check that caught defect 2:

    EVERY NEW CONTROL SHIPS WITH A TEST THAT IT *FIRES*, NOT A TEST THAT IT EXISTS.

A test proving a guard is importable is not a test proving the guard raises. All three
defects above would have been caught at build time by that single rule, and it costs
about one assertion per control. Adding a control to this system now means adding a
case here — that is the price of the control, and it is cheap.

Note the shape of what is asserted: each case drives the control the way production
drives it and demands the refusal. Nothing here checks that a function is defined.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

PASS, FAIL = 0, 0


def check(name, got, want):
    global PASS, FAIL
    ok = got == want
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: got {got!r}, want {want!r}")
    PASS += ok
    FAIL += (not ok)


def fires(fn):
    """True if the control REFUSED. A control that returns quietly has not fired."""
    try:
        fn()
        return False
    except Exception:
        return True


# ---------------------------------------------------------------------------
print("1) THE TRADE PAUSE fires on EVERY registration path, not just the tidy one")
# This is defect 2, pinned. pre_batch.py calls pre_edgescore.register(), which appends
# to the ledger directly and NEVER calls pre_register(). A guard on pre_register alone
# covered the route nobody runs.
from pre_engine import Judgment, Market
import pre_ledger
import pre_edgescore

_M = Market(price=100.0, avg_abs_open=5.0, confirmed_quarters=8,
            dollar_vol_20d=4e8, share_vol_20d=5e6, implied_move=5.0, capital=18_000,
            vix=16.0, spy_5d_realvol_wow=0.0, spx_day=0.0)

check("1a pre_ledger.pre_register() is blocked while paused",
      fires(lambda: pre_ledger.pre_register("X", Judgment(), _M, event_date="2026-12-01")), True)
check("1b pre_edgescore.register() — THE PRODUCTION PATH — is blocked too",
      fires(lambda: pre_edgescore.register("X", Judgment(), _M, event_date="2026-12-01")), True)
check("1c the pause is actually active (else 1a/1b prove nothing)",
      bool(pre_ledger.trade_paused()), True)
check("1d the FORECAST layer is NOT blocked — stopping it teaches nothing",
      __import__("pre_forecast").forecast("X", expectations=0.3).direction in ("UP", "DOWN"),
      True)
check("1e the refusal NAMES the resume conditions, not just 'paused'",
      len(pre_ledger.trade_paused()["resume_conditions"]) >= 3, True)

# ---------------------------------------------------------------------------
print("\n2) VOIDING actually removes rows from the STATISTICS (defect 1)")
# It is not enough that a void row can be written. The question is whether stats() obeys it.
tmp = Path(tempfile.mkdtemp()) / "ledger.jsonl"
j = Judgment(up_revisions_30d=3, down_revisions_30d=0, covering_analysts=6,
             GG=1, VEL=1, FLAG=0, CBR="CLEAN", G0="CONFIRMED",
             stock_pct_since_last_earnings=5.0, sector_etf_pct_same_window=4.0,
             pct_below_52w_high=10.0)
e = pre_ledger.pre_register("AAA", j, _M, event_date="2026-07-20", ledger_path=tmp,
                            allow_paused=True)
pre_ledger.record_outcome(e["id"], stock_open_pct=6.0, etf_open_pct=1.0, ledger_path=tmp)
before = pre_ledger.stats(tmp)["n_outcome"]
pre_ledger.void_entry(e["id"], "scored after its own print", ledger_path=tmp)
after = pre_ledger.stats(tmp)
check("2a the row counted before voiding", before, 1)
check("2b and is GONE from the stats after", after["n_outcome"], 0)
check("2c the exclusion is REPORTED, not silent", after["n_voided_trades"], 1)
check("2d a void with no stated reason is REFUSED",
      fires(lambda: pre_ledger.void_entry(e["id"], "  ", ledger_path=tmp)), True)

# ---------------------------------------------------------------------------
print("\n3) THE SURPRISE GATE refuses on EACH limb independently")
from pre_errors import SurpriseClaim, observe, dispose
base = dict(ticker="AMKR", event_date="2026-07-28",
            deciding_variable="Q3 revenue guided ~4% below consensus on comms decline",
            first_public_at="2026-07-28 AMC release", idio_pct=-10.15,
            name_worst_gap=-6.0, was_a_model_input=False,
            sourceable_pre_print=False, prior_claims=0)
check("3a a genuine claim passes (else the limbs below prove nothing)",
      SurpriseClaim(**base).evaluate()["verdict"], "SURPRISE")
for limb, kw in [("unobservable (vague variable)", {"deciding_variable": "sentiment"}),
                 ("not_sourceable", {"sourceable_pre_print": True}),
                 ("outside_distribution", {"idio_pct": -2.0}),
                 ("not_recurrent", {"prior_claims": 1})]:
    check(f"3b limb {limb} FIRES",
          SurpriseClaim(**{**base, **kw}).evaluate()["verdict"], "NOT_SURPRISE")

# ---------------------------------------------------------------------------
print("\n4) THE ERROR LEDGER refuses the filings it is supposed to refuse")
p = Path(tempfile.mkdtemp()) / "errors.jsonl"
check("4a Type B with no named deciding variable is REFUSED",
      fires(lambda: observe("X", "2026-01-01", "SEMIS", "c", axis="DIRECTION",
                            failure_type="B", subtype="NA", path=p)), True)
check("4b Type A with no MECHANICAL/JUDGMENT split is REFUSED",
      fires(lambda: observe("X", "2026-01-01", "SEMIS", "c", axis="DIRECTION",
                            failure_type="A", subtype="NA", path=p)), True)
check("4c SHIPPED with no named mechanism is REFUSED",
      fires(lambda: dispose("c", "SHIPPED", rationale="numbers look better",
                            abstraction_limb1=True, repairs_confirmed=["X"], path=p)), True)
check("4d SHIPPED that breaks a CONFIRMED thesis and repairs nothing is REFUSED",
      fires(lambda: dispose("c", "SHIPPED", rationale="r", mechanism="m",
                            abstraction_limb1=True, breaks_confirmed=["AEHR"], path=p)), True)
check("4e SHIPPED with an EMPTY flip set is REFUSED ('none checked' != 'none broken')",
      fires(lambda: dispose("c", "SHIPPED", rationale="r", mechanism="m",
                            abstraction_limb1=True, path=p)), True)

print("\n   the INDEPENDENCE RULE actually collapses a cluster")
p2 = Path(tempfile.mkdtemp()) / "errors.jsonl"
for t in ("LRCX", "KLAC", "AMAT"):
    observe(t, "2026-08-09", "SEMIS", "same-class", axis="DIRECTION",
            failure_type="A", subtype="JUDGMENT", path=p2)
from pre_errors import pending, ripe
c = pending(p2)[0]
check("4f three same-night same-sector names = ONE confirmation", c["confirmations"], 1)
check("4g and the raw count is still shown, so the cluster is visible", c["raw_hits"], 3)
check("4h so nothing ripens off a single night", len(ripe(p2)), 0)

# ---------------------------------------------------------------------------
print("\n5) THE DOSSIER CAP actually purges (a retention rule that does not delete is a lie)")
from pre_dossier import record, load, MAX_EVENTS
root = Path(tempfile.mkdtemp())
for i in range(1, MAX_EVENTS + 3):
    record("NVDA", f"2026-{i:02d}-01", sector="SEMIS", idio_pct=float(i),
           deciding_variable="forward guide", root=root)
d = load("NVDA", root)
check("5a exactly MAX_EVENTS kept", len(d["events"]), MAX_EVENTS)
check("5b the overflow was PURGED, not silently kept", d["rollup"]["purged_events"], 2)
check("5c but the recurring mechanism survived the purge",
      d["rollup"]["recurring_variables"]["forward guide"], 2)

# ---------------------------------------------------------------------------
print("\n6) THE KILL SWITCH fires on the state it was built for")
sig = {"n_outcome": 20, "accuracy": 0.30, "expectancy_pct": -2.0,
       "expectancy_ex_top_pct": -4.0, "components": {}, "type_b_last10": 0,
       "n_high": 0, "acc_high": None, "n_med": 0, "acc_med": None}
res = {n: s for n, s, _ in pre_ledger.kill_switches(sig)}
check("6a both-bad -> PAUSE", res.get("expectancy<=0 AND idio-sign<50% @ n>=15"), "PAUSE")
sig2 = {**sig, "expectancy_pct": +2.0}
res2 = {n: s for n, s, _ in pre_ledger.kill_switches(sig2)}
check("6b sign bad but expectancy GOOD -> REVIEW, never an auto-pause",
      res2.get("sign<50% but expectancy>0"), "REVIEW")
check("6b2 ...and it does NOT pause (this is the gap-capture profile)",
      res2.get("expectancy<=0 AND idio-sign<50% @ n>=15"), "ok")
sig3 = {**sig, "accuracy": 0.60, "expectancy_pct": -2.0}
res3 = {n: s for n, s, _ in pre_ledger.kill_switches(sig3)}
check("6c sign GOOD but expectancy bad -> REVIEW (the dangerous one)",
      res3.get("sign>=50% but expectancy<=0"), "REVIEW")

# ---------------------------------------------------------------------------
print("\n7) THE NORMALISATION AUDIT TRAIL makes a logged tier RE-DERIVABLE")
# Not a control that refuses — a control that PRESERVES. It fires by being complete
# enough to reconstruct the answer, so that is what is asserted.
jv = Judgment(up_revisions_30d=0, down_revisions_30d=0, covering_analysts=0,
              GG=None, VEL=1, vel_basis="BOOKINGS", FLAG=0, CBR="CLEAN", G0="CONFIRMED",
              stock_pct_since_last_earnings=-30.0, sector_etf_pct_same_window=0.0,
              pct_within_52w_high=40.0, pct_below_52w_high=40.0)
v = pre_edgescore.edge_score("SAT_CASE", jv, _M)
check("7a the raw numerator is logged", v.fund_leg_sum is not None, True)
check("7b the divisor actually used is logged", v.fund_norm, 1.0)
check("7c and which legs set it", v.verified_legs, ["VEL"])
check("7d a lone 3-state leg DOES saturate — the known, queued defect",
      (v.expectations_momentum, v.conviction), (1.0, "MAXIMUM"))
_exp4 = max(-1.0, min(1.0, v.fund_leg_sum / 4.0))
_edge4 = (pre_edgescore.W_EXPECTATIONS * _exp4
          + pre_edgescore.W_POSITIONING * v.positioning) * v.confidence
_tier4 = next((n for lo, n, _ in pre_edgescore.TIERS if abs(_edge4) >= lo), "NONE")
check("7e the tier re-derives under a DIFFERENT norm from the logged row alone",
      _tier4, "HIGH")

# ---------------------------------------------------------------------------- 8
# THE ERROR BOARD MUST BE ABLE TO PRINT.
#
# `pre_errors.py board` is STEP 1 of the /pre runbook -- the command answering "what
# is this model currently known to get wrong?" BEFORE a forecast is frozen. On a
# stock Windows console stdout is cp1252, and the PENDING glyph U+23F3 raised
# UnicodeEncodeError, so on 2026-09-05 the board CRASHED on every plain run. A class
# was live at 2/3 at that moment; a session that shrugged and skipped the board would
# have frozen a forecast without ever seeing it.
#
# This suite's own thesis, one more time: the control existed, was documented, and was
# never executed on the platform it runs on. So the case drives the REAL board over the
# REAL ledger through a cp1252 writer and demands bytes out -- never an import check.
import io
import pre_errors

_board = pre_errors.render()
check("8a the board renders over the real error ledger", bool(_board.strip()), True)

_buf = io.BytesIO()
_cp1252 = io.TextIOWrapper(_buf, encoding="cp1252", errors="strict", newline="")
try:
    _cp1252.write(_board)
    _cp1252.flush()
    _wrote = True
except UnicodeEncodeError:
    _wrote = False
check("8b raw board text is NOT cp1252-encodable (the latent hazard is real)",
      _wrote, False)

# The guard lives in main(), so drive the CLI the way the runbook does. Defect 2 in
# this file was exactly a guard installed on a function production does not call.
_env = dict(os.environ, PYTHONIOENCODING="cp1252", PYTHONPATH=".")
_r = subprocess.run([sys.executable, "pre_errors.py", "board"],
                    cwd=str(Path(__file__).resolve().parent.parent),
                    capture_output=True, env=_env)
check("8c `pre_errors.py board` exits 0 on a cp1252 console", _r.returncode, 0)
check("8d and raised no UnicodeEncodeError",
      b"UnicodeEncodeError" in _r.stderr, False)
check("8e and actually printed the board, not an empty buffer",
      b"PRE ERROR LEDGER" in _r.stdout, True)

# ---------------------------------------------------------------------------- 9
# THE FORECAST LAYER IS CLOCK-GUARDED TOO.
#
# --register was refused after the cutoff; a DRY run past it printed a warning and
# logged the forecast anyway, unmarked. clock_guard's docstring said "label it VOID"
# and nothing labelled it -- void-status-in-prose-only, defect 1 above, a fourth time.
# It bites harder here: the trade layer is PAUSED, so the forecast layer is the only
# one still accruing a record, and score() is what the open questions turn on.
#
# The record was audited clean (0 of 23 post-cutoff) BEFORE this shipped, so the guard
# is a no-op on real data -- which is the point: wire it while it costs nothing.
import pre_forecast

_hind = pre_forecast.Forecast(ticker="HINDSIGHT", direction="UP", conviction="HIGH",
                              basis="EVIDENCED", signal=0.9, expected_move=5.0,
                              regime="SOFT/HIGH_MOVE", event_date="2020-01-02",
                              session="amc")
with tempfile.TemporaryDirectory() as _td:
    _fp = Path(_td) / "f.jsonl"
    _rec = pre_forecast.log_forecast(_hind, path=_fp)
    check("9a a forecast logged years after its event is STAMPED post_cutoff",
          _rec["post_cutoff"], True)
    check("9b and the stamp says how far past, not just that it is past",
          _rec["minutes_before_cutoff"] < 0, True)
    # the stamp must CHANGE A STATISTIC, or it is decoration
    pre_forecast.log_outcome("HINDSIGHT", "2020-01-02", 9.9, path=_fp)
    _sc = pre_forecast.score(path=_fp)
    check("9c score() EXCLUDES it rather than counting a free win", _sc["n"], 0)
    check("9d and discloses the exclusion rather than hiding it",
          _sc.get("excluded_post_cutoff"), 1)

    # a genuine pre-print freeze on the same path must still be counted
    _fut = pre_forecast.Forecast(ticker="BLIND", direction="UP", conviction="LOW",
                                 basis="WEAK", signal=0.2, expected_move=3.0,
                                 regime="SOFT/HIGH_MOVE", event_date="2099-01-02",
                                 session="amc")
    _r2 = pre_forecast.log_forecast(_fut, path=_fp)
    check("9e a real pre-print freeze is NOT stamped", _r2["post_cutoff"], False)
    pre_forecast.log_outcome("BLIND", "2099-01-02", 4.0, path=_fp)
    check("9f and IS counted -- the guard excludes hindsight, not everything",
          pre_forecast.score(path=_fp)["n"], 1)

# and the live record is unchanged by all of the above
check("9g the real record lost nothing to this guard",
      pre_forecast.score().get("excluded_post_cutoff"), 0)

print(f"\n=== {PASS} passed, {FAIL} failed ===")
raise SystemExit(1 if FAIL else 0)
