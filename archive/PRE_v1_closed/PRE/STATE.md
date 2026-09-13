# PRE — STATE · ⛔ **CLOSED EXPERIMENT**
**No longer rewritten. This file is the final record of a retired model.**
**Superseded session blocks live in `archive/SESSION_LOG.md`.**
**Updated 2026-09-12 · engine v1.5.6 · edge-score v1.5.0 · forecast v1.0.0 · errors v1.0.0 ·
dossier v1.0.0 · 497 assertions across 11 suites**

---

---

# ⛔ CLOSED 2026-09-13 — THE DIRECTIONAL FORECAST IS RETIRED

**Owner's decision (Jacob, 2026-09-13), after four independent external reviews all reached the
same verdict.** Full reasoning: **`PRE/pre_closed.py`**. Sentinel: **`PRE/CLOSED`**.

## THE FINAL RECORD
```
27 blind, pre-registered, integrity-hashed directional forecasts
  14 correct  =  51.9%      p = 1.00  against a pre-specified 50% null
  separation (mean idio UP - DOWN)  =  -1.86pp    t = -0.50
  idio sigma  8.2% (UP leg) / 11.1% (DOWN leg)
  OUT-OF-SAMPLE n FOR THE FINAL SCORING STACK  =  5

trade layer: 4/12, expectancy -1.15%/trade, PAUSED since 2026-08-09 and never resumed
ledgers frozen: forecasts.jsonl 55 | ledger.jsonl 135 | errors.jsonl 21
```
A clean negative result, honestly obtained under blind pre-registration. **Kept, not deleted —
it is worth more than a flattering one.**

## WHY — and it is not the hit rate
🔴 **The scoring stack was edited FOUR TIMES inside its own measurement window** (2026-08-09,
08-12, 09-05 x2), each time in response to observed misses. `value`/`vrich`/`SAT` cut mid-sample;
on 2026-09-02 the `DEFAULT_ETF` change altered **the benchmark used to compute idio** for 6 of 7
names in that batch. So 51.9% is the blended in-sample score of a sequence of different models,
and the history **cannot be replayed** — `rev_raw`/`gg`/`vel` were null on every row before
2026-09-12.

🔴 **And waiting would have made it worse.** The error ledger existed to detect mechanisms and
demand changes; every change it extracted reset the out-of-sample clock and destroyed the frozen
spec a record requires. Against pure noise the 3-confirmation firing rule reached a RIPE class
**~68% of the time** over 13 misses with author-chosen labels. **The governance layer was not
merely disproportionate to the evidence — it was the thing preventing evidence from existing.**

## ⚠ NOT THE REASONS — two of the audit brief's three arguments were OVERTURNED
Recorded so they do not survive as folklore. Both re-verified from source before being accepted.
| the brief claimed | verdict | the test |
|---|---|---|
| always-DOWN beats it by 3.7pp | **overturned** | identical predictions on **16 of 27**; differ on 11, 5 right vs 6. **McNemar exact p = 1.00.** Benchmark also chosen after seeing the data. |
| effective sample is 6 event-dates | **overturned** | **Tarone/Pearson chi2 4.92 on 5 df, dispersion 0.98.** Cluster bootstrap 33-70% vs naive 33-70%. No block structure in *correctness*. |
| ~780 events needed | **weakened** | right arithmetic; it prices only the binary-direction design, not earnings research |

Also withdrawn: the **Singapore time-zone argument** (21:30 SGT is 9:30pm; a real 2pp edge on
10pp sigma is per-trade Sharpe ~0.2) and the **inverted conviction gradient**, which was noise on
cells of n=2 and n=6 and was wrongly reported as a finding for three sessions.

## WHAT SURVIVED, AND WHERE IT WENT
**Two rules, into `.claude/skills/earnings/SKILL.md`** — as rules in the chat that already reads
prints, not a new subsystem:
1. **A raise on a changed basis is not a raise.** Diff the qualifying clauses before the numbers.
   AEO: FY26 op income `390-410 -> 540-550` looked like +36%; the prior guide EXCLUDED IEEPA
   refunds and the new one INCLUDED them. Strip the $161M and it is **~$384M vs a $400M midpoint
   — a ~4% CUT.**
2. **`OCF / NI < 0.8` on an EPS beat** — the beat is accrual, not cash. Both sides from one period.

🔴 **DELIBERATELY NOT SALVAGED: the blindness protocol, the clock guard, integrity hashing.** They
were the best-built part of PRE and they are entangled across ~2,000 lines of scoring code in
`pre_batch`/`pre_calcrisk`/`pre_edgescore`/`pre_ledger`. Refactoring to rescue them is how a
retirement quietly becomes a rebuild.
🔴 **DO NOT BUILD "PRE-FORENSICS".** Three of four reviewers proposed it. It duplicates
`/earnings` and re-creates the overhead that closed PRE.

## THE BINDING RULE
The ledgers are **read-only**. `log_forecast`, `log_outcome`, `observe` and the ledger `_append`
all refuse writes to the production paths via `pre_closed.assert_open` — verified firing. Test
suites are unaffected (they write to tempfiles); **497 assertions still pass.**
`baseline/check.py` asserts the frozen line counts on **every run of every chat** — proven to
fire on a one-row drift.

