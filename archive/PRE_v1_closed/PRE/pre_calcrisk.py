"""
PRE Calculated-Risk layer — PRIMARY output for earnings-wave capture.
================================================================================
STRUCTURAL (owner-approved 2026-07-14). Status: PROVISIONAL until forward-validated.
Layer version: 1.1.0  (see CHANGELOG at the bottom of this docstring)

Why this exists: the sealed sign-classifier abstains on beaten-down / priced-in setups
because sign != EV. For "capture the wave" the right question is PAYOFF ASYMMETRY, not
sign. This layer answers the decision in exactly three outcomes — BUY / SHORT / NO TRADE —
plus a SIZE and a reason, reasoning about the distribution rather than forcing a directional integer.

It sits ON TOP of pre_engine and NEVER weakens a protection:
  - hard gates (G1/G2) and CBR long-block are inherited from the sealed engine,
  - the falling-knife guard is re-expressed as the VALUE-TRAP rule (beaten down AND
    deteriorating -> NO TRADE),
  - the sign verdict (DS) is kept as a SECONDARY confirmation, not the gate.

Five deterministic reads (no fabricated probabilities — same anti-overfit philosophy):
  IRM/RICH : implied_move / avg_abs_open  -> gap-space: over/under-charging for the move
  VRICH    : implied vs REALIZED vol      -> vol-space richness (the GOOG measurement gap)
  WASH     : idiosyncratic drawdown       -> is the downside already used up
  FUND     : REV+GG+VEL trajectory        -> stable/improving vs deteriorating (trap discriminator)
  DIR      : sign(DS)                     -> secondary directional confirmation

SOURCING RULES (judgment layer — from the AEHR 2026-07-14 miss; see memory
pre-aehr-miss-forcing-functions). These change what the inputs MEAN, not the arithmetic:
  * VEL for ORDER-DRIVEN businesses (semis-cap-equip, defense, project/EPC) keys off FORWARD
    BOOKINGS / BACKLOG velocity, NOT trailing revenue. Trailing revenue lags and inverts the
    signal on names ramping a new end-market. (AEHR: trailing rev -44% YoY but record bookings.)
    -> This is now MACHINE-ENFORCED by engine C12 (`Judgment.order_driven` + `vel_basis`).
  * A regime-JUMP in implied move on a normally-quiet name = STRUCTURAL-CHANGE / bimodal signal
    that CORROBORATES a fundamental inflection -> do NOT read it as sell-the-news. Only fade rich
    vol on high-expectation names that are NOT beaten/inflecting.
  * Positioning ("crowded/exhausted") is a MODIFIER, never a driver; it may not veto a live
    fundamental inflection.
  * A recent confirmed positive catalyst (orders/design wins) should LIFT conviction (Bayesian),
    not be logged as narrative. [FLAG is subtract-only today -> positive-catalyst channel is a
    proposed LOGIC change, WATCH-gated.]

CHANGELOG (layer)
  v1.1.0 (2026-07-23) — post-mortem remediation batch, owner sign-off:
    [1] FUND_UNDEFINED -> NO_TRADE. The washout-BUY now requires FUND *VERIFIED* >= 0
        (>=2 of REV/GG/VEL actually measured), not merely "not negative". THE CORE LEAK:
        missing legs default to 0 and `fund >= 0` read that as "not deteriorating", which
        contradicts the model's own fail-closed philosophy. Named failures: NFLX (-10.6%),
        QS (-2.9%, a confident MED BUY on a PRE-REVENUE company). Shipped PAIRED with engine
        C12 forward-sourcing — without that pairing this gate would have blocked AEHR (+35%).
    [2] Cliff-fragility -> abstain. Within FRAGILE_BAND of the IRM 1.30 / 0.85 cliff the read
        is one noisy input from flipping; if it is load-bearing the stance becomes NO_TRADE.
    [3] Sell-the-news conviction defect FIXED (case: GOOG). The old SHORT confirms list
        contained `fund <= 0`, which penalised exactly the setup a sell-the-news short IS —
        great fundamentals priced to perfection. FUND is now dropped from the SHORT confirms
        entirely (it does not discriminate) and MEDIUM requires all 3 remaining confirms.
        Strictly conservative: the confirm bar went from 3-of-4 to 3-of-3.
    [4] Vol-space richness (VRICH) enters the decision path as a CONSERVATIVE read. This is
        the GOOG gap: richness was measured only as implied/avg_gap (1.09, "fair") while the
        real signal was IV ~60% vs realized. VRICH can DEMOTE or ABSTAIN; it cannot by itself
        create a trade (that is Stage-2 and needs its own n-bar).
    [5] INPUT_INVALID now returns NO_TRADE, not "AVOID". "AVOID" was a fourth decision value
        contradicting the documented "exactly three outcomes".
    [6] Conviction labels normalised to the engine's vocabulary: MEDIUM / LOW / NONE
        (was MED/LOW, which silently never matched `pre_ledger.stats()`'s "MEDIUM" key,
        so calc-risk tier calibration was being computed on an empty set).
    [7] Expression layer: names the correct INSTRUMENT (equity / long straddle / put spread).
        Recommendation only — this repo contains NO option-pricing model, so no premium,
        breakeven or greeks are computed and none may be claimed.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from pre_engine import (Judgment, Market, Truth, Skew, EngineConfig, evaluate, PARAMS,
                        __version__ as ENGINE_VERSION)

__layer_version__ = "1.3.0"
# CHANGELOG (layer)
#  v1.3.0 (2026-07-29) Tier-1 fixes from the INDEPENDENT ADVERSARIAL REVIEW (owner-approved):
#     * REMOVED the v1.2.0 guide-freshness GATE. It failed both limbs of the Abstraction Test:
#       it would not have prevented AMKR (Type-B / unobservable) and it BLOCKS AEHR (the only
#       winner). Freshness is retained as a LOGGED DIAGNOSTIC so it can earn its way back with
#       evidence. This is a deliberate self-reversal of a patch shipped 24h earlier.
#     * RAISED the SHORT hurdle: `wash <= 0` -> `wash == -1` (must be actually EXTENDED).
#       Shorts fight the documented long-side earnings-announcement premium, so they need a
#       higher bar than longs. Monotonically conservative. Abstentions caused by the new bar
#       are logged, not silent.
#  v1.2.0 (2026-07-28) guide-freshness gate — REVERTED in v1.3.0, see above.
#  v1.1.0 (2026-07-23) FUND-verified gate, cliff-fragility, VRICH, sell-the-news conviction fix.

# thresholds — DIAGNOSTIC layer, OUTSIDE the 30-param scoring budget; unvalidated priors.
CR = {
    "IRM_CHEAP": 0.85, "IRM_RICH": 1.30,
    "FRAGILE_BAND": 0.05,         # within this of a cliff, the read is one input from flipping
    # VRICH bands — event-implied vol / realized vol, BOTH annualized. These live in a
    # DIFFERENT space from IRM (an earnings straddle is structurally 1.5-2.5x baseline vol,
    # so an IRM-style 1.30 cutoff would call everything rich). UNVALIDATED PRIORS, n=0.
    "VRICH_HI": 2.50, "VRICH_LO": 1.30,
    "WASH_EXCESS": -15.0, "WASH_DRAWDOWN": 20.0, "EXTENDED_EXCESS": 15.0,
    "EXTREME_GAP": 15.0,          # avg_abs_open above this -> washout unreliable (whipsaw name)
    "FUND_MIN_LEGS": 2,           # REV/GG/VEL legs that must be VERIFIED for FUND to be DEFINED
    "FRESH_MIN_7D": 3,            # up-revisions in the last 7d to count as a FRESH wave (not a straggler)
    "UNITS_MED": 0.75, "UNITS_LOW": 0.5,   # payoff bets are SMALL by design
}


def _sign(x) -> int:
    return 1 if x > 0 else (-1 if x < 0 else 0)


@dataclass
class CalcRisk:
    ticker: str
    stance: str          # BUY / SHORT / NO_TRADE   (the decision — exactly three)
    asymmetry: str       # POSITIVE / NEGATIVE / TRAP / NONE  (the reason)
    conviction: str      # MEDIUM / LOW / NONE  (engine vocabulary — ledger stats key on this)
    irm: Optional[float]
    rich: int
    wash: int
    fund: int
    dir: int
    size_units: float
    shares: int
    gap_at_risk: float
    sign_action: str     # sealed-engine verdict (secondary cross-check)
    rationale: list = field(default_factory=list)
    caveats: list = field(default_factory=list)
    # --- v1.1.0 additions ---
    fund_status: str = "UNDEFINED"      # DEFINED / UNDEFINED
    fund_legs: list = field(default_factory=list)   # which of REV/GG/VEL were VERIFIED
    vrich: Optional[int] = None         # vol-space richness (-1 rich / 0 fair / +1 cheap / None n/a)
    vrich_ratio: Optional[float] = None  # event-implied annualized vol / realized vol
    fund_fresh: Optional[bool] = None    # was the positive FUND signal THIS-print-fresh (v1.2.0)
    fragile: bool = False
    expression: str = "equity"
    capital: float = 0.0                # book size the sizing was computed against


def calc_risk(ticker: str, j: Judgment, m: Market, t: Optional[Truth] = None,
              cfg: Optional[EngineConfig] = None, skew: Optional[Skew] = None) -> CalcRisk:
    cfg = cfg or EngineConfig(fasttrack=True, watch=False, react_in_ds=False)
    r = evaluate(j, m, t=t, cfg=cfg, skew=skew)   # sealed engine: protections + DS (secondary)
    rat, cav = [], []

    # ---- inherited protections ----
    if r.action == "INPUT_INVALID":
        # [5] was "AVOID" — a fourth decision value. Fail closed as NO_TRADE.
        return CalcRisk(ticker, "NO_TRADE", "NONE", "NONE", None, 0, 0, 0, 0, 0.0, 0, 0.0,
                        r.action, capital=m.capital,
                        rationale=["INPUT_INVALID (fail closed): " + "; ".join(r.warnings)])
    gate_fail = (r.no_trade_subtype == "GATE_FAIL") or r.action == "DRY_RUN"

    # ---- read 1: gap-space richness ----
    irm = round(m.implied_move / m.avg_abs_open, 2) if (m.implied_move and m.avg_abs_open) else None
    rich = 1 if (irm is not None and irm <= CR["IRM_CHEAP"]) else \
        (-1 if (irm is not None and irm >= CR["IRM_RICH"]) else 0)

    # [2] cliff fragility — is this read one noisy input away from flipping?
    fragile = irm is not None and (
        abs(irm - CR["IRM_RICH"]) <= CR["FRAGILE_BAND"]
        or abs(irm - CR["IRM_CHEAP"]) <= CR["FRAGILE_BAND"])
    if fragile:
        cav.append(f"FRAGILE: IRM {irm} sits within {CR['FRAGILE_BAND']} of a cliff "
                   f"({CR['IRM_CHEAP']}/{CR['IRM_RICH']}) — the RICH read is not robust")

    # ---- read 2: vol-space richness (VRICH) — [4] the GOOG measurement gap ----
    # Measures what IRM structurally CANNOT: is the OPTION expensive, versus is the expected
    # gap big relative to this name's own gap history.
    #
    # NOTE this deliberately does NOT reuse the Stage-1 skew overlay's RICH sub-score.
    # That one divides by max(realized_horizon, avg_abs_open) — the floor re-imports
    # gap-space and collapses RICH back onto IRM exactly when avg_abs_open is the larger
    # term, which is the GOOG case itself. Stage-1 RICH is left untouched (it is a sealed
    # logged diagnostic); VRICH computes the pure ratio here.
    #
    #   event-implied annualized vol = implied_move% * sqrt(252 / days_to_event)
    #   vrich_ratio                  = that / realized_vol_3m
    vrich, vrich_ratio = None, None
    if (skew is not None and skew.realized_vol_3m and skew.days_to_event
            and m.implied_move is not None):
        implied_annualized = m.implied_move * math.sqrt(252.0 / skew.days_to_event)
        vrich_ratio = round(implied_annualized / skew.realized_vol_3m, 2)
        vrich = -1 if vrich_ratio >= CR["VRICH_HI"] else \
            (+1 if vrich_ratio <= CR["VRICH_LO"] else 0)

    # ---- read 3: washout ----
    excess = None
    if j.stock_pct_since_last_earnings is not None and j.sector_etf_pct_same_window is not None:
        excess = j.stock_pct_since_last_earnings - j.sector_etf_pct_same_window
    dd = j.pct_below_52w_high
    washed = (excess is not None and excess <= CR["WASH_EXCESS"]) and \
             (dd is not None and dd >= CR["WASH_DRAWDOWN"])
    extended = (excess is not None and excess >= CR["EXTENDED_EXCESS"])
    wash = 1 if washed else (-1 if extended else 0)

    # ---- read 4: FUND, with [1] the VERIFIED requirement ----
    # A leg that is absent scores 0. Summing absent legs and calling the result ">= 0 =
    # not deteriorating" is the core leak. FUND is DEFINED only when the legs were MEASURED.
    fund_legs = [leg for leg in ("REV", "GG", "VEL") if leg in (r.verified or [])]
    fund_defined = len(fund_legs) >= CR["FUND_MIN_LEGS"]
    fund = _sign(r.components["REV"] + r.components["GG"] + r.components["VEL"])
    fund_status = "DEFINED" if fund_defined else "UNDEFINED"
    if not fund_defined:
        cav.append(f"FUND UNDEFINED — only {len(fund_legs)}/3 trajectory legs verified "
                   f"({', '.join(fund_legs) or 'none'}); absent != stable")

    dir_ = _sign(r.ds)

    # ---- [GF] guide-freshness — DIAGNOSTIC ONLY as of v1.3.0 (was a GATE in v1.2.0) ----
    # HISTORY, so this is not re-litigated: after AMKR (a washout with "verified" positive
    # fundamentals that gapped -11% on a Q3 guide-down), v1.2.0 made a washout-BUY *require*
    # THIS-PRINT-FRESH positives. An independent review then applied the Abstraction Test
    # (see docs/POSTMORTEM_SOP.md) and the gate FAILED BOTH LIMBS:
    #   (a) it would NOT have prevented AMKR — that guide-down was unobservable pre-print
    #       (a Type-B failure; no pre-print signal existed), and
    #   (b) it BLOCKS AEHR, the only winner in the sample (bookings were revealed IN the
    #       print, so at T-1 nothing fresh was declarable).
    # A fix that doesn't prevent the failure it was built for AND kills a winner is a
    # symptom patch. It is REMOVED from the decision path. Freshness is still COMPUTED and
    # LOGGED so the ledger accrues evidence on whether it predicts anything — if it earns
    # its keep at real n, it can be re-proposed with evidence instead of a vivid loss.
    fresh_by_revs = (j.up_revisions_7d is not None
                     and j.up_revisions_7d >= CR["FRESH_MIN_7D"]
                     and j.up_revisions_7d > (j.down_revisions_7d or 0))
    fund_fresh = bool(j.guidance_fresh) or fresh_by_revs
    fund_fresh_known = (j.guidance_fresh is not None) or (j.up_revisions_7d is not None)

    extreme = m.avg_abs_open > CR["EXTREME_GAP"]
    # VOL-SETUP flag (AEHR 2026-07-14 lesson): an extreme mover where the straddle isn't
    # richly priced is a MAGNITUDE bet, not a DIRECTION bet. The equity BUY structurally
    # undersizes it; a long straddle captures the move direction-free.
    vol_setup = extreme and (irm is None or irm <= 1.15) and (vrich is None or vrich >= 0)
    if extreme:
        cav.append(f"extreme mover (avg gap {m.avg_abs_open:.0f}%) — washout unreliable; "
                   f"treat as coin-flip, size tiny")
    if vol_setup:
        cav.append("VOL-SETUP: magnitude edge > direction edge -> a LONG STRADDLE captures the "
                   "move direction-free; the equity BUY undersizes a big-reaction conviction")
    if m.g2_estimated:
        cav.append("G2 ESTIMATED (<4 confirmed quarters) — cannot be the deciding margin")

    # ---- decision — exactly three outcomes: BUY / SHORT / NO_TRADE ----
    # (asym carries the REASON: POSITIVE / NEGATIVE / TRAP / NONE)
    if gate_fail:
        stance, asym = "NO_TRADE", "NONE"; rat.append("hard gate failed — sealed protection")
    elif wash >= 1 and fund_defined and fund < 0:
        stance, asym = "NO_TRADE", "TRAP"
        rat.append("beaten down AND fundamentals deteriorating = value trap (falling-knife guard)")
    elif wash >= 1 and not fund_defined:
        # [1] the NFLX / QS failure mode. "Cheap" is not a thesis; an inflection is.
        stance, asym = "NO_TRADE", "NONE"
        rat.append("washout BUY requires VERIFIED non-deteriorating fundamentals; FUND is "
                   "UNDEFINED (fail closed, per the model's own missing-input philosophy)")
    elif wash >= 1 and fund >= 0:
        stance, asym = "BUY", "POSITIVE"
        rat.append(f"downside used up: idiosyncratic drawdown (excess {excess:+.0f}pts vs sector, "
                   f"{dd:.0f}% off high)")
        rat.append(f"fundamentals VERIFIED not deteriorating ({'+'.join(fund_legs)}) -> "
                   f"low bar / positive skew")
        if fund_fresh_known and not fund_fresh:
            cav.append("FRESHNESS (diagnostic, not gating): the positive legs are trailing/stale, "
                       "no this-print-fresh catalyst declared. Logged for evidence — the print "
                       "can still reset the forward guide (the AMKR failure mode).")
    elif rich <= -1 and wash == -1:
        # [SHORT HURDLE, v1.3.0] Was `wash <= 0` (merely NOT beaten down). Raised to `wash == -1`
        # (actually EXTENDED into the print). WHY: the earnings-announcement premium is a
        # documented LONG-side risk premium — announcing firms earn positive abnormal returns
        # over the announcement window. A short therefore starts with a negative-EV headwind
        # before any directional edge, so it must clear a HIGHER bar than a long, not the same
        # one. Requiring the name to have actually RUN UP (not just "not fallen") is that bar,
        # and it matches what the SHORT conviction confirms already demand. Monotonically
        # conservative: can only turn a SHORT into a NO_TRADE. (Our one short, ASML, lost.)
        stance, asym = "SHORT", "NEGATIVE"
        rat.append(f"rich vol (IRM {irm}) + EXTENDED into the print -> priced-for-perfection / "
                   f"sell-the-news (bar raised: shorts fight the announcement premium)")
        if vrich == -1:
            rat.append("vol-space CONFIRMS: implied rich vs realized (independent of gap history)")
    else:
        stance, asym = "NO_TRADE", "NONE"; rat.append("no clear payoff asymmetry")
        # [4] surface the GOOG case rather than silently missing it. NOT actioned: letting
        # VRICH originate a SHORT is a Stage-2 change and needs its own evidence bar.
        if vrich == -1 and rich == 0 and wash <= 0:
            cav.append("MEASUREMENT NOTE: vol-space says RICH (implied >> realized) while "
                       "gap-space says fair. Sell-the-news SHORT candidate — NOT actioned "
                       "(VRICH-originated trades require Stage-2 sign-off). Log it.")
        # v1.3.0: a name that WOULD have shorted under the old `wash <= 0` bar. Logged so the
        # cost of the raised hurdle is visible and auditable, not silently swallowed.
        if rich <= -1 and wash == 0:
            cav.append("SHORT HURDLE: rich vol but the name is neither washed NOR extended. "
                       "Would have been a SHORT before v1.3.0; now abstained because shorts "
                       "fight the announcement premium and need a higher bar. Logged.")

    # [2] cliff-fragility abstention — only where the fragile read is LOAD-BEARING.
    # A SHORT here is manufactured entirely by `rich`; one noisy implied_move flips it.
    if stance == "SHORT" and fragile:
        stance, asym = "NO_TRADE", "NONE"
        rat = ["FRAGILE: SHORT rests entirely on a RICH read sitting on the IRM cliff — abstain"]

    # CBR long-block (protection) applies to calc-risk BUYs too
    if stance == "BUY" and j.CBR != "CLEAN":
        stance, asym = "NO_TRADE", "TRAP"; rat.append("CBR MANUFACTURED — long blocked (protection)")

    # ---- conviction ----
    conv = "NONE"
    if stance == "BUY":
        confirms = [wash == 1, fund >= 0, rich >= 0, dir_ >= 0]
        need = 3
    elif stance == "SHORT":
        # [3] FIX (case: GOOG). The old list was [rich==-1, wash<=0, fund<=0, dir<=0].
        # BOTH `fund<=0` and `dir<=0` penalise strong fundamentals — and DIR = sign(DS) is
        # dominated by REV+GG+VEL, so it is very nearly a DUPLICATE of FUND, not an
        # independent confirm. A sell-the-news short IS great fundamentals + rich vol +
        # crowded expectations, so that pair made the correct setup structurally unable to
        # reach MEDIUM. Both are REMOVED (not flipped — flipping is non-conservative and
        # there are no holdouts). The replacements are de-correlated and in the right space:
        #   rich == -1   gap-space richness
        #   wash == -1   actually EXTENDED (stricter than the old "merely not beaten down")
        #   vrich == -1  vol-space richness — independent of this name's gap history
        # Bar goes from 3-of-4 easy terms to 3-of-3 hard ones: strictly conservative.
        # DIR is retained below as a CONTRADICTION flag only.
        confirms = [rich == -1, wash == -1, vrich == -1]
        need = 3
    else:
        confirms, need = [], 0
    if stance in ("BUY", "SHORT"):
        conv = "MEDIUM" if sum(1 for c in confirms if c) >= need else "LOW"
        if extreme or m.g2_estimated or fragile:
            conv = "LOW"
        # [4] VRICH demotions — conservative only, never a promotion.
        if stance == "BUY" and vrich == -1:
            conv = "LOW"
            cav.append("paying RICH vol on a washout BUY (implied >> realized) — demoted to LOW")
        if vrich is not None and rich != 0 and vrich != 0 and _sign(vrich) != _sign(rich):
            conv = "LOW"
            cav.append(f"richness reads CONTRADICT (gap-space {rich:+d} vs vol-space {vrich:+d}) "
                       f"— demoted to LOW")
        # DIR is a CONTRADICTION flag, not a confirm (see the SHORT confirms note above).
        if dir_ != 0 and _sign(dir_) != (1 if stance == "BUY" else -1):
            cav.append(f"sign-engine DIR {dir_:+d} CONTRADICTS the {stance} — secondary "
                       f"cross-check disagrees; the payoff read is carrying this alone")

    # ---- sizing (payoff bet: small, gap-normalized) ----
    base_unit = (PARAMS["RISK_BUDGET"] * m.capital) / ((m.avg_abs_open / 100.0) * m.price)
    units = {"MEDIUM": CR["UNITS_MED"], "LOW": CR["UNITS_LOW"], "NONE": 0.0}[conv]
    vol_hot = (m.vix > PARAMS["VIX_HOT"] or m.spy_5d_realvol_wow > PARAMS["SPY_RV_WOW_HOT"]
               or abs(m.spx_day) > PARAMS["SPX_DAY_HOT"])
    if m.macro_overlap:
        units *= 0.5
    if vol_hot:
        units *= 0.5
    shares = math.floor(base_unit * units)
    gap_at_risk = shares * m.price * (m.avg_abs_open / 100.0)

    # ---- [7] expression: name the right instrument (NO pricing — none exists here) ----
    expression = "equity"
    if stance == "BUY" and vol_setup:
        expression = "LONG STRADDLE (defined risk = premium paid) — direction-free magnitude bet"
    elif stance == "SHORT":
        expression = "DEFINED-RISK PUT SPREAD (equity short = unbounded gap risk)"
    elif stance in ("BUY", "SHORT"):
        expression = f"equity {stance.lower()}"
    if ("STRADDLE" in expression) or ("SPREAD" in expression):
        cav.append("EXPRESSION is a recommendation only — this repo contains NO option-pricing "
                   "model, so premium / breakeven / greeks are NOT computed and MUST NOT be quoted")

    if stance == "SHORT":
        cav.append("equity short = unbounded gap risk -> prefer DEFINED-RISK PUT SPREAD")
        if not (m.borrow_locate and m.borrow_fee <= PARAMS["G4_FEE_MAX"]):
            cav.append("borrow unavailable/expensive")

    return CalcRisk(ticker, stance, asym, conv, irm, rich, wash, fund, dir_,
                    round(units, 3), shares, round(gap_at_risk, 0), r.action,
                    rationale=rat, caveats=cav,
                    fund_status=fund_status, fund_legs=fund_legs, vrich=vrich,
                    vrich_ratio=vrich_ratio, fund_fresh=(fund_fresh if fund_fresh_known else None),
                    fragile=fragile, expression=expression, capital=m.capital)


# ------------------------------------------------------------------- ranking / print
_ORDER = {"BUY": 0, "SHORT": 1, "NO_TRADE": 2}
_CONV = {"MEDIUM": 0, "MED": 0, "LOW": 1, "NONE": 2}


def rank(results):
    return sorted(results, key=lambda c: (_ORDER.get(c.stance, 9), _CONV.get(c.conviction, 9)))


def render(c: CalcRisk) -> str:
    vr = "n/a" if c.vrich is None else f"{c.vrich:+d}"
    L = [f"{c.ticker:5s}  {c.stance:8s} / {c.asymmetry:8s} / conv {c.conviction:6s}"
         f"   IRM={c.irm}  [RICH {c.rich:+d} VRICH {vr} WASH {c.wash:+d} "
         f"FUND {c.fund:+d}({c.fund_status[:3]}) DIR {c.dir:+d}]"
         f"   (sign-engine: {c.sign_action})"]
    if c.shares:
        pct = (c.gap_at_risk / c.capital * 100.0) if c.capital else 0.0
        L.append(f"        size: {c.size_units}u  {c.shares} sh  gap-at-risk ${c.gap_at_risk:,.0f} "
                 f"({pct:.2f}% of ${c.capital:,.0f})")
        L.append(f"        expression: {c.expression}")
    for r in c.rationale:
        L.append(f"        + {r}")
    for cav in c.caveats:
        L.append(f"        ! {cav}")
    return "\n".join(L)


# ------------------------------------------------------------------- ledger registration
def register(ticker, j, m, t=None, cfg=None, event_date=None,
             entry_close_date=None, exit_open_date=None, sector_etf=None,
             note="", ledger_path=None, skew=None):
    """Freeze the calc-risk decision (BUY/SHORT/NO_TRADE) into the ledger with its
    entry/exit dates + sector benchmark, ready for post-mortem scoring."""
    from pre_ledger import _append, _hash, _now, _dc, DEFAULT_LEDGER, SCHEMA
    ledger_path = ledger_path or DEFAULT_LEDGER
    cfg = cfg or EngineConfig(fasttrack=True, watch=False, react_in_ds=False)
    c = calc_risk(ticker, j, m, t, cfg, skew=skew)
    r = evaluate(j, m, t=t, cfg=cfg, skew=skew)     # for secondary components

    verdict = {
        "action": c.stance,              # BUY / SHORT / NO_TRADE — record_outcome & stats read this
        "layer": "calc-risk", "layer_version": __layer_version__,
        "conviction": c.conviction, "asymmetry": c.asymmetry,
        "reads": {"irm": c.irm, "rich": c.rich, "vrich": c.vrich,
                  "vrich_ratio": c.vrich_ratio, "wash": c.wash,
                  "fund": c.fund, "fund_status": c.fund_status, "fund_legs": c.fund_legs,
                  "fund_fresh": c.fund_fresh,
                  "dir": c.dir, "fragile": c.fragile},
        "size_units": c.size_units, "shares": c.shares, "gap_at_risk": c.gap_at_risk,
        "capital": c.capital, "expression": c.expression,
        "rationale": c.rationale, "caveats": c.caveats,
        "sign_action": c.sign_action, "components": r.components, "verified": r.verified,
        "skew": r.skew, "skew_components": r.skew_components, "skew_status": r.skew_status,
        "exit": {"entry_close_date": entry_close_date, "exit_open_date": exit_open_date,
                 "sector_etf": sector_etf},
    }
    frozen = {"schema": SCHEMA, "engine_version": ENGINE_VERSION, "ticker": ticker,
              "event_date": event_date or (_now()[:10]), "inputs":
              {"judgment": _dc(j), "market": _dc(m), "truth": _dc(t), "skew": _dc(skew),
               "cfg": _dc(cfg)},
              "verdict": verdict}
    ih = _hash(frozen)
    entry_id = f"{ticker}:{frozen['event_date']}:{ih[7:15]}"
    record = {"type": "entry", "id": entry_id, "logged_at": _now(), "note": note,
              **frozen, "integrity_hash": ih}
    _append(ledger_path, record)
    return record, c
