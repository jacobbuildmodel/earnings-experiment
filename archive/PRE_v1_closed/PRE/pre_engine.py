"""
PRE — Pre-earnings directional-sign classifier (sealed core + governed upgrades)
================================================================================
Version : 1.5.5
Status  : built from MODEL_DISCLOSURE.md v1.2.2 (§14 is the source of truth for the
          sealed core). This file did NOT previously exist in this workspace; it is a
          faithful reconstruction of the sealed core plus the tiered upgrades from
          PRE_UPGRADE_PLAN.md. If a canonical v1.2.2 exists elsewhere, DIFF against it
          before trusting any "byte-identical replay" claim.

ARCHITECTURE (unchanged from §0)
  - The engine NEVER fetches and NEVER guesses. It buckets, sums, gates, sizes, logs.
  - All judgment RAW values are supplied by the caller (the LLM/reasoning layer).
  - A missing input scores 0 and is flagged UNAVAILABLE. Gates fail closed.

GOVERNANCE TIERS IMPLEMENTED HERE
  PLUMBING  (always on) ....... C1 sanity bounds, C2 NO-TRADE subtypes,
                                C3 sensitivity score, C11 append-only record.
  FAST-TRACK LOGIC (cfg.fasttrack, default ON — owner build sign-off, holdout-waived,
                    every one is monotonically CONSERVATIVE: can only turn a trade
                    into a non-trade, never the reverse)
                                C4 cross-source reconciliation gate,
                                C5 CONFIDENCE field -> worst-case band,
                                C6 REV/SAT swung in the worst-case band,
                                C9 both-dampers -> NO TRADE,
                                C12 VEL forward-sourcing rule (order-driven names must
                                    source VEL from bookings/backlog, else UNAVAILABLE).
  CANONICAL LOGIC (cfg.watch, default OFF — REQUIRES 2 non-anomaly holdouts + sign-off
                   that DO NOT YET EXIST; shadow-only until then)
                                C7 SAT(b) parabolic-pullback fix (parameter-free),
                                C8 ALIGN>=3 trade filter + retire HIGH 1.5x multiplier.

  STRUCTURAL (NOT in this file — see docs/skew_overlay_design.md): EV/skew overlay,
  options expressions, learned weights, per-KPI VEL. Escalate for owner approval.

  STRUCTURAL — STAGE 1 ONLY (owner-approved): the EV/skew overlay's DIAGNOSTIC layer.
                                SKEW is computed from separate caller-supplied inputs and
                                LOGGED on every decision. It NEVER enters DS, the cascade,
                                or sizing. Stage 2 (veto) and Stage 3 (calculated-risk
                                upgrade) are NOT implemented and require their own n-bar +
                                a separate owner sign-off. Do not add gating here.

CHANGELOG
  v1.5.6  C13 REV-FEED INTEGRITY (C1 family, PLUMBING, fail-closed, 0 new params). The four
          revision counts were the ONLY decision-carrying inputs with no validation of any
          kind, and after v1.5.5 they are the sole surviving fundamental term. Two definitional
          rules: the 7d window cannot exceed the 30d window it sits inside; and |R| cannot
          reach 1.0 for a metric defined as a net fraction of the covering panel. Both were
          violated by the live feed on 2026-07-29 (MSFT up7=10 > up30=8; FTNT 38/0 vs 37
          analysts -> R=+1.03 -> a MAXIMUM bullish REV=+2 off a period-roll artifact).
          Refuses the name rather than nulling the leg — see rev_feed_integrity() for why
          nulling is NOT the conservative choice at the edge-score layer. Breaks 0 of 93
          existing ledger rows.
  v1.5.5  "REVISIONS" removed from FORWARD_VEL_BASES — analyst estimate-revisions measure the
          EXPECTATIONS BAR, not the company's forward trajectory. See the note at that constant.
  v1.5.4  IMPLIED-MOVE PROVENANCE (review #2 item 4). `implied_move` was the least-verified
          input in the system while carrying decision weight: no function, no C1 bound, no
          reconciliation, no record of what a stored number WAS. Now:
          * Market gains implied_move_raw / _basis / _expiry / _extra_days.
          * C1 bounds it and REJECTS a DECONTAMINATED value stored without its raw, or one
            that exceeds its raw — such a row is unauditable.
          * The decontamination is a real function at last (pre_impliedmove.decontaminate);
            it previously existed only as a PROSE COMMENT in one dated run script.
          * It now FAILS CLOSED when the correction would remove >50% of the straddle's
            variance: an estimate whose correction exceeds its result is not a measurement.
            Re-deriving the stored values, that rule REFUSES NVTS (88% removed), GLW (89%)
            and SPGI (56%) — the "cheap vol" on NVTS (IRM 0.47) and GLW (0.68) was an
            artifact of the adjustment, not a reading of the market. Both were HIGH-tier
            BUYs and both lost.
  v1.5.3  Tier-1 fixes from the INDEPENDENT ADVERSARIAL REVIEW (owner-approved 2026-07-29):
          * LEDGER: market-model abnormal return. Beta was HARD-ASSUMED = 1; it is now
            estimated on a clean pre-event window (see pre_postmortem.estimate_beta) and
            AR = R - beta*R_mkt. Beta=1 remains the fallback but the row is FLAGGED so the
            two methods are never silently mixed. Material: AMKR's beta is 1.344, CLS's
            1.111 — re-scoring flipped CLS from a marginal loss to a marginal win.
          * calc-risk v1.3.0 REMOVED the guide-freshness gate (failed the Abstraction Test)
            and RAISED the short hurdle. See pre_calcrisk.py changelog.
          * docs/POSTMORTEM_SOP.md is now BINDING on every closed trade.
  v1.5.2  Judgment freshness provenance fields (up_revisions_7d / guidance_fresh).
  v1.5.1  Ledger hold-to-close SHADOW (both exit horizons accrue; live exit unchanged).
  v1.5.0  Post-mortem remediation batch (owner sign-off 2026-07-23):
          * C12 FAST-TRACK LOGIC (conservative): VEL forward-sourcing. `vel_basis` must be
            declared; on `order_driven` names a TRAILING_REVENUE basis is NOT a valid VEL
            source (it inverts on ramping names) -> VEL becomes UNAVAILABLE (scores 0, widens
            the worst-case band). Can only turn a trade into a non-trade.
          * PLUMBING: input provenance fields (`vel_basis`, `gg_basis`, `rev_basis`,
            `order_driven`) + `Result.verified` set, so downstream layers can ask
            "was this leg VERIFIED?" instead of reading a defaulted 0 as "stable".
          * STRUCTURAL Stage-1 (diagnostic-only, owner-approved): POSITIONING/FLOW inputs
            (short interest %float, days-to-cover, put/call OI) folded into the SKEW POS
            sub-score. Still LOGGED ONLY — never gates, never sizes.
          * Market.capital default 500_000 -> 18_000 (the real book; the old default silently
            oversized every example by ~28x).
  v1.4.0  STRUCTURAL Stage-1 skew DIAGNOSTIC logging (owner-approved): score_skew() +
          Skew inputs; SKEW/RICH/POS/PAYOFF logged, verdict-neutral. No gating.
  v1.3.0  built sealed core from §14; added PLUMBING (C1/C2/C3/C11), FAST-TRACK
          conservative LOGIC (C4/C5/C6/C9) active, CANONICAL LOGIC (C7/C8) shadow-gated.
  v1.2.2  (spec reference) sealed core as disclosed.

The sealed core (all arithmetic, gate logic, the cascade, sizing, fail-closed
behaviour, INCOMPLETE/worst-case logic, CBR long-block, falling-knife guard) is
INVIOLABLE. No upgrade in this file weakens a protection; C7/C4/C5/C6/C9 only tighten.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from typing import Optional

__version__ = "1.5.6"   # 1.5.6 C13 REV-feed integrity (see rev_feed_integrity)

# C12 — bases that legitimately measure FORWARD trajectory. A VEL sourced from anything
# else on an order-driven business is a trailing proxy and is NOT accepted (this is the
# rule the AEHR post-mortem demanded; it is the price of the FUND_UNDEFINED gate in the
# calc-risk layer, which would otherwise have blocked that winner).
# v1.5.5 — "REVISIONS" REMOVED from this list. Every remaining basis is something the
# COMPANY reported about its own forward book. Analyst estimate-revisions are not: they
# measure what ANALYSTS EXPECT, i.e. the height of the bar, not the trajectory of the
# business. Scoring a rising bar as a bullish trajectory signal is a category error of the
# same family as `value` (variance read as direction).
# Exposed by VRT 2026-07-29: VEL=+1 was sourced from consensus revenue growth accelerating
# 28% -> 39%. That IS the bar being raised. VRT then MISSED revenue ($3.27B vs $3.38B) and
# gapped -6.93% idio. The model had read the raised bar as a reason to be more long.
# NOTE this is a MECHANISM cut, not a patch justified by that loss: the Abstraction Test
# governs fixes invented in response to a failure; the mechanism standard governs whether a
# component belongs at all. It also breaks NO winning trade (checked: zero winners relied on
# a REVISIONS-sourced non-zero VEL).
FORWARD_VEL_BASES = ("BOOKINGS", "BACKLOG", "ORDERS", "GUIDANCE", "DESIGN_WINS")
ORDER_DRIVEN_HINT = ("semi-cap equipment, defense primes/subs, project & EPC, capital goods, "
                     "anything where revenue recognizes quarters after the order lands")


# ============================================================================
# PARAMETER REGISTRY  (ceiling = 30; the disclosure states 23 currently in use)
# ----------------------------------------------------------------------------
# Every tunable threshold lives here so the ceiling is machine-checkable and any
# new parameter must be added explicitly (and must name an ablation in the plan).
# NOTE: this is the CODE-AUTHORITATIVE count. Reconcile with the disclosure's "23";
# they may enumerate differently. C7 adds 0 (reuses SAT_SATURATION + VEL). C8 adds
# ALIGN_MIN (+1) and retires HIGH_UNITS (-1) => net 0.
# ============================================================================
PARAMS = {
    # REV buckets (4)
    "REV_STRONG": 0.30, "REV_MILD": 0.10, "REV_MILD_NEG": -0.10, "REV_STRONG_NEG": -0.30,
    # SAT (4)
    "SAT_SATURATION": 20.0, "SAT_VACUUM": -10.0, "SAT_52W_NEAR": 5.0, "SAT_52W_FAR": 25.0,
    # VEL (2)
    "VEL_UP_BPS": 400.0, "VEL_DN_BPS": -400.0,
    # execution band + conviction (3)  (MEDIUM lower bound == T_BUY, shared)
    "T_BUY": 3, "T_SHORT": -3, "HIGH_CUT": 5,
    # gates (5)
    "G1_DOLLAR_VOL_MIN": 25_000_000.0, "G1_ADV_FRAC_MAX": 0.01,
    "G2_GAP_MIN": 2.0, "G2_MIN_QTRS": 4, "G4_FEE_MAX": 5.0,
    # dampers (4)
    "VIX_HOT": 28.0, "SPY_RV_WOW_HOT": 50.0, "SPX_DAY_HOT": 1.5, "DAMPER_MULT": 0.5,
    # sizing (2)
    "RISK_BUDGET": 0.005, "HIGH_UNITS": 1.5,
    # C8 canonical (WATCH): +1 (offsets HIGH_UNITS retirement -> net 0 when active)
    "ALIGN_MIN": 3,
}
PARAM_CEILING = 30

# ----------------------------------------------------------------------------
# SKEW DIAGNOSTIC THRESHOLDS (Stage-1 overlay) — DELIBERATELY OUTSIDE the scoring
# budget above. These never move a verdict (SKEW is logged, never gated), so they do
# NOT count against PARAM_CEILING. All are UNVALIDATED PRIORS to calibrate at n>=20;
# they are not discoveries. If Stage 2/3 is ever approved, these migrate INTO PARAMS
# and must then respect the ceiling + ablation rule.
# ----------------------------------------------------------------------------
SKEW_PARAMS = {
    "RICH_HI": 1.30, "RICH_LO": 0.75,      # vol_ratio bands
    "SKEW_HIGH": 3.0, "SKEW_LOW": -1.0,    # 25-delta skew (vol points)
    "PT_HI": 15.0, "PT_LO": 0.0,           # consensus price-target upside %
    "PAYOFF_RATIO": 1.8,                   # up/down gap asymmetry
    "PAYOFF_MIN_N": 3,                     # min beats AND misses for a PAYOFF read
    # positioning / flow (v1.5.0) — crowding bands
    "SI_HIGH": 10.0, "SI_LOW": 3.0,        # short interest, % of float
    "DTC_HIGH": 5.0,                       # days-to-cover
    "PCR_HIGH": 1.20, "PCR_LOW": 0.60,     # front-expiry put/call open interest
}


def _param_count() -> int:
    # HIGH_UNITS is retired when C8 (watch) is active; ALIGN_MIN only "counts" then.
    # For the ceiling check we count the full registry (worst case) = conservative.
    return len(PARAMS)


assert _param_count() <= PARAM_CEILING, (
    f"parameter ceiling breached: {_param_count()} > {PARAM_CEILING}"
)


# ============================================================================
# CONFIG
# ============================================================================
@dataclass
class EngineConfig:
    fasttrack: bool = True   # C4/C5/C6/C9 — conservative, owner-signed-off, holdout-waived
    watch: bool = False      # C7/C8 — canonical LOGIC, shadow-only until 2 holdouts + sign-off
    react_in_ds: bool = True # C10 (owner directive): if False, REACT leaves the DS sum and is
                             #   surfaced as a CONFIRMATION signal only (agrees/contradicts sign(DS)).
                             #   Default True preserves the sealed core; runner sets False per Jacob.
    # C4 reconciliation tolerances (validation layer; OUTSIDE the scoring param budget)
    tol_ped_pp: float = 5.0
    tol_52w_pp: float = 3.0
    # C12 (v1.5.0): when True, a judgment leg with NO declared basis is treated as
    # UNVERIFIED (not merely undeclared). Default False so existing callers are unchanged;
    # the order-driven TRAILING_REVENUE block below is enforced regardless of this flag.
    strict_sourcing: bool = False


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


# ============================================================================
# INPUTS
# ============================================================================
@dataclass
class Judgment:
    """LLM-supplied RAW judgment values. CONFIDENCE (C5) is per-input."""
    # REV raw
    up_revisions_30d: Optional[int] = None
    down_revisions_30d: Optional[int] = None
    covering_analysts: Optional[int] = None
    # pre-bucketed {-1,0,+1} (None => UNAVAILABLE)
    GG: Optional[int] = None
    VEL: Optional[int] = None
    REACT: Optional[int] = None
    FLAG: int = 0                      # already clamped [-2,0] by caller per §14
    CBR: str = "CLEAN"                 # {"CLEAN","MANUFACTURED"}
    G0: Optional[str] = "CONFIRMED"    # {"CONFIRMED","DRY_RUN","UNRESOLVED",None}
    # SAT inputs
    stock_pct_since_last_earnings: Optional[float] = None
    sector_etf_pct_same_window: Optional[float] = None
    pct_within_52w_high: Optional[float] = None
    pct_below_52w_high: Optional[float] = None
    # C5 CONFIDENCE: map input-name -> {"HIGH","MED","LOW","UNAVAILABLE"}
    confidence: dict = field(default_factory=dict)
    # --- PROVENANCE (v1.5.0, PLUMBING) --------------------------------------
    # WHERE each judgment leg came from. None = "not declared" and is treated as
    # unsourced by C12. These never enter the arithmetic; they decide whether a leg
    # counts as VERIFIED, which is what the downstream FUND gate reads.
    order_driven: bool = False          # True for backlog/bookings businesses (see ORDER_DRIVEN_HINT)
    vel_basis: Optional[str] = None     # e.g. "BOOKINGS" | "BACKLOG" | "TRAILING_REVENUE" | "GUIDANCE"
    gg_basis: Optional[str] = None
    rev_basis: Optional[str] = None
    # --- FRESHNESS (v1.5.2, PLUMBING; read by the calc-risk guide-freshness gate) --------
    # The washout-BUY's fatal flaw (AMKR 2026-07-28): positive FUND legs were scored from
    # STALE trailing data (a guidance raise 3 months old, 30-day revisions), but the print
    # itself delivered a DOWN guide. These fields let the caller declare whether the positive
    # fundamentals are THIS-print-fresh. They never touch the arithmetic.
    up_revisions_7d: Optional[int] = None    # analyst up-revisions in the last 7 days
    down_revisions_7d: Optional[int] = None
    guidance_fresh: Optional[bool] = None    # a THIS-cycle positive catalyst (pre-announce,
                                             # same-week reiteration/raise). None = not asserted.


@dataclass
class Market:
    price: float
    avg_abs_open: float                # % avg absolute earnings-day open gap
    confirmed_quarters: int
    dollar_vol_20d: float
    share_vol_20d: float
    # --- SIZING DENOMINATOR (v1.5.5) ---------------------------------------
    # `avg_abs_open` is the MEAN of this name's recent earnings gaps. Sizing off the mean
    # makes "risk budget" mean "what I lose on a TYPICAL print", which is not what a budget
    # is. `gap_bad_case` is the empirical BAD case (max / high percentile of the same
    # history). See the sizing note in pre_edgescore.py. Optional: falls back to the mean,
    # flagged, so old callers keep working.
    gap_bad_case: Optional[float] = None
    implied_move: Optional[float] = None
    # --- IMPLIED-MOVE PROVENANCE (v1.5.4). `implied_move` used to be a bare hand-entered
    # float with no record of what it was. Two contradictions reached the ledger because of
    # it (ASML 6.30 vs 8.36 on one event; NVTS 5.70 stored against a 16.70 transactable
    # straddle). A stored number must now say what it IS. See pre_impliedmove.py.
    implied_move_raw: Optional[float] = None       # the TRANSACTABLE straddle (what you pay)
    implied_move_basis: Optional[str] = None       # "RAW" | "DECONTAMINATED"
    implied_move_expiry: Optional[str] = None      # which expiry it came from
    implied_move_extra_days: Optional[int] = None  # trading days from event to that expiry
    capital: float = 18_000.0          # REAL book (3 accounts, ~10K/5K/3K). Was 500_000 —
                                       # that default silently oversized every worked example.
    vix: float = 15.0
    spy_5d_realvol_wow: float = 0.0
    spx_day: float = 0.0
    macro_overlap: bool = False        # G3
    borrow_locate: bool = True         # G4
    borrow_fee: float = 0.0            # annualized %
    g2_estimated: bool = False         # True if <4 confirmed quarters (ESTIMATED)


@dataclass
class Truth:
    """C4: values from a PRE-REGISTERED market-data source, supplied by the caller.
    The engine does NOT fetch these — it only compares. None => no reconciliation."""
    stock_pct_since_last_earnings: Optional[float] = None
    pct_within_52w_high: Optional[float] = None
    pct_below_52w_high: Optional[float] = None
    price: Optional[float] = None


@dataclass
class Skew:
    """Stage-1 diagnostic inputs (STRUCTURAL overlay). Caller-supplied; engine never
    fetches. Every field optional — a missing field makes its sub-score UNAVAILABLE
    (contributes 0, flagged) rather than fabricating one. SKEW is LOGGED, never gated."""
    realized_vol_3m: Optional[float] = None      # annualized %
    days_to_event: Optional[int] = None
    skew_25d: Optional[float] = None             # 25Δ put vol − call vol, vol points
    consensus_pt_upside: Optional[float] = None  # % upside to avg price target
    median_up_gap: Optional[float] = None        # % median open on historical beats
    median_down_gap: Optional[float] = None      # % median open on historical misses
    n_beats: int = 0
    n_misses: int = 0
    # --- POSITIONING / FLOW (v1.5.0) — the #1 missing data stream per the post-mortem.
    # Decision-relevant in AEHR / NFLX / GOOG but measured NOWHERE before this. Still
    # DIAGNOSTIC ONLY: it feeds the POS sub-score, which is logged and never gates.
    short_interest_pct_float: Optional[float] = None   # % of float sold short
    days_to_cover: Optional[float] = None             # short interest / ADV
    put_call_oi_ratio: Optional[float] = None         # front-expiry open-interest ratio


# ============================================================================
# COMPONENT SCORING (§14.A) — sealed core
# ============================================================================
def score_rev(up, down, cov):
    if cov is None or cov <= 0 or up is None or down is None:
        return 0, "UNAVAILABLE"
    R = (up - down) / cov
    if R >= PARAMS["REV_STRONG"]:      return 2, "OK"
    if R >= PARAMS["REV_MILD"]:        return 1, "OK"
    if R > PARAMS["REV_MILD_NEG"]:     return 0, "OK"
    if R > PARAMS["REV_STRONG_NEG"]:   return -1, "OK"
    return -2, "OK"


def score_sat(j: Judgment, rev: int, vel: int, cfg: EngineConfig):
    """SAT = clamp(a + b). a=saturation/vacuum (REV-gated). b=52wk (falling-knife guard).
    C7 (watch): the SAT(b) 'cheap +1' is disabled when the name is in saturation
    territory (excess_PED >= SAT_SATURATION, reusing the existing cutoff -> 0 new params)
    OR when VEL < 0 (deteriorating). Parameter-free. CONSERVATIVE (only removes a +1)."""
    a_avail = (j.stock_pct_since_last_earnings is not None
               and j.sector_etf_pct_same_window is not None)
    excess = None
    a = 0
    if a_avail:
        excess = j.stock_pct_since_last_earnings - j.sector_etf_pct_same_window
        if excess >= PARAMS["SAT_SATURATION"]:
            a = -1 if rev < 0 else 0          # saturation needs REV<0
        elif excess <= PARAMS["SAT_VACUUM"]:
            a = +1 if rev > 0 else 0          # vacuum needs REV>0
    b = 0
    if j.pct_within_52w_high is not None and j.pct_within_52w_high <= PARAMS["SAT_52W_NEAR"]:
        b = -1
    elif j.pct_below_52w_high is not None and j.pct_below_52w_high > PARAMS["SAT_52W_FAR"]:
        # falling-knife guard: +1 only if REV >= 0
        b = +1 if rev >= 0 else 0
        if cfg.watch and b == +1:
            # C7 parabolic fix: kill the +1 if extended (excess>=+20) or VEL deteriorating
            if (excess is not None and excess >= PARAMS["SAT_SATURATION"]) or vel < 0:
                b = 0
    sat_unavail = not (a_avail or j.pct_within_52w_high is not None
                       or j.pct_below_52w_high is not None)
    return int(_clamp(a + b, -2, 2)), sat_unavail, excess


def score_skew(skew: Optional[Skew], m: Market):
    """STAGE-1 DIAGNOSTIC. Returns (SKEW total | None, sub-scores dict, status list).
    RICH = implied-vs-realized richness; POS = positioning; PAYOFF = gap asymmetry.
    This output is LOGGED ONLY. It is never summed into DS, never consulted by the
    cascade, and never changes sizing. Do NOT wire it into a verdict at this version."""
    if skew is None:
        return None, {}, ["NO_SKEW_DATA"]
    P = SKEW_PARAMS
    comps, status = {}, []

    # RICH — vol_ratio = implied_move / max(realized·√(days/252), avg_abs_open)
    if (skew.realized_vol_3m is not None and skew.days_to_event
            and m.implied_move is not None):
        horizon = skew.realized_vol_3m * math.sqrt(skew.days_to_event / 252.0)
        denom = max(horizon, m.avg_abs_open)
        if denom > 0:
            vr = m.implied_move / denom
            comps["RICH"] = -1 if vr >= P["RICH_HI"] else (+1 if vr <= P["RICH_LO"] else 0)
        else:
            comps["RICH"] = 0; status.append("RICH:UNAVAILABLE")
    else:
        comps["RICH"] = 0; status.append("RICH:UNAVAILABLE")

    # POS — positioning = options-implied leg + (v1.5.0) short-interest / flow leg.
    # Sign convention: -1 = crowded long / high expectations (vulnerable to sell-the-news),
    # +1 = downside already pre-sold (squeeze fuel). Both legs are independently optional.
    pos_opt = 0
    if skew.skew_25d is not None and skew.consensus_pt_upside is not None:
        if skew.skew_25d > P["SKEW_HIGH"] and skew.consensus_pt_upside > P["PT_HI"]:
            pos_opt = -1
        elif skew.skew_25d < P["SKEW_LOW"] and skew.consensus_pt_upside < P["PT_LO"]:
            pos_opt = +1
    else:
        status.append("POS:UNAVAILABLE")

    pos_flow, flow_seen = 0, False
    if skew.short_interest_pct_float is not None:
        flow_seen = True
        if (skew.short_interest_pct_float >= P["SI_HIGH"]
                or (skew.days_to_cover is not None and skew.days_to_cover >= P["DTC_HIGH"])):
            pos_flow += 1                      # heavily shorted -> downside pre-sold
        elif skew.short_interest_pct_float <= P["SI_LOW"]:
            pos_flow -= 1                      # nobody short -> no cushion, crowded long
    if skew.put_call_oi_ratio is not None:
        flow_seen = True
        if skew.put_call_oi_ratio >= P["PCR_HIGH"]:
            pos_flow += 1                      # puts already owned -> hedged/pessimistic
        elif skew.put_call_oi_ratio <= P["PCR_LOW"]:
            pos_flow -= 1                      # call-heavy -> crowded long
    if not flow_seen:
        status.append("POS_FLOW:UNAVAILABLE")

    comps["POS"] = int(_clamp(pos_opt + int(_clamp(pos_flow, -1, 1)), -1, 1))

    # PAYOFF — asymmetry (needs >=3 beats AND >=3 misses of magnitude history)
    if (skew.median_up_gap and skew.median_down_gap
            and skew.n_beats >= P["PAYOFF_MIN_N"] and skew.n_misses >= P["PAYOFF_MIN_N"]):
        up, dn = skew.median_up_gap, skew.median_down_gap
        if dn > 0 and up / dn >= P["PAYOFF_RATIO"]:
            comps["PAYOFF"] = +1
        elif up > 0 and dn / up >= P["PAYOFF_RATIO"]:
            comps["PAYOFF"] = -1
        else:
            comps["PAYOFF"] = 0
    else:
        comps["PAYOFF"] = 0; status.append("PAYOFF:UNAVAILABLE")

    total = int(_clamp(sum(comps.values()), -2, 2))
    return total, comps, status


# ============================================================================
# ENGINE
# ============================================================================
@dataclass
class Result:
    action: str
    ds: int
    ds_floor: int
    ds_ceil: int
    conviction: str
    components: dict
    unavailable: list
    reasons: list
    shares: int = 0
    gap_at_risk: float = 0.0
    final_units: float = 0.0
    sensitivity: float = 0.0       # C3
    warnings: list = field(default_factory=list)
    no_trade_subtype: Optional[str] = None  # C2
    # Stage-1 skew DIAGNOSTIC (logged only; never affects action/ds/sizing)
    skew: Optional[int] = None
    skew_components: dict = field(default_factory=dict)
    skew_status: list = field(default_factory=list)
    # C10 REACT-as-confirmation (when react_in_ds=False)
    react_raw: Optional[int] = None
    react_confirms: Optional[str] = None   # confirms / contradicts / neutral
    # C12 (v1.5.0) provenance: which legs are VERIFIED (present, in-band confidence and,
    # for order-driven names, forward-sourced). Downstream layers MUST read this rather
    # than inferring "stable" from a leg that merely defaulted to 0.
    verified: list = field(default_factory=list)


def _hard_gates(j: Judgment, m: Market, shares_guess: float):
    """Return (ok, subtype_if_fail, reasons). G1 liquidity, G2 gap-history.
    G3 (macro) and vol are dampers, handled in sizing. G4 (borrow) handled at cascade."""
    reasons = []
    # G1 liquidity
    g1 = (m.dollar_vol_20d >= PARAMS["G1_DOLLAR_VOL_MIN"]
          and (shares_guess <= PARAMS["G1_ADV_FRAC_MAX"] * m.share_vol_20d))
    if not g1:
        reasons.append("G1 liquidity FAIL")
    # G2 gap-history
    g2 = (m.avg_abs_open >= PARAMS["G2_GAP_MIN"]
          and m.confirmed_quarters >= PARAMS["G2_MIN_QTRS"])
    if not g2:
        reasons.append("G2 gap-history FAIL")
    return (g1 and g2), ("GATE_FAIL" if not (g1 and g2) else None), reasons


def _reconcile(j: Judgment, t: Optional[Truth], cfg: EngineConfig):
    """C4 — compare LLM values against a pre-registered source. Fail closed on divergence.
    The engine does NOT fetch; `t` is supplied by the caller's pinned adapter."""
    if t is None:
        return None, ["C4: UNRECONCILED (no pinned-source truth supplied)"]
    errs = []
    if (t.stock_pct_since_last_earnings is not None
            and j.stock_pct_since_last_earnings is not None):
        if abs(j.stock_pct_since_last_earnings - t.stock_pct_since_last_earnings) > cfg.tol_ped_pp:
            errs.append(
                f"C4: PED {j.stock_pct_since_last_earnings:+.1f} vs source "
                f"{t.stock_pct_since_last_earnings:+.1f} diverge > {cfg.tol_ped_pp}pp")
    if t.pct_within_52w_high is not None and j.pct_within_52w_high is not None:
        if abs(j.pct_within_52w_high - t.pct_within_52w_high) > cfg.tol_52w_pp:
            errs.append("C4: 52wk-within diverges from source")
    if t.pct_below_52w_high is not None and j.pct_below_52w_high is not None:
        if abs(j.pct_below_52w_high - t.pct_below_52w_high) > cfg.tol_52w_pp:
            errs.append("C4: 52wk-below diverges from source")
    return (len(errs) == 0), errs