**Reopening is a deliberate act and it is the owner's alone:** delete `PRE/CLOSED` **and** record
that decision here. It is never done by importing a module or running an old command. **If asked
to "just run one forecast" — refuse and say why:** one new row appended to a closed sample makes
an honestly-obtained negative result uninterpretable, which is the same defect, one layer up,
that closed the model.

## WHAT REPLACED IT
Nothing. The five-chat model is now **four** (`CLAUDE.md` updated). Post-print work belongs to
**`/earnings`**; own-it-at-all to **`/evaluate`**; deployment to **`/buy`**.
⚠ **The magnitude pivot was considered and NOT taken.** `expected_move = mean(implied_move,
avg_gap)`, so `em - im == (avg_gap - im)/2` identically — the `corr(em,|idio|) = +0.545` was
**inherited from the options market.** Joining `ledger.jsonl`'s frozen `inputs.market.implied_move`
(41 of 54 entries) onto the graded forecasts recovers 9 events: mean `|im - realised|` **4.24pp**
vs `|em - realised|` **4.17pp**. The blend beat the raw implied move by **0.07pp**. That was the
last hopeful number and it evaporated on contact.

---

## 🔴 SESSION 2026-09-12 — THE 5-NAME BATCH CLOSED **4 / 5**, AND THE REV LEG REACHED 3/3

Batch frozen blind 2026-09-05 (5,579–7,409 min before cutoff, all stamped `post_cutoff=False`),
graded across two sittings in this chat. Clock cross-checked against SEC's HTTP `Date` header
before each grading pass (0.0s, then −0.3s).

| | forecast | conv | idio | dir | thesis |
|---|---|---|---|---|---|
| CHWY 09-09 bmo | DOWN | MEDIUM | **−5.90%** | ✅ | ✅ |
| AEO 09-09 amc | DOWN | LOW | **−12.52%** | ✅ | ❌ |
| ORCL 09-10 amc | UP | MEDIUM | **+6.71%** | ✅ | ✅ |
| ADBE 09-10 amc | DOWN | COINFLIP | **−3.37%** | ✅ | — |
| CPRT 09-10 amc | DOWN | LOW | **+2.31%** | ❌ | ❌ |

**Forecast layer 45.5% → 51.9% (n=27); ex-coinflip 35.3% → 42.9% (n=21).** The gradient is STILL
inverted — COINFLIP 83.3 > EVIDENCED 50.0 > WEAK 33.3 — but EVIDENCED climbed 40.0→50.0 on this
batch. ⚠ **Jacob's call, still unpatched.**

### 🔴 `rev-leg-points-against-the-print` IS **3/3 AND RIPE**
CPRT's expectations of −0.50 came **entirely from REV** (GG and VEL both unsourced): falling
revisions → forecast DOWN → gap **UP**, the same sign as PLAB. `INDUSTRIALS|2026-09-10` is distinct
from `SEMIS|2026-08-26` and `SEMIS|2026-09-02` — **three sectors, three nights, a real sample.**
Revenue BEAT while EPS **missed by 14.6%** and the tape bought it anyway on record total loss
frequency and ACV. Surprise gate RUN and **FAILED** (`not_sourceable`, `outside_distribution`)
→ A/JUDGMENT. Rate holds 0/10.

### 🔴 AND ITS FLIP SET COULD NOT BE COMPUTED — now partly fixed
`rev_raw`, `gg` and `vel` were accepted by `pre_forecast.forecast()` and reached only the driver
STRING. **All three were None on every one of the 28 rows written before 2026-09-12.**
`components["expectations"]` is a NET number, so no row can say which leg produced it — making
Abstraction limb 2 (*which previous winners would this fix break?*) **unanswerable for exactly the
change the RIPE class demands.** The trade layer fixed its own version of this
(`fund_leg_sum`/`fund_norm`/`verified_legs`); the forecast layer never got the plumbing and is now
**the only layer still accruing a record.** Now persisted inside `components` — not as a dataclass
field, because `Forecast` is built POSITIONALLY and a new field silently shifts `components`.
**Moves nothing.** ⚠ **It cannot repair the 28 existing rows. That gap is permanent.**

🔴 **NOT SHIPPED, deliberately: the REV sign.** Needs a proposal + both limbs + sign-off, and
limb 2 stays unanswerable until the new plumbing accrues rows. ⚠ **Also NOT wired:**
`pre_forecast.py:146` holds a direction-only `rev_raw` fallback for precisely the case where
expectations fail-closes to 0 — **`pre_batch` never passes `rev_raw`, so it has never fired.**
Wiring it would inject the very leg we now have 3/3 evidence is inverted. **The dead plumbing has
been protecting the model.** Leave it dead until the sign question is settled.

