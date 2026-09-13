"""
PRE edge-score self-test (layer v1.0.0 — the PRODUCTION scorer).
Run: python tests/edgescore_selftest.py

These lock the properties the design depends on. They are NOT a backtest.
Every block names the failure or design guarantee it protects.
"""
import tempfile
from pathlib import Path

from pre_engine import Judgment, Market, Truth, Skew, EngineConfig
import pre_edgescore as E
from pre_edgescore import edge_score, rank, register, EDGE_MIN, CONF_FLOOR

PASS, FAIL = 0, 0


def check(name, got, want):
    global PASS, FAIL
    ok = got == want
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: got {got!r}, want {want!r}")
    PASS += ok
    FAIL += (not ok)


CFG = EngineConfig(fasttrack=True, watch=False, react_in_ds=False)
MKT = Market(price=100.0, avg_abs_open=8.0, confirmed_quarters=8,
             dollar_vol_20d=200_000_000, share_vol_20d=5_000_000,
             capital=18_000, vix=15.0, implied_move=8.0)          # IRM 1.00 = fair


def J(**kw):
    base = dict(REACT=None, FLAG=0, CBR="CLEAN", G0="CONFIRMED",
                stock_pct_since_last_earnings=-30.0, sector_etf_pct_same_window=10.0,
                pct_below_52w_high=45.0)
    base.update(kw)
    return Judgment(**base)


T = Truth(stock_pct_since_last_earnings=-30.0, pct_below_52w_high=45.0, price=100.0)

# ---------------------------------------------------------------------------
# 1) THE CORE DESIGN GUARANTEE — uncertainty SHRINKS the bet, it does not kill it.
#    This is the entire reason the layer exists (the over-abstention complaint).
# ---------------------------------------------------------------------------
print("1) uncertainty must SHRINK size, never abstain (the confidence floor)")
full = J(up_revisions_30d=2, down_revisions_30d=0, covering_analysts=10,   # REV +1
         rev_basis="ESTIMATE_REVISIONS", GG=1, gg_basis="FILED", VEL=1, vel_basis="GUIDANCE")
sparse = J(up_revisions_30d=2, down_revisions_30d=0, covering_analysts=10,  # REV +1, GG/VEL absent
           rev_basis="ESTIMATE_REVISIONS")            # GG + VEL UNAVAILABLE
v_full = edge_score("FULL", full, MKT, T, CFG)
v_sparse = edge_score("SPARSE", sparse, MKT, T, CFG)
check("complete info -> BUY", v_full.stance, "BUY")
check("SPARSE info STILL trades (not NO_TRADE)", v_sparse.stance, "BUY")
check("sparse confidence < full confidence", v_sparse.confidence < v_full.confidence, True)
check("sparse size < full size", v_sparse.shares < v_full.shares, True)
check("confidence never falls below the floor", v_sparse.confidence >= CONF_FLOOR, True)

# 2) ... but a genuinely EMPTY read still abstains. "Uncertain" != "no edge".
print("\n2) an empty read must still abstain — uncertainty is not the same as no-edge")
empty = J(stock_pct_since_last_earnings=2.0, sector_etf_pct_same_window=1.0,
          pct_below_52w_high=5.0)                      # nothing verified, not washed
v_empty = edge_score("EMPTY", empty, MKT, T, CFG)
check("no signal -> NO_TRADE", v_empty.stance, "NO_TRADE")
check("edge inside the dead-band", abs(v_empty.edge_score) < EDGE_MIN, True)

# ---------------------------------------------------------------------------
# 3) THE FIX FOR GENSPARK'S BROKEN FORMULA — fair vol must NOT zero a strong long.
#    Under `edge = signal x completeness x asymmetry`, value=0 zeroed the product.
# ---------------------------------------------------------------------------
print("\n3) fairly-priced vol must NOT zero out a strong fundamental read")
check("IRM 1.00 -> value == 0", v_full.value, 0.0)
check("...yet the trade still fires (additive, not multiplicative)", v_full.stance, "BUY")
check("...with a real edge", v_full.edge_score > EDGE_MIN, True)

# 4) Tiers must be REACHABLE (GenSpark's multiplicative form made them impossible).
print("\n4) conviction tiers must be reachable")
strong = J(up_revisions_30d=8, down_revisions_30d=0, covering_analysts=10,
           rev_basis="ESTIMATE_REVISIONS", GG=1, gg_basis="FILED",
           VEL=1, vel_basis="GUIDANCE")
