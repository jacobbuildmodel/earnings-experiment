# PRE — METHOD
### The complete pre-earnings method, written to be audited by someone who did not build it.
**Version:** engine v1.5.6 · edge-score v1.5.0 · forecast v1.0.0 · errors v1.0.0 · dossier v1.0.0
**Tests:** 485 assertions, 11 suites, all passing · **Written:** 2026-08-09

> **READ THIS PARAGRAPH BEFORE ANY OTHER.** This model is **losing money**, and until 2026-08-09 it
> had no statistic capable of saying so.
>
> ```
> CLEAN RECORD (void rows now excluded IN THE DATA, computed by pre_ledger.stats)
>   n = 11 trades over 5 event-days      hit rate 4/11 = 36.4%
>   avg win +10.51%   avg loss -7.79%    payoff ratio 1.35
>   EXPECTANCY  -1.13% per trade         cumulative idio  -12.47%   (before slippage)
> ```
> Every number this document previously quoted about itself — "5/15", "8/14", "44% excluding
> coinflips" — was a **sign** statistic, and a sign statistic cannot distinguish a good system from a
> dead one. 5/15 at a 3:1 payoff is a fine model; 5/15 at 1.18:1 is not. The kill switch inherited
> the same blindness: `idio-sign < 50% -> PAUSE` fires on a profitable model and stays silent on an
> unprofitable one. Expectancy was computable from these same rows the entire time and was never
> computed. **That omission, not any threshold, is the most serious defect this document has ever
> disclosed.** Shorts are 1-for-5; the forecast layer is 8/14 raw — but see §14.10, that sample
> spans **two event-days**. The 31-event backtest in HANDOFF §20 is **contaminated**
> — the layer post-dates its own outcomes — and may not be cited as evidence. Two entries in the
> record are void: the 2026-07-29 batch of 8 (scored after its own prints) and AMKR (registered
> after its outcome was known). **This document describes a method under construction, not a
> validated edge.**
>
> An earlier draft ended this section: *"the question worth answering is whether the method is sound
> and improvable, not whether it currently wins."* **That was a smuggle and it is withdrawn**
> (external review #3). Everything is improvable; a coin flip is improvable. The question an evaluator
> should hold is **whether the apparatus is proportionate to the evidence** — and it is not, by more
> than an order of magnitude. Twelve modules, 436 assertions, a parameter registry and a four-limb
> proof obligation, wrapped around **two** signals, one of which is analyst opinion, betting a
> near-constant 0.39–0.50%, with negative measured expectancy.

---

## 0. WHAT THIS MODEL IS, AND WHAT IT IS NOT

PRE forecasts the **direction of the opening gap after an earnings print**, and decides whether that
forecast is worth capital. The bet is held for **one open**: enter at the last close before the
print, exit at the first open after it.

**It is not a valuation model and it is not an investment process.** A name can be a perfect PRE
trade and a terrible thing to own. That distinction is load-bearing for the handoff in §9 — routing
a gap-capture artifact into the portfolio as a buy idea is a category error the system is explicitly
built to prevent.

### The two layers, and why they are separate
This is the model's most important structural decision.

| layer | question | may it abstain? | log | graded on |
|---|---|---|---|---|
| **FORECAST** `pre_forecast.py` | *what do I think will happen?* | **NEVER** | `forecasts.jsonl` | **every event** |
| **TRADE** `pre_edgescore.py` | *should I put money on it?* | yes | `ledger.jsonl` | trades only |

One output was answering two questions. Whenever the *bet* was unjustified, the *prediction*
vanished with it — on 2026-07-29 the stack produced 7 NO_TRADEs across a night spanning −20.0% to
+19.3% idio, and learned nothing from any of them. A prediction never made is never scored, and a
model whose predictions are never scored cannot improve. The trade gates were left exactly as they
were (they protect capital); the forecast layer runs alongside and is graded unconditionally.

---

## 1. THE PIPELINE, END TO END

```
                       ┌─────────────────────────────────────────┐
  T-1, before the      │ 0. DOSSIER READ    pre_dossier.py brief  │  what do we already
  print                │    ERROR BOARD     pre_errors.py board   │  know about this name?
                       └────────────────────┬────────────────────┘
                                            ↓
   ┌────────────────────────────────────────────────────────────────────┐
   │ 1. INPUT SOURCING — all primary-source, all fail-closed            │
   │    REV  analyst revisions (30d up/down/coverage)                   │
   │    GG   company guidance      pre_guidance.py + pre_edgar.py (SEC) │
   │    VEL  forward-book velocity pre_vel.py (SEC XBRL RPO) AUTOMATED  │
   │    SAT  price vs sector ETF + 52-week position                     │
   │    IRM  implied move          pre_impliedmove.py (fail-closed)     │
   └────────────────────┬───────────────────────────────────────────────┘
                        ↓
   ┌────────────────────────────────────┐   ┌──────────────────────────────┐
   │ 2a. SEALED CORE  pre_engine.py     │   │ 2b. FORECAST  pre_forecast   │
   │     integer buckets → DS           │   │     continuous signal        │
   │     hard gates G0–G4, CBR, C1–C13  │   │     NEVER abstains           │
   └────────────────┬───────────────────┘   └──────────────┬───────────────┘
                    ↓                                      │
   ┌────────────────────────────────────┐                  │
   │ 3. PRODUCTION SCORER pre_edgescore │                  │
   │    continuous edge × confidence    │                  │
   │    → BUY / SHORT / NO_TRADE + size │                  │
   └────────────────┬───────────────────┘                  │
                    ↓                                      ↓
   ┌────────────────────────────────────────────────────────────────────┐
   │ 4. FREEZE  pre_batch.py --register → ledger.jsonl + forecasts.jsonl │
   │    integrity-hashed · CLOCK GUARD refuses after the session cutoff  │
   └────────────────────┬───────────────────────────────────────────────┘
                        ↓  THE PRINT
   ┌────────────────────────────────────────────────────────────────────┐
   │ 5. SCORE → 6. POST-MORTEM → 7. SURPRISE GATE → 8. ERROR LEDGER     │
   │                          → 9. DOSSIER → 10. ROUTE TO OTHER MODELS  │
   └────────────────────────────────────────────────────────────────────┘
```

`pre_batch.py` is the only supported entry point. Dated one-off drivers in `runs/` are immutable
history and must not be re-run or edited.

---

## 2. THE INPUTS — five legs, and only two of them currently speak

| leg | what it measures | source | range | status |
|---|---|---|---|---|
| **REV** | analyst revision momentum, `R = (up₃₀ − down₃₀) / coverage` | market data | −2 … +2 | **live** |
| **GG** | company's own forward guidance, bucketed | SEC 8-K/6-K via `pre_edgar.py` | −1 … +1 | **rarely sourced — the #1 gap** |
| **VEL** | forward-book velocity (RPO/backlog acceleration, ±400bps) | SEC XBRL, automated | −1 … +1 | live where RPO is filed |
| **SAT** | price saturation vs sector + 52-week position | market data | −2 … +2 | **removed from the score in v1.2.0** |
| **REACT** | historical reaction pattern | market data | −1 … +1 | **excluded from DS by default (C10)** |
| **FLAG** | integrity penalties, subtract-only | engine | −2 … 0 | live |

### 🔴 The honest consequence, stated rather than hidden
With GG unsourced on most names and SAT/REACT out of the sum, the fundamental read reduces to
**`expectations = REV / 4`** — analyst revisions and nothing else. **This model has exactly two
independent signals: expectations momentum and price positioning.** Two is a fine number. Claiming
five was the problem.

**Sourcing GG is therefore the single highest-value unblocking action available**, because it is the
only proposed directional term that is *company-reported, knowable pre-print, and not analyst
opinion*. Everything else is either a derivative of price or a derivative of sell-side sentiment.

### What was deliberately removed, and why — each is a category error, not a sample result
| removed | version | reason |
|---|---|---|
| **`value`** (IRM-based) | v1.1.0 | Option richness forecasts the **magnitude** of a move and carries **no information about its sign**. Wiring "cheap → long / rich → short" was a variance estimate used as a direction estimate. GLW (IRM 0.68) and NVTS (0.47) both moved hard — right as variance forecasts, wrong as direction forecasts. Weight cut 0.30 → **0.00**. |
| **`SAT` from the fundamental sum** | v1.2.0 | (a) SAT measures **price**, not the business — it never belonged in a fundamental term. (b) SAT and `wash` are computed from the **same two raw inputs**; measured on the ledger `corr(SAT, wash) = +0.69`, same sign or both zero on 16/21 entries. "This stock is beaten down" was being priced **twice**, and accounted for a **mean 92% / median 56% of \|raw_edge\|**. The model was, in substance, *"buy beaten-down stocks into earnings"* while presenting itself as a multi-factor score. |
| **`vrich`** | v1.2.0 | Same category error as `value`; populated on 4 of 21 entries, so mostly a no-op that occasionally injected an unjustified directional opinion. |
| **sector weights** | v1.3.0 | See §5. 18 invented numbers that changed **zero verdicts out of 21**. |

**This is the model's most credible feature and an evaluator should weigh it as such:** every removal
above deleted a term that was making the score *look* richer while contributing nothing or worse.

---

## 3. THE SEALED CORE — hard gates and the discrete cascade

`DS = REV + GG + VEL + SAT + REACT + FLAG`, integers only, equal-weight buckets. **True bound is
[−9, +7]**, not the "≈[−6,+6]" the original disclosure claimed — the asymmetry is larger than
documented, because FLAG is subtract-only.

### The gates. These are SAFETY, not edge. They are binary and they are sealed.
| gate | test | why |
|---|---|---|
| **G0** | is it actually T−1? `CONFIRMED / DRY_RUN / UNRESOLVED` | a batch scored after its own print is a counterfactual |
| **G1** | 20d dollar volume ≥ **$25M** and position ≤ **1%** of ADV | you cannot exit a gap trade you cannot trade out of |
| **G2** | avg \|open gap\| ≥ **2%** and ≥ **4** confirmed quarters | no gap history, no gap edge; estimated history demotes |
| **G3** | macro overlap (Fed/CPI same session) | a damper, not a block |
| **G4** | borrow available and fee ≤ **5%** — shorts only | an unborrowable short is not a trade |
| **CBR** | `MANUFACTURED` → **longs blocked** | manufactured beats |
| **C1–C13** | sanity bounds, cross-source reconciliation, sourcing discipline, feed integrity | see §4 |

### The cascade — §14.C, first match wins
```
G0 unresolved                              → NO_TRADE (GATE_FAIL)
G0 == DRY_RUN                              → DRY_RUN
any hard gate fails                        → NO_TRADE (GATE_FAIL)
DS ≥ +3 and CBR CLEAN and DS_floor ≥ +3    → BUY
DS ≥ +3 and CBR MANUFACTURED               → NO_TRADE (LONG_BLOCKED)
DS ≤ −3 and borrow ok and DS_ceil ≤ −3     → SHORT
DS ≤ −3 and borrow not ok                  → NO_TRADE (SHORT_BLOCKED)
unavailable inputs could still reach ±3    → INCOMPLETE
otherwise                                  → NO_TRADE (LOW_CONVICTION)
```

**`DS_floor` / `DS_ceil` are the worst-case band.** Every input that is missing — or that the caller
declared LOW confidence (C5) — is swung to its worst value. **A verdict must survive its own worst
case.** This is why "the model is uncertain" produces abstention rather than a smaller number: an
unknown is treated as adversarial, not as zero.

---

## 4. THE PRODUCTION SCORER — what actually decides a trade

`pre_edgescore.py` is what runs. The sealed core supplies components and gates; the scorer converts
them to a continuous edge.

```
expectations = clamp( (REV + GG + VEL + FLAG) / 4 ,  −1, +1 )
value        = 0                              # weight zero, retained only in the log
positioning  = +1 if WASHED, −1 if EXTENDED, else 0
               WASHED   := excess ≤ −15 pts vs sector ETF  AND  ≥20% below 52w high
               EXTENDED := excess ≥ +15 pts vs sector ETF

completeness = fraction of {REV, GG, VEL, WASH} actually verified
confidence   = 0.55 + 0.45 × completeness            # 0.55 … 1.00

raw_edge     = 0.71 × expectations + 0.00 × value + 0.29 × positioning
edge_score   = raw_edge × confidence
```

### 🔴 THE UNITS DEFECT — the published weighting is not the actual weighting
**Found by external review #3, 2026-08-09; reproduced in code (`verify_claims.py`).**

`0.71 / 0.29` reads as *fundamentals dominate positioning*. It does not mean that, because the two
terms have **different realized ranges**:

| term | realized range | weight | contribution per unit of information |
|---|---|---|---|
| `expectations` = REV/4 (GG, VEL unsourced) | **[−0.5, +0.5]** | 0.71 | one REV notch = **0.1775** |
| `positioning` | **{−1, 0, +1}** | 0.29 | the washout flag = **0.2900** |

**The washout flag is worth 1.63 notches of analyst revisions.** Per notch the realized weighting is
~0.355 vs 0.29 — near parity, tilted the *other way* from the published split.

Run through the real `edge_score()` at `confidence = 0.775`:

| case | edge | verdict |
|---|---|---|
| WASHED, REV = 0 | **+0.225** | BUY, STANDARD |
| not washed, REV = +1 | +0.138 | BUY, EXPLORATORY |
| **WASHED, REV = −1 (deteriorating)** | **+0.087** | **BUY** ⬅ clears the 0.08 bar |

**So the system §2 claims to have dismantled was not dismantled.** Cutting SAT removed the
*double-count*; it did not remove the *dominance*. A beaten-down name with worsening revisions is
still a buy, and `WASHED/HIGH_MOVE` is the regime running ~6/15.

**And it is the same defect class §5 takes a victory lap on.** The sector weights were broken because
the normaliser was calibrated for a different weight-sum. **That identical normalisation bug is live
in the production scorer right now** — §14.3 filed the 0.71/0.29 split under "un-audited thresholds",
which is a tuning frame. It is not a tuning question. **It is a units question.**

Second consequence: max `|edge|` on a REV-only name = `0.645 × 0.775 = 0.4999 < 0.55`. **MAXIMUM
conviction is unreachable by construction** on any name without GG or VEL — the whole
pharma/financial/consumer universe. "1 HIGH call ever, 0-for-1" needs no market explanation; the
range is clipped. With GG and VEL verified the same read scores 1.000 and reaches MAXIMUM, so the
ceiling is a **sourcing** ceiling, not a market one.

### The verdict thresholds — exact
| outcome | condition |
|---|---|
| **NO_TRADE** | any hard gate failed, **or** `\|edge\| < 0.08` (the dead-band — genuinely no read) |
| **BUY** | `edge ≥ +0.08` and CBR CLEAN |
| **NO_TRADE** | `−0.20 < edge < −0.08` — bearish but inside the **asymmetric short band** |
| **SHORT** | `edge ≤ −0.20` **and** `expectations < 0` **and** the name is **not** already washed |

**Why the short bar is higher (0.20 vs 0.08).** Equities carry positive unconditional drift *plus* a
positive average abnormal return around earnings announcements. A short fights the base rate and must
clear a higher bar. The two extra conditions exist because of a real defect: **both shorts in the
model's entire history (ASML, INTC) were taken against a POSITIVE fundamental read** — the score was
dragged negative purely by the `value` term, which cannot forecast sign. Shorting your own bullish
view was structurally possible and is now impossible.

### Conviction — and the fact that it does not size
| tier | `\|edge\|` ≥ | nominal budget |
|---|---|---|
| MAXIMUM | 0.55 | 1.50% |
| HIGH | 0.35 | 1.00% |
| STANDARD | 0.20 | 0.60% |
| EXPLORATORY | 0.08 | 0.25% |

**`SIZE_BY_CONVICTION = False`.** The ladder is **logged and reported but does not size anything.**
Actual budget is `0.50% × confidence`.

> 🔴 **CORRECTED 2026-08-09 (review #3, verified in code).** This previously read "→ 0.275%–0.50%".
> **That range is unreachable.** The 0.275% floor needs `completeness = 0`, i.e. neither REV nor the
> washout term available — a state with no signal at all, which yields `edge = 0` and therefore
> `NO_TRADE`. REV and WASH are present on essentially every covered name, so completeness ≥ 0.50 and
> the **real trading range is 0.388%–0.500%: a 1.29× spread.**
>
> The live consequence is larger than the arithmetic error. Conviction does not size, and confidence
> varies by 29%. **This is a flat-bet system**, and the entire sizing apparatus is scaffolding around
> a parameter that barely moves.

This distinction is the one most often got wrong, including once inside this model as a live bug:

> **CONVICTION** = `\|edge\|` = *how strong is my read.* Unvalidated → **must not scale risk.**
> **CONFIDENCE** = information completeness = *how much do I actually know.* Sizing down on thin
> information is **risk hygiene**, not a bet on a signal — so it *does* scale size.

An earlier justification for switching sizing off cited a tier-vs-return table showing conviction
"perfectly inverted." **That table was invalid** — it dropped 3 of 11 outcomes through a de-dup
mismatch and the dropped rows were both tails; its only MAXIMUM-tier trade was the retro-registered
AMKR; and the tier label was as hindsight-contaminated as the P&L it was being tested against. The
switch stays off anyway, on a **prior that needs no backtest: an unvalidated signal must not scale
risk.**

**Dampers demote one tier each** (they no longer halve size): macro overlap · hot vol
(VIX > 28, or SPY 5d realised vol WoW > 50%, or \|SPX day\| > 1.5%) · estimated gap history.

### Sizing — "sizing is the stop"
```
risk_per_share = (gap_bad_case / 100) × price          # the BAD case, never the mean
shares         = (budget × capital) / risk_per_share
```
**The denominator is the worst gap of the name's last ~10 prints.** Sizing off the *mean* made the
stated risk budget mean *"the loss on a typical print"*, so every worse-than-typical print breached
it, and the breach scaled with the surprise. KLAC has a 3.03% mean gap, so a "0.5% risk" trade bought
$2,479 of it (13.8% of an $18k book); it moved 8% and lost ~2.6× its budget. The mean also **mis-ranks
names**: it sizes *up* the quiet ones, where a surprise is proportionally most damaging. KLAC's gap
history is bimodal — [8.6, 7.1, 2.8, 2.6, 2.2, 2.0] — and both the mean and the p80 sit in the quiet
mode and miss the loud one entirely.

**Concentration is REPORTED, never capped** (owner directive: no portfolio caps in this model).

---

## 5. 🔴 SECTORS — THE HONEST ANSWER

**There is no sector-specific metric set in this model. Every sector is scored with the same four
legs.** This is the largest gap between what the method looks like from outside and what it is.

Sector enters in exactly **three** places, none of them a differentiated metric:
1. **The benchmark ETF** used to strip beta from the outcome (`idio = stock_open − β × etf_open`).
2. **`excess` = stock % since last earnings − sector ETF % over the same window** — this feeds the
   washout/extension positioning term and the regime label. Sector here is a *yardstick*, not a factor.
3. **A log label**, so results can be sliced by sector afterwards.

### Why sector weights were removed — and what would have to be true to bring them back
`SECTOR_WEIGHTS` existed as 18 numbers (24 before SAT was cut) claiming that, say, VEL matters more in
semis than in pharma. Tested against **every entry in the ledger, weighting changed ZERO verdicts out
of 21** versus flat weights. They were 18 unvalidated parameters purchasing no decision. They also
**cannot** be validated: ~21 events over 6 sectors will never fit a per-sector weight. They survive as
an identity map purely so the label keeps flowing into the log.

A second, subtler defect they had: as written they changed not only *which factor mattered* but *how
loud the sector was*, because the normaliser was calibrated for the default weight-sum. An identical
maxed-out read scored 1.00 in SEMIS but 0.55 in PHARMA — pharma and energy could **never** reach the
top tiers regardless of fundamentals, while semis silently clipped and threw away real signal at the
top. That was fixed by gain-normalisation before the weights were cut entirely.

### The sector differentiation that WOULD be legitimate — proposed, not built
The right axis is not *weights*, it is **which KPI populates a leg**. That is a mechanism claim and it
survives the standard the weights failed:

| sector | what VEL should read | why the generic version fails |
|---|---|---|
| **semis / equipment** | bookings, book-to-bill, RPO | trailing revenue **inverts** on a name ramping a new end-market |
| **software / SaaS** | RPO, cRPO, net revenue retention | revenue is a lagging echo of bookings already contracted |
| **pharma / biotech** | trial readout calendar, PDUFA dates | **there is no forward book at all** — the entire leg is undefined |
| **industrial** | backlog, orders | same as semis but slower-turning |
| **financial** | NIM trajectory, provision build, NPL formation | no "book" in the RPO sense; credit quality is the forward variable |

**This is already half-implemented and no one has said so plainly.** C12 forward-sourcing rejects a
`TRAILING_REVENUE` basis on an order-driven name — that *is* a sector-specific rule, expressed as a
sourcing constraint rather than a weight. Extending it is the honest path: **differentiate what gets
measured, never how loudly it is counted.**

**Open question for the evaluator, stated as the model's own uncertainty:** for pharma, financials and
consumer names, VEL is not merely unsourced — it is **undefined**. On those names the model runs on
REV alone, at `confidence = 0.55 + 0.45 × 0.5 ≈ 0.78` at best. Whether the model should *decline to
cover* sectors where its forward leg has no referent is an unresolved design question, and arguably
the most important one in this document.

---

## 6. THE FORECAST LAYER — the call that is always made

Runs alongside the trade layer, feeds nothing into it, and is graded on every event.

```
positioning_c = clamp( −excess / 15 , −1, +1 )      # CONTINUOUS, not the ±15 step
                halved if the name is < 20% off its 52-week high
flow          = +0.5  if put/call OI ≥ 2.0          # crowded puts → upside on a miss of the fear
                −0.25 if put/call OI ≤ 0.5          # call-crowded
                +0.5  if short interest ≥ 10% of float
signal        = 0.55 × expectations + 0.35 × positioning_c + 0.10 × flow
direction     = UP if signal > 0, DOWN if signal < 0, UP if exactly 0 (labelled COINFLIP)
```

**The continuous positioning term exists because of a measured failure:** the trade layer's ±15 step
scored LRCX (−10.1) and ARM (+13.8) as exactly **zero** on 2026-07-29. Both were most of the way to
the bar; both then moved **+19.3%** and **+8.2%**. A forecast has no reason to discard that distance.

| conviction | `\|signal\|` ≥ | | basis | `\|signal\|` ≥ |
|---|---|---|---|---|
| HIGH | 0.50 | | EVIDENCED | 0.25 |
| MEDIUM | 0.25 | | WEAK | 0.10 |
| LOW | 0.10 | | COINFLIP | below that |
| COINFLIP | 0.00 | | | |

**`basis` is an honesty field.** A call with no information is labelled COINFLIP and the direction
defaults to UP — the base rate, because equities drift up and earnings carry a positive average
abnormal return. A coinflip dressed as a view is how a scorecard gets flattered.

**Regime** = `{WASHED ≤−15 / SOFT ≤−5 / NEUTRAL / FIRM ≥+5 / EXTENDED ≥+15}` × `{HIGH_MOVE if
expected ≥5%, else LOW_MOVE}`. The regime label is what makes the log answerable: *"when does a name
gap hard, and which way?"* becomes a question the accumulated record can address.

### 🔴 What the first clean grading of this layer found — and it points the wrong way
```
overall             57.1%  (8/14)     vs a ~51.6% base rate
EXCLUDING COINFLIP  44.4%  (9)        ← WORSE THAN GUESSING
by conviction:  COINFLIP 80.0% (5) | MEDIUM 50.0% (6) | LOW 50.0% (2) | HIGH 0.0% (1)
by basis:       COINFLIP 80.0% (5) | WEAK 50.0% (2)   | EVIDENCED 42.9% (7)
regime WASHED/HIGH_MOVE: 33.3% (3)  →  ~6/15 lifetime on the model's core idea
```
**The 57% is carried entirely by the calls the model labelled as having NO BASIS.** Every call it
claimed evidence for did worse than a coin flip, and the single HIGH-conviction call was wrong.

An earlier note claimed the opposite gradient on n=8 (*"EVIDENCED 2/3 … the gradient is the right
shape"*). **On the fuller sample it inverted.** That is exactly why n=8 was never evidence, and it is
recorded here rather than quietly dropped. **n=14 is not a refutation. It is also not nothing.**

---

## 7. THE POST-MORTEM — how a result becomes knowledge

`docs/POSTMORTEM_SOP.md` is **binding** and runs on **every closed trade, wins included.**

### Why it exists, stated in its own words
> The model's builder also grades the model. Left unchecked that produces a predictable pathology:
> every loss gets explained, every explanation becomes a new gate, the gates accumulate, and the
> win-rate doesn't move. Between 2026-07-14 and 2026-07-28 exactly that happened — FUND-verified gate
> → guide-freshness gate → and the record went 1-for-5.

### The six steps
1. **State the outcome with no adjectives.** Banned words: *unlucky, unfortunately, despite, should
   have, obviously, just*. Numbers only.
2. **Name the deciding variable** — what *actually* moved the stock, not what you predicted would.
3. **Classify the failure type, before proposing any fix.**
4. **Apply only the response that type permits.**
5. **THE ABSTRACTION TEST** — mandatory on every proposed fix.
6. **Record** outcome, deciding variable, type, response, test result. **No type = no fix.**

| type | definition | fixable? | permitted response |
|---|---|---|---|
| **A** observable miss | the signal existed pre-print; we ignored, mis-sourced or mis-scored it | **yes** | fix the input or the scoring |
| **B** unobservable | the deciding variable did not exist in the pre-print observation space | **no** | **PATCHING FORBIDDEN.** Change the bet *type* or accept the variance |
| **C** right thesis, wrong expression | direction was right; exit or instrument captured it wrong | **yes** | fix the expression/exit — **never** the signal |
| **D** random | move inside the name's normal earnings distribution | **no** | log it; any patch here is overfitting by definition |

### THE INVERSION — the clause a self-grading builder will otherwise skip
> **When a call is wrong, the FIRST hypothesis is "the model is wrong." You must DISPROVE that before
> you are allowed to conclude "unlucky."**

To discharge the burden you must **positively demonstrate** Type B, C, or D. Absent one of those, the
default conclusion is *the model is wrong, and the root cause is named*. **The burden of proof sits on
the model, not on the critic.**

### THE ABSTRACTION TEST — both limbs, or it does not ship
> **Limb 1** — would this fix have prevented the **last failure of the same type**? If no, it is a
> symptom patch.
> **Limb 2** — does this fix break any previously **winning** trade? If yes, it is overfitting to the
> latest loss.

**Worked example — the fix this test killed.** The guide-freshness gate: Limb 1, would it have
prevented AMKR? **No** — that was Type B, unobservable. Limb 2, does it break a winner? **Yes** — it
blocks AEHR (+35%), whose bookings were revealed *in* the print, so nothing fresh was declarable at
T−1. **Failed both. Reverted one day after shipping.**

**Anti-gaming clause.** You may **not** rescue a fix by asserting a favourable input. This is in the
SOP because it happened: `guidance_fresh=True` was set on AEHR to keep the suite green, with a comment
justifying it. That is fabricating evidence to protect a patch. **If a fix survives only on an input
you chose to make it survive, it has failed.**

### Attribution, not P&L
| question | if yes |
|---|---|
| did it move for the reason I predicted? | thesis **confirmed** — even if P&L was negative |
| did it move for a **different** reason? | thesis **wrong** — even if P&L was positive |
| was the move inside the normal distribution? | Type **D** — no evidence either way |

> **A winning trade can be a wrong thesis. A losing trade can be a right thesis.** P&L is not truth;
> attribution is.

### Fact-checking discipline
- **Filed data beats coverage of filed data, always.** GAAP comes from
  `data.sec.gov/api/xbrl/companyconcept/CIK<10-digit>/us-gaap/<Concept>.json` with a real
  `User-Agent` header. ⚠ **Filed data LAGS the print** — an inflection can be unverifiable at exactly
  the moment it matters.
- **Score on the OPEN gap, never the close.** They diverge materially: HUM open −0.13% vs close
  −6.14%. Pre-market is not the open either.
- **Strip beta:** `idio = stock_open% − β × etf_open%`, β from a market model. A name that is more
  than **15%** of its own benchmark ETF is flagged **CIRCULAR** — the subtraction understates idio —
  and must be re-benchmarked before use.
- **Provenance ranks:** `FILED > COMPANY > MARKET > ANALYST > PROSE`.

---

## 8. 🔴 THE ERROR LEDGER — what a wrong call now costs

**New 2026-08-09.** Built on one observation, which was correct: *"when your results are wrong, you do
nothing."*

That was structural. The SOP's four branches terminated in *do nothing* three times out of four, and
the fourth ("fix it") had **no counter** — it fired on n=1 or never. **The model was simultaneously
trigger-happy and inert:** it shipped two gates off single vivid trades and went 1-for-5, while
accumulating Type B/D misses that produced no response of any kind, ever.

### The mechanism — `pre_errors.py`
Every graded event — **wins included** — writes an observation against an **error CLASS**. A class is
a **mechanism** ("washout-term-fires-on-cheap-for-a-reason"), never a ticker; tickers recur too rarely
to accumulate. Classes are slugged so two spellings cannot split a count.

**Four axes**, because a call has more than one way to be wrong:
`DIRECTION` (the sign) · `CONVICTION` (the confidence was unearned) · `MAGNITUDE` (`expected_move` off
by >2×) · `EXPRESSION` (Type C) · `PROCESS` (the run itself broke).

**CONVICTION as a first-class axis is not decoration** — the record's central finding (EVIDENCED 42.9%
vs COINFLIP 80%) is invisible to direction accuracy alone.

### The firing rule
| type | disposition | fires at | permitted response |
|---|---|---|---|
| **A · MECHANICAL** | `FIX_NOW` | **1** | fix now — a bug is not evidence, it is a bug; waiting for it to recur twice more is three known-wrong runs |
| **A · JUDGMENT** | `PEND` | **3** | propose a change; both Abstraction limbs + sign-off |
| **C** | `PEND` | **3** | fix the expression/exit only |
| **B** | `BOUNDARY` | **3** | ⛔ **never patch.** Ask the **bet-selection** question |
| **D** | `VARIANCE` | **3** | ⛔ **never patch.** Ask the **distribution** question |

The MECHANICAL/JUDGMENT split is tested by **reproducibility, not severity**: a mechanical error
produces a value wrong *against its own definition*, so anyone re-running the step gets the same
verdict without holding an opinion. A judgment error produces a value that is correct against its
definition, and the definition is what is in doubt. **A Type A observation is refused in code without
this declaration.**

**This is what ends the silence on B and D.** They still may never be patched — that protection is
intact and load-bearing. But at 3 they stop being *invisible*. "We have now lost to a forward guide on
semis on three separate nights" is not a parameter change; it is a question about whether to take that
bet at all, and it is now raised automatically instead of never.

### 🔴 THE INDEPENDENCE RULE — the part that is easy to get wrong and expensive to get wrong
**Confirmations are counted over distinct `(sector, event_date)` keys.** Three semiconductor names
printing the same night are **ONE** confirmation, not three. They share the macro tape, the sector
print, and usually the deciding variable itself.

Counting them as three would fire a permanent model change off n=1 while displaying "3/3
confirmations" — the exact laundering the SOP exists to prevent, wearing a counter. The board prints
both numbers (`3/3 independent (5 raw — clustered)`) so a cluster can never be quoted as a sample.

*This implements the owner's own reasoning: same-sector prints "build each other up" — they corroborate
a **read**. They do not multiply the **evidence**.*

### 🔴 THE LOOP MAY NOT BE ABLE TO FIRE AT ALL — two brakes that multiply
**Review #3, accepted.** Treated separately in the design, these compound:

1. **Abstraction Limb 2 vetoes any fix that breaks a previously winning trade.** With **4 winners in
   the clean record**, nearly any real logic change touches one. And the limb is **asymmetric**:
   there is a veto for breaking a winner and **no credit for repairing a loser**. A change converting
   three losses to wins and one win to a loss **fails** and is rejected. That is not overfitting
   protection — **it is a ratchet toward permanence.**
2. **The independence rule** requires 3 distinct `(sector, event_date)` keys. At ~6 event-days per
   month over ~6 sectors, a class accrues roughly one independent confirmation per sector per
   quarter. Time-to-fire for a JUDGMENT class is **on the order of a year.**

Multiply them and **the loop's cycle time exceeds the model's plausible lifetime.** The open question
is not whether 3 is the right count (§16.3) — it is **whether Limb 2 should be a veto at all at
n=11, or a DISCLOSURE**: *"this fix breaks AEHR, here is why I am taking it anyway."*

And the honest reading of §8's answer to the B/D silence: **it is still silence, with a counter.**
"Raises a bet-selection question" has **no named answerer, no evidence standard, and no resolution
state.** The diagnosis was inertia; what shipped was a logger. That is an improvement over nothing
and it is not the fix.

**Nothing ships from this module alone**
`dispose(..., "SHIPPED", ...)` is **refused in code** unless both Abstraction limbs are recorded, both
pass, and a **specific winning trade is named as checked** ("none checked" is not "none broken"). The
guide-freshness gate cannot ship through this path — that is a regression test, not a hope.

---

## 9. 🔴 THE SURPRISE GATE — a claim that must be proved

**"Unobservable" is the most abusable verdict in this system.** It is the one that ends the inquiry,
and the model grades itself. The SOP already warned that Type B "is the one that gets misclassified" —
but a warning is not a gate. So a surprise is now a **claim proved on four limbs, all recorded, all
required.**

| limb | passes only if | rationale |
|---|---|---|
| **1 · unobservable** | the deciding variable is **named specifically** (≥12 chars; "sentiment", "macro", "the guide", "positioning" are refused), you can say **where and when it first became public**, and it is **not already a model input** | an unnameable cause is an unexamined one |
| **2 · not sourceable** | it could **not** have been obtained at T−1 even in principle | obtainable-and-not-obtained is a Type **A** sourcing miss — fixable, and calling it a surprise is the excuse being guarded against |
| **3 · outside distribution** | `\|idio\|` exceeds the name's **own worst gap over its last 10 prints** (aligned with the sizing window 2026-08-09; it read 8 and sizing read 10 — same statistic, two windows) | a −6% gap on a name that gaps 6% every quarter is not a surprise, it is Tuesday. Unknown distribution → **cannot claim** |
| **4 · not recurrent** | SURPRISE has **never** been claimed before on this name/class | **the anti-excuse limb** |

**Limb 4 is the heart of it.** The second time the same thing blindsides us, it was not
unforecastable — it was a **known blind spot we declined to close**. AMKR's forward guide was
legitimately unobservable *once*. A second guide-down on the same mechanism **auto-reclassifies to
Type A / JUDGMENT** and enters the pending queue as work.

### 🔴 THE HOLE THIS GATE OPENED — Type D is now the unguarded door
**Review #3, accepted in full.** The four limbs make Type B nearly unpassable (limb 3 alone is a
~11% prior event; conjoined the pass rate is very low). **Type B is now closed. Type D is not.**

*"Move inside the name's normal earnings distribution"* has a one-line definition, **no gate, no
limbs, and the identical do-nothing terminus.** Every claim that would previously have been laundered
as "unobservable" now has an unguarded door labelled **"normal variance"** three feet to the left —
and it is the *more comfortable* claim, because it requires proving nothing at all.

**The gate belongs on the PAIR, not on B.** Until that ships, a `D` classification should be read as
an *unproven* claim, and the same limb-3 test (is the move inside the name's own last-10 gap
distribution?) is the obvious first limb for it — it is already computed. **Not shipped: it is a
LOGIC change to a component built four hours earlier, and shipping a fix to a fix inside one session
is how the guide-freshness gate happened.**

**The surprise budget.** If SURPRISE exceeds **30% of the trailing 10** graded outcomes, the model is
not unlucky — it is **betting on unobservables**, which is a bet-*selection* problem that no amount of
input work fixes. The board prints the rate and flags the breach. This gives the SOP's *"if Type B
dominates, escalate to a structural review"* an actual number, so it can fire instead of waiting for
someone to notice a pattern.

---

## 10. THE DOSSIER — why the next look is better than this one

`pre_dossier.py`. PRE had two records and **neither compounded per name**: both are event logs
optimised for scoring the *model*. Nothing was optimised for the question actually asked at T−1 of the
next print: **what do we already know about how this company behaves into earnings?**

So every quarter started from zero, and the same name could be blindsided by the same mechanism twice
with nothing noticing.

- **Read at `/pre`** (`pre_dossier.py brief <T>`), **written at `/post`**.
- Carries **no portfolio data of any kind** — only PRE's own history — so reading it inside the blind
  chat is safe **by construction**. It is the one memory the blind half is allowed.
- The **lesson** field is about the **company**, not the model ("guides Q+1 revenue with the print;
  the guide, not the quarter, sets the gap"). Model lessons are error classes and live in §8.
- **Standing notes** hold durable behavioural facts that outlive any quarter and are **not** subject
  to the retention cap.
- It **states, never recommends** — asserted by a test. Prior context must not become a channel
  through which last quarter's outcome anchors this quarter's call.

### Retention — owner rule, implemented literally
**The last 5 events per name. The sixth pushes the oldest out, automatically and permanently, on
every write.** There is no configuration knob that can quietly grow it back.

**One deliberate deviation, flagged rather than assumed:** a purged event's **counters** are folded
into a fixed-size rollup first — event count, hit count, gap sum, and the recurring deciding
variables — about 200 bytes, constant forever, versus ~2KB for full event detail. The reason is that
the file's entire purpose is to catch a mechanism that keeps recurring, and a hard delete would make a
blind spot invisible at exactly the moment it became provable: **the sixth occurrence would read as
the first.** Detail is deleted; the fact that it happened is not.

---

## 11. THE HANDOFF — what PRE sends to the other models, and how it decides

PRE is chat 1 of five. It feeds chat 2 (earnings read-through) and chat 3 (evaluation) through an
append-only inbox, `data/inbox_earnings.jsonl`, via `inbox.py`.

**Gate:** the scout runs only when the outcome is recorded **and** the position is closed or was never
opened. PRE's alpha lands intraday; a scout running post-print but pre-exit is analysing a name the
model is still being graded on.

### The routing rule — `action_hint` is a route, and a route with a default is not a route
| hint | when | consumer |
|---|---|---|
| **`EVALUATE`** | the print changed a **durable forward mechanism**, a decision needs a **score**, it plausibly clears the evaluation model's **~30%-in-6-months** bar, and there is **no current card** | chat 3, full DRIVE v3.2 Stage 0–5 — **expensive; do not spend it on a gap trade** |
| **`SIGNAL`** | the mechanism matters but **the vehicle does not** — read-through on supply, pricing, demand, a competitor | chat 2 `/earnings`. **The default for most PRE prints.** |
| **`TRACK`** | quality is real, no live decision, catalyst dated but not near | watchlist + provenance |
| **`DROP`** | evaluated and rejected | written down so the **next** look is not the first look |

**The distinction that costs money when it is got wrong:** PRE's edge is a gap-capture event lasting
one open. That is **not** a reason to own a company. **Route on the durability of the mechanism, never
on whether the trade worked.**

`action_hint` used to default to `EVALUATE`, so every row the earnings chat wrote — including pure
read-throughs about names that would never be bought — was stamped "evaluate this." The flag carried
zero information, and the two names it was supposed to escalate drowned in the noise and were never
evaluated. It is now a required enum with no default.

**Every run writes a HEARTBEAT**, even with nothing to report. Otherwise "inbox empty" is
indistinguishable from "the scout broke three weeks ago", and you train yourself to ignore it.

---

## 12. THE CONTAMINATION BOUNDARY — why this is one chat per event

```
NEW CHAT → /pre (blind) → the print → /post (portfolio-aware) → CLOSE THE CHAT
```

**What is being protected is not "a post-mortem reading a forecast."** It is **portfolio knowledge
reaching a FUTURE pre-registration.** A chat that registers X, waits for the print, grades X and stops
has **zero contamination** — X was frozen before any portfolio context entered the room. The damage
happens only if that same chat then pre-registers a **new** name with the book in its memory.

**So the rule is not "never mix." It is "never pre-register after a post-mortem."**

An earlier proposed guard — *require the run to be byte-identical with and without the portfolio
context file* — was **deleted**, because it tested **file absence** while the actual channel is the
**conversation**. A context window is persistent; everything said earlier is re-sent on every turn and
silently anchors what follows. No filesystem check can see that, which is why the boundary is the chat
and not a code guard.

**The subtler channel, and the one that actually matters at this sample size:** closing the chat
protects forecast *N*. It does **not** protect forecast *N+1*, because preference leaks through
**coverage selection** — which names get screened at all. At n=15, selection effects dominate the
record; pre-registering only the names already liked is how an honest-per-event log becomes a
dishonest aggregate. **The name list comes from the earnings calendar, never from the book.**

**The audit half.** Every registration writes `context: {portfolio_aware, sources, status}` **inside
the frozen payload**, so `integrity_hash` covers it. Stripping the declaration or forging `BLIND` onto
an aware row both break the hash. This is detection, not prevention — deliberately the same shape as
`_is_retro()`, which never *prevented* the AMKR retro-registration but made it **detectable
afterwards**. A declaration can be wrong; it cannot be quietly changed later.

**The clock guard.** `--register` is refused once the session cutoff has passed (16:00 ET AMC / 09:30
ET BMO, resolved in exchange time via `zoneinfo` so DST is handled). A batch scored after its own
print is a counterfactual, not a record — that is what voided the 2026-07-29 batch of 8.

---

## 13. GOVERNANCE — what may change, and on what evidence

| tier | definition | bar to land |
|---|---|---|
| **PLUMBING** | autonomous; re-running the full log reproduces byte-identical values *and* verdicts | none |
| **DEFECT** *(new 2026-08-09)* | a change whose **sole claim is that behaviour now matches documentation**. No edge asserted. | sign-off + **mandatory full ledger re-score disclosing every verdict that flips**. Holdouts **waived**. |
| **LOGIC** | moves any logged value or verdict | named failure case + **2 independent non-anomaly holdouts** + owner sign-off. *Exception:* a purely **conservative** change (can only turn trade → non-trade) has no edge to prove — sign-off + false-positive check, holdouts waived |
| **STRUCTURAL** | new data stream / ML / EV-skew / options / changes what is optimised | owner approval to **build** |

**Parameter ceiling = 30, registry-enforced in code.** Any new parameter must name an ablation.

### 🔴 WHY THE DEFECT TIER HAD TO EXIST — the governance problem the units bug exposed
The LOGIC tier requires a named failure case **plus 2 independent non-anomaly holdouts**. The units
fix is not purely conservative — it turns some trades into non-trades *and* promotes REV-only reads
across the 0.08 bar — so the holdout requirement bites. **And holdouts are years away** at ~6
event-days a month.

So an **arithmetic correction inherited an evidence bar designed for edge claims, and the model
became uncorrectable.** Every arithmetic bug found from here would have been permanently unfixable —
the same ratchet as Limb 2 in a different costume.

The DEFECT tier resolves it without loosening anything that matters: there is no edge to prove
because **no edge is being claimed.** What replaces the holdouts is a harder disclosure obligation —
the full flip set, published. `rescore_units.py` is the first instance: **22 of 53 verdicts flip.**

> **The DEFECT claim must be exactly this and nothing more:** *the model was doing something other
> than what it said, and a record produced by a mis-specified scorer cannot be interpreted.* The
> moment a DEFECT filing says "and this should improve the hit rate", it is a LOGIC change wearing
> the wrong tier, and the holdouts come back.

### The evidence bars — none of which have been met
| claim | bar | n required | n actual |
|---|---|---|---|
| beats 50% / the straddle, net of costs | idio-sign materially > 50% | ≥ 15 | 15 trades, **5 wins** |
| beats the trivial shadow (`REV≥+1 ∧ GG≥0 → BUY`) | several-pp margin | ≥ 15 | not run |
| a component earns its keep | standalone ≥ 50% | n_nonzero ≥ 20 | no |
| HIGH conviction is real | HIGH ≥ MEDIUM | ≥ 10 per tier | **1 HIGH call, 0-for-1** |
| learned weights | — | **≥ 100** | **do not attempt** |

**Be honest about "flip it on at n ≥ 20 per tier":** at ~15 trades in three weeks clustering to ~6
event-days, that bar is **years away and probably unreachable.** Every component must therefore earn
its place **by mechanism**, because none of them will ever get a statistical justification. That is the
standard `value`, `vrich`, `SAT`-in-directional and the sector weights all failed.

### Kill switches (auto-arm at their n-bars)
idio-sign < 50% at n ≥ 15 → **PAUSE** · a component < 50% at n_nonzero ≥ 20 → **ablate** · Type-B
> 2/10 → SAT recalibrate · HIGH < MEDIUM inversion at n_HIGH ≥ 10 → **suspend the tier**. ANOMALY
outcomes are frozen out of all tuning statistics.

### What may never change
The sealed core arithmetic, cascade, fail-closed and INCOMPLETE logic; the CBR long-block; the
falling-knife guard; the REV-gate on SAT(a); gap-at-risk sizing; equal-weight integer buckets; the ±3
band and the n=1–2 thresholds (**freeze**, do not tune). No learned weights at n ≪ 100. No continuous
scoring, no probability layer, no per-KPI VEL (+9 parameters → ceiling breach, **rejected**), and no
full historical backtest presented as validation — the judgment layer is not reconstructable at T−1
without look-ahead, so the only legitimate "backtest" is a market-data-only study of gates and sizing.

---

## 14. KNOWN WEAKNESSES — stated by the model, not extracted from it

1. **The core thesis is not holding.** `WASHED/HIGH_MOVE` — "buy the washout" — is roughly **6/15
   lifetime**. It is the regime a third of every batch lands in.
2. **The conviction gradient is inverted.** EVIDENCED 42.9% vs COINFLIP 80.0% on n=14. Un-patched by
   deliberate choice: n=14 cannot justify flipping a sign, and doing so would be the sample-chasing
   the mechanism standard exists to prevent. **It is a premise-level result awaiting an owner decision.**
3. **Un-audited thresholds**, each frozen rather than fitted, each unjustified by anything but a
   prior: `EDGE_MIN 0.08` · `CONF_FLOOR 0.55` (**never binds**) · the tier boundaries · the 0.71/0.29
   split · and **the ±15 washout bar, the prime suspect** — it silenced LRCX and ARM before +19.3% and
   +8.2% moves.
4. **GG is essentially unsourced**, so `expectations` is `REV/4` — sell-side revisions alone. The
   model's fundamental leg is currently an analyst-sentiment leg.
5. **No sector-differentiated metrics** (§5). For pharma, financials and consumer names the forward
   leg is not merely unsourced but **undefined**.
6. **Filed data lags the print.** An inflection can be unverifiable at exactly the moment it matters.
7. **Shorts are 1-for-5** and both historical shorts were structurally defective (taken against a
   positive fundamental read). The asymmetric bar addresses the mechanism; the record is unchanged.
8. **The exit horizon is unresolved, and §14.8 used to state it incoherently.** It read "alpha lands
   intraday" while the live exit *is* the open — which would make that alpha unreachable by
   definition. What is actually true: post-mortems on 2026-07-24 and 2026-07-28 found the move often
   **continued past the opening print**, so the hold-to-close shadow is instrumented in parallel and
   **has never been evaluated**. The claim belongs to the shadow, not the live expression.
9. **n is the binding constraint on everything.** 11 clean trades clustering to **5 event-days**.
   Every number in this document is a prior or an observation, and none of them is a finding.
10. **The sample is smaller than every number quoted.** By the model's own independence rule — which
    it enforces on error classes and never applied to itself — the **14 forecasts span 2 event-dates**
    and the 11 clean trades span 5. `pre_ledger.stats()` now prints `n_event_days` beside `n`. The
    "inverted conviction gradient" that PRE/STATE.md leads with is **n=2 by this model's own
    standard**, and elevating it to a research priority was self-flagellation overfitting to noise.
11. **The published weighting is not the actual weighting** (§4). A units defect, not a threshold.
12. **`SIZE_BY_CONVICTION=False` + a 1.29× confidence spread makes this a flat-bet system** — the
    sizing apparatus is scaffolding around a parameter that barely moves.
13. **Void status lived in prose, not in data, for weeks.** `ledger.jsonl` had no void field, so every
    statistic — including the "5/15" the model quoted about itself and the kill-switch dashboard —
    silently included rows the documentation called void. Fixed 2026-08-09 with an append-only
    `{"type":"void"}` row and exclusion in `stats()`. **This is the system's signature failure in its
    purest form: a fact that exists in a document and not in the data plane, with every gate green.**
14. **Execution is unmodelled.** Outcomes are scored on the official opening print, which is not a
    fill. On a name gapping 8% into an opening auction, the gap between print and achievable price is
    a real fraction of an edge measured entirely inside one print. **The clean −1.13%/trade is
    therefore an overstatement of the live record by an unknown amount.**
15. **`flow` (put/call OI, short interest) is an unvalidated narrative mechanism** inside the layer
    whose whole justification is measurement. Small weight (0.10), same species as `value` and
    `vrich`, which were both cut for exactly this.
16. **Coverage selection is identified and unmitigated.** *"The name list comes from the earnings
    calendar"* is a sentence, not a control — contrast the integrity hash on `context`, which is one.
    **Which 5 of tonight's 40 get screened is where preference re-enters, and nothing detects it.**

---

## 15. HOW TO RUN IT

```bash
# gate — must pass before anything
python run_tests.py                    # 436 assertions, 10 suites

# T-1
python pre_dossier.py brief NVDA                       # what we know about the name
python pre_errors.py board                             # what the model is known to get wrong
python pre_batch.py --tickers NVDA --event-date 2026-08-27 --session amc --gg-fetch
python pre_batch.py --tickers NVDA --event-date 2026-08-27 --session amc            # dry run
python pre_batch.py --tickers NVDA --event-date 2026-08-27 --session amc --register # FREEZE

# after the print
python pre_postmortem.py                               # realized OPEN gaps -> outcomes
python -c "from pre_forecast import score; print(score())"
python pre_errors.py board                             # what moved, what is ripe

# looking things up
python pre_ledger.py show 10 | outcomes | stats
python pre_vel.py TICKER            # forward-book velocity + its audit trail
python pre_edgar.py TICKER          # the guidance documents themselves
python pre_errors.py show <class>   # every observation in one error class
python pre_dossier.py list
```

**Canonical files:** `ledger.jsonl` (capital record, integrity-hashed, append-only) ·
`forecasts.jsonl` (prediction record — separate on purpose, so paper calls can never contaminate the
capital track record) · `errors.jsonl` (error classes) · `dossiers/<T>.json` (per-name memory) ·
`STATE.md` (where we left off) · `docs/POSTMORTEM_SOP.md` (**binding**).

---

## 16. QUESTIONS FOR THE EVALUATOR

The five that would change what gets built next:

1. **Is the inverted conviction gradient a premise failure or a sample artifact at n=14?** If the
   former, the positioning term is the prime suspect and the model's core idea is wrong.
2. **Should the model decline to cover sectors where its forward leg (VEL) has no referent** — pharma,
   financials, consumer — rather than running on REV alone at 0.78 confidence?
3. **Is 3 independent confirmations the right firing threshold**, given that at ~6 event-days per
   month a class may take a year to ripen? Is slow-and-right better than fast-and-overfit here, or is
   the model simply too small to learn at all?
4. **Is the ±15 washout bar defensible?** It silenced LRCX (−10.1) and ARM (+13.8) before +19.3% and
   +8.2% moves. The forecast layer already reads the distance continuously; the trade layer does not.
5. **Is gap-capture the right expression?** Alpha lands intraday, but AMKR shows the forward guide can
   invert a correct fundamental read inside a single open. Is a defined-risk options expression the
   honest answer, or is that just adding complexity to an unvalidated signal?

---

## 17. EXTERNAL REVIEW #3 — EVERY CLAIM RUN AGAINST THE CODE

The reviewer read this document, not the implementation, and said so: *"anything numerical below is
'the doc says X, and X implies Y' — check Y against the implementation before acting on it."*
That check is `PRE/verify_claims.py`, re-runnable, read-only, sourced from `edge_score()` and the
live ledger. **Six claims confirmed, two refuted, one new finding produced by the verification.**

| # | claim | verdict | evidence |
|---|---|---|---|
| 1 | washout ≈ 1.6 REV notches; washed + REV=−1 still BUY | ✅ **CONFIRMED** | 1.63×; edge **+0.0872** vs `EDGE_MIN` 0.08 |
| 2 | MAXIMUM unreachable on a REV-only name | ✅ **CONFIRMED** | max edge **0.4999** vs tier 0.55; reaches 1.000 with GG+VEL |
| 3 | the 0.275%–0.50% sizing range is unreachable | ✅ **CONFIRMED** | real range **0.388%–0.500%**, 1.29× |
| 4 | REV and positioning are negatively correlated → the score is a value construct in disguise | ❌ **REFUTED** | `corr(REV, positioning) = +0.026` over 53 entries; near-orthogonal. The hypothesis was reasonable and the data does not support it |
| 5 | the trivial shadow is the cheapest available evidence and is unrun | ✅ **CONFIRMED — and now run** | `REV≥+1 ∧ GG≥0` fires 11/38, **2/11 up, mean idio −4.38%** |
| 6 | there is no expectancy anywhere | ✅ **CONFIRMED** | now in `pre_ledger.stats()`: clean **−1.13%/trade, payoff 1.35** |
| 7 | "COINFLIP 80%" is the up-drift because COINFLIP defaults to UP | ❌ **REFUTED** | of 5 graded COINFLIPs, **2 UP / 3 DOWN**. `basis=COINFLIP` means \|signal\| < 0.10, **not** signal = 0; the UP default fires only at exactly zero, which never occurred. The **n=5 objection stands**; the proposed mechanism does not |
| 8 | the independence rule is not applied to the model's own stats | ✅ **CONFIRMED, worse than stated** | the 14 forecasts span **2** event-dates, not the ~5 estimated |
| — | **NEW, found while verifying:** void status existed only in prose | 🔴 | 0 void fields in `ledger.jsonl`; 5 rows retro-detectable by timestamp. Every quoted statistic included them |

### The finding that outranks the rest
**Claim 5 is the one to sit with.** The trivial shadow — the benchmark this model is supposed to
beat — fires on 11 events and is **2/11 with mean idio −4.38%**. The model's only surviving
fundamental signal is not merely uninformative in its own ledger; **it points the wrong way.**

That is n=11 over few event-days and is not conclusive. But combined with a measured expectancy of
−1.13%/trade, the honest summary is: **there is no evidence either signal works, and weak evidence
that one is inverted.** Neither the sign scorecard nor the kill switches could see this.

### Shipped in response (mechanical only — nothing that moves a verdict)
- `pre_ledger.stats()` now reports **expectancy, avg win/loss, payoff ratio, total idio, and
  `n_event_days`** alongside the sign statistics.
- `pre_ledger.void_entry()` / `voided()` — **append-only** void marking; `stats()` excludes voided
  rows and **reports how many it excluded**. The 19 void/retro rows are now marked in the data.
- `verify_claims.py` — this table, re-runnable.
- Documentation corrections: the sizing range, the surprise window (8 → 10, aligned with sizing), the
  incoherent §14.8, and the §0 framing sentence, withdrawn.

### 17.1 SHIPPED AFTER OWNER DECISION — v1.5.7
**1. Units: normalise by the legs actually populated.** Not a static rescale (that hard-codes the
degenerate case and breaks the day GG arrives) and not a doc restatement (that changes nothing real).
`fund_norm = sum of the RANGE of each VERIFIED leg` — self-correcting, no new parameter.
**`/4` was never arbitrary: it is the correct normaliser for three populated legs, and we run one.**
So this was never an independent bug — **it is the GG/VEL sourcing gap expressing itself as a silent
gain error.**

> **Sold honestly:** this makes REV louder in order to demote washout, and **REV has no standalone
> validation either.** It reallocates authority between two unvalidated terms. The justification is
> *not* "this improves the hit rate" — it is that a record produced by a mis-specified scorer cannot
> be interpreted. That is sufficient on its own, and it is the entire DEFECT claim.

**The mandatory re-score — `rescore_units.py`, 22 of 53 verdicts flip:**
- The two washed-with-deteriorating-revisions BUYs correctly become NO_TRADE: **MSTR** (was a -3.96%
  loss) and **TEM** (was a +5.37% win). Removing a loser and a winner — reported as **cost**, never
  as justification.
> 🔴 **AMENDMENT, and it belongs here rather than being found later.** The units fix
> **increases the authority of REV — the exact leg the trivial shadow just measured at 2/11**
> (mean idio −4.38% against a 35.5% same-day base rate). **Its expected effect on the hit rate is
> therefore plausibly NEGATIVE.** The fix is still correct: its claim is that behaviour matches
> documentation, and that claim is independent of whether REV predicts anything. But a DEFECT filing
> that stays silent about a likely degradation is **the abuse clause firing in reverse** — the
> clause bars claiming "this should improve the hit rate", and omitting a probable worsening is the
> same omission wearing the opposite sign. Appended to `errors.jsonl` as an amendment, not a rewrite.

### 🔴 THE SATURATION DEFECT — resolved as WRONG, queued not shipped
With a single ±1-range leg verified, **one notch saturates the whole term**: APLD and AZN go
HIGH → **MAXIMUM** on a lone VEL=+1.

**The "confidence separates that concern" defence does not survive arithmetic.** Dropping the norm
from 4 to 1 **inflates `expectations` 4×**. Confidence's entire live span is 0.775→1.00, a
**1.29× discount**. You cannot absorb a fourfold inflation with a 29% haircut. The concern is not
separated; it is abandoned.

**The clean statement of the defect:** normalisation answers *"how strong is this reading relative to
the instrument."* Conviction claims *"how strong is my read."* Those coincide **only when the
instrument has resolution.** VEL is 3-state. A 3-state instrument can express **direction**; it
cannot express **strength**. So MAXIMUM off one VEL notch is **an instrument limit being logged as a
signal** — the same species of error as reading a variance estimate as a direction estimate, which
is why `value` was cut.

**The harm is not cosmetic, and it is also not urgent, in that order.**
- **Not cosmetic:** conviction does not size, so no capital is exposed. What is exposed is the
  **tier-vs-outcome table** you would need to answer *"is HIGH real"* — the ladder with **one**
  observation on it. Inflated labels contaminate the only statistic that could ever validate the
  thing. **That is evidence damage, not display damage.**
- **Timing turns on one question, and it is answered:** `pre_batch.py:374` feeds
  `expectations_momentum` **straight into `pre_forecast`.** The layers share the term. So
  `forecasts.jsonl` **is** accruing inflated conviction labels right now, during the pause, on the
  one layer deliberately left running.

**SHIPPED INSTEAD — the zero-logic move that makes the correction reversible.** `fund_leg_sum`
(raw numerator), `fund_norm` (divisor used) and `verified_legs` are logged on every verdict and
persisted into the ledger row. **Adds logged values, moves nothing → PLUMBING.** Every row written
from here can have its **true tier re-derived under any future norm**, converting an irreversible
**evidence corruption** into a recoverable **labelling artifact**. Same principle as the dossier
keeping counters after deleting detail, and as detection-not-prevention on the integrity hash.
Asserted in `controls_fire_selftest.py` §7.

**QUEUED with the resume, where the ledger re-score happens anyway and every historical tier can be
re-derived under both norms in one pass. And the spec is NOT a norm change:**

> **Gate the conviction ladder on RESOLUTION: MAXIMUM and HIGH unreachable with fewer than two
> verified legs. Leave the normaliser alone — it is correct.**
>
> The score is honest (*"I maxed the only thing I measured"*); **the label is the lie.** This touches
> **no verdict** — BUY/SHORT/NO_TRADE come off `|edge|` thresholds, not tiers — so it is
> conservative-on-labels, asserts no edge, and has the smallest blast radius available. Capping the
> norm's floor at 2 would also work, but it moves **every score** to fix a **labelling** problem.

**2. Limb 2 re-aimed** — it was protecting the wrong *object*, not the wrong *strength*. It vetoed
P&L winners inside a system whose own attribution table says *"a winning trade can be a wrong
thesis."* It now protects **theses CONFIRMED by attribution**, reports the flip set **both ways**
(broken *and* repaired), and vetoes only when a change **breaks a confirmed thesis and repairs
nothing.** Unattributed winners get **disclosure, not veto** — you cannot claim protection for a
thesis you never recorded.

> **Written into the clause, because otherwise this swaps a ratchet for an overfitting machine:**
> at n=11 **the flip set IS the training set.** The net count is evidence about **cost**; it is
> **never the reason to ship.** `dispose()` refuses a SHIPPED filing with no named mechanism.

**And the finding that forced it:** `thesis_confirmed` is listed as a MANDATORY ledger field in the
SOP and has been written on **zero of 60 outcome rows.** It was not "recorded and never consulted" —
**it was never recorded.** `observe()` now carries it.

### 17.2 THE PAUSE — trade layer only, and the reason is validity, not performance
**Pausing on the sign kill-switch would mean acting on the metric just shown to be the wrong one** —
right action, wrong justification, and nothing would be learned. The reason is that **the record was
generated by a scorer nobody had correctly described**, and 22 of 53 verdicts move under the
corrected arithmetic. You cannot interpret outcomes produced by a mis-specified mechanism.

**That is a VALIDITY failure, not a performance failure** — the same species as the clock guard
voiding the 2026-07-29 batch for *process*, not results. The precedent already existed.

🔴 **The FORECAST layer is NOT paused, and must not be.** It costs nothing, it is graded
unconditionally, and stopping it is how you arrive in three months with the same n and nothing
learned. **This is the entire payoff of the two-layer split: the model can stop betting without
stopping learning.** Pause both and the split never earned anything.

**The resume gate is a gate, not a feeling** (`pre_ledger.TRADE_PAUSE`, enforced in code on *both*
registration paths — the guard was initially installed only on `pre_register()`, which is not the
route `pre_batch` uses; **a control that does not cover the live path is not a control**):
1. ✅ Units normalised by populated legs.
2. ✅ All entries re-scored under both arithmetics, flip set disclosed.
3. ⛔ **Beat the shadow AND clear positive expectancy ex-best-trade.** **NOT MET on both limbs.**

> **Why the shadow is the bar:** `REV>=+1 AND GG>=0 -> BUY` **uses no weights at all**, so it is the
> one number the units defect cannot have touched — the only clean benchmark that exists.
>
> **But 2/11 is NOT yet a bar, and the reason matters more than the gate.** 2/11 is uninterpretable
> without its base rate: if the rule runs 2/11, the inverse runs 9/11, and there are two readings —
> REV is anti-predictive, or those events sat in a tape that punished longs. **The control was free
> and is now run:**
>
> | | up | mean idio |
> |---|---|---|
> | all graded events | 17/38 = **44.7%** | −0.42% |
> | the shadow fires | 2/11 = **18.2%** | −4.38% |
> | **same event-days, all names** | 11/31 = **35.5%** | −1.56% |
>
> **The tape explains part of it** — those four days ran 35.5% against a 44.7% overall base — **and
> the shadow still sits materially below its own days.** REV plausibly picked worse than the tape.
> But 11 events over **four** event-days is n≈4 by this model's own independence rule, so it is
> suggestive and **not a refutation of REV** — the identical discipline that applies to
> COINFLIP-at-80%, pointed the other way. There a base-rate default risked being read as skill; here
> a base-rate collapse risks being read as a failed signal.
>
> **So beating 18% proves nothing, and condition 3 has two limbs.** The second exists because
> expectancy is **−1.13%, and −4.75% excluding AEHR**: that is not a model with a units problem, it
> is **a model with no edge and one lucky print** — which settles the pause far more cleanly than
> 33% ever could.

**A mild positive check worth recording:** the new switch **validated on first contact** — sign bad,
expectancy bad, both-bad → PAUSE, arrived at independently and agreeing with a decision already made
on validity grounds. Almost nothing else in this system has passed a live test.

### 17.3 KILL SWITCHES — both metrics, structurally. Never swap sign FOR expectancy.
At n~15 expectancy is dominated by one tail, so a raw-expectancy trigger gets jerked around by a
single print. Hence:

| condition | action |
|---|---|
| expectancy <= 0 **and** sign < 50% | **PAUSE** — both bad, no ambiguity |
| sign < 50% **but** expectancy > 0 | **REVIEW, never auto-pause** — the *expected* gap-capture profile (few large winners). Killing it on a sign switch is how you shut down a working strategy |
| sign >= 50% **but** expectancy <= 0 | **REVIEW** — picking up pennies, and the **more dangerous** of the two because the sign dashboard reads green all the way down |

Plus one line that answers *"is this a strategy, or is it AEHR?"*:
**expectancy `-1.13%` -> `-4.75%` excluding the single largest winner.**

### 17.5 🔴 ONE PROCESS DEFECT, THREE TIMES — and the standing rule that ends it
| # | control | how it failed |
|---|---|---|
| 1 | **void status** | recorded in prose, **no field in the data** — every statistic, including the kill-switch dashboard, counted rows the docs called void |
| 2 | **the trade pause** | installed on `pre_register()`, which **is not the function `pre_batch` calls** |
| 3 | **`thesis_confirmed`** | **mandatory in the SOP, written on 0 of 60 rows** |

**These are not three bugs. They are one defect: this system reliably builds the control and does not
wire it.** Every gate was green throughout.

**And #3 is larger than it first reads.** It does not merely leave Limb 2 with an empty protected set
— though it does, which means **the ratchet is now more fully released than intended.** It means
the SOP's **central epistemic commitment has never once been executed.** *"P&L is not truth,
attribution is"* is binding, and **every post-mortem in the record was graded on P&L.** So the A/B/C/D
classifications, the win count and the deciding-variable field were all assigned **without the input
that is supposed to drive them.**

> ## THE STANDING RULE
> **Every new control ships with a test that it FIRES on real data — not a test that it exists.**
> A test proving a guard is importable is not a test proving the guard raises. **All three defects
> above would have been caught at build time by this single rule**, at a cost of about one assertion
> per control.

Made executable as `tests/controls_fire_selftest.py` (**34 assertions**), wired into `run_tests.py`.
Adding a control to this system now means adding a case there — that is the price of the control.

One assertion was *strengthened* by the same reasoning while this shipped: the forecast/trade
separation test searched the source for the **substring** `pre_forecast`, so it broke on a comment
and **would have passed an `importlib` import**. It now walks the AST for a real import edge and
checks the runtime namespace. **Assert what the control is FOR, not that it exists.**

### 17.4 QUEUED, NOT BUILT — the Type B/D gate
Not shipping a fix-to-a-fix inside one session is the guide-freshness lesson applied. When built:

**Build ONE gate over B *and* D, not a D-gate.** They are the same claim wearing different clothes —
*"no action is warranted."* Gate them separately and the abuse migrates a third time, to **Type C**,
which is already open, already comfortable, and whose permitted response (*"fix the expression, never
the signal"*) **explicitly shields the signal from revision.** At a one-open holding period there is
almost no expression to fix, **so C claims should be near-zero — and if they are not, that is the
tell.**

Proposed D limbs, mostly reusing what exists:
1. **Inside the distribution** — surprise limb 3 with the inequality flipped. Free.
2. **Not nameable** — if you can name what moved it, it is not random; it is A or B depending on
   observability. **Today D is claimable while you know exactly what happened.** The failure to
   identify a deciding variable must itself be recorded as a failure.
3. **Not recurrent** — B's limb 4 verbatim. Three "random" moves on the same mechanism in the same
   direction is not random. **This is the limb that turns D from a terminus into a class that can
   ripen.**
4. **A budget tighter than B's 30%** — D is more claimable, so it needs the harder cap. **If more
   than half of graded outcomes are D, you are not forecasting; you are observing noise and calling
   it a distribution.**

### The reviewer's three recommended actions, and their status
| # | action | status |
|---|---|---|
| 1 | run the trivial shadow | ✅ **done** — and it is the worst result in this document |
| 2 | report expectancy, raw-n and independence-adjusted; re-arm the kill switches on it | ✅ **done** — reported, and the switches now key on sign x expectancy (§17.3) |
| 3 | fix the normalisation | ✅ **shipped v1.5.7** under the new DEFECT tier, flip set published |