### AEO — a guide that CHANGED BASIS, and the clause was in my hand at T−1
Q2 operating profit $211M vs $103M LY **included a $161M net IEEPA refund benefit** → underlying
~$50M against a $45–50M guide, the **top of the guide, not a beat**. FY26 OI "raised" $390–410M →
$540–550M, but the prior guide **EXCLUDED** refunds and the new one is *"inclusive of net tariff
refund benefit"*: `545 − 161 ≈ 384` vs a $400M midpoint — **a ~4% CUT dressed as a +36% raise.**
🔴 **The exclusion clause was in the excerpt I transcribed at T−1 and I did not flag it.**
`GuidanceRecord` has no field for a stated exclusion, so GG scored MAINTAINED on a guide that was
not comparable to its successor. Direction right, thesis wrong. New class **1/3**.

### 🟢 SHIPPED — the ledger could not record a wrong thesis on a WINNING call
`_class_rows` built classes only from rows with `correct is not True`, so a mechanism **first
observed on a win created no class at all** — both of that day's observations landed in
`errors.jsonl` and were invisible to `board`/`pending`/`ripe`/`show`. A loop built because *"when
your results are wrong, you do nothing"* **was doing nothing when the results were RIGHT and the
thesis was wrong.** A class is now confirmed by `correct is not True` **OR** `thesis_confirmed is
False`. Audited first: two rows change partition (AEO, and SNPS 2026-08-26), and SNPS's key
`SOFTWARE|2026-08-26` matches four existing rows — **raw 4→5, independent 1→1, no disposition
moves.** Also corrected the docstring claiming `thesis_confirmed` "is None on every historical
row" (it is 10 False / 2 True / 2 None) — the same moving-fact-in-a-doc defect as the retracted 5/15.

### ORCL — the cleanest win, and a limb-2 counterexample
VEL +1 off a forward book **already months public** (RPO filed 06-22 and 03-11) — *the same
structure that made AVGO wrong* — and here it was right: OCI +121% to $7.4B, revenue $19.3B +30%,
FY27 raised to ≥$90B. Logged as a **WIN touching `vel-scores-a-forward-book-already-public`**,
which correctly stays **1/3**. **Any fix discounting VEL for an already-public book breaks this.**
The pre-registered falsifier named a sequential margin step-down; margin came in **flat at ~42%**,
so it correctly did **not** fire. ⚠ Bear case stands regardless: flat margin on +30% revenue,
**$28.5B capex in one quarter, FCF −$5.4B.**

### ✅ GAP-CAPTURE VALIDATED AGAIN, HARD
**ORCL opened +7.51% and had given back 8.61pts to −1.10% — below the prior close — by 15:06 ET.**
CPRT gave back 5.97pts. ADBE ran the other way (+4.21pts). *Provisional: session still open when
measured.* The entire ORCL move existed at the open, exactly as PLAB taught.

### MAGNITUDE, measured rather than asserted
Median expected/realised ratio **1.05 (n=27)** — `expected_move` is CENTRED with fat tails both
ways: 12 of 27 outside 2×, 8 of them overshoots, **6 of those 8 inside the single 07-30 batch.**
ADBE (2.24×) logged **D/VARIANCE**, which never patches. Nothing justifies touching the estimator.

### SCOUT
**ORCL → EVALUATE.** Its card is dated **2026-07-21, pinned $126.50, MoS −18.1%**, and its own text
says *"re-underwrite at the Q1 FY27 print"* — **that print is this one, and the stock is ~30% above
the pin.** **ADBE → EVALUATE** because `inbox.py` REFUSED the TRACK I first chose (a reported
watchlist name is stale by definition) — **its bar is +10.5% and does NOT clear 30%/6mo.**
**CPRT → read-through (NA)**, outside the universe. `inbox.py` also refused EVALUATE without a
priced `--bar`; both controls fired correctly against me. EVAL_QUEUE rendered, baseline PASS.

```
🔴 RIPE    rev-leg-points-against-the-print            3/3  A/JUDGMENT   PROPOSE + both limbs + sign-off
🔴 RIPE    conviction-label-ignores-leg-resolution     1/1  A/MECHANICAL FIX_NOW (owner's queued spec)
⏳ PENDING guide-changes-basis-and-the-raise-is-not-comparable 1/3  AEO
⏳ PENDING expected-move-overshoots-an-in-line-print     1/3  D/VARIANCE  ADBE
⏳ PENDING gap-model-blind-to-same-night-complex-event   1/3  (raw 5, clustered)
⏳ PENDING vel-scores-a-forward-book-already-public       1/3  AVGO wrong / ORCL right — points BOTH ways
⏳ PENDING analyst-override-uses-variable-outside-graded-horizon 1/3
   SURPRISE RATE  0/10 = 0%  (budget 30%)
```