cheap = Market(price=100.0, avg_abs_open=8.0, confirmed_quarters=8,
               dollar_vol_20d=200_000_000, share_vol_20d=5_000_000,
               capital=18_000, vix=15.0, implied_move=4.5)        # IRM 0.56 = very cheap
v_strong = edge_score("STRONG", strong, cheap, T, CFG)
check("a strong+cheap+washed setup reaches HIGH or MAXIMUM",
      v_strong.conviction in ("HIGH", "MAXIMUM"), True)

# ---------------------------------------------------------------------------
# 5) SIZING IS FLAT WHILE CONVICTION IS UNVALIDATED.
#    Tier returns rank-ordered INVERSELY in the decision backtest (MAXIMUM -10.15%,
#    EXPLORATORY +1.27%, n=8). The ladder is logged but must not size.
# ---------------------------------------------------------------------------
print("\n5) conviction is LOGGED but must NOT size (it rank-ordered inversely, n=8)")
check("SIZE_BY_CONVICTION is OFF", E.SIZE_BY_CONVICTION, False)
check("budget is flat-x-confidence, NOT the tier ladder",
      round(v_strong.risk_budget, 6), round(E.FLAT_RISK_BUDGET * v_strong.confidence, 6))
check("a WEAK read and a STRONG read size the same when equally informed "
      "(conviction must not size)", v_full.risk_budget, v_strong.risk_budget)
check("but THIN information sizes smaller (confidence still does)",
      v_sparse.risk_budget < v_full.risk_budget, True)
check("but the tier is still recorded for calibration",
      v_strong.conviction in ("EXPLORATORY", "STANDARD", "HIGH", "MAXIMUM"), True)
check("the non-sizing is surfaced, not silent",
      any("NOT sizing" in c for c in v_strong.caveats), True)

# ---------------------------------------------------------------------------
# 6) SHORT HURDLE — v1.5.0 (HANDOFF §9.1, owner-approved 2026-07-30).
#    The `value < 0` RICHNESS VETO IS GONE: on an equity short you are short delta, not
#    vega, so straddle richness cannot touch the payoff. It is replaced by an ASYMMETRIC
#    DEAD-BAND (SHORT_EDGE_MIN = the STANDARD tier floor), which is the defensible form of
#    the same caution — shorts fight positive drift and the announcement premium, and that
#    is a statement about the PRIOR, so it belongs in the threshold.
#    These assertions lock BOTH halves so neither can creep back.
# ---------------------------------------------------------------------------
print("\n6) short hurdle — richness veto CUT, asymmetric dead-band IN")
from pre_edgescore import SHORT_EDGE_MIN, EDGE_MIN
bear = J(up_revisions_30d=0, down_revisions_30d=6, covering_analysts=10,
         rev_basis="ESTIMATE_REVISIONS", GG=-1, gg_basis="FILED", VEL=-1, vel_basis="GUIDANCE",
         stock_pct_since_last_earnings=5.0, sector_etf_pct_same_window=4.0,
         pct_below_52w_high=10.0)
bear_t = Truth(stock_pct_since_last_earnings=5.0, pct_below_52w_high=10.0, price=100.0)
rich = Market(price=100.0, avg_abs_open=8.0, confirmed_quarters=8,
              dollar_vol_20d=200_000_000, share_vol_20d=5_000_000,
              capital=18_000, vix=15.0, implied_move=13.0)             # IRM 1.63 = rich

# 6a) THE REVERSAL. Strongly bearish at FAIR vol now SHORTS. Under v1.4.0 the richness veto
#     refused this, which is precisely the gate that had no mechanism.
v_bear_fair = edge_score("BEAR_FAIR", bear, MKT, bear_t, CFG)          # IRM 1.00, fair
check("6a bearish + FAIR vol -> SHORT (veto cut)", v_bear_fair.stance, "SHORT")
check("6a and vol richness is irrelevant to the stance",
      edge_score("BEAR_RICH", bear, rich, bear_t, CFG).stance, v_bear_fair.stance)