def rev_feed_integrity(up30, down30, up7, down7, cov):
    """C13 (v1.5.6) — REV FEED INTEGRITY. Returns a list of fatal reasons (empty = clean).

    THE HOLE THIS CLOSES. After v1.5.5 removed REVISIONS from FORWARD_VEL_BASES, analyst
    estimate-revisions feed exactly ONE surviving term: REV — the largest single input to
    `directional`, which is 71% of the live edge score. Nothing anywhere in the stack ever
    checked whether that feed was internally coherent. C1 bounds `covering_analysts` and
    `implied_move`; the four revision counts had NO validation at all.

    Two rules, both DEFINITIONAL — no new parameters, nothing tuned:

    1. WINDOW SUBSET. The 7-day window is contained in the 30-day window, so up7 <= up30 and
       down7 <= down30 are arithmetic identities, not expectations. A feed that violates one
       is not a noisy measurement, it is a broken measurement.
       Observed 2026-07-29 pre-print: MSFT reported up7=10 vs up30=8.

    2. DOMAIN OF R. `score_rev` reads R = (up30 - down30) / covering_analysts and buckets it
       against +/-0.30 / +/-0.10 — i.e. R is DEFINED as a net fraction of the covering panel.
       |R| >= 1.0 means the net one-way revisions equalled or exceeded the entire panel in a
       month. That is the signature of an estimate RE-BASING (the vendor's period pointer
       rolling to a new quarter, so every analyst's estimate is logged as "new"), not of
       opinion changing. 1.0 is the definitional edge of a fraction, not a threshold.
       Observed 2026-07-29 pre-print: FTNT reported 38 up / 0 down against 37 covering
       analysts -> R = +1.03 -> REV = +2, the MAXIMUM bullish fundamental read the model can
       produce, on an artifact.

    FAIL CLOSED, deliberately. This lives in C1 and voids the whole evaluation rather than
    just nulling REV, and that choice is the conservative one on purpose: at the edge-score
    layer, merely ZEROING a rejected REV is *not* monotonically conservative — if REV opposed
    the other terms, removing it can INCREASE |edge| and manufacture a trade. Refusing the
    name cannot. A broken feed means the model does not know what it thinks; the honest
    output is silence, not a smaller opinion.

    GOVERNANCE. Parameter cost 0. Breaks no prior entry: all 93 ledger rows were checked and
    ZERO violate either rule, so no historical winner is disturbed (Abstraction Test limb 2).
    Limb 1 is not applicable — this is a MECHANISM-class input validation, not a fix invented
    in response to a loss (HANDOFF section 2, the distinction that matters).
    """
    bad = []
    if None not in (up7, up30) and up7 > up30:
        bad.append(f"C13: up_7d({up7}) > up_30d({up30}) — the 7d window is a SUBSET of the "
                   f"30d window; this revisions feed is arithmetically impossible")
    if None not in (down7, down30) and down7 > down30:
        bad.append(f"C13: down_7d({down7}) > down_30d({down30}) — same subset violation")
    if None not in (up30, down30, cov) and cov:
        R = (up30 - down30) / cov
        if abs(R) >= 1.0:
            bad.append(f"C13: R=(up-down)/coverage={R:+.2f} is outside the domain of a "
                       f"net-fraction-of-panel metric (|R|>=1 => every covering analyst moved "
                       f"one way in a month: an estimate RE-BASING artifact, not opinion)")
    return bad