⚠ **STILL OPEN AND OWNER-ONLY:** the conviction RESOLUTION gate, the inverted gradient, the REV
sign, and benchmark self-inclusion for mega-caps in their own ETF (ORCL is a large IGV component
and moved IGV on its own print night — ADBE's idio is measured against a benchmark ORCL pushed).
⚠ **CHWY/AEO/CPRT all benchmarked to SPY** — the 2026-09-02 `DEFAULT_ETF` extension covered
software and semis only. Extend the table BEFORE a freeze, never after seeing a dry run.

⛔ **THIS CHAT IS BURNED — it has read the book. CLOSE IT. The next batch starts a fresh chat.**

---

## 🔴 SESSION 2026-09-05 — AVGO GRADED **0 / 1**, AND IT BEAT ITS OWN GUIDE TWICE ON THE WAY DOWN

`/pre` ran 2026-09-02 10:58 ET, **302 min before the AMC cutoff** — a valid blind freeze. The chat
then **straddled the print** and resumed 2026-09-05, so `/post` ran here, in the correct chat.
⚠ **The OS clock was verified against SEC's HTTP `Date` header before anything was graded** (agreed
to 1s). The clock guard trusts `datetime.now()`; a skewed machine would defeat it silently and no
test covers that. Checking it is now the first move of any resumed PRE chat.

| | forecast | actual | verdict |
|---|---|---|---|
| DIRECTION | UP | idio **−3.746%** | ❌ |
| CONVICTION | HIGH / EVIDENCED | — | ❌ **HIGH is now 0-for-2** |
| MAGNITUDE | +6.8% | −4.22% raw | ✅ 1.6×, inside the 2× bar |

🔴 **THE PRINT WAS A DOUBLE BEAT AND THE STOCK STILL GAPPED −4.22% ON SPY +0.36%.** Q3 revenue
**$29.591B vs its own $29.4B guide**; non-GAAP op margin **67.9% vs ~67% guided**; Q4 guided
**$34.8B, +93% YoY**, AI semi **$16.7B → $21.7B (+236% YoY)**. Nothing in the fundamentals missed.

🔴 **DECIDING VARIABLE — THE MARGIN LINE, READ SEQUENTIALLY.** Q4 non-GAAP op margin guided **~66%
against 67.9% just delivered = −1.9pt sequential**, on AI/XPU mix, alongside +17.6% sequential
revenue. **The CFO framed it YoY — "flat from a year ago" — which is true and which hides the
step-down from the quarter just reported.** Read the guided margin against the ACTUAL prior quarter,
never against the year-ago quarter, and never as management frames it.

**SURPRISE GATE RUN AND FAILED** — limb 2 `not_sourceable` (AI-mix dilution was a public dynamic at
T−1) and limb 3 `outside_distribution` (−3.7% against a name whose last 10 prints reach 18.4% is
Tuesday). → **A / JUDGMENT.** Not luck. Work. Surprise rate holds 0/10.

### 🔴 `rev-leg-points-against-the-print` → **2 / 3**, AND IT IS A REAL MECHANISM
PLAB and AVGO are **distinct `(sector, event_date)` keys** — `SEMIS|2026-08-26` vs `SEMIS|2026-09-02`
— so this is a genuine independent confirmation, not a cluster.
**They are mirror images with opposite signs:** PLAB REV falling → expectations −1.00 → forecast DOWN
→ **+27.5%**. AVGO REV rising (25up/9down, 46 analysts) → expectations +1.00 → forecast UP → **−3.75%**.
**In both, REV pointed opposite to the gap.** The mechanism is coherent rather than fitted:
**estimate revisions move the BAR, and the open gap is the print measured AGAINST the bar** — so
rising revisions into a print are *bearish* for the gap and falling ones *bullish*. **Still 2/3.
NOTHING SHIPS. Do not flip the sign at n=2.**

### NEW CLASS — `vel-scores-a-forward-book-already-public` 1/3
VEL saturated expectations to +1.00 off RPO **$45.0B → $164.6B**, a fact **FILED 2026-06-09 and ~3
months public**. VEL reads the last filed 10-Q and is **one quarter stale by construction**: it cannot
tell "accelerating, newly disclosed" from "accelerating, already priced." Same species as the errors
already cut (`value`/`vrich`/SAT-in-directional) — **a known fundamental logged in a term that is
supposed to measure surprise.** 🔴 **It SHARES ITS EVENT with the rev-leg row above: one event, two
mechanisms, neither corroborates the other.**
**The RPO number itself was verified against SEC XBRL `companyconcept` BEFORE the freeze** — one
context per period-end, no partial/total ambiguity, 13 prior quarters in a 20–45B band. Real as filed.

### THE FORECAST LAYER — n=22, THE GRADIENT WIDENED A **THIRD** TIME
```
overall            45.5%  (10/22)
EXCLUDING COINFLIP 35.3%  (17)     <-- was 37.5% at n=21, 37.5% at n=16
by conviction  COINFLIP 80.0% (5) | MEDIUM 50.0% (8) | LOW 28.6% (7) | HIGH 0.0% (2)
by basis       COINFLIP 80.0% (5) > EVIDENCED 40.0% (10) > WEAK 28.6% (7)
```
**Three independent additions, same direction of travel: the calls the model says have NO BASIS keep
beating the ones it claims evidence for.** ⚠️ **STILL DO NOT PATCH.** n≈4 event-days. Jacob's call.

