# PRE / CATALYST — Independent Evaluation Brief
### For a fresh third-party AI reviewer (no prior context). Paste this whole document.

---

## 0. WHO YOU ARE AND WHAT I NEED FROM YOU

You are an independent, adversarial reviewer of a pre-earnings trading model called **PRE**
(project name **CATALYST**). You did **not** build it and you have no loyalty to it. Your job
is to think **outside its current paradigm** and tell me — the operator — where it is wrong,
where it is over-engineered, where it is too timid, and what a genuinely better version looks
like. The model's author is an AI that both **built** the model and **grades** it, which is a
structural conflict (marking its own homework). I am bringing you in precisely to break that
conflict. **Do not be polite about it. Attack the premises.**

I will give you: (a) full context on me and my risk appetite, (b) the complete model — its
philosophy, inputs, scoring, gates, decision logic, conviction, sizing, sourcing, and learning
loop, (c) the honest track record and every known failure, (d) the actual Python, and (e) a
prioritized list of the questions I need you to answer. At the very end is a section titled
**"WHAT I NEED BACK FROM YOU"** — that is your deliverable spec.

---

## 1. THE OPERATOR (me) AND THE MANDATE

- I am a Singapore-based active retail investor. **No coding background** — an AI does all the
  technical work from my plain-English direction.
- **Real capital: ~US$18,000** across three accounts (~10k / 5k / 3k). Positions are sized
  small in dollar terms but I run them per-account on each name's own merit.
- **I am a HIGH RISK TAKER by temperament, but a CALCULATED one.** My exact stance: *"If there
  is a logical reason to buy it, I'll buy it. I don't mind risking a lot on a read I've
  reasoned through. I calculate the risk — a logical risk — and then I take it."* I do **not**
  want a model that hides in cash. I want a model that **decides**, sizes the risk to the
  conviction, and pulls the trigger when there's a reason.
- **My single biggest complaint: the model is far too conservative. It says NO_TRADE on almost
  everything.** Recent batches of 6–12 names returned NO_TRADE on all-but-one. That is useless
  to me. Abstention is not free — a model that never bets never compounds. I need you to tell me
  how to convert its constant abstention into **calibrated, sized, decisive bets** without
  turning it into a coin-flip gambler.

## 2. WHAT THE MODEL IS FOR

**Capture the price reaction to an individual stock's earnings print.** It is NOT a
long-term investing model. One trade = one earnings event.

- **Trade mechanic (the exit rule is fixed and load-bearing):** enter the last session
  **before** the print, exit the **first market open after** it. This is pure **overnight gap
  capture**. AMC (after-market-close) print on day D → enter D's close, exit D+1's open. BMO
  (before-market-open) print on day D → enter D−1's close, exit D's open.
- **Decision vocabulary: exactly three outputs — BUY / SHORT / NO_TRADE.** Plus a conviction
  label and a position size.
- **Horizon: ~18 hours (overnight).** This matters enormously and is one of the things I most
  want you to challenge (see §11 and the Questions).

## 3. ARCHITECTURE — TWO STACKED LAYERS

The system is two decision layers that share one set of protections.

1. **The sealed sign-engine** (`pre_engine.py`, v1.5.2). A directional-**sign** classifier. It
   buckets a handful of judgment inputs into small integers, sums them into a **Decision Score
   (DS)**, and maps DS through a strict cascade to BUY / SHORT / NO_TRADE / INCOMPLETE. Called
   "sealed" because its arithmetic, gates and fail-closed behaviour are treated as inviolable.
2. **The calculated-risk layer** (`pre_calcrisk.py`, v1.2.0) — this is the **PRIMARY** output.
   It sits on top and reframes the question from *sign* to **payoff asymmetry**: sign ≠ expected
   value. It reads the distribution — is the move over/under-priced? is the downside already
   used up? are fundamentals stable or deteriorating? — and returns BUY / SHORT / NO_TRADE with
   a reason and a size. It inherits every protection from the engine below it.