# 6b) THE NEW BAR. A MARGINAL bearish read — inside [EDGE_MIN, SHORT_EDGE_MIN) — must NOT
#     short.
#
#     RE-PINNED v1.5.7 (DEFECT: normalise by populated legs). The ASSERTION IS UNCHANGED
#     — the asymmetric short band must still block a marginal bearish read. What changed
#     is WHICH read is marginal, and that is the fix doing its job, not the test being
#     bent to fit it:
#       * OLD: REV=-1 with GG/VEL UNSOURCED gave -1/4 = -0.25 -> |edge| 0.14 -> blocked.
#         But dividing a one-leg read by the three-leg range is exactly the defect; that
#         read was being quietly halved.
#       * NEW: the same REV=-1 with all three legs VERIFIED gives -1/4 = -0.25 and is
#         still blocked. The constant 4 was never wrong — it was only ever right for the
#         fully-populated case, which is what this now tests.
#     The single-leg version of this read is asserted separately in 6b2 below, because it
#     now behaves differently and that difference must be visible, not hidden.
marg_bear = J(up_revisions_30d=0, down_revisions_30d=2, covering_analysts=10,
              rev_basis="ESTIMATE_REVISIONS", GG=0, VEL=0,
              gg_basis="GUIDANCE", vel_basis="BOOKINGS",
              stock_pct_since_last_earnings=5.0, sector_etf_pct_same_window=4.0,
              pct_below_52w_high=10.0)
v_marg_bear = edge_score("MARG_BEAR", marg_bear, MKT, bear_t, CFG)
check("6b marginal short is inside the asymmetric band",
      EDGE_MIN <= abs(v_marg_bear.edge_score) < SHORT_EDGE_MIN, True)
check("6b -> NO_TRADE, not SHORT", v_marg_bear.stance, "NO_TRADE")
check("6b and the reason names the asymmetry",
      any("ASYMMETRIC" in r for r in v_marg_bear.reasons), True)

# 6b2) THE SIDE-EFFECT OF THE UNITS FIX, ASSERTED SO IT CANNOT BE FORGOTTEN.
#      The SAME REV=-1 read with GG/VEL UNSOURCED is normalised by REV's range alone
#      (2), giving -0.50 — and it now CLEARS the short bar where it used to be blocked.
#      This is the intended separation of concerns: `expectations` states how bearish the
#      read I ACTUALLY HAVE is, on its own scale, and `confidence` separately discounts
#      for how little I know. But it means a ONE-LEG read saturates the term quickly, and
#      for a +-1-range leg (GG or VEL) a SINGLE notch saturates it completely.
#      *** OPEN, owner's call: see METHOD.md 17.1. Not silently corrected. ***
marg_bear_1leg = J(up_revisions_30d=0, down_revisions_30d=2, covering_analysts=10,
                   rev_basis="ESTIMATE_REVISIONS", GG=None, VEL=None,
                   stock_pct_since_last_earnings=5.0, sector_etf_pct_same_window=4.0,
                   pct_below_52w_high=10.0)
v_1leg = edge_score("MARG_BEAR_1LEG", marg_bear_1leg, MKT, bear_t, CFG)
check("6b2 one-leg REV=-1 normalises to -0.50, not -0.25",
      v_1leg.expectations_momentum, -0.5)
check("6b2 and therefore now clears the short bar (documented consequence)",
      v_1leg.stance, "SHORT")
check("6b2 the caveat says which legs the norm used",
      any("normalised by the" in c for c in v_1leg.caveats), True)

# 6c) THE ASYMMETRY IS REAL: the mirror-image LONG at the SAME magnitude does trade.
marg_bull = J(up_revisions_30d=2, down_revisions_30d=0, covering_analysts=10,
              rev_basis="ESTIMATE_REVISIONS", GG=0, VEL=0,
              gg_basis="GUIDANCE", vel_basis="BOOKINGS",
              stock_pct_since_last_earnings=5.0, sector_etf_pct_same_window=4.0,
              pct_below_52w_high=10.0)
v_marg_bull = edge_score("MARG_BULL", marg_bull, MKT, bear_t, CFG)
check("6c identical |edge| on the long side",
      abs(v_marg_bull.edge_score) == abs(v_marg_bear.edge_score), True)
check("6c -> BUY (longs keep the lower bar)", v_marg_bull.stance, "BUY")
check("6c the short bar is strictly higher than the long bar",
      SHORT_EDGE_MIN > EDGE_MIN, True)