### 🔴 THE FALSIFIER I WROTE BEFORE THE PRINT FIRED, EXACTLY AS WRITTEN
The registered falsifier named two limbs; limb 2 was *"an AI-ASIC margin/mix disclosure that reframes
the backlog as low-margin."* **That is precisely what happened.** The pre-print report also stated the
central risk in plain terms — the $164.6B was 3 months public and the market had sold the stock 23%
anyway — **and the forecast was registered UP regardless, because doctrine forbids hand-adjusting a
frozen call.** That was the correct process and it produced a wrong answer.
**Do NOT read this as "trust the analyst":** the counter-case is SNPS, where the analyst override was
WRONG and is logged as `analyst-override-uses-variable-outside-graded-horizon`. **1–1. Neither ripens.**
The open question this raises is Jacob's: *the disclosure channel records a concern but cannot act on
one, so a correctly-identified falsifier still costs a call.*

### SHIPPED THIS SESSION — both small, both pre-verified
- **`AVGO → SMH` in `DEFAULT_ETF`** (added BEFORE the freeze). AVGO was absent and would have
  benchmarked to **SPY** — the same A/MECHANICAL class that shipped 2026-09-02, whose own table
  extension omitted the largest AI-semi after NVDA. Zero historical rows touched.
- **`log_outcome(backfill_reason=...)` parameterised.** It hardcoded *"the layer was never scored
  between 07-30 and 08-09"*, which would have written a **factually false reason** onto this row and
  every future backfill. Default unchanged.
- ⚠ **DOC DRIFT:** `.claude/skills/post/SKILL.md` documents `--action-hint SIGNAL`; the enum in
  `inbox.py` is `EVALUATE|TRACK|DROP|PORTFOLIO|NA` and **has no SIGNAL**. The skill's own worked
  example uses `NA`, which is the equivalent. Routed as `NA`. **Not fixed — owner's call which side
  moves.**
- ⚠ **BENCHMARK SELF-INCLUSION, unfixed:** AVGO is ~8% of SMH (NVDA ~20%), so a mega-cap's own gap
  moves its benchmark and **measured idio is understated**. Recorded as a standing note, not patched.

### SCOUT
AVGO is **HELD, 29.99% of the 10K**, and the portfolio chat already re-underwrote it 2026-09-03
(CQS 73→76). A current card exists → **not EVALUATE**. Routed `NA` / `VERIFIED` / `FILED` as
read-through: *custom-silicon mix is margin-dilutive across the AI-semi complex even where it is
revenue-explosive.* `earnings|2026-09-05|AVGO|b2b0b732`.

```
⏳ PENDING   rev-leg-points-against-the-print                 2/3   PLAB + AVGO, INDEPENDENT
⏳ PENDING   gap-model-blind-to-same-night-complex-event      1/3   (raw 4, clustered to 1)
⏳ PENDING   analyst-override-uses-variable-outside-graded-horizon  1/3
⏳ PENDING   vel-scores-a-forward-book-already-public         1/3   shares AVGO's event
   SURPRISE RATE  0/10 = 0%  (budget 30%)
```

### 🟢 SHIPPED 2026-09-05 — TWO CONTROLS THAT EXISTED ON PAPER AND DID NOT RUN

**1 · `pre_errors.py board` CRASHED on every plain Windows run.** stdout is cp1252 there and the
PENDING glyph U+23F3 raised `UnicodeEncodeError`. **That command is STEP 1 of the `/pre` runbook** —
*"what is this model currently known to get wrong?"* — so the one control that surfaces a RIPE class
**before a forecast is frozen** was unrunnable without an env var. A class was live at 2/3 while it
was broken. Fixed in `main()` with `errors="replace"` so a future glyph degrades instead of killing
the board. Surveyed all 14 PRE CLIs: **this was the only one that actually crashed.**

**2 · 🔴 THE FORECAST LAYER WAS NEVER CLOCK-GUARDED.** `--register` is refused after the cutoff, but a
**dry** run past it printed a warning and **logged the row anyway, unmarked**. `clock_guard`'s own
docstring says *"label it VOID"* — **and nothing labelled it.** That is `void-status-in-prose-only`,
the first of the three defects `controls_fire_selftest.py` was built for, **recurring a fourth time**.
It bites harder here than on the trade layer: **the trade layer is PAUSED, so the forecast layer is
the only one still accruing a record**, and `score()` is the statistic the two open owner questions
turn on. `log_forecast` now stamps `post_cutoff` / `minutes_before_cutoff` / `cutoff_session`, and
`score()` **excludes** stamped rows and **discloses the count** — including on the all-excluded path,
where a bare `n=0` would otherwise read as "nothing logged yet" instead of "all of it was hindsight."
✅ **AUDITED FIRST: 0 of 23 existing rows are post-cutoff, so this is a provable NO-OP on the record**
(n=22, 45.5%, 35.3% ex-coinflip — byte-identical before and after). **That is precisely when to wire
a guard.**

**Both ship with FIRING tests** (`controls_fire_selftest.py` cases 8 and 9, +12 assertions →
**497 across 11 suites**): the board is driven through a real cp1252 writer over the real ledger, and
a hindsight row is proven to be stamped, excluded, disclosed — while a genuine pre-print freeze on
the same path is proven still counted.