def _sanity(j: Judgment, m: Market):
    """C1 — hard bounds. Returns list of fatal errors."""
    e = []
    if not (0 < m.price < 100_000):            e.append("C1: price out of range")
    if j.covering_analysts is not None and not (0 <= j.covering_analysts <= 60):
        e.append("C1: covering_analysts implausible")
    if not (0 <= m.avg_abs_open <= 60):        e.append("C1: avg_abs_open out of range")
    # C13 (v1.5.6) — the revisions feed itself. See rev_feed_integrity().
    e += rev_feed_integrity(j.up_revisions_30d, j.down_revisions_30d,
                            j.up_revisions_7d, j.down_revisions_7d, j.covering_analysts)
    # C1 for implied_move — review #2 found it had NO bound at all while carrying decision
    # weight. Delegated so the rule lives with the module that derives it.
    try:
        from pre_impliedmove import sanity as _im_sanity
        e += _im_sanity(m.implied_move, m.implied_move_raw, m.implied_move_basis)
    except Exception:
        pass
    for name, v in (("GG", j.GG), ("VEL", j.VEL), ("REACT", j.REACT)):
        if v is not None and v not in (-1, 0, 1):
            e.append(f"C1: {name}={v} outside [-1,+1]")
    if not (-2 <= j.FLAG <= 0):                e.append("C1: FLAG outside [-2,0]")
    return e