# 6d) SHORT_EDGE_MIN must stay DERIVED from TIERS — it is parameter-neutral by design.
from pre_edgescore import TIERS as _T
check("6d short bar == the STANDARD tier floor (0 new params)",
      SHORT_EDGE_MIN, next(lo for lo, n, _ in _T if n == "STANDARD"))

# 6e) A washed-out name still cannot be shorted, however bearish. Inherited protection.
wash_bear = J(up_revisions_30d=0, down_revisions_30d=6, covering_analysts=10,
              rev_basis="ESTIMATE_REVISIONS", GG=-1, gg_basis="FILED", VEL=-1,
              vel_basis="GUIDANCE", stock_pct_since_last_earnings=-30.0,
              sector_etf_pct_same_window=5.0, pct_below_52w_high=40.0)
wash_t = Truth(stock_pct_since_last_earnings=-30.0, pct_below_52w_high=40.0, price=100.0)
check("6e beaten-down name is never shorted",
      edge_score("WASH_BEAR", wash_bear, rich, wash_t, CFG).stance != "SHORT", True)

# ---------------------------------------------------------------------------
# 6f) §9.2 RENAME — `directional` -> `expectations_momentum`. The number is unchanged;
#     only the name is honest now. The old attribute must still resolve, because dated
#     drivers in runs/ are immutable history.
# ---------------------------------------------------------------------------
print("\n6f) §9.2 rename — expectations_momentum")
check("6f canonical field exists", hasattr(v_marg_bull, "expectations_momentum"), True)
check("6f legacy alias still resolves", v_marg_bull.directional,
      v_marg_bull.expectations_momentum)
# RE-PINNED v1.5.7. This assertion used to read "with GG/VEL unsourced it is exactly
# REV/4" — it was pinning the DEFECT itself: a one-leg read divided by the three-leg
# range. It now pins the corrected contract, both ways.
check("6f with all three legs verified it is REV/4 (the constant was the full case)",
      v_marg_bull.expectations_momentum, 0.25)
_one_leg_bull = J(up_revisions_30d=2, down_revisions_30d=0, covering_analysts=10,
                  rev_basis="ESTIMATE_REVISIONS", GG=None, VEL=None,
                  stock_pct_since_last_earnings=5.0, sector_etf_pct_same_window=4.0,
                  pct_below_52w_high=10.0)
check("6f with GG/VEL UNSOURCED it is REV/2 — normalised by what was populated",
      edge_score("X", _one_leg_bull, MKT, bear_t, CFG).expectations_momentum, 0.5)
check("6f render labels it 'exp', not 'dir'", "exp " in E.render(v_marg_bull), True)

# 7) Inherited protections must survive the rewrite.
print("\n7) inherited protections still hold")
cbr = J(up_revisions_30d=4, down_revisions_30d=0, covering_analysts=10,
        rev_basis="ESTIMATE_REVISIONS", GG=1, gg_basis="FILED",
        VEL=1, vel_basis="GUIDANCE", CBR="MANUFACTURED")
check("CBR MANUFACTURED blocks the long", edge_score("CBR", cbr, MKT, T, CFG).stance, "NO_TRADE")
illiq = Market(price=100.0, avg_abs_open=8.0, confirmed_quarters=8,
               dollar_vol_20d=1_000_000, share_vol_20d=5_000, capital=18_000)
check("G1 liquidity gate blocks", edge_score("ILLIQ", full, illiq, T, CFG).stance, "NO_TRADE")
dry = J(up_revisions_30d=4, down_revisions_30d=0, covering_analysts=10,
        rev_basis="ESTIMATE_REVISIONS", GG=1, gg_basis="FILED",
        VEL=1, vel_basis="GUIDANCE", G0="DRY_RUN")
check("G0 DRY_RUN blocks", edge_score("DRY", dry, MKT, T, CFG).stance, "NO_TRADE")
bad = edge_score("BAD", full, MKT, Truth(stock_pct_since_last_earnings=+90.0), CFG)
check("C4 reconciliation failure -> NO_TRADE", bad.stance, "NO_TRADE")

# 8) Exactly three outcomes, always.
print("\n8) the decision vocabulary is exactly three values")
alls = [v_full, v_sparse, v_empty, v_strong, v_bear_fair, v_marg_bear, v_marg_bull, bad]
check("every stance in {BUY, SHORT, NO_TRADE}",
      set(v.stance for v in alls) <= {"BUY", "SHORT", "NO_TRADE"}, True)