🔴 **TWO NEAR-MISSES WORTH MORE THAN THE FIXES.**
- `Forecast` is constructed **POSITIONALLY**. Adding `session` in the obvious place silently shifted
  `components` into it, blanking the dict on every forecast. **Caught by the EXISTING
  `forecast_selftest.py` 2a — not by either test I wrote.** The field now carries a comment saying it
  must stay last.
- `forecast_selftest.py` 7 then failed because its fixtures used a **past** `event_date`, so the new
  guard correctly called them hindsight. **The fixture was what was unrealistic** — it never
  represented a pre-print freeze. Re-dated to 2099 with the reasoning recorded. **The guard was not
  weakened to make a test pass.**

### 🟢 DOC DEFECTS FIXED — both would have misinformed the next session
- **`/post` SKILL.md hardcoded "capital 5/15, shorts 1-for-5, forecast 8/14".** All three were wrong
  by 2026-09-05, and `5/15` was worse than stale — **this file had formally retracted it** (*"included
  void rows and carried no expectancy at all"*). The skill was instructing the model to quote a number
  the system had disowned. Replaced with **the command that reads it live**; a moving statistic baked
  into a doc always drifts.
- **`/post` SKILL.md documents `--action-hint SIGNAL`, which `inbox.py` REFUSES** (enum is
  `EVALUATE|TRACK|DROP|PORTFOLIO|NA`). Found while routing AVGO. Doc now says write `NA`.
  ⚠ **The design question is OPEN and is Jacob's:** `NA` means *no hint*, `SIGNAL` means *route to
  `/earnings` as read-through* — different instructions, and collapsing them loses the routing.
- Assertion counts resynced (`449→497` in the `/pre` runbook, `485→497` here, `34→46` for the
  controls suite).

⚠ **STILL UNFIXED, deliberately:** the conviction RESOLUTION gate (Jacob's), the inverted gradient
(Jacob's), benchmark self-inclusion for mega-caps in their own ETF, and the clock guard's reliance on
an **unverified local OS clock** — this session cross-checked it against SEC's HTTP `Date` header by
hand, and nothing in code or tests does that.

⛔ **THIS CHAT IS BURNED — it has read the book. CLOSE IT. The next batch starts a fresh chat.**

---

## 🟢 SHIPPED 2026-08-09 — THE LEARNING LOOP. A WRONG CALL NOW COSTS SOMETHING.

Jacob's diagnosis, and it was correct: *"when your results are wrong, you do nothing."* That was
**structural**. The SOP's four branches terminated in *do nothing* three times out of four, and the
fourth had no counter so it fired on n=1 or never. The model was **simultaneously trigger-happy and
inert** — two gates shipped off single vivid trades (1-for-5), while Type B/D misses accumulated
forever with no response of any kind.

| new | what it does |
|---|---|
| **`pre_errors.py`** | every graded event — **wins included** — writes an observation against an error CLASS (a mechanism, never a ticker). Classes accumulate to **3 INDEPENDENT confirmations**, then demand a response. |
| **`pre_dossier.py`** | per-name memory. Read at `/pre`, written at `/post`. **Hard 5-event retention**, auto-purged. |
| **`METHOD.md`** | the full auditable method, written for the external evaluator. |
| **`/pre` · `/post`** | renamed from `/pre-register` · `/pre-post`. Old phrases still trigger. |

**THE FIRING RULE.** A-MECHANICAL → `FIX_NOW` at **1** (a bug is not evidence, it is a bug).
A-JUDGMENT and C → `PEND` to **3**. **B → `BOUNDARY` and D → `VARIANCE`: still never patched at any
count** — but at 3 they stop being *silent* and raise a **bet-selection** or **distribution** question
instead. That is the half that was missing.

**🔴 THE INDEPENDENCE RULE.** Confirmations count distinct `(sector, event_date)` keys. **Three semis
on one night is ONE confirmation.** Counting it as three would fire a permanent change off n=1 while
displaying "3/3" — the exact laundering the SOP exists to prevent, wearing a counter. The board prints
both (`3/3 independent (5 raw — clustered)`).

**🔴 THE SURPRISE GATE — 4 limbs, all required.** *unobservable* (variable named specifically, not
"sentiment"/"macro") · *not sourceable* at T−1 even in principle · *outside* the name's own worst gap
of its last 8 prints · **and *not recurrent* — the anti-excuse limb.** The second time the same thing
blindsides us it was a **blind spot, not bad luck**: it auto-reclassifies to Type A and becomes work.
Surprise above **30% of the trailing 10** flags bet-selection, not variance.

**Nothing ships from this alone.** `dispose(..., "SHIPPED")` is **refused in code** without both
Abstraction limbs passing and a **named** winning trade checked. The guide-freshness gate cannot ship
through this path — that is a regression test, not a hope.

---

## ⛔⛔ THE TRADE LAYER IS PAUSED. THE FORECAST LAYER IS NOT. READ THIS FIRST.

`pre_ledger.TRADE_PAUSE` is **active since 2026-08-09** and enforced in code on **both** registration
paths. `pre_batch.py --register` refuses. **Running the batch WITHOUT `--register` still works and
every name still gets a graded forecast — do that.**

**THE REASON IS VALIDITY, NOT PERFORMANCE.** Not the 36% hit rate — pausing on the sign switch would
mean acting on the metric just shown to be the wrong one. The reason: **the record was produced by a
scorer nobody had correctly described.** 22 of 53 verdicts flip under the corrected arithmetic. You
cannot interpret outcomes produced by a mis-specified mechanism. Same species as the clock guard
voiding the 07-29 batch — **voided for process, not for results.**

🔴 **DO NOT PAUSE THE FORECAST LAYER.** It costs nothing and is graded unconditionally. Stopping it
is how you arrive in three months with the same n and nothing learned. **That is the whole payoff of
the two-layer split: stop betting without stopping learning.**

### 🔴 THE SATURATION DEFECT — resolved WRONG, but NOT corrected a third time
A lone ±1 leg (GG or VEL alone) saturates the term on one notch: VEL=+1 → **MAXIMUM**.
**The "confidence separates that" defence fails on arithmetic:** norm 4→1 inflates expectations
**4×**; confidence's whole live span is 0.775→1.00, a **1.29× discount**. You cannot absorb a
fourfold inflation with a 29% haircut. Normalisation asks *how strong relative to the instrument*;
conviction claims *how strong is my read*. Those agree only if the instrument has **resolution** —
and a 3-state VEL can express direction, never strength. **MAXIMUM off one notch is an instrument
limit logged as a signal**, the same category error that got `value` cut.

**Harm is NOT cosmetic** (conviction doesn't size, so no capital — but it contaminates the
tier-vs-outcome table, the only statistic that could ever validate the ladder: **evidence damage**).
**And it IS live:** `pre_batch.py:374` feeds `expectations_momentum` into `pre_forecast`, so
`forecasts.jsonl` is accruing inflated labels **during the pause**, on the layer left running.

**SHIPPED the reversible move instead (PLUMBING, moves nothing):** `fund_leg_sum`, `fund_norm`,
`verified_legs` logged on every verdict + persisted to the ledger row — **any row's true tier is
re-derivable under any future norm.** Irreversible evidence corruption → recoverable labelling
artifact.
**QUEUED with the resume, and the spec is NOT a norm change:** *gate the conviction ladder on
RESOLUTION — MAXIMUM/HIGH unreachable below two verified legs. Leave the normaliser alone; it is
correct. The score is honest, the LABEL is the lie.* Touches no verdict (stances come off |edge|).

### 🔴 ONE PROCESS DEFECT, THREE TIMES — and the STANDING RULE
void-status-in-prose-only · pause-guard-on-the-wrong-function · `thesis_confirmed`-never-written.
**Not three bugs: this system builds the control and does not wire it.** Every gate green throughout.
And #3 is bigger than it reads — **the SOP's central commitment has never once been executed**:
*"P&L is not truth, attribution is"* is binding, and **every post-mortem was graded on P&L**, so the
A/B/C/D types, the win count and the deciding variables were all assigned without their driving input.

> **STANDING: every new control ships with a test that it FIRES on real data — not that it exists.**
> `tests/controls_fire_selftest.py`, 46 assertions, wired into `run_tests.py`. All three defects would
> have been caught at build time. Adding a control now means adding a case there.

### RESUME GATE — all three, no exceptions
| | condition | status |
|---|---|---|
| 1 | units normalised by populated legs | ✅ shipped v1.5.7 |
| 2 | full ledger re-score under both arithmetics, flip set disclosed | ✅ `rescore_units.py`, 22 flips |
| 3 | **beat the shadow AND clear positive expectancy ex-best-trade** | ⛔ **NOT MET, both limbs** |

**Why the shadow is the bar:** it uses **no weights at all**, so the units defect cannot have touched
it. **But 2/11 was not yet a bar — the base-rate control was missing and is now run:**
all graded **17/38 = 44.7% up**; the shadow **2/11 = 18.2%**; **same event-days, all names
11/31 = 35.5%**. The tape explains part of it and **the shadow still sits below its own days** — but
11 events over **4** event-days is n≈4 by our own independence rule. Suggestive, **not a refutation
of REV**; the same discipline as COINFLIP-at-80%, pointed the other way. So beating 18% proves
nothing, and limb 2 exists because expectancy is **−1.13%, −4.75% ex-AEHR** — not a model with a
units problem, **a model with no edge and one lucky print.**

✅ **The new kill switch validated on first contact:** sign bad + expectancy bad → PAUSE, reached
independently and agreeing with a decision already made on validity grounds. Almost nothing else in
this system has passed a live test.

---

## SUPERSEDED BLOCKS — MOVED OUT 2026-09-02
The 2026-08-09 *Owner decisions on review #3* and *External review #3* sections now live in
`archive/SESSION_LOG.md`. Nothing is retracted; they are history, not current state. The findings
that remain LIVE — the units DEFECT, the kill switches, the void rows, and the trivial shadow at
2/11 — are carried in the sections above and below.

---

## THE FORECAST LAYER — n=21, AND THE INVERTED GRADIENT WIDENED

```
overall            47.6%   (10/21)
EXCLUDING COINFLIP 37.5%   (16)      <-- WORSE THAN GUESSING, and worse than it was at n=14

by basis       COINFLIP 80.0% (5)  >  EVIDENCED 44.4% (9)  >  WEAK 28.6% (7)
by conviction  COINFLIP 80.0% (5) | MEDIUM 50.0% (8) | LOW 28.6% (7) | HIGH 0.0% (1)
```

**The 2026-08-26 batch added 7 clean forward observations and the gradient did not correct — it
widened.** The calls the model labels as having NO BASIS still beat every call it claims evidence
for. At n=14 this spanned 2 event-days and was explicitly not evidence; it is now **3 event-days**,
which is more and is still small. The direction of travel has not changed across two independent
additions.

> ⚠️ **STILL DO NOT PATCH THIS.** By this model's own independence rule the layer is n≈3
> event-days. The SOP forbids tuning on small samples and every component must be justifiable by
> mechanism alone. **This remains a premise-level result and it is Jacob's call.**

`forecasts.jsonl` 43 rows (22 forecasts / 21 outcomes). The one ungraded forecast is
`AAPL 2026-12-01` — a future event, not a missing outcome.

---

## THE CHAT SPLIT — IN FORCE FROM 2026-08-09
| chat | when | may read the book? |
|---|---|---|
| **`/pre`** | pre-print | **NO.** No DRIVE file, no account file, no holdings. Refuses to run in a chat that has already run `/post`, `/earnings`, `/review`, `/buy` or `/evaluate`. |
| **`/post`** | post-print | **Yes.** Outcome scoring → post-mortem → `/earnings` → scout → `data/inbox_earnings.jsonl` |

Three external reviewers independently found that hosting the scout and `/earnings` in the PRE chat
puts portfolio state in a **persistent context window** that is still there when the next forecast is
frozen. The originally proposed guard — *byte-identical with and without the portfolio context file* —
**tested file absence; the channel is the conversation.** Deleted.
**The subtler channel:** time-gating protects forecast *N*, not *N+1* — preference leaks through
**coverage selection**. The name list comes from the earnings calendar, never from the book.

**Audit half:** `register()` writes `context: {portfolio_aware, sources, status}` **inside the frozen
payload**, so `integrity_hash` covers it. 7 assertions lock it, including that stripping the
declaration or forging `BLIND` onto an aware row both break the hash. Same shape as `_is_retro()`:
detection, not prevention.

---

## THE RECORD, STATED HONESTLY
```
CAPITAL   5 / 15   (33%)     shorts 1-for-5      NOTHING IS VALIDATED
  clean     4 / 11 over 5 event-days   expectancy -1.13%/trade  (-4.75% ex-best-trade)
  dashboard n=12, acc 33%, expectancy -1.15%  (-4.44% ex-top-trade)
FORECAST  10 / 21  (47.6%)   37.5% excluding coinflips
LEDGER    135 rows   NO outstanding outcomes
FORECASTS 43 rows    ERRORS 13 rows    DOSSIERS 7 names + 4 standing notes
TESTS     497 assertions, 11 suites, all pass
```
The 2026-07-29 AMC batch of 8 remains **VOID** (scored after its own prints). AMKR remains
**retro-registered** and is not a valid pre-registration. Neither may ever be cited as evidence.

---

## NEXT
0. **The learning loop is live and NO LONGER EMPTY** — 3 classes PENDING at 1/3, one MECHANICAL
   shipped. Nothing ripens until three INDEPENDENT `(sector, event_date)` keys agree, and the
   2026-08-26 cluster contributed **one**, not four. That is the design working, not a stall.
1. 🔴 **Jacob's call on the CONVICTION RESOLUTION GATE.** CRM proved the harm is live and not
   cosmetic: an EVIDENCED/MEDIUM label was emitted off ONE leg, over a feed the trade layer had
   already fail-closed. Spec unchanged, and it is NOT a norm change — *gate the ladder on
   RESOLUTION: MAXIMUM/HIGH unreachable below two verified legs. Leave the normaliser alone.*
   Touches no verdict; stances come off |edge|.
2. 🔴 **Jacob's call on the inverted gradient.** Do not patch, do not tune, do not flip a sign.
3. **The forecast layer scores each name as if its gap were independent.** The 2026-08-26 batch is
   the first hard evidence that this breaks when a complex-setting name prints the same night.
   The class is PENDING at 1/3 — **do not build a cross-name coupling term on one night.**
4. **GG sourcing remains the highest-value unblocking action.** But NVDA and PLAB both guide ONE
   QUARTER forward only, so GG is *structurally* unavailable for them — that is not a sourcing
   failure and must not be chased. Standing notes now record which names have this shape.
5. Un-audited by the mechanism standard: `CONF_FLOOR 0.55`, `EDGE_MIN 0.08`, the tier boundaries, the
   0.71/0.29 split, and **the ±15 washout bar — still the prime suspect.**
6. `catalyst/` public repo is **6 versions behind and unscrubbed** — real tickers in committed
   history. Needs an explicit go-ahead; nothing has been pushed.