def _worst_case_band(components: dict, unavailable: list, cfg: EngineConfig):
    """DS_floor / DS_ceil. Spec swings GG/VEL/REACT/FLAG.
    C6 (fasttrack): also swing REV over [-2,+2] when coverage UNAVAILABLE, and SAT over
    [-2,+2] when a SAT input is UNAVAILABLE. C5 (fasttrack): any input tagged LOW in
    `unavailable` is treated as UNAVAILABLE here (added upstream)."""
    ds = sum(components.values())
    ranges = {"GG": (-1, 1), "VEL": (-1, 1), "REACT": (-1, 1), "FLAG": (-2, 0)}
    if cfg.fasttrack:
        ranges["REV"] = (-2, 2)
        ranges["SAT"] = (-2, 2)
    floor = ds
    ceil = ds
    for name in unavailable:
        if name in ranges:
            lo, hi = ranges[name]
            floor += lo - components.get(name, 0)
            ceil += hi - components.get(name, 0)
    return floor, ceil


def _cascade(ds, ds_floor, ds_ceil, cbr, g0, gates_ok, g4_ok, m: Market,
             conviction, align, cfg: EngineConfig):
    """§14.C strict cascade, first match wins. Returns (action, subtype, reasons)."""
    reasons = []
    if g0 in (None, "UNRESOLVED"):
        return "NO_TRADE", "GATE_FAIL", ["G0 unresolved"]
    if g0 == "DRY_RUN":
        return "DRY_RUN", None, ["G0 not T-1"]
    if not gates_ok:
        return "NO_TRADE", "GATE_FAIL", ["hard gate fail"]

    # C8 (watch): a trade must also have ALIGN >= ALIGN_MIN (breadth, not just magnitude)
    align_ok = (not cfg.watch) or (align >= PARAMS["ALIGN_MIN"])

    if ds >= PARAMS["T_BUY"] and cbr == "CLEAN":
        if not align_ok:
            return "NO_TRADE", "LOW_CONVICTION", ["C8: ALIGN < %d" % PARAMS["ALIGN_MIN"]]
        if ds_floor < PARAMS["T_BUY"]:
            return "INCOMPLETE", None, ["worst-case DS_floor %d < +3" % ds_floor]
        return "BUY", None, reasons
    if ds >= PARAMS["T_BUY"] and cbr != "CLEAN":
        return "NO_TRADE", "LONG_BLOCKED", ["CBR MANUFACTURED long-block"]
    if ds <= PARAMS["T_SHORT"] and g4_ok:
        if not align_ok:
            return "NO_TRADE", "LOW_CONVICTION", ["C8: ALIGN < %d" % PARAMS["ALIGN_MIN"]]
        if ds_ceil > PARAMS["T_SHORT"]:
            return "INCOMPLETE", None, ["worst-case DS_ceil %d > -3" % ds_ceil]
        return "SHORT", None, reasons
    if ds <= PARAMS["T_SHORT"] and not g4_ok:
        return "NO_TRADE", "SHORT_BLOCKED", ["borrow unavailable/expensive"]
    # INCOMPLETE if unavailable inputs could reach the band
    if ds_floor <= PARAMS["T_SHORT"] or ds_ceil >= PARAMS["T_BUY"]:
        return "INCOMPLETE", None, ["unavailable inputs could reach the band"]
    return "NO_TRADE", "LOW_CONVICTION", ["DS inside (-3,+3)"]