check("NO_TRADE never carries size",
      all(v.shares == 0 for v in alls if v.stance == "NO_TRADE"), True)

# 9) Ledger round-trip: the record must be readable by pre_ledger's stats/outcome path.
print("\n9) ledger registration round-trip (temp file; real ledger untouched)")
with tempfile.TemporaryDirectory() as td:
    lp = Path(td) / "t.jsonl"
    # allow_paused: this writes to a TEMP ledger. The pause guards LIVE capital,
    # not the test that proves the registration path still works.
    rec, v = register("TEST", full, MKT, T, CFG, event_date="2026-08-01",
                      allow_paused=True,
                      entry_close_date="2026-08-01", exit_open_date="2026-08-02",
                      sector_etf="SMH", note="selftest", ledger_path=lp)
    check("entry written", rec["type"], "entry")
    check("action is in the ledger's vocabulary",
          rec["verdict"]["action"] in ("BUY", "SHORT", "NO_TRADE"), True)
    check("conviction logged for tier calibration",
          "conviction" in rec["verdict"], True)
    check("sizing basis recorded", rec["verdict"]["sized_by"], "FLAT")
    check("exit spec present", rec["verdict"]["exit"]["exit_open_date"], "2026-08-02")
    check("integrity hash present", rec["integrity_hash"].startswith("sha256:"), True)
    check("calc-risk SHADOW captured", "action" in rec["verdict"]["shadow_calcrisk"], True)
    from pre_ledger import record_outcome, stats
    o = record_outcome(rec["id"], stock_open_pct=3.0, etf_open_pct=1.0,
                       beta=1.2, benchmark="SMH", ledger_path=lp)
    # AR = 3.0 - 1.2*1.0 = 1.8 (market-model, beta supplied)
    check("outcome scores against the edge verdict", o["idio_open_pct"], 1.8)
    s = stats(lp)
    check("stats sees the trade", s["n_trades"], 1)

# 10) rank(): live bets first, strongest edge on top.
print("\n10) rank() puts live bets first, strongest edge on top")
ordered = rank([v_empty, v_full, v_strong])
check("first is a live bet", ordered[0].stance != "NO_TRADE", True)
check("strongest edge leads", ordered[0].ticker, "STRONG")
check("abstention sinks to the bottom", ordered[-1].stance, "NO_TRADE")

# ---------------------------------------------------------------------------
# 14) [REVIEW #2 item 4] IMPLIED-MOVE PROVENANCE.
#     A stored implied move must say what it IS. CONTRADICTORY provenance is fatal;
#     merely UNDECLARED provenance is a warning — making it fatal broke every existing
#     caller at once, which is the wrong reading of fail-closed (that doctrine governs
#     missing DATA that would change a decision, not missing METADATA about present data).
# ---------------------------------------------------------------------------
print("\n14) implied-move provenance: contradictions fatal, gaps only warned")
from pre_engine import evaluate as _ev
from pre_impliedmove import decontaminate, sanity as im_sanity
_ok = Market(price=100.0, avg_abs_open=8.0, confirmed_quarters=8, dollar_vol_20d=200_000_000,
             share_vol_20d=5_000_000, capital=18_000, implied_move=8.0)
check("undeclared basis stays USABLE", _ev(full, _ok, T, CFG).action != "INPUT_INVALID", True)
check("...but is WARNED as unauditable",
      any("no declared basis" in w for w in _ev(full, _ok, T, CFG).warnings), True)
_bad = Market(price=100.0, avg_abs_open=8.0, confirmed_quarters=8, dollar_vol_20d=200_000_000,
              share_vol_20d=5_000_000, capital=18_000, implied_move=5.0,
              implied_move_basis="DECONTAMINATED", implied_move_raw=None)
check("DECONTAMINATED with no raw is FATAL", _ev(full, _bad, T, CFG).action, "INPUT_INVALID")
_imp = Market(price=100.0, avg_abs_open=8.0, confirmed_quarters=8, dollar_vol_20d=200_000_000,
              share_vol_20d=5_000_000, capital=18_000, implied_move=9.0,
              implied_move_basis="DECONTAMINATED", implied_move_raw=7.0)
check("decontaminated > raw is FATAL", _ev(full, _imp, T, CFG).action, "INPUT_INVALID")
check("out-of-range implied move is FATAL", bool(im_sanity(180.0, 180.0, "RAW")), True)