**The founding principle (and possibly the model's greatest weakness — challenge it):**
> The engine **never fetches data and never guesses.** All raw judgment values are supplied by
> the caller (an LLM reasoning layer — i.e. the AI operating it). A **missing input scores 0 and
> is flagged UNAVAILABLE. Gates fail closed. A would-be trade with an unresolved input becomes
> INCOMPLETE / NO_TRADE, not a guess.**

This "fail-closed" philosophy is *why* the model abstains so much. Every missing or uncertain
input pushes toward NO_TRADE. I need you to judge whether this is prudent discipline or
pathological timidity for someone with my risk appetite.

**Prime directive: anti-overfitting.** The sample is tiny (n≈5 real trades). The model is built
to *freeze* its thresholds and *widen* abstention at small n rather than "learn" from noise.
Nothing is validated. (Again — challenge whether this is the right posture, or whether it's an
excuse for never committing.)

---

## 4. THE INPUTS (all caller-supplied; the engine never sources them itself)

### 4.1 Judgment inputs (the fundamental read)
| Input | Meaning | Scored to |
|---|---|---|
| **REV** | analyst estimate revisions: (up − down) / covering analysts, last 30 days | −2 … +2 |
| **GG** | guidance / growth direction | {−1, 0, +1} |
| **VEL** | *velocity* of the forward trajectory — for order-driven names this MUST come from **bookings / backlog / orders / guidance**, NOT trailing revenue (trailing rev inverts the signal on ramping names) | {−1, 0, +1} |
| **REACT** | post-print price reaction (used only as a confirmation, not in DS) | {−1, 0, +1} |
| **FLAG** | penalty flag (subtract-only) | [−2, 0] |
| **CBR** | earnings quality — CLEAN vs MANUFACTURED (blocks longs if manufactured) | flag |
| **SAT** | saturation / 52-week position — the "falling-knife guard" | −2 … +2 (derived) |

**Provenance fields** (declared per input, drive the verification gates):
`order_driven`, `vel_basis`, `gg_basis`, `rev_basis`, `up_revisions_7d`, `down_revisions_7d`,
`guidance_fresh`, and a per-input `confidence` map (HIGH/MED/LOW/UNAVAILABLE).

### 4.2 Market inputs (numeric, price-derived — I compute these from Yahoo Finance)
`price`, `avg_abs_open` (mean |earnings-day open gap| over last ~10 confirmed prints),
`confirmed_quarters`, `dollar_vol_20d`, `share_vol_20d`, `implied_move` (from the ATM straddle,
decontaminated — see §8), `capital`, `vix`, borrow availability/fee, `g2_estimated`.

### 4.3 Skew / positioning inputs (diagnostic only — logged, never gate)
`realized_vol_3m`, `days_to_event`, `skew_25d`, `consensus_pt_upside`, historical median
up/down gaps, `short_interest_pct_float`, `days_to_cover`, `put_call_oi_ratio`.

---

## 5. THE SIGN-ENGINE — SCORING, BANDS, GATES, CASCADE

### 5.1 Decision Score
`DS = REV + GG + VEL + SAT + REACT + FLAG`

- **BUY** if DS ≥ **+3** (`T_BUY`); **SHORT** if DS ≤ **−3** (`T_SHORT`); else **NO_TRADE**.
- **Conviction:** HIGH if |DS| ≥ 5 (`HIGH_CUT`); MEDIUM if |DS| ≥ 3; else NONE.

### 5.2 Worst-case band (the abstention engine)
Every UNAVAILABLE input is swung across its full range to produce `DS_floor` and `DS_ceil`.
If the band straddles the threshold (e.g. DS = +4 but `DS_floor` = +1 < +3), the verdict is
downgraded to **INCOMPLETE** (→ effectively NO_TRADE). **This is the single biggest source of
abstention.** Uncertainty in any one input collapses the trade.

### 5.3 Hard gates (all fail closed)
- **G0** timing: must be T−1 (the session before the print) or it's a DRY_RUN (screen-only).
- **G1** liquidity: $-volume ≥ $25M and our share size ≤ 1% of ADV.
- **G2** gap history: avg gap ≥ 2% and ≥ 4 confirmed quarters (else `g2_estimated`, can't be the deciding margin).
- **G3** macro overlap → sizing damper (halves size).
- **G4** borrow: shorts need locate and fee ≤ 5%.

### 5.4 The cascade (first match wins)
```
G0 unresolved            -> NO_TRADE
G0 not T-1               -> DRY_RUN
hard gate fail           -> NO_TRADE
DS>=+3 & CBR clean & floor>=+3 -> BUY     (if floor<+3 -> INCOMPLETE)
DS>=+3 & CBR manufactured -> NO_TRADE (LONG_BLOCKED)
DS<=-3 & borrow ok & ceil<=-3  -> SHORT   (if ceil>-3 -> INCOMPLETE)
DS<=-3 & no borrow       -> NO_TRADE (SHORT_BLOCKED)
band could reach a threshold  -> INCOMPLETE
else                     -> NO_TRADE (LOW_CONVICTION)
```

### 5.5 Sizing (gap-at-risk)
`base_units = (RISK_BUDGET × capital) / ((avg_abs_open/100) × price)`, with `RISK_BUDGET = 0.5%`.
Size is set so a one-average-gap adverse move risks a fixed fraction of capital. Macro overlap
and vol-hot each multiply size by 0.5. **Size scales to the gap, not to conviction** (conviction
only shifts a small multiplier). Question for you: is this the right way to size for a
high-risk operator?

**Full parameter registry (23 scoring params, ceiling 30):**
```
REV_STRONG .30  REV_MILD .10  REV_MILD_NEG -.10  REV_STRONG_NEG -.30
SAT_SATURATION 20  SAT_VACUUM -10  SAT_52W_NEAR 5  SAT_52W_FAR 25
VEL_UP_BPS 400  VEL_DN_BPS -400
T_BUY +3  T_SHORT -3  HIGH_CUT 5
G1_DOLLAR_VOL_MIN 25M  G1_ADV_FRAC_MAX 1%  G2_GAP_MIN 2%  G2_MIN_QTRS 4  G4_FEE_MAX 5%
VIX_HOT 28  SPY_RV_WOW_HOT 50  SPX_DAY_HOT 1.5  DAMPER_MULT 0.5
RISK_BUDGET 0.5%  HIGH_UNITS 1.5x  ALIGN_MIN 3
```
Every threshold is **hand-set**. There are NO learned weights, no ML, no probabilistic model.

---

## 6. THE CALC-RISK LAYER (PRIMARY) — FIVE READS AND THE DECISION TREE

### 6.1 The five reads
| Read | Formula | Captures |
|---|---|---|
| **IRM / RICH** | `implied_move / avg_abs_open` | gap-space richness: is the market over/under-charging vs THIS name's own gap history? RICH = −1 if IRM ≥ 1.30; CHEAP = +1 if ≤ 0.85 |
| **VRICH** | event-implied annualized vol / realized_vol_3m | vol-space richness: is the *option* expensive? (−1 if ratio ≥ 2.5, +1 if ≤ 1.3) |
| **WASH** | idio drawdown: excess-vs-sector ≤ −15 **and** ≥ 20% off high → +1; extended (excess ≥ +15) → −1 | is the downside already used up? |
| **FUND** | `sign(REV+GG+VEL)`, **DEFINED only if ≥2 of the 3 legs were actually VERIFIED** | trajectory / trap discriminator |
| **DIR** | `sign(DS)` | secondary directional cross-check (contradiction flag only) |

### 6.2 The decision tree (this is the heart of the model)
```
gate fail                                   -> NO_TRADE
washed + FUND defined + fund < 0            -> NO_TRADE / TRAP  (beaten down AND deteriorating)
washed + FUND undefined                     -> NO_TRADE         (need >=2 verified legs)
washed + fund >= 0 + NOT this-print-fresh   -> NO_TRADE         (guide-freshness gate, v1.2.0)
washed + fund >= 0 + FRESH                  -> BUY  / POSITIVE
rich(-1) + not washed                       -> SHORT / NEGATIVE (sell-the-news)
else                                        -> NO_TRADE         (no payoff asymmetry)
```
Plus overrides: cliff-fragility abstention (if IRM sits within 0.05 of the 0.85/1.30 cliff and
the trade rests entirely on that read → abstain); CBR-manufactured long-block.

### 6.3 The guide-freshness gate (just added — the newest patch, and a good example of the
"keep patching" problem I want you to critique)
A washout-BUY now also requires the positive fundamentals to be **THIS-print-fresh**: ≥3
up-revisions in the last 7 days, OR an explicitly-declared this-cycle catalyst
(`guidance_fresh`). Reason: the model bought AMKR (washed + strong 30-day revisions + "guidance
raised") and it gapped −11% because the *raise was 3 months stale* and the print itself guided
Q3 down. **The honest limit: this gate is a humility filter, not a guide-cut predictor — AMKR's
guide-down was genuinely unpredictable pre-print.** I want you to judge whether this is a real
fix or a band-aid on a deeper structural flaw (see §11).

### 6.4 Conviction (calc-risk)
- **BUY** confirms = `[wash==1, fund>=0, rich>=0, dir>=0]` → **MEDIUM** if ≥3 true, else **LOW**.
- **SHORT** confirms = `[rich==-1, wash==-1, vrich==-1]` → **MEDIUM** if all 3, else **LOW**.
- **Demotions to LOW:** extreme mover (avg gap > 15%), g2_estimated, fragile, paying rich vol on
  a buy, contradicting richness reads.
- Sizing: MEDIUM = 0.75 units, LOW = 0.5 units (units are the gap-at-risk base from §5.5).

### 6.5 Expression layer
The model names the appropriate instrument — equity / **long straddle** (for a magnitude bet) /
**defined-risk put spread** (for a short) — but it **computes NO option prices** (no
Black-Scholes, no greeks). `implied_move` is an INPUT, not a modeled output. This is a stated
structural gap: the model can only bet **direction**, never **magnitude**, even when it flags
that magnitude is the real edge (the "VOL-SETUP" note).

---

## 7. HOW CONVICTION AND SECTOR ARE (AND AREN'T) HANDLED — a known weakness

- **Conviction weighting is crude and NOT predictive.** It's a count of confirming reads
  (3-of-N → MEDIUM). In the live record, MEDIUM-conviction calls are **0/3**. There is no
  evidence the tiers rank-order outcomes. I want you to design a conviction scheme that actually
  maps to hit-rate / expected value.
- **There is NO sector-specific weighting matrix.** Every name runs the same thresholds, whether
  it's a semi-cap-equipment company, a mega-cap pharma, a fintech, or a utility. But these behave
  completely differently into prints (a semi on book-to-bill vs a pharma on trial data vs a
  payments network on volumes). I want you to propose **sector-appropriate weighting matrices** —
  which factors matter more per sector, and how to encode that without exploding the parameter
  count or overfitting.

---

## 8. SOURCING, VERIFICATION, AND DATA HYGIENE

- **Web-source before fail-closed:** on a covered name with an empty/thin data feed, a second
  web venue is checked before marking a leg UNAVAILABLE (Yahoo's US revision feed is empty for
  foreign ADRs, etc.).
- **C4 cross-source reconciliation:** the judgment values are compared against a pinned-source
  "Truth" object; divergence beyond tolerance → INPUT_INVALID (fail closed). Catches
  fat-finger/hallucinated inputs.
- **C1 sanity bounds** on every numeric input.
- **Implied-move decontamination:** no listed option expiry ever sits exactly on the event, so
  the raw straddle prices the event PLUS extra days of vol. I strip it:
  `event_IM = sqrt(IM_raw² − (realized_daily_vol² × trading_days_to_expiry))`. If the only expiry
  is >~20 days out, IM is treated as unmeasurable (None). This recently prevented false
  "rich → short" reads on several mega-caps.
- **Perimeter adjustment:** for a spin-off (e.g. a company that spun off a division 3 weeks
  before its print), PED / 52-week-high / revenue-growth are all corrupted; they're adjusted to
  a constant perimeter before scoring.

---

## 9. THE LEARNING LOOP (ledger) — and why it isn't yet a real learning loop

`pre_ledger.py` (v1.5.1). Append-only, integrity-hashed.

- **Pre-registration:** before each print, the full decision + inputs are frozen with a SHA-256
  hash (no look-ahead possible).
- **Outcome:** after the open, `idio = stock_open% − etf_open%` (beta **assumed = 1** — this is
  a market-adjusted return, **NOT** an event study, no test statistic).
- **Hold-to-close SHADOW (just added):** records the same-day CLOSE move alongside the open gap,
  so both exit horizons accrue in parallel. Current reading: mean |idio| **gap 2.87% vs close
  6.90%** — i.e. the move is 2.4× bigger by the close than at the open the model exits on.
- **Kill-switches (arm at n≥15):** idio-sign accuracy < 50%, any component < 50%, a saturation-
  misread rate, HIGH<MEDIUM conviction inversion. None are armed yet (n too small).
- **Override logging:** any narrative override of a mechanical signal is logged and scored.

**Why it's not yet real learning:** it *records* but does not *revise*. Thresholds are frozen by
doctrine. There is no mechanism that turns accumulated outcomes into updated weights/thresholds
in a principled, non-overfitting way. **I want you to design that mechanism** (see Questions).

---

## 10. THE HONEST TRACK RECORD

**Lifetime directional bets: 1 win in 5 (20%), below coin-flip.**

| Call | Conviction | idio GAP result | Notes |
|---|---|---|---|
| AEHR BUY | LOW | **+35%** ✅ | record bookings; the one win. On honest replay the current gate would have *blocked* it (VEL unsourced at decision time) |
| ASML SHORT | LOW | +1.7% ❌ | wrong |
| NFLX BUY | MED | −10.6% ❌ | washout-buy on undefined fundamentals |
| CLS BUY | MED | −0.34% ❌ (gap) | right thesis, but opened down then rallied +4.7% to close — exit-at-open caught the dip |
| AMKR BUY | MED | **−11.3%** ❌ | beat Q2, guided Q3 down — the model can't see the forward guide |

**The two most important empirical findings:**
1. **The model's abstentions have been better than its bets.** Its NO_TRADEs correctly avoided
   several bad longs; its actual BUYs lost. That's a damning pattern for a model whose purpose is
   to *trade*.
2. **The alpha is intraday, not overnight.** Repeatedly, the gap the model trades is tiny and the
   real move happens during the day (GLW −0.4% gap / −13.5% close; PYPL flat gap / +6.2% close).
   The model's fixed exit-at-open structurally misses this.

---

## 11. KNOWN STRUCTURAL DOUBTS (be harsh here)

- **Pre-print directional betting may be structurally unwinnable.** The single biggest price
  driver — the forward **guidance** delivered *in* the print — is unknowable beforehand. AMKR and
  CLS were near-identical on every input the model can see and went opposite ways purely on the
  guide. If the deciding variable is unobservable pre-print, does a directional model have any
  edge at all?
- **Maybe it should be a MAGNITUDE (straddle) engine, not a direction engine.** The model keeps
  flagging "magnitude edge > direction edge → a long straddle captures the move direction-free"
  and then can't act (no options pricing). AMKR: a straddle would have *won* (big move either
  way); the directional buy lost. Is direction the wrong bet entirely?
- **The fail-closed / anti-overfit doctrine may be a rationalization for never committing.** For a
  high-risk operator, is "abstain on any uncertainty" the right default, or should the model bet
  more and size to conviction?
- **The builder keeps patching symptoms, not root causes.** FUND gate → freshness gate → next
  patch. Each fix is locally defensible; the win-rate hasn't moved. This is the pattern I most
  want broken.

---

## 12. THE QUESTIONS I NEED YOU TO ANSWER (prioritized)

**Q1 — DECISIVENESS / RISK APPETITE (highest priority).** I am a calculated high-risk taker and
this model hides in NO_TRADE. Redesign the decision posture so it makes **full, sized, decisive
calls** when there is a logical reason, without becoming reckless. Specifically: how do I convert
"uncertain → abstain" into "uncertain → smaller position / defined-risk expression"? How should
risk be weighed and sized for someone who will happily risk a lot on a well-reasoned read? Give
me a concrete sizing-to-conviction framework.

**Q2 — THE BUY / SELL / NO_TRADE LOGIC.** Critique and redesign what determines each verdict. Is
the washout-BUY / sell-the-news-SHORT / else-NO_TRADE tree sound? Where is it wrong? What would a
better decision boundary look like? Is the worst-case-band abstention mechanism (§5.2) sensible
or is it the core disease?

**Q3 — CONVICTION WEIGHTING.** Design a conviction scheme that actually predicts outcomes
(current MEDIUM = 0/3). How should each conviction tier be defined, weighted, and sized?

**Q4 — SECTOR MATRICES.** Propose sector-appropriate factor-weighting matrices (semis / pharma /
fintech / industrials / energy / software behave differently into prints). Which factors matter
more per sector, and how do I encode that without overfitting or blowing the parameter budget?

**Q5 — MAGNITUDE vs DIRECTION.** Should this pivot to a magnitude/straddle engine? If so, what's
the minimal viable options layer (it currently prices nothing)? If not, defend keeping direction.

**Q6 — SUSTAINABLE, CONTINUOUS LEARNING.** Design the mechanism that turns the accumulating
outcome ledger into **principled, ongoing revision** of the thresholds/weights — a living matrix
that keeps improving, WITHOUT overfitting to a tiny sample. How do I "backlog" every trade and
learn from it sustainably, so this isn't a one-off? Give me the actual update rule / cadence /
guardrails.

**Q7 — POST-MORTEM METHODOLOGY.** State the *proper* way to run a post-mortem on a losing (or
winning) trade: the exact criteria and steps that guarantee it is logical, attacks the **root
cause** rather than the symptom, and improves the model **as a whole** — so the "next bomb"
doesn't keep recurring. Right now post-mortems tend to produce one more local patch.

**Q8 — EPISTEMIC ATTITUDE.** The builder keeps *defending* each verdict. When a call is wrong,
how should it genuinely reason from "the verdict was wrong" back to "here is the true reason it
was wrong" and then to "here is the root-cause fix"? Give me a disciplined falsification/
attribution procedure that prevents motivated defending and symptom-patching.

**Q9 — CODE & ARCHITECTURE.** (You have the full Python below.) Improve the structure, the
decision framework, the data flow, and the learning loop. Point out design smells, fragilities,
and better patterns. Concrete refactors welcome.

---

## 13. APPENDIX — KEY PYTHON (faithful excerpts)

> Full files are ~600 (engine) + ~400 (calc-risk) + ~350 (ledger) lines. These are the
> load-bearing pieces; ask for any full file if you need it.

### 13.1 Sign-engine cascade (`pre_engine.py`)
```python
def _cascade(ds, ds_floor, ds_ceil, cbr, g0, gates_ok, g4_ok, m, conviction, align, cfg):
    if g0 in (None, "UNRESOLVED"):     return "NO_TRADE", "GATE_FAIL", ["G0 unresolved"]
    if g0 == "DRY_RUN":                return "DRY_RUN", None, ["G0 not T-1"]
    if not gates_ok:                   return "NO_TRADE", "GATE_FAIL", ["hard gate fail"]
    if ds >= T_BUY and cbr == "CLEAN":
        if ds_floor < T_BUY:           return "INCOMPLETE", None, ["worst-case floor < +3"]
        return "BUY", None, []
    if ds >= T_BUY and cbr != "CLEAN": return "NO_TRADE", "LONG_BLOCKED", ["CBR MANUFACTURED"]
    if ds <= T_SHORT and g4_ok:
        if ds_ceil > T_SHORT:          return "INCOMPLETE", None, ["worst-case ceil > -3"]
        return "SHORT", None, []
    if ds <= T_SHORT and not g4_ok:    return "NO_TRADE", "SHORT_BLOCKED", ["borrow"]
    if ds_floor <= T_SHORT or ds_ceil >= T_BUY:
        return "INCOMPLETE", None, ["unavailable inputs could reach the band"]
    return "NO_TRADE", "LOW_CONVICTION", ["DS inside (-3,+3)"]
```

### 13.2 Calc-risk decision tree (`pre_calcrisk.py`)
```python
# reads: irm/rich (gap-space), vrich (vol-space), wash, fund (sign of REV+GG+VEL),
#        fund_defined (>=2 legs verified), fund_fresh (this-print-fresh), dir_, fragile
if gate_fail:                                   stance = "NO_TRADE"          # timing/liquidity
elif wash >= 1 and fund_defined and fund < 0:   stance, asym = "NO_TRADE","TRAP"
elif wash >= 1 and not fund_defined:            stance = "NO_TRADE"          # <2 verified legs
elif wash >= 1 and fund >= 0 and not fund_fresh:stance = "NO_TRADE"          # guide-freshness gate
elif wash >= 1 and fund >= 0:                   stance, asym = "BUY","POSITIVE"
elif rich <= -1 and wash <= 0:                  stance, asym = "SHORT","NEGATIVE"  # sell-the-news
else:                                           stance = "NO_TRADE"          # no asymmetry

if stance == "SHORT" and fragile:               stance = "NO_TRADE"          # cliff abstention
if stance == "BUY" and CBR != "CLEAN":          stance = "NO_TRADE"          # long-block

# conviction
if stance == "BUY":   confirms = [wash==1, fund>=0, rich>=0, dir_>=0]; need = 3
elif stance == "SHORT": confirms = [rich==-1, wash==-1, vrich==-1];    need = 3
conv = "MEDIUM" if sum(confirms) >= need else "LOW"
# demote to LOW on: extreme mover, g2_estimated, fragile, paying rich vol on a buy,
#                   contradicting richness reads
```

### 13.3 Component scoring + worst-case band (`pre_engine.py`)
```python
def score_rev(up, down, cov):
    if not cov or up is None or down is None: return 0, "UNAVAILABLE"
    R = (up - down) / cov
    return (2 if R>=.30 else 1 if R>=.10 else 0 if R>-.10 else -1 if R>-.30 else -2), "OK"

# SAT = clamp(a + b): a = saturation/vacuum (REV-gated), b = 52-week falling-knife guard (+1
#   only if REV>=0). DS = REV+GG+VEL+SAT+REACT+FLAG.
# worst-case band: each UNAVAILABLE input swung across its range -> DS_floor, DS_ceil.
#   BUY needs DS_floor >= +3; SHORT needs DS_ceil <= -3; else INCOMPLETE.
```

### 13.4 Sizing (`pre_engine.py` / `pre_calcrisk.py`)
```python
base_units  = (RISK_BUDGET * capital) / ((avg_abs_open/100.0) * price)   # RISK_BUDGET = 0.5%
units       = {"MEDIUM":0.75, "LOW":0.5, "NONE":0.0}[conviction]
if macro_overlap: units *= 0.5
if vol_hot:       units *= 0.5
shares      = floor(base_units * units)
gap_at_risk = shares * price * (avg_abs_open/100.0)     # $ lost on a one-avg-gap adverse move
```

### 13.5 Learning ledger (`pre_ledger.py`)
```python
idio_open  = stock_open_pct - etf_open_pct         # beta assumed = 1 (NOT an event study)
idio_close = stock_close_pct - etf_close_pct        # hold-to-close SHADOW (both horizons accrue)
correct    = (sign(idio_open) == predicted_sign)    # per trade
# kill-switches arm at n>=15: idio-sign<50%, component<50%, HIGH<MEDIUM inversion, saturation-misread
# thresholds are FROZEN — there is currently NO automated revision rule. (Design one — Q6.)
```

---

## 14. WHAT I NEED BACK FROM YOU (your deliverable)

1. **A blunt verdict:** does this model have any edge, or is the premise (pre-print directional
   betting on an 18-hour overnight gap) broken? If broken, what should it become?
2. **A redesigned decision + conviction + sizing framework** answering Q1–Q3 concretely, tuned
   for a **calculated high-risk operator** (not a cash-hugger).
3. **Sector weighting matrices** (Q4) I can actually implement.
4. **A ruling on magnitude vs direction** (Q5), with the minimal options layer if you say pivot.
5. **A sustainable continuous-learning mechanism** (Q6): the exact update rule, cadence, and
   anti-overfit guardrails that turn the ledger into ongoing improvement.
6. **A post-mortem SOP** (Q7) and an **epistemic/falsification procedure** (Q8) that kill the
   symptom-patching loop.
7. **Concrete code/architecture improvements** (Q9).
8. Rank your recommendations by expected impact, and flag which are safe to ship immediately vs
   which need forward validation.

Assume I will act on strong recommendations. Be specific, be adversarial, show your reasoning,
and do not defer to the model's existing choices. If the honest answer is "scrap it and do X,"
say that.