def _size(conviction, m: Market, cfg: EngineConfig):
    """§14.D gap-at-risk sizing. C8 (watch): retire the HIGH 1.5x multiplier (all 1.0x)
    until HIGH>MEDIUM is validated. C9 (fasttrack): both dampers firing -> caller sees
    a NO_TRADE upstream, so here we only compute the size for a surviving trade."""
    base_unit = (PARAMS["RISK_BUDGET"] * m.capital) / ((m.avg_abs_open / 100.0) * m.price)
    if cfg.watch:
        raw_units = 1.0                       # C8: retire HIGH bump
    else:
        raw_units = PARAMS["HIGH_UNITS"] if conviction == "HIGH" else 1.0
    damper = 1.0
    if m.macro_overlap:
        damper *= PARAMS["DAMPER_MULT"]
    vol_hot = (m.vix > PARAMS["VIX_HOT"] or m.spy_5d_realvol_wow > PARAMS["SPY_RV_WOW_HOT"]
               or abs(m.spx_day) > PARAMS["SPX_DAY_HOT"])
    if vol_hot:
        damper *= PARAMS["DAMPER_MULT"]
    final_units = raw_units * damper
    shares = math.floor(base_unit * final_units)
    gap_at_risk = shares * m.price * (m.avg_abs_open / 100.0)
    return shares, gap_at_risk, final_units