# ---------------------------------------------------------------------------
# 15) The decontamination must FAIL CLOSED rather than fabricate cheapness.
#     NVTS's stored implied_move of 5.70 (IRM 0.47, "screamingly cheap") came from a
#     correction that removed 88% of a straddle the market was charging 16.70% for.
#     An estimate whose correction exceeds its result is not a measurement.
# ---------------------------------------------------------------------------
print("\n15) decontamination must refuse to fabricate cheapness")
nvts = decontaminate(16.70, 144.0, 3)          # the real NVTS inputs
check("NVTS correction removes >50% of variance", nvts["variance_removed_pct"] > 50, True)
check("...so it REFUSES rather than returning 5.7", nvts["implied_move"], None)
check("...and states why", "FAIL CLOSED" in (nvts["refused_reason"] or ""), True)
be = decontaminate(23.16, 120.0, 2)            # the real BE inputs — a modest correction
check("a modest correction is ACCEPTED", be["implied_move"] is not None, True)
check("...and never exceeds its raw", be["implied_move"] <= be["implied_move_raw"], True)
check("expiry ON the event needs no correction",
      decontaminate(9.0, 100.0, 0)["implied_move_basis"], "RAW")

# ---------------------------------------------------------------------------
# 16) THE BLINDNESS DECLARATION (2026-08-09)
#
#     Three external reviewers independently found that hosting the postmortem,
#     the scout and /earnings in the PRE chat leaves portfolio state in a
#     persistent context window that later produces pre-registrations. The
#     structural fix is the /pre-register vs /pre-post chat split. THIS is the
#     audit half: a declaration of what the forecast could see, frozen INSIDE
#     the integrity hash so it cannot be revised once an outcome is known.
#
#     The rejected alternative was asserting that scoring is byte-identical
#     with and without a portfolio-context FILE present. That tests file
#     absence; the channel is the conversation. It would have proved nothing.
# ---------------------------------------------------------------------------
print("\n16) the blindness declaration is frozen inside the integrity hash")
import tempfile as _tf
from pathlib import Path as _P
from pre_ledger import _hash as _lh

_tmp = _P(_tf.mkdtemp()) / "ctx.jsonl"
_j = Judgment(up_revisions_30d=12, down_revisions_30d=2, covering_analysts=20,
              stock_pct_since_last_earnings=-30.0, sector_etf_pct_same_window=2.0)
_m = Market(price=100.0, avg_abs_open=8.0, confirmed_quarters=8,
            dollar_vol_20d=200_000_000, share_vol_20d=5_000_000,
            capital=18_000, vix=15.0, implied_move=8.0)

_blind, _ = register("AAA", _j, _m, event_date="2026-09-01", ledger_path=_tmp,
                         allow_paused=True)
check("default is BLIND", _blind["context"]["status"], "BLIND")
check("...and says so explicitly", _blind["context"]["portfolio_aware"], False)

_aware, _ = register("BBB", _j, _m, event_date="2026-09-01", ledger_path=_tmp,
                     portfolio_aware=True, context_sources=["accounts/10K.json"],
                     allow_paused=True)
check("an aware row is tagged PORTFOLIO_AWARE", _aware["context"]["status"], "PORTFOLIO_AWARE")
check("...and names what it saw", _aware["context"]["sources"], ["accounts/10K.json"])

# The property that matters: context is covered by the hash. Rehash the frozen
# payload WITHOUT context and the hash must not reproduce - i.e. you cannot
# strip or flip the declaration after the fact and still pass a tamper check.
_frozen_full = {k: _aware[k] for k in
                ("schema", "engine_version", "ticker", "event_date", "inputs", "verdict", "context")}
check("hash reproduces from the full frozen payload", _lh(_frozen_full), _aware["integrity_hash"])

_frozen_stripped = {k: v for k, v in _frozen_full.items() if k != "context"}
check("removing the declaration BREAKS the hash", _lh(_frozen_stripped) != _aware["integrity_hash"], True)

_frozen_flipped = dict(_frozen_full)
_frozen_flipped["context"] = {"portfolio_aware": False, "sources": [], "status": "BLIND"}
check("forging BLIND onto an aware row BREAKS the hash",
      _lh(_frozen_flipped) != _aware["integrity_hash"], True)

print(f"\n=== {PASS} passed, {FAIL} failed ===")
raise SystemExit(1 if FAIL else 0)
