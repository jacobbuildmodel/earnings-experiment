"""
PRE Edge-Score layer — **PRODUCTION SCORER** (owner-wired 2026-07-29).
================================================================================
This is now the PRIMARY decision layer. `pre_calcrisk.calc_risk` is demoted to a
SHADOW cross-check: it is still evaluated on every decision and logged alongside, so the
counterfactual ("what would the old scorer have said?") keeps accruing for free.

Layer order is now:  pre_engine (sign/DS, protections)
                       -> pre_calcrisk (payoff asymmetry, SHADOW)
                         -> pre_edgescore (continuous edge, LIVE)

OWNER DECISION RECORD (2026-07-29). Wired in over my recommendation to shadow it first.
The recommendation and its basis are preserved here so the decision stays auditable:
  * FOR: it fixes the real complaint. Abstention 88% -> 56% on the frozen ledger; 3 live
    bets become 11; two genuine gap winners the old scorer refused (SAP +3.66%,
    APLD +5.20%) become trades.
  * AGAINST (my position at the time): the conviction ladder appeared to rank-order returns
    inversely. **That evidence was later shown to be invalid** — see SIZE_BY_CONVICTION below.
    The switch stays off on a prior (unvalidated signals must not scale risk), not on that.
  * EVERYTHING measured on the ledger is HINDSIGHT-CONTAMINATED — not only the P&L but the
    TIER LABEL too, since this scorer post-dates every logged row. Nothing here is validated.
    Forward evidence only.

v1.1.0 (external review #2) — three fixes, all argued from MECHANISM, not from sample P&L:
  * `value` (option richness) REMOVED from the directional sum. Variance cannot forecast sign.
  * A SHORT now requires a bearish FUNDAMENTAL read. Both historical shorts were taken against
    the model's own bullish view, dragged negative purely by `value`. Both lost.
  * Sector weights normalised by sum(w)/4 — they were changing overall GAIN, not just factor
    MIX, so pharma/energy could never reach the top tiers and semis/software silently clipped.

WHAT PROBLEM IT SOLVES
  The live model conflates "I have no edge" with "I am uncertain". Any UNAVAILABLE input
  widens the worst-case band, the band straddles the threshold, and the trade dies. That is
  a MAXIMIN rule — right when a wrong bet is catastrophic, wrong on an $18k book where the
  cost of never betting exceeds the cost of a small wrong bet.

  Fix: uncertainty SHRINKS THE POSITION rather than killing it, via a confidence FLOOR.

WHY ADDITIVE, NOT MULTIPLICATIVE
  The external review proposed edge = signal x completeness x asymmetry. That form is
  unusable: (a) three sub-1.0 factors make the top tiers mathematically unreachable,
  (b) asymmetry = 0 (fairly-priced vol) ZEROES a screaming fundamental long — more
  restrictive than today, the opposite of the goal, and (c) a max(0, cheapness) term cannot
  express a short, which wants vol RICH. Additive with a confidence floor fixes all three.

OWNER DIRECTIVE (2026-07-29): NO portfolio-level caps. Verdict and size are emitted as
computed; position-level risk management is the operator's, not the model's. The
correlation exposure of same-night same-sector clusters was raised once and declined.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from pre_engine import Judgment, Market, Truth, Skew, EngineConfig, evaluate, PARAMS

__version__ = "1.5.7"

# ============================================================================
# v1.5.0 — HANDOFF §9.1 and §9.2, both OWNER-APPROVED 2026-07-30.
# These are the two premise-level questions that sat open for weeks. Neither was
# argued from sample P&L; both are mechanism arguments, which is the only kind of
# argument available at n=8.
#
# §9.1 THE SHORT LEG — the richness veto is CUT.
#   `short_ok` required `value < 0` (a richly-priced straddle). On an equity short you are
#   short DELTA, not short VEGA: you never pay the straddle, so its richness cannot touch
#   your payoff. This is the same category error already cut twice — `value` out of the
#   directional sum (v1.1.0) and `vrich` out of positioning (v1.2.0) — a VARIANCE estimate
#   used as a DIRECTION filter. It breaks no winner by construction: there are no short
#   winners (0-for-3 lifetime), so Abstraction-Test limb 2 is satisfied trivially, and limb 1
#   is waived because this is a mechanism cut, not a fix invented after a loss.
#
#   REPLACED BY an ASYMMETRIC DEAD-BAND, which is the defensible form of the same caution.
#   Shorts genuinely do face a worse base rate — positive unconditional equity drift plus a
#   positive average abnormal return around earnings announcements. That is a statement about
#   the PRIOR, so it belongs in the THRESHOLD, not smuggled in as a vol filter.
#   SHORT_EDGE_MIN reuses the EXISTING STANDARD tier floor rather than inventing a number:
#   **a short may not be taken at EXPLORATORY conviction at all.** Parameter cost: ZERO.
#
#   WHAT WAS ALSO LEARNED (2026-07-29 batch): the veto was never the binding constraint.
#   FICO scored edge -0.225 with positioning -1 and was still refused, because
#   `expectations_momentum = 0`. That clause requires NEGATIVE ANALYST REVISIONS — i.e. the
#   short leg is gated on the model's least defensible term. It is retained for now, but it
#   is the next thing to examine, and it is why FICO stays NO_TRADE even after this change.
#
# §9.2 `directional` IS RENAMED `expectations_momentum`.
#   It was never a fundamental read. Since v1.5.5 removed REVISIONS from FORWARD_VEL_BASES,
#   and GG has been unsourced on 100% of names in every recent batch:
#         expectations_momentum = (REV + GG + VEL + FLAG) / 4 = REV / 4
#   — one analyst-revisions number divided by four, wearing the name "the fundamental read".
#   The rename is free and it stops the category error propagating; calling this term
#   "directional" is what let the confusion survive as long as it did.
#
#   THE SIGN IS DELIBERATELY NOT FLIPPED. Two real mechanisms oppose: revision momentum as an
#   INFORMATION proxy (bullish, and among the most durable documented anomalies) versus the
#   raised-bar argument (bearish). n=10 cannot adjudicate, and the only forward evidence that
#   exists points the WRONG WAY FOR THE BAR ARGUMENT (§10: max-raised-bar names gapped +8.31%
#   mean). Flipping a sign on a hypothesis the data currently contradicts would be exactly the
#   sample-chasing the mechanism standard exists to prevent.
#
#   HONEST CONSEQUENCE, stated rather than hidden: this model has exactly TWO independent
#   signals — expectations momentum and price positioning. Two is a fine number. Claiming
#   five was the problem. The real fix is to source GG (company-reported, knowable pre-print,
#   the only proposed directional term that is not analyst opinion).
# ============================================================================

# ---- weights & bands (PRIORS, frozen — not discoveries) ---------------------
# v1.1.0: W_VALUE cut from 0.30 to 0.0. THE REASON IS MECHANISM, NOT SAMPLE P&L.
#   `value` is derived from IRM = implied_move / avg_abs_open — option richness. Option
#   richness is a forecast of the MAGNITUDE of a move. It carries NO information about its
#   SIGN. Wiring it into a directional score as "cheap -> long / rich -> short" is a category
#   error: a variance estimate used as a direction estimate. There is no mechanism by which
#   a richly-priced straddle implies the stock falls.
#   The sample merely fails to contradict this — the term expressed a directional opinion on
#   6 of 11 scored trades and was wrong on essentially all of them, and it was the clearest
#   possible demonstration: GLW (IRM 0.68) and NVTS (IRM 0.47) both DID make large moves
#   (-13.5% and -8.8% to close) — right as a variance forecast, wrong as a direction forecast.
#   `value` is still COMPUTED, LOGGED, and used as a SHORT VETO (a filter on richness, which
#   is a legitimate use of a variance signal). It no longer votes on direction.
W_EXPECTATIONS, W_VALUE, W_POSITIONING = 0.71, 0.00, 0.29
W_DIRECTIONAL = W_EXPECTATIONS      # DEPRECATED alias (§9.2 rename) — dated run files in
                                    # runs/ are immutable history and still import this.
CONF_FLOOR, CONF_SPAN = 0.55, 0.45      # confidence = FLOOR + SPAN * completeness
# v1.2.0: 6.0 -> 4.0. SAT was removed from the directional sum (see below), so the maximum
# fundamental read is now REV(+2) + GG(+1) + VEL(+1) = 4.
EXPECTATIONS_NORM = 4.0                 # LEGACY: the full-population norm, kept for the
                                        # deprecated alias and for replay of dated runs/.
# v1.5.7 — the RANGE of each fundamental leg. Their sum IS EXPECTATIONS_NORM (2+1+1=4),
# which is the point: the constant was never arbitrary, it was the fully-populated case.
# These are not new parameters; they are the bucket bounds the engine already enforces.
LEG_RANGE = {"REV": 2, "GG": 1, "VEL": 1}
LEG_RANGE_TOTAL = sum(LEG_RANGE.values())
DIRECTIONAL_NORM = EXPECTATIONS_NORM   # DEPRECATED alias (§9.2 rename)
VALUE_NORM = 0.45                       # IRM distance from 1.0 that saturates the read
EDGE_MIN = 0.08                         # below this, genuinely no read -> NO_TRADE

TIERS = [  # (min_abs_edge, name, risk_budget_pct_of_capital)
    (0.55, "MAXIMUM",     0.0150),
    (0.35, "HIGH",        0.0100),
    (0.20, "STANDARD",    0.0060),
    (0.08, "EXPLORATORY", 0.0025),
]

# §9.1 (owner-approved 2026-07-30) — THE ASYMMETRIC DEAD-BAND that replaces the richness veto.
# A short must clear the STANDARD tier floor; an exploratory-strength short is not a trade.
# DERIVED, NOT INVENTED: it reuses TIERS' existing STANDARD boundary, so the parameter count is
# UNCHANGED. Mechanism: equities carry positive unconditional drift plus a positive average
# abnormal return around earnings announcements, so a short fights the base rate and must clear
# a higher bar. A base-rate prior belongs in a threshold — it does not belong disguised as a
# filter on implied volatility, which is what `value < 0` was.
SHORT_EDGE_MIN = next(lo for lo, name, _ in TIERS if name == "STANDARD")   # = 0.20

# ---------------------------------------------------------------------------
# SIZE_BY_CONVICTION — DEFAULT FALSE.
#
# CORRECTED RATIONALE (external review #2). An earlier version of this comment justified the
# switch with a tier-vs-return table showing conviction "perfectly inverted". THAT TABLE WAS
# INVALID; its numbers do not reproduce. Three compounding defects:
#   1. the backtest silently dropped 3 of 11 outcomes through an entry-id / de-dup mismatch,
#      and the dropped rows were BOTH TAILS (AEHR +35.04%, NFLX -10.64%, ASML +1.69%);
#   2. the only trade in the MAXIMUM tier (AMKR) was registered AFTER its outcome was known,
#      so it was never a live pre-registration;
#   3. decisively — the TIER LABEL is exactly as hindsight-contaminated as the P&L.
#      `edge_score()` was written knowing these outcomes, so a post-hoc function assigning its
#      top score to the known-worst trade is NOT evidence that top scores are bad. Quarantining
#      the P&L column while trusting the tier column was a logical error.
#
# The switch stays FALSE regardless, on a PRIOR rather than a finding:
#       **an unvalidated signal must not scale risk.**
# The ladder was never validated, so it should never have been sizing. That argument needs no
# backtest and is untouched by the table being wrong.
#
# And be honest about "flip it on at n >= 20 per tier": at ~11 trades in three weeks clustering
# to ~6 event-days, that bar is years away and probably unreachable. Every component here must
# therefore earn its place by MECHANISM, because none of them will ever get a statistical
# justification. That is the standard `value` failed (see W_VALUE above).
# ---------------------------------------------------------------------------
SIZE_BY_CONVICTION = False
FLAT_RISK_BUDGET = 0.0050          # 0.50% of capital per trade while tiers are unvalidated

# SECTOR WEIGHTS — **REMOVED in v1.3.0.** They are retained as an identity map ONLY so the
# sector label keeps flowing into the log.
#
# WHY CUT. They were 18 invented numbers (24 before SAT went). Tested against every entry in
# the ledger: **weighting changed ZERO verdicts out of 21** versus flat weights. So they were
# 18 unvalidated parameters purchasing no decision. They cannot be validated either — with ~21
# events spread over 6 sectors there will never be enough per-sector data to fit them, and the
# standard now in force is that a component must earn its place by MECHANISM. "Semis lead on
# bookings" is a real economic story, but it justifies the ORDERING of factors, never the
# specific number 2.0 — and the ordering bought nothing measurable.
#
# If they ever return they must come back as a mechanism with a stated magnitude, not a
# hand-tuned table.
SECTOR_WEIGHTS = {
    "SEMIS":      {"REV": 1.0, "GG": 1.0, "VEL": 1.0},
    "PHARMA":     {"REV": 1.0, "GG": 1.0, "VEL": 1.0},
    "FINTECH":    {"REV": 1.0, "GG": 1.0, "VEL": 1.0},
    "SOFTWARE":   {"REV": 1.0, "GG": 1.0, "VEL": 1.0},
    "INDUSTRIAL": {"REV": 1.0, "GG": 1.0, "VEL": 1.0},
    "ENERGY":     {"REV": 1.0, "GG": 1.0, "VEL": 1.0},
    "DEFAULT":    {"REV": 1.0, "GG": 1.0, "VEL": 1.0},
}

SECTOR_OF = {
    "AEHR": "SEMIS", "ASML": "SEMIS", "AMKR": "SEMIS", "INTC": "SEMIS", "TSM": "SEMIS",
    "NVTS": "SEMIS", "RMBS": "SEMIS", "KLAC": "SEMIS", "TER": "SEMIS", "CLS": "SEMIS",
    "APLD": "SEMIS", "SKHY": "SEMIS",
    "AZN": "PHARMA", "UNH": "PHARMA", "MEDP": "PHARMA",
    "PYPL": "FINTECH", "V": "FINTECH", "SPGI": "FINTECH",
    "NFLX": "SOFTWARE", "CDNS": "SOFTWARE", "SAP": "SOFTWARE", "NOW": "SOFTWARE",
    "IBM": "SOFTWARE", "GOOG": "SOFTWARE", "CHTR": "SOFTWARE", "VZ": "SOFTWARE",
    "GLW": "INDUSTRIAL", "FLEX": "INDUSTRIAL", "NOK": "INDUSTRIAL", "WIT": "INDUSTRIAL",
    "UPS": "INDUSTRIAL", "BE": "INDUSTRIAL",
    "NEE": "ENERGY", "QS": "ENERGY",
}


def _fund_weight_sum(W):
    """Sum of the FUNDAMENTAL sector weights (REV/GG/VEL). Used to hold overall gain equal
    across sectors so the weights express factor MIX only, never loudness."""
    return W["REV"] + W["GG"] + W["VEL"]


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def _sign(x):
    return 1 if x > 0 else (-1 if x < 0 else 0)


@dataclass
class EdgeVerdict:
    ticker: str
    stance: str                 # BUY / SHORT / NO_TRADE
    conviction: str             # MAXIMUM / HIGH / STANDARD / EXPLORATORY / NONE
    edge_score: float
    raw_edge: float
    expectations_momentum: float   # §9.2: was `directional`. It is REV/4 — analyst revisions,
                                   # NOT a fundamental read. `.directional` still resolves.
    value: float
    positioning: float
    completeness: float
    confidence: float
    sector: str
    risk_budget: float          # fraction of capital
    shares: int
    gap_at_risk: float
    notional: float
    sizing_basis: str
    capital: float
    irm: Optional[float]
    reasons: list = field(default_factory=list)
    caveats: list = field(default_factory=list)
    # ---- v1.5.7b PLUMBING: THE NORMALISATION AUDIT TRAIL ----------------------
    # Adds LOGGED VALUES and moves nothing — no verdict, no size, no tier depends
    # on these. PLUMBING by the governance definition (re-running reproduces
    # byte-identical verdicts).
    #
    # WHY IT EXISTS. `expectations` is now normalised by the range of the legs
    # actually verified, which is correct — but with a single +-1 leg the divisor
    # falls to 1 and ONE NOTCH SATURATES THE TERM. A lone VEL=+1 reads MAXIMUM.
    # The "confidence separates that concern" defence does not survive arithmetic:
    # dropping the norm 4 -> 1 INFLATES expectations 4x, and confidence's entire
    # live span is 0.775 -> 1.00, a 1.29x discount. A fourfold inflation is not
    # absorbed by a 29% haircut. The concern is not separated; it is abandoned.
    #
    # The label is the lie, not the score: normalisation answers "how strong is
    # this reading relative to the instrument", conviction claims "how strong is
    # my read". Those coincide only when the instrument HAS RESOLUTION. VEL is
    # 3-state; a 3-state instrument can express DIRECTION but not STRENGTH. So
    # MAXIMUM off one VEL notch is an INSTRUMENT LIMIT LOGGED AS A SIGNAL — the
    # same species of error as reading a variance estimate as a direction
    # estimate, which is why `value` was cut.
    #
    # The fix is queued, not shipped (a third correction in one session is how the
    # guide-freshness gate happened). These three fields make the delay SAFE
    # rather than merely deferred: with the raw numerator and the divisor on every
    # row, any row written from here can have its true tier RE-DERIVED under any
    # future norm. That converts an irreversible EVIDENCE corruption into a
    # recoverable LABELLING artifact — the same principle as the dossier keeping
    # counters after deleting detail, and as detection-not-prevention on the hash.
    #
    # This matters NOW and not later: pre_batch.py feeds `expectations_momentum`
    # straight into pre_forecast, so forecasts.jsonl is accruing conviction labels
    # during the pause, on the one layer deliberately left running.
    fund_leg_sum: Optional[float] = None      # RAW weighted numerator, pre-division
    fund_norm: Optional[float] = None         # the divisor actually used
    verified_legs: list = field(default_factory=list)   # which legs set that divisor


# Back-compat for the §9.2 rename: dated drivers in runs/ are immutable history and read
# `.directional`. Read-only alias — the canonical field is `expectations_momentum`.
EdgeVerdict.directional = property(lambda self: self.expectations_momentum)


def edge_score(ticker: str, j: Judgment, m: Market, t: Optional[Truth] = None,
               cfg: Optional[EngineConfig] = None, skew: Optional[Skew] = None,
               sector: Optional[str] = None) -> EdgeVerdict:
    cfg = cfg or EngineConfig(fasttrack=True, watch=False, react_in_ds=False)
    r = evaluate(j, m, t=t, cfg=cfg, skew=skew)
    sec = sector or SECTOR_OF.get(ticker, "DEFAULT")
    W = SECTOR_WEIGHTS.get(sec, SECTOR_WEIGHTS["DEFAULT"])
    reasons, caveats = [], []

    # ---- hard gates stay BINARY. These are safety, not edge. -----------------
    if r.action == "INPUT_INVALID":
        return EdgeVerdict(ticker, "NO_TRADE", "NONE", 0, 0, 0, 0, 0, 0, 0, sec, 0, 0, 0,
                           0.0, "", m.capital, None,
                           ["INPUT_INVALID (fail closed): " + "; ".join(r.warnings)])
    gate_fail = (r.no_trade_subtype == "GATE_FAIL") or r.action == "DRY_RUN"

    # ---- A. DIRECTIONAL EDGE (sector-weighted fundamentals) ------------------
    # v1.2.0 — SAT REMOVED from the directional sum. Two independent reasons, both mechanism:
    #
    #   (a) CATEGORY. `directional` is meant to be the FUNDAMENTAL read — what the business is
    #       doing. SAT measures where the PRICE sits relative to its sector and its 52-week
    #       range. That is a positioning measure, not a fundamental one. It never belonged in
    #       this term.
    #   (b) DOUBLE-COUNT. SAT and `wash` are computed from the SAME TWO RAW INPUTS
    #       (excess-vs-sector, 52-week position). Measured on the ledger: corr(SAT, wash) =
    #       +0.69, same sign or both zero on 16/21 entries. So "this stock is beaten down" was
    #       being priced TWICE — once through directional x0.71 and again through
    #       positioning x0.29. Quantified across 21 entries, that one observation accounted for
    #       a MEAN 92% / MEDIAN 56% of |raw_edge|, and 100% on NFLX, AEHR, SAP, INTC, GLW, PYPL
    #       (>100% on BE and TER, where it overwhelmed opposing fundamentals).
    #
    # This is why the model was, in substance, "buy beaten-down stocks into earnings" while
    # presenting itself as a multi-factor score. Washout is now counted ONCE, in positioning.
    c = r.components
    weighted = (W["REV"] * c["REV"] + W["GG"] * c["GG"]
                + W["VEL"] * c["VEL"] + c["FLAG"])
    # v1.1.0 GAIN NORMALISATION. Sector weights were intended to change WHICH FACTOR matters
    # per sector; as written they also changed HOW LOUD the sector is, because DIRECTIONAL_NORM
    # was calibrated for the DEFAULT weight-sum of 4.0. Consequence: an identical maxed-out
    # read scored 1.00 in SEMIS but only 0.55 in PHARMA — pharma and energy could NEVER reach
    # the top tiers regardless of fundamentals, while semis/software silently CLIPPED, throwing
    # away real signal at the top. Dividing by (sum(w)/4.0) restores equal gain across sectors
    # so the weights express factor MIX only.
    # ---- v1.5.7 DEFECT FIX: NORMALISE BY THE LEGS ACTUALLY POPULATED ---------
    # THE DEFECT (external review #3, verified in verify_claims.py).
    # `EXPECTATIONS_NORM = 4.0` is the summed RANGE of the three fundamental legs:
    # REV(+-2) + GG(+-1) + VEL(+-1) = 4. It is the CORRECT normaliser for a model
    # running all three. We run ONE. So with GG and VEL unsourced, `expectations`
    # could only ever span [-0.5,+0.5] while `positioning` spanned {-1,0,+1} — and
    # the published 0.71/0.29 split then realises as:
    #       one REV notch  = 0.71 * 0.25 = 0.1775
    #       the washout flag = 0.29 * 1  = 0.2900   <-- 1.63x LOUDER
    # Measured consequence: a WASHED name with DETERIORATING revisions (REV=-1)
    # scored +0.0872 and BOUGHT, over the 0.08 bar. So "buy beaten-down stocks into
    # earnings, wearing a multi-factor costume" — the thing v1.2.0 claims to have
    # dismantled — was never dismantled. Cutting SAT removed the DOUBLE-COUNT; it
    # did not remove the DOMINANCE.
    #
    # This is NOT an independent bug. It is the GG/VEL sourcing gap expressing itself
    # as a silent gain error, which decides the right fix:
    #   * dividing by a hard-coded 2 would fit the normaliser to a temporary outage
    #     and break on the day GG lands;
    #   * restating the weights in the documentation changes nothing real;
    #   * normalising by the legs ACTUALLY VERIFIED is self-correcting, adds NO
    #     parameter, and auto-adjusts when GG arrives.
    # It is the same gain-normalisation already applied to the sector weights in
    # v1.1.0 before they were cut, for exactly the same reason.
    #
    # HONEST STATEMENT OF WHAT THIS BUYS: it makes REV louder in order to demote
    # washout, and REV has no standalone validation either. It REALLOCATES AUTHORITY
    # BETWEEN TWO UNVALIDATED TERMS. The justification is NOT "this improves the hit
    # rate" — it is that the model was doing something other than what it said, and a
    # record produced by a mis-specified scorer cannot be interpreted. That is
    # sufficient on its own, and it is the whole DEFECT-tier claim.
    _verified_legs = [leg for leg in ("REV", "GG", "VEL") if leg in (r.verified or [])]
    fund_norm = sum(LEG_RANGE[leg] for leg in _verified_legs)
    _fund_leg_sum = weighted          # RAW numerator, logged pre-division (PLUMBING)
    if fund_norm <= 0:
        # nothing verified: no fundamental read exists. Fail to zero rather than
        # dividing by a constant that implies legs we do not have.
        expectations = 0.0
        caveats.append("no fundamental leg VERIFIED -> expectations 0 (was silently "
                       "divided by the full 3-leg range)")
    else:
        norm = fund_norm * (_fund_weight_sum(W) / 3.0)
        expectations = _clamp(weighted / norm, -1.0, 1.0)
        if fund_norm < LEG_RANGE_TOTAL:
            caveats.append(f"expectations normalised by the {fund_norm} of "
                           f"{LEG_RANGE_TOTAL} leg-range actually verified "
                           f"({'+'.join(l for l in ('REV','GG','VEL') if l in (r.verified or []))})")

    # ---- B. VALUE EDGE (signed: serves longs AND shorts) ---------------------
    irm = round(m.implied_move / m.avg_abs_open, 2) if (m.implied_move and m.avg_abs_open) else None
    value = _clamp((1.0 - irm) / VALUE_NORM, -1.0, 1.0) if irm is not None else 0.0

    # ---- C. POSITIONING EDGE -------------------------------------------------
    excess = None
    if j.stock_pct_since_last_earnings is not None and j.sector_etf_pct_same_window is not None:
        excess = j.stock_pct_since_last_earnings - j.sector_etf_pct_same_window
    dd = j.pct_below_52w_high
    washed = (excess is not None and excess <= -15.0) and (dd is not None and dd >= 20.0)
    extended = (excess is not None and excess >= 15.0)
    wash = 1 if washed else (-1 if extended else 0)
    # v1.2.0 — `vrich` REMOVED (was 40% of positioning). Same category error as `value`:
    # implied-vs-realized vol is a VARIANCE forecast and carries no information about SIGN.
    # It was also populated on only 4 of 21 ledger entries, so it was mostly a no-op that
    # occasionally injected an unjustified directional opinion. Still computed upstream and
    # logged by the engine; it simply no longer votes.
    vrich_sign = 0
    if skew is not None and r.skew_components:
        vrich_sign = _sign(r.skew_components.get("RICH", 0))   # logged only
    positioning = float(wash)

    # ---- completeness over the 5 information slots --------------------------
    # COMPLETENESS = how much of what FEEDS THE SCORE was actually measured.
    # v1.3.0 fixes two defects here:
    #   * SAT was a slot but no longer feeds anything (removed from directional in v1.2.0).
    #   * IRM was a slot, but since `value` stopped voting it informs NOTHING on a long — it
    #     survives only as a short-side richness veto. Counting it penalised the position size
    #     of a long for missing an input that could not have changed the long thesis. Perverse:
    #     the model docked you for lacking the one input that had been hurting you.
    # Slots are now exactly the terms that move the score: the three fundamentals + washout.
    slots = {"REV": "REV" in (r.verified or []), "GG": "GG" in (r.verified or []),
             "VEL": "VEL" in (r.verified or []), "WASH": excess is not None and dd is not None}
    completeness = sum(1 for v in slots.values() if v) / len(slots)
    confidence = CONF_FLOOR + CONF_SPAN * completeness      # <-- the floor is the design

    raw = W_EXPECTATIONS * expectations + W_VALUE * value + W_POSITIONING * positioning
    score = raw * confidence

    missing = [k for k, v in slots.items() if not v]
    if missing:
        caveats.append(f"unverified: {', '.join(missing)} -> confidence {confidence:.2f} "
                       f"(size shrunk, NOT abstained)")

    # ---- verdict -------------------------------------------------------------
    # A short must ALSO have the event richly priced and the name not beaten down —
    # shorts fight the long-side earnings-announcement premium, so they clear a higher bar.
    # v1.1.0: a SHORT now additionally requires the FUNDAMENTAL read to be bearish.
    # Both shorts in the model's entire history (ASML, INTC) were taken against a POSITIVE
    # directional read — the score was dragged negative purely by the `value` term, which
    # cannot forecast sign. Shorting your own bullish fundamental view was structurally
    # possible and is now impossible. `value < 0` is retained as a richness VETO (a short
    # must also be richly priced), which is a legitimate use of a variance signal.
    # v1.5.0 (§9.1, owner-approved): the `value < 0` richness veto is GONE. What remains is a
    # bearish expectations read, a name that is not already beaten down, and — new — an
    # ASYMMETRIC dead-band that a marginal short cannot clear. See SHORT_EDGE_MIN.
    short_ok = (expectations < 0) and (positioning <= 0)
    if gate_fail:
        stance = "NO_TRADE"; reasons.append("hard gate failed — sealed protection")
    elif abs(score) < EDGE_MIN:
        stance = "NO_TRADE"; reasons.append(f"edge {score:+.3f} inside the +/-{EDGE_MIN} dead-band "
                                            f"— genuinely no read")
    elif score >= EDGE_MIN:
        stance = "BUY"
        reasons.append(f"edge {score:+.3f} (exp {expectations:+.2f} / val {value:+.2f} / "
                       f"pos {positioning:+.2f}) x conf {confidence:.2f}")
    elif score > -SHORT_EDGE_MIN:
        stance = "NO_TRADE"
        reasons.append(f"edge {score:+.3f} is bearish but inside the ASYMMETRIC short band "
                       f"(needs <= -{SHORT_EDGE_MIN}): shorts fight positive drift and the "
                       f"earnings-announcement premium, so an EXPLORATORY-strength short is "
                       f"not a trade")
    elif short_ok:
        stance = "SHORT"
        reasons.append(f"edge {score:+.3f} clears the asymmetric short bar (<= -{SHORT_EDGE_MIN}), "
                       f"expectations {expectations:+.2f} bearish and the name is not beaten down")
    else:
        stance = "NO_TRADE"
        reasons.append(f"edge {score:+.3f} negative but the SHORT bar is unmet "
                       f"(needs bearish expectations AND not-washed)")

    # CBR long-block (inherited protection)
    if stance == "BUY" and j.CBR != "CLEAN":
        stance = "NO_TRADE"; reasons.append("CBR MANUFACTURED — long blocked (protection)")

    # ---- conviction & size ---------------------------------------------------
    conv, budget = "NONE", 0.0
    if stance in ("BUY", "SHORT"):
        for lo, name, b in TIERS:
            if abs(score) >= lo:
                conv, budget = name, b
                break
        # dampers DEMOTE one tier each (they no longer halve size)
        demotions = 0
        vol_hot = (m.vix > PARAMS["VIX_HOT"] or m.spy_5d_realvol_wow > PARAMS["SPY_RV_WOW_HOT"]
                   or abs(m.spx_day) > PARAMS["SPX_DAY_HOT"])
        if m.macro_overlap: demotions += 1
        if vol_hot: demotions += 1
        if m.g2_estimated: demotions += 1
        if demotions:
            idx = next(i for i, (_, n, _) in enumerate(TIERS) if n == conv)
            idx = min(idx + demotions, len(TIERS) - 1)
            conv, budget = TIERS[idx][1], TIERS[idx][2]
            caveats.append(f"{demotions} damper(s) -> demoted to {conv}")
        # The ladder is LOGGED; it only SIZES once it has earned it (see SIZE_BY_CONVICTION).
        if not SIZE_BY_CONVICTION:
            # CONVICTION and CONFIDENCE are different quantities and must be treated
            # differently — conflating them was a real bug caught by the self-test:
            #   * CONVICTION = |edge_score| = "how strong is my read". The backtest showed
            #     it rank-orders INVERSELY, so it must NOT scale size.
            #   * CONFIDENCE = information completeness = "how much do I actually know".
            #     Sizing down on thin information is risk hygiene, not a bet on a signal.
            # Flat-sizing on the ladder alone silently destroyed the layer's central promise
            # (uncertainty shrinks the bet): a 2-of-5-inputs read got the same size as a
            # 5-of-5 read. Confidence is therefore applied to size DIRECTLY here.
            budget = FLAT_RISK_BUDGET * confidence          # 0.275% .. 0.50%
            caveats.append(f"conviction {conv} LOGGED but NOT sizing (tiers rank-ordered "
                           f"INVERSELY, n=8); size = flat {FLAT_RISK_BUDGET*100:.2f}% x "
                           f"confidence {confidence:.2f} = {budget*100:.3f}%")

    # ---- SIZING (v1.4.0) — size off the BAD-CASE gap, not the mean --------------------
    # THE DEFECT THIS FIXES. Sizing divided by `avg_abs_open`, the MEAN of the name's recent
    # gaps. That makes the stated "risk budget" the loss under a TYPICAL print — so any
    # worse-than-typical print breaches it, and the breach scales with the surprise.
    # Measured over the 17 scored events, |realized| / avg_gap exceeded 1.0x on 3 and reached
    # 2.02x. Live case: KLAC has a 3.03% mean gap, so a "0.5% risk" trade bought $2,479 of it
    # (13.8% of an $18k book); it moved 8% and lost ~2.6x its budget.
    #
    # Worse, the mean also MIS-RANKS names: it sizes UP the quiet ones (where a surprise is
    # proportionally most damaging) and DOWN the volatile ones. KLAC's gap history is bimodal
    # — [8.6, 7.1, 2.8, 2.6, 2.2, 2.0] — so both mean AND p80 (3.62) sit in the quiet mode and
    # miss the loud one completely. Only the bad case sees it.
    #
    # A budget must hold in a BAD case; that is what makes it a budget. The denominator is now
    # the empirical bad case (max/high-percentile of the same history the mean came from).
    # Positions shrink ~1.2-2.4x. That is not a loss of risk appetite — appetite belongs in
    # FLAT_RISK_BUDGET, an explicit dial. The mean was not appetite, it was an understated
    # budget that broke silently.
    shares = 0
    gar = 0.0
    notional = 0.0
    sizing_gap = m.gap_bad_case if (m.gap_bad_case and m.gap_bad_case > 0) else m.avg_abs_open
    sizing_basis = "BAD_CASE" if (m.gap_bad_case and m.gap_bad_case > 0) else "MEAN_FALLBACK"
    if sizing_basis == "MEAN_FALLBACK" and m.avg_abs_open:
        caveats.append("sizing off the MEAN gap (no gap_bad_case supplied) — the budget only "
                       "holds on a typical print; supply gap_bad_case to make it a real budget")
    if budget > 0 and sizing_gap and sizing_gap > 0:
        risk_per_share = (sizing_gap / 100.0) * m.price
        shares = int((budget * m.capital) / risk_per_share)
        gar = shares * risk_per_share
        notional = shares * m.price
        # Concentration is REPORTED, never capped (owner directive: no caps).
        if m.capital and notional > 0.10 * m.capital:
            caveats.append(f"NOTIONAL {notional:,.0f} = {notional/m.capital*100:.0f}% of book "
                           f"on a {budget*100:.2f}% risk budget — gap-normalised sizing takes "
                           f"large positions in quiet names; reported, not capped")

    return EdgeVerdict(ticker, stance, conv, round(score, 4), round(raw, 4),
                       round(expectations, 3), round(value, 3), round(positioning, 3),
                       round(completeness, 3), round(confidence, 3), sec, budget,
                       shares, round(gar, 0), round(notional, 0), sizing_basis,
                       m.capital, irm, reasons, caveats,
                       fund_leg_sum=round(_fund_leg_sum, 3), fund_norm=float(fund_norm),
                       verified_legs=_verified_legs)


# ------------------------------------------------------------------- ranking
_ORDER = {"BUY": 0, "SHORT": 1, "NO_TRADE": 2}


def rank(results):
    """Live bets first, then by |edge| descending — the strongest read at the top."""
    return sorted(results, key=lambda v: (_ORDER.get(v.stance, 9), -abs(v.edge_score)))


# ------------------------------------------------------- ledger registration
def register(ticker, j, m, t=None, cfg=None, event_date=None,
             entry_close_date=None, exit_open_date=None, sector_etf=None,
             note="", ledger_path=None, skew=None, sector=None,
             portfolio_aware=False, context_sources=None, allow_paused=False):
    """Freeze the EDGE-SCORE decision into the ledger with its entry/exit dates.

    Writes `action` / `conviction` in the vocabulary `pre_ledger.stats()` reads, so
    tier calibration accrues even though conviction is NOT sizing yet — that is exactly
    the evidence needed to decide whether SIZE_BY_CONVICTION can ever flip to True.

    Also evaluates `pre_calcrisk.calc_risk` and stores it under `shadow_calcrisk`, so the
    demoted scorer's counterfactual keeps accruing at zero cost.

    BLINDNESS DECLARATION (added 2026-08-09, after three external reviews)
    ---------------------------------------------------------------------
    `portfolio_aware` / `context_sources` record what this forecast could see, and they go
    INSIDE the frozen payload, so they are covered by `integrity_hash` and cannot be edited
    after an outcome is known.

    WHY A DECLARATION AND NOT A GUARD. The restructure plan proposed asserting that
    "pre-print scoring is byte-identical with and without the portfolio context file
    present." That tests FILE ABSENCE. The contamination channel is the CONVERSATION: a chat
    that ran a postmortem and absorbed portfolio state still holds it a week later when the
    next forecast is frozen. No filesystem check can see that, so the real control is the
    chat boundary enforced by the /pre-register and /pre-post skills.

    This field is the AUDIT half, and it is deliberately the same shape as the rest of PRE's
    discipline: `_is_retro()` never prevented the AMKR retro-registration either — it made it
    DETECTABLE afterward. A declaration can be wrong; it cannot be quietly changed later.

    `portfolio_aware=True` marks the row PORTFOLIO_AWARE. Such a row is a counterfactual,
    never evidence, and must be excluded from the capital record.
    """
    from pre_ledger import (_append, _hash, _now, _dc, DEFAULT_LEDGER, SCHEMA,
                            trade_paused)

    # TRADE PAUSE — enforced HERE as well as in pre_ledger.pre_register.
    #
    # WHY IT IS DUPLICATED, AND WHY THAT IS NOT REDUNDANT: this function does NOT call
    # pre_register(). It appends to the ledger directly, and it is the path pre_batch.py
    # actually uses. A guard installed only on pre_register() would therefore have covered
    # the route nobody runs and left the production route open — a control that exists and
    # does not cover the live path. That is the same defect class as the void status living
    # in prose while every statistic ignored it, so it is stated rather than quietly patched.
    paused = trade_paused()
    if paused and not allow_paused:
        nl = chr(10)
        raise RuntimeError(
            f"TRADE REGISTRATION IS PAUSED since {paused['since']}.{nl}"
            f"  REASON: {paused['reason']}{nl}"
            f"  SCOPE:  {paused['scope']}{nl}"
            f"  RESUME CONDITIONS:{nl}    "
            + (nl + "    ").join(paused["resume_conditions"])
            + nl + "  The FORECAST layer is unaffected — run the batch WITHOUT "
                   "--register and every name still gets a graded call.")
    from pre_engine import __version__ as ENGINE_VERSION
    from pre_expectations import expectations_bar as _bar
    ledger_path = ledger_path or DEFAULT_LEDGER
    cfg = cfg or EngineConfig(fasttrack=True, watch=False, react_in_ds=False)

    v = edge_score(ticker, j, m, t, cfg, skew=skew, sector=sector)
    r = evaluate(j, m, t=t, cfg=cfg, skew=skew)

    shadow = None
    try:
        from pre_calcrisk import calc_risk, __layer_version__ as CR_VERSION
        c = calc_risk(ticker, j, m, t, cfg, skew=skew)
        shadow = {"layer_version": CR_VERSION, "action": c.stance,
                  "conviction": c.conviction, "asymmetry": c.asymmetry,
                  "shares": c.shares, "agrees": c.stance == v.stance}
    except Exception as e:                       # a shadow must never block a live decision
        shadow = {"error": repr(e)[:200]}

    verdict = {
        "action": v.stance, "layer": "edge-score", "layer_version": __version__,
        "conviction": v.conviction,
        "sized_by": "CONVICTION" if SIZE_BY_CONVICTION else "FLAT",
        # §9.2 rename: `expectations_momentum` is canonical. `directional` is written as a
        # LEGACY MIRROR so the 40 rows already in the ledger and every reader that keys on
        # the old name keep resolving. Same number, two keys — never allow them to diverge.
        "edge": {"score": v.edge_score, "raw": v.raw_edge,
                 "expectations_momentum": v.expectations_momentum,
                 "directional": v.expectations_momentum,
                 "value": v.value, "positioning": v.positioning,
                 "completeness": v.completeness, "confidence": v.confidence,
                 "irm": v.irm, "sector": v.sector,
                 # v1.5.7b: the normalisation audit trail, so a tier written under
                 # today's norm can be re-derived under tomorrow's.
                 "fund_leg_sum": v.fund_leg_sum, "fund_norm": v.fund_norm,
                 "verified_legs": v.verified_legs},
        "risk_budget": v.risk_budget, "shares": v.shares, "gap_at_risk": v.gap_at_risk,
        "capital": v.capital, "reasons": v.reasons, "caveats": v.caveats,
        "components": r.components, "verified": r.verified,
        "sign_action": r.action, "ds": r.ds,
        # DIAGNOSTIC — logged on every decision, feeds nothing. See pre_expectations.py.
        "expectations_bar": _bar(j, m, r.components),
        "skew": r.skew, "skew_components": r.skew_components, "skew_status": r.skew_status,
        "shadow_calcrisk": shadow,
        "exit": {"entry_close_date": entry_close_date, "exit_open_date": exit_open_date,
                 "sector_etf": sector_etf},
    }
    frozen = {"schema": SCHEMA, "engine_version": ENGINE_VERSION, "ticker": ticker,
              "event_date": event_date or (_now()[:10]),
              "inputs": {"judgment": _dc(j), "market": _dc(m), "truth": _dc(t),
                         "skew": _dc(skew), "cfg": _dc(cfg)},
              "verdict": verdict,
              # Inside the hash on purpose - see the blindness note in the docstring.
              "context": {"portfolio_aware": bool(portfolio_aware),
                          "sources": sorted(context_sources or []),
                          "status": "PORTFOLIO_AWARE" if portfolio_aware else "BLIND"}}
    ih = _hash(frozen)
    entry_id = f"{ticker}:{frozen['event_date']}:{ih[7:15]}"
    record = {"type": "entry", "id": entry_id, "logged_at": _now(), "note": note,
              **frozen, "integrity_hash": ih}
    _append(ledger_path, record)
    return record, v


def render(v: EdgeVerdict) -> str:
    L = [f"{v.ticker:5s} {v.stance:8s} {v.conviction:11s} edge={v.edge_score:+.3f}  "
         f"[exp {v.expectations_momentum:+.2f} val {v.value:+.2f} pos {v.positioning:+.2f}] "
         f"conf={v.confidence:.2f} ({v.sector})"]
    if v.shares:
        L.append(f"      size {v.risk_budget*100:.2f}% = {v.shares} sh  "
                 f"notional ${v.notional:,.0f} ({v.notional/v.capital*100:.1f}% of book)  "
                 f"gap-at-risk ${v.gap_at_risk:,.0f}  [{v.sizing_basis}]")
    for r in v.reasons:
        L.append(f"      + {r}")
    for c in v.caveats:
        L.append(f"      ! {c}")
    return "\n".join(L)