def _both_dampers(m: Market) -> bool:
    vol_hot = (m.vix > PARAMS["VIX_HOT"] or m.spy_5d_realvol_wow > PARAMS["SPY_RV_WOW_HOT"]
               or abs(m.spx_day) > PARAMS["SPX_DAY_HOT"])
    return m.macro_overlap and vol_hot


def evaluate(j: Judgment, m: Market, t: Optional[Truth] = None,
             cfg: Optional[EngineConfig] = None, skew: Optional[Skew] = None,
             _compute_sensitivity: bool = True) -> Result:
    cfg = cfg or EngineConfig()
    warnings = []

    # --- C1 sanity bounds (PLUMBING) ---
    sane = _sanity(j, m)
    if sane:
        return Result("INPUT_INVALID", 0, 0, 0, "NONE", {}, [], sane,
                      no_trade_subtype="INPUT_INVALID", warnings=sane)

    # --- implied-move provenance (non-fatal; see pre_impliedmove.sanity scope note) ---
    try:
        from pre_impliedmove import provenance_warning as _im_warn
        _w = _im_warn(m.implied_move, m.implied_move_basis)
        if _w:
            warnings.append(_w)
    except Exception:
        pass

    # --- C4 cross-source reconciliation (FAST-TRACK LOGIC) ---
    if cfg.fasttrack:
        ok, msgs = _reconcile(j, t, cfg)
        if ok is False:
            return Result("INPUT_INVALID", 0, 0, 0, "NONE", {}, [], msgs,
                          no_trade_subtype="INPUT_INVALID", warnings=msgs)
        if ok is None:
            warnings += msgs   # unreconciled: warn, don't block

    # --- components (sealed core) ---
    rev, rev_status = score_rev(j.up_revisions_30d, j.down_revisions_30d, j.covering_analysts)
    vel = j.VEL if j.VEL is not None else 0

    # --- C12 VEL forward-sourcing (FAST-TRACK LOGIC; monotonically CONSERVATIVE) ---
    # On an order-driven business, trailing revenue is not a trajectory measurement — it
    # lags and INVERTS on a name ramping a new end-market. Such a VEL is discarded (0) and
    # marked UNAVAILABLE, which widens the worst-case band and can only kill a trade.
    vel_unsourced = False
    basis = (j.vel_basis or "").upper()
    if cfg.fasttrack and j.VEL is not None:
        if j.order_driven and basis not in FORWARD_VEL_BASES:
            vel_unsourced = True
            warnings.append(f"C12: order-driven name, VEL basis {j.vel_basis!r} is not "
                            f"forward ({'/'.join(FORWARD_VEL_BASES)}) -> VEL discarded")
        elif cfg.strict_sourcing and not basis:
            vel_unsourced = True
            warnings.append("C12 strict: VEL has no declared basis -> UNVERIFIED")
    if vel_unsourced:
        vel = 0

    gg = j.GG if j.GG is not None else 0
    gg_unsourced = cfg.strict_sourcing and j.GG is not None and not (j.gg_basis or "")
    if gg_unsourced:
        gg = 0
        warnings.append("C12 strict: GG has no declared basis -> UNVERIFIED")
    react_raw = j.REACT if j.REACT is not None else 0
    react = react_raw if cfg.react_in_ds else 0   # C10: exclude from DS when owner sets confirmation-mode
    flag = j.FLAG
    sat, sat_unavail, excess = score_sat(j, rev, vel, cfg)
    components = {"REV": rev, "GG": gg, "VEL": vel, "SAT": sat, "REACT": react, "FLAG": flag}
    ds = sum(components.values())

    # --- unavailable set (spec + C5 + C6) ---
    unavailable = []
    if j.GG is None or gg_unsourced: unavailable.append("GG")
    if j.VEL is None or vel_unsourced: unavailable.append("VEL")
    if j.REACT is None and cfg.react_in_ds: unavailable.append("REACT")  # not in band when confirmation-only
    # FLAG defaults to 0; treat as available unless caller marks LOW/UNAVAILABLE
    if cfg.fasttrack:
        if rev_status == "UNAVAILABLE": unavailable.append("REV")
        if sat_unavail: unavailable.append("SAT")
        # C5: LOW-confidence inputs treated as UNAVAILABLE for the band
        for name, conf in j.confidence.items():
            if conf in ("LOW", "UNAVAILABLE") and name in components and name not in unavailable:
                unavailable.append(name)

    ds_floor, ds_ceil = _worst_case_band(components, unavailable, cfg)

    # --- C12 VERIFIED set: legs that were actually measured, not defaulted to 0 ---
    # REV is verified only when coverage existed (rev_status OK) — note that when fasttrack
    # is off, REV never enters `unavailable`, so it must be checked directly.
    verified = []
    if rev_status == "OK" and "REV" not in unavailable: verified.append("REV")
    for leg in ("GG", "VEL", "SAT"):
        if leg not in unavailable:
            if leg == "SAT" and sat_unavail:
                continue
            if leg in ("GG", "VEL") and getattr(j, leg) is None:
                continue
            verified.append(leg)

    # --- Stage-1 skew DIAGNOSTIC (logged only; NEVER gates) ---
    sk_val, sk_comp, sk_status = score_skew(skew, m)

    def _attach(r: Result) -> Result:
        r.skew, r.skew_components, r.skew_status = sk_val, sk_comp, sk_status
        r.verified = verified
        return r

    # --- conviction (§1.2) + ALIGN/OPPOSE (C8 diagnostic; gates only under watch) ---
    sign = 1 if ds > 0 else (-1 if ds < 0 else 0)
    align = sum(1 for v in components.values() if v != 0 and (v > 0) == (sign > 0)) if sign else 0
    oppose = sum(1 for v in components.values() if v != 0 and (v > 0) != (sign > 0)) if sign else 0
    if abs(ds) >= PARAMS["HIGH_CUT"]:
        conviction = "HIGH"
    elif abs(ds) >= PARAMS["T_BUY"]:
        conviction = "MEDIUM"
    else:
        conviction = "NONE"

    # --- G4 borrow (shorts only) ---
    g4_ok = m.borrow_locate and (m.borrow_fee <= PARAMS["G4_FEE_MAX"])

    # --- provisional size for G1 share-fraction gate ---
    shares_guess, _, _ = _size(conviction, m, cfg)
    gates_ok, gate_subtype, gate_reasons = _hard_gates(j, m, shares_guess)

    # --- C9 both-dampers kill (FAST-TRACK LOGIC): a would-be trade dies ---
    if cfg.fasttrack and _both_dampers(m):
        would_trade = (ds >= PARAMS["T_BUY"] and j.CBR == "CLEAN") or \
                      (ds <= PARAMS["T_SHORT"] and g4_ok)
        if would_trade and gates_ok:
            r = Result("NO_TRADE", ds, ds_floor, ds_ceil, conviction, components,
                       unavailable, ["C9: macro-overlap AND vol-damper both fire"],
                       no_trade_subtype="GATE_FAIL", warnings=warnings)
            return _attach(r)

    # --- ESTIMATED hard override (§14.F): G2 estimated + would-trade -> NO TRADE ---
    if m.g2_estimated and ((ds >= PARAMS["T_BUY"]) or (ds <= PARAMS["T_SHORT"])):
        return _attach(Result("NO_TRADE", ds, ds_floor, ds_ceil, conviction, components,
                      unavailable, ["ESTIMATED input cannot be deciding margin"],
                      no_trade_subtype="GATE_FAIL", warnings=warnings))

    # --- cascade ---
    action, subtype, reasons = _cascade(ds, ds_floor, ds_ceil, j.CBR, j.G0,
                                        gates_ok, g4_ok, m, conviction, align, cfg)
    reasons = gate_reasons + reasons

    res = Result(action, ds, ds_floor, ds_ceil, conviction, components, unavailable,
                 reasons, no_trade_subtype=subtype, warnings=warnings)
    _attach(res)

    # C10: REACT confirmation read (only when it is not a DS term)
    if not cfg.react_in_ds:
        res.react_raw = react_raw
        s_ds = 1 if ds > 0 else (-1 if ds < 0 else 0)
        if react_raw == 0 or s_ds == 0:
            res.react_confirms = "neutral"
        elif (react_raw > 0) == (s_ds > 0):
            res.react_confirms = "confirms"
        else:
            res.react_confirms = "contradicts"

    # --- sizing for real trades ---
    if action in ("BUY", "SHORT"):
        res.shares, res.gap_at_risk, res.final_units = _size(conviction, m, cfg)

    # --- C3 sensitivity score (PLUMBING, diagnostic) ---
    if _compute_sensitivity:
        res.sensitivity = _sensitivity(j, m, t, cfg, action)
    return res


def _sensitivity(j: Judgment, m: Market, t, cfg, base_action):
    """C3 — fraction of single-input +/-1-bucket perturbations that flip the action.
    Diagnostic only; never changes the verdict. Perturbs the pre-bucketed judgment
    components {GG,VEL,REACT} and REV (via a +/-1 net revision). Nested evaluate() calls
    pass _compute_sensitivity=False so there is no recursion."""
    flips = 0
    trials = 0

    def action_of(jj) -> str:
        return evaluate(jj, m, t, cfg, _compute_sensitivity=False).action

    for name in ("GG", "VEL", "REACT"):
        cur = getattr(j, name) or 0
        for delta in (-1, +1):
            newv = int(_clamp(cur + delta, -1, 1))
            if newv == cur:
                continue
            jj = Judgment(**{**asdict(j), name: newv})
            trials += 1
            if action_of(jj) != base_action:
                flips += 1
    if j.covering_analysts and j.up_revisions_30d is not None:
        for delta in (-1, +1):
            jj = Judgment(**{**asdict(j),
                             "up_revisions_30d": max(0, (j.up_revisions_30d or 0) + max(delta, 0)),
                             "down_revisions_30d": max(0, (j.down_revisions_30d or 0) + max(-delta, 0))})
            trials += 1
            if action_of(jj) != base_action:
                flips += 1
    return round(flips / trials, 3) if trials else 0.0


if __name__ == "__main__":
    print(f"PRE engine v{__version__} loaded. Scoring params: {_param_count()}/{PARAM_CEILING} "
          f"(+{len(SKEW_PARAMS)} skew diagnostic params, off-budget)")
