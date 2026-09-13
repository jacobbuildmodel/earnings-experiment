# PRE / CATALYST — HANDOFF
**Updated 2026-07-30 (early ET).** Supersedes the 2026-07-29 handoff.
Read this first; it is the source of truth for "where we left off".

---

## 0. CURRENT STATE — 60-SECOND VERSION

```
pre_engine.py      v1.5.6   sealed core + C13 REV-feed integrity (NEW, see §14)
pre_calcrisk.py    v1.3.0   payoff-asymmetry layer — DEMOTED TO SHADOW (logged, never decides)
pre_edgescore.py   v1.5.0   *** THE LIVE PRODUCTION SCORER *** §9.1 + §9.2 SHIPPED 07-30
pre_impliedmove.py v1.0.0   implied-move derivation + provenance + fail-closed decontamination
pre_expectations.py v1.0.0  expectations-bar DIAGNOSTIC (logged only, never trades)
pre_guidance.py    v1.0.0   GG construction + provenance contract (§15)
pre_edgar.py       v1.0.0   SEC EDGAR primary-source fetcher for GG (§15)
pre_vel.py         v1.0.0   VEL from SEC XBRL — fully automated (NEW, §17)
pre_batch.py       v1.0.0   *** THE BATCH RUNNER — clock guard + GG + VEL wired (§16) ***
pre_ledger.py      v1.5.3   append-only, market-model beta, hold-to-close shadow
```
**Tests: 316 pass** — `python run_tests.py` (47 engine + 59 calc-risk + 12 ledger + 60 edge
+ 76 guidance + 36 VEL + 26 batch).
**All four judgment legs are now sourced: REV · GG · VEL · WASH → 4/4 completeness reachable.**
**Track record: 3 / 8 = 38% idio-sign.** Below coin-flip. NOTHING is validated.
**Ledger: 93 rows / 40 entries / 53 outcomes. Nothing awaiting an outcome.**

> ⚠️ The 2026-07-29 AMC batch (MSFT/META/ARM/HOOD/QCOM/LRCX/FTNT/FICO) is **VOID** — see §14.
> It is a counterfactual, not a pre-registration, and adds nothing to the record.

---

## 1. STANDING OWNER DIRECTIVES — do not re-litigate these

| Directive | Detail |
|---|---|
| **NO portfolio caps** | Emit verdict + size unmodified. Jacob does his own risk management. Concentration is REPORTED (notional %-of-book) but never capped. Raised once, declined. |
| **Exit stays gap-capture** | Enter last session BEFORE the print, exit FIRST open AFTER. Hold-to-close is instrumented as a SHADOW measurement only. Proposed and rejected. |
| **Leave REV/GG/VEL signs alone** | The expectations-bar diagnostic logs; it does not trade. |
| **Paper vs real** | The 2026-07-29 10-name batch was PAPER (no capital). Say so in any writeup. |

---

## 2. THE STANDARD NOW IN FORCE (this is the big one)

> **Every component must be justifiable by MECHANISM alone, because none of them will ever be
> justifiable by data.**

Kill-switches arm at n≥15; `SIZE_BY_CONVICTION` needs n≥20/tier = 80 trades. At ~11 trades in
three weeks clustering to ~6 event-days, **those bars will never be reached.** "Log it and let
evidence decide" had become a way to ship unjustified components. Applying the mechanism test
removed roughly half the model in one session (see §4).

**`docs/POSTMORTEM_SOP.md` is BINDING** on every closed trade:
- **A** Observable-miss (fix input/scoring) · **B** Unobservable — information boundary
  (**patching FORBIDDEN**) · **C** Right thesis, wrong expression (fix exit/instrument only) ·
  **D** Random (**patching FORBIDDEN**)
- **THE ABSTRACTION TEST** — a fix ships only if (1) it would have prevented the LAST failure of
  the same type AND (2) it breaks no previously WINNING trade.
- **Anti-gaming clause:** you may not rescue a fix by asserting a favourable input.
- **The inversion:** when a call is wrong the FIRST hypothesis is "the model is wrong"; you must
  DISPROVE that before concluding "unlucky".
- **Distinction that matters:** the Abstraction Test governs *fixes invented in response to a
  failure*. The mechanism standard governs *whether a component belongs at all*. A mechanism cut
  does not need to pass Limb 1.

---

## 3. WHAT EXTERNAL REVIEW #2 FOUND (Opus, read the repo not my summary)

**Every material error pointed the same way — toward the model looking better.** Not deliberate;
it is what happens when the party that builds a thing also computes its scorecard.

1. **The backtest silently dropped 3 of 11 outcomes.** Entries de-duped by (ticker, event_date),
   outcomes looked up by entry-id → re-registered names orphaned their results. The dropped rows
   were **BOTH TAILS** (AEHR +35.04, NFLX −10.64, ASML +1.69).
2. **AMKR was registered AFTER its outcome was known** (logged 07-28T13:44Z, 15 min after the
   13:30Z open that printed its −14.52% gap). It carried an integrity hash indistinguishable from
   a real pre-registration, and it was the single row justifying a design change.
3. **THE LOGICAL ERROR TO NEVER REPEAT:** I quarantined the P&L as hindsight-contaminated and
   then trusted the TIER label from the same backtest. The tier is assigned by a function written
   *after* knowing the outcomes. **Contamination applies to every output of a post-hoc function,
   not just the money column.**
4. The `value` term (option richness) was 30% of the score and cannot forecast sign.
5. Idio was being reported under a "$ P&L" heading; the account earns RAW.
6. `implied_move` had no function, no bound, no provenance.

Two further de-dup layers found afterwards (same family): `event_date` was applied
inconsistently (AMC rows labelled with the EXIT day, previews with the PRINT day → one print
counted twice), and sign-layer rows with no exit spec were counted as events at all.
**Everything now keys on the trade window `(ticker, entry_close, exit_open)`.**

---

## 4. WHAT WAS CUT (all mechanism-argued, none tuned to sample P&L)

| Cut | Why |
|---|---|
| **`value`** (was 30% of score) | Option richness forecasts MAGNITUDE, never SIGN. Kept only as a short-side richness veto + log. |
| **`vrich`** (was 40% of positioning) | Identical category error; also populated on just 4/21 entries. |
| **SAT out of `directional`** | (a) category — SAT measures PRICE, not fundamentals; (b) **double-count**: SAT and `wash` come from the SAME two raw inputs, corr **+0.69**. That one observation was **mean 92% / median 56% of every score** (100% on NFLX, AEHR, SAP, INTC, GLW, PYPL). It is why the model was, in substance, *"buy beaten-down stocks."* |
| **All 18 sector weights** | Tested: changed **ZERO verdicts out of 21**. Unvalidatable at ~21 events / 6 sectors. |
| **IRM from the completeness denominator** | Since `value` stopped voting, IRM informs nothing on a LONG — yet a missing IRM was cutting long size. Docking you for lacking the input that was hurting you. |
| **`REVISIONS` from `FORWARD_VEL_BASES`** | Analyst revisions measure the **expectations BAR**, not the company's forward trajectory. Every other basis is company-reported. Exposed by VRT (see §6). Breaks zero winners. |

Also **REVERTED**: the guide-freshness gate I had shipped the day before — it failed both limbs
of the Abstraction Test (wouldn't have prevented AMKR; blocks AEHR, the only winner). I had made
its test pass by asserting `guidance_fresh=True` on AEHR, which is why the anti-gaming clause exists.

---

## 5. THE LIVE SCORER (`pre_edgescore.py` v1.5.0)

```python
# §9.2: renamed. This is NOT a fundamental read — with GG/VEL unsourced it is literally REV/4.
expectations_momentum = clamp(sector_weighted(REV + GG + VEL + FLAG) / 4.0, -1, 1)
value       = clamp((1.0 - IRM) / 0.45, -1, 1)      # COMPUTED, LOGGED, does NOT vote
positioning = wash                                   # washout only (vrich removed)

raw_edge    = 0.71*expectations_momentum + 0.00*value + 0.29*positioning
completeness= verified({REV, GG, VEL, WASH}) / 4
confidence  = 0.55 + 0.45*completeness               # FLOOR 0.55 — never observed to bind
edge_score  = raw_edge * confidence

if hard_gate_fail:                     NO_TRADE
elif abs(edge) < 0.08:                 NO_TRADE      # symmetric dead-band: genuinely no read
elif edge >= +0.08:                    BUY
elif edge >  -0.20:                    NO_TRADE      # §9.1 ASYMMETRIC short band (= STANDARD
                                                     # tier floor; 0 new params). Shorts fight
                                                     # drift + the announcement premium.
elif short_ok:                         SHORT
# short_ok = (expectations_momentum < 0) and (positioning <= 0)
#   v1.5.0 CUT `value < 0` — on an equity short you are short DELTA, not VEGA, so straddle
#   richness cannot touch the payoff. Measured: cutting it moved 0 of 40 recorded verdicts;
#   the binding clause was always `expectations < 0` (true on 3/40 vs richness on 16/40).
```
**SIZING (v1.4.0 — the fix that mattered):**
```python
budget       = FLAT_RISK_BUDGET(0.50%) * confidence   # CONVICTION does NOT size
sizing_gap   = m.gap_bad_case or m.avg_abs_open       # BAD CASE, not the mean
shares       = (budget * capital) / (sizing_gap/100 * price)
```
- **CONVICTION** (|edge|) is LOGGED but must NOT size — `SIZE_BY_CONVICTION = False`, on the PRIOR
  that an unvalidated signal must not scale risk. (The old "tiers are inverted" justification was
  computed on the corrupt sample and is void.)
- **CONFIDENCE** (information completeness) DOES size. These are different quantities; conflating
  them once silently destroyed the layer's whole promise.

---

## 6. THE SIZING DEFECT AND ITS FIX — most valuable finding of the session

Sizing divided by `avg_abs_open`, the **MEAN** gap. That makes "risk budget" mean *the loss on a
TYPICAL print* — so any worse-than-typical print breaches it, and the breach scales with the
surprise. Measured over 17 scored events, |realized| / mean-gap **exceeded 1.0× on 3 and reached
2.02×**.

It also **mis-ranks names**: it sizes UP the quiet ones (where a surprise hurts proportionally
most) and DOWN the volatile ones. Live case: **KLAC** mean gap 3.03%, so a "0.5% risk" trade
bought **$2,479 — 13.8% of an $18k book**; it moved 8% and lost **2.6× its budget**. KLAC's gap
history is bimodal `[8.6, 7.1, 2.8, 2.6, 2.2, 2.0]` — mean AND p80 both sit in the quiet mode.

**Fix: `gap_bad_case` = the worst gap in the name's last 10 prints.** A budget must hold in a BAD
case; that is what makes it a budget. Positions shrink 1.2–2.4×. **That is not lost risk appetite
— appetite belongs in `FLAT_RISK_BUDGET`, an explicit dial.** On its first live outing (SOFI /
VRT / CTSH) **all three stayed inside budget for the first time.**

**ALWAYS pass `gap_bad_case`** on new runs, or the model falls back to the mean with a caveat.

---

## 7. TRACK RECORD (genuine live pre-registrations only)

| Call | Conv | idio gap | Result |
|---|---|---|---|
| AEHR BUY | LOW | **+35.04%** | ✅ |
| ASML SHORT | LOW | +1.69% | ❌ |
| NFLX BUY | MED | −10.64% | ❌ |
| CLS BUY | MED | +0.02% | ✅ |
| AMKR BUY | MED | −10.15% | ❌ **retro-registered — not a valid pre-registration** |
| SOFI BUY | STANDARD | −6.59% | ❌ |
| VRT BUY | HIGH | −6.93% | ❌ |
| CTSH BUY | STANDARD | **+3.96%** | ✅ |

**3 / 8 = 38%.** Shorts are **0 for 3** lifetime.
**BE / TER / KLAC / V were NEVER live pre-registrations** — logged as DRY_RUN previews; verdicts
only obtained by forcing the timing gate afterward. They are counterfactuals, not a record.

**The abstentions remain better than the bets.** 2026-07-29 batch: 4 of 7 abstentions correct
(JCI +3.95, AVTR +16.73, VRSK +3.10 would all have lost as shorts; BSX −7.30 and PG −4.20 avoided).
**BSX is the model's best save**: deeply washed (−43 vs XLV, 58% off high) but **0 up / 10 down**
revisions put it in the dead-band.

---

## 8. POST-MORTEM CLASSIFICATIONS — 2026-07-29

- **SOFI — Type B.** Beat (+43% rev, record originations), RAISED revenue guidance, but held the
  earnings outlook flat. Deciding variable = the guidance MIX, delivered in the print. Type B
  **forbids patching**.
- **VRT — Type A + B.** **MISSED revenue** ($3.27B vs $3.38B) while beating EPS and raising guidance.
  The miss is Type B. But the model's bullish read was **Type A**: VEL=+1 came from consensus
  revenue growth accelerating 28%→39% — *that is the bar being raised*, scored as bullish. Fixed by
  removing REVISIONS from `FORWARD_VEL_BASES`.

---

## 9. THE TWO PREMISE-LEVEL QUESTIONS — **APPROVED AND SHIPPED 2026-07-30** (edge-score v1.5.0)

Both were left alone deliberately for weeks. Answers below are **mechanism arguments**, because
neither will ever get a statistical one. Owner approved both on 2026-07-30; both are now LIVE in
`pre_edgescore.py` v1.5.0 with 12 new locking assertions (suite 166 → **178**).

> ### ⚠️ MEASURED IMPACT: **0 of 40 recorded verdicts changed.** (`_impact_v150.py`)
> Comparing the v1.4.0 and v1.5.0 cascades on **identical stored inputs** — not against the
> stored `action`, which would confound the calc-risk→edge-score layer switch — **not one stance
> moves.** That is not a null result, it is the *proof* of the §9.1 finding below:
>
> | on the 40-entry record | count |
> |---|---|
> | negative edge (a short candidate at all) | **5** |
> | richly priced, i.e. the cut veto would have PASSED | **16** |
> | negative `expectations_momentum` — what the leg actually needs | **3** |
>
> The richness veto was passing on 40% of rows. `expectations < 0` was true on 7.5%. **The veto
> was never the binding constraint** — removing it was right on mechanism and changes nothing in
> practice. The short leg stays structurally dead until the remaining clause is dealt with, and
> that is blocked on §9.2 / GG sourcing.

### 9.1 Should the SHORT leg exist? — **YES, but not the one that exists now.**

**The richness veto has no mechanism and should be cut.** `short_ok` requires `value < 0`, i.e. a
richly-priced straddle. For an equity short you are short DELTA, not short VEGA — you never pay
the straddle, so its richness cannot touch your payoff. This is the *same category error* already
cut twice (`value` from the directional sum in v1.1.0; `vrich` from positioning in v1.2.0): a
VARIANCE estimate used as a DIRECTION filter. Cutting it breaks no winner, trivially — **there
are no short winners to break** (0-for-3), so Abstraction-Test limb 2 is satisfied by construction,
and limb 1 is waived because this is a mechanism cut, not a fix invented after a loss.

**But the veto is not what is actually killing the short leg.** The 07-29 batch made this visible:
FICO scored **edge −0.225** with `positioning = −1` and was still refused — because
`directional = 0`. And `directional < 0` **requires a negative REV**, since GG and VEL are
unsourced on every name in every recent batch. So:

> The short leg is gated on net-negative analyst revisions — which by §9.2 is the model's
> *least* defensible term, and the one whose sign is most likely backwards for a gap.

That is a stronger objection than Jacob's. The veto is indefensible; the `directional < 0` clause
is *worse*, because it is both binding and mis-specified.

**SHIPPED (v1.5.0):**
1. ✅ **Cut** `value < 0` from `short_ok` — no mechanism, breaks no winner.
2. ✅ **Replaced** with an ASYMMETRIC dead-band, `SHORT_EDGE_MIN = 0.20`. The defensible reason
   shorts clear a higher bar is the **positive unconditional equity drift plus the positive
   average abnormal return around earnings announcements** — a base-rate prior, correctly
   expressed as a threshold, not smuggled in as a vol filter. **Parameter cost: ZERO** — it is
   `next(lo for lo, name, _ in TIERS if name == "STANDARD")`, i.e. it reuses the existing tier
   boundary rather than inventing a number. In words: *a short may not be taken at EXPLORATORY
   conviction at all.*
3. ⏳ Clause `expectations < 0` **retained but blocked on §9.2** — it is now the sole gate, and
   the impact table above shows it is the one that matters (3 of 40 vs 16 of 40). Do not defend
   it until §9.2's GG work lands. FICO stays NO_TRADE on the 07-29 batch for exactly this reason.

### 9.2 The fundamental terms are all analyst expectations — **TRUE, and worse than stated.**

Confirmed, and the 07-29 batch shows the end state concretely. Since v1.5.5 removed REVISIONS from
`FORWARD_VEL_BASES`, and GG has been `None` on **100% of names in the last two batches**:

```
directional  =  (REV + GG + VEL + FLAG) / 4  =  REV / 4        <- literally one number
```

So the "multi-factor fundamental read" is one analyst-revisions figure divided by four. The V2/V3
counterfactuals frozen in `_variants0729b.json` decompose every name into its analyst half and its
price half, and the result is stark: **no name in the batch had both.** META's entire score is REV;
FICO's entire score is `wash`. This is not a multi-factor model — it is two single-factor models
that never overlap, wearing one name.

**But it does NOT gut the model, and the sign should NOT be flipped.** Two real mechanisms oppose:
- *Bullish* (current): revision momentum is an INFORMATION proxy — analysts revise up on improving
  channel checks and company commentary. Revision momentum / PEAD is among the most durable
  documented anomalies.
- *Bearish* (the bar argument): a raised consensus is a higher hurdle, and the gap is scored
  against the bar, not against last year.

Both are true; they oppose; **n=10 cannot adjudicate.** And the only forward evidence there is
(§10) points the *wrong way for the bar argument* — max-raised-bar names gapped **+8.31%** mean.
Flipping the sign on a hypothesis the data currently contradicts would be exactly the
sample-chasing the mechanism standard exists to prevent.

**SHIPPED (v1.5.0):**
1. ✅ **Renamed `directional` → `expectations_momentum`** everywhere. Free, and it stops the
   category error propagating. `W_DIRECTIONAL` / `DIRECTIONAL_NORM` / `.directional` survive as
   deprecated aliases because dated drivers in `runs/` are immutable history, and `register()`
   writes BOTH keys so the 40 existing ledger rows keep resolving. Same number, two keys —
   never let them diverge.
2. ✅ **Sign kept.** It has a mechanism (revision momentum as an information proxy) and the only
   forward evidence available (§10) contradicts the opposing hypothesis. Flipping a sign on a
   hypothesis the data currently contradicts is the sample-chasing the standard exists to prevent.
3. ⏳ **The real fix is not a sign flip — it is GG.** Guidance direction is COMPANY-reported,
   knowable pre-print, and would be the model's first genuinely non-analyst directional term.
   It has been `None` on every name for two batches running. **Highest-value unblocking action
   in the system**, and it is a sourcing problem, not a modelling one. NOT DONE.
4. ✅ Stated plainly, in the module header: the model has exactly **two** independent signals
   (expectations momentum, price positioning). Two is a fine number. Claiming five was the problem.

### 9.3 Trade rate
**~81%** on the 07-29 BMO batch at the 0.08 dead-band — but **12.5% (1 of 8)** on the AMC batch,
because with VEL and GG both unsourced the dead-band swallows everything. The trade rate is not a
tuned property; it is a hostage of how much of the input vector happens to be populated that day.

---

## 10. THE EXPECTATIONS-BAR DIAGNOSTIC — first forward data is AGAINST it

Pre-registered hypothesis: *a higher pre-print bar → more negative gap.* `bar = sign(rev_balance)
+ sign(price_run)`. **Logged only, never trades.** Falsifier is fixed in code (`BAR_HYPOTHESIS`).

**FORWARD n = 10 / 30:**
| bar | n | mean idio |
|---|---|---|
| **+2 (max raised)** | 2 | **+8.31%** ← wrong direction |
| 0 | 3 | +0.04% |
| −1/−2 (low) | 5 | −6.78% |

**AVTR carried the maximum raised bar and gapped +16.73%** — the cleanest contradiction available.
n=10 of 30, so not a refutation yet; **but the first honest evidence VINDICATES the current
REV/GG/VEL signs**, which is the opposite of what I expected when I built it.
Backfilled rows (n=43) are marked `backfilled: True` and **can never be evidence** — the hypothesis
was derived from those same outcomes.

---

## 11. STANDING OPERATIONAL RULES

- **Score on the OPEN gap, never the close.** Jacob usually quotes intraday/close prices; the model
  exits at the open and they diverge materially (07-29: HUM open −0.13% vs close −6.14%; KLAC open
  −6.91% vs close −2.66%). **Always fetch the actual open.**
- **Pre-market ≠ the open.** 07-29 drift: BE +11.33→+9.99, KLAC −8→−6.91, V −0.44→−2.62.
- **Never create a ledger entry after its own event.** `_is_retro()` detects it; `backtest_edgescore.py`
  excludes such rows.
- **Web-source before fail-closed** on a covered name with a thin feed.
- **Beta is estimated** on a clean pre-event window (60d, 21d buffer, clamp [0.2, 3.0]); β=1 is a
  FLAGGED fallback. Real betas run 0.39–2.42 — it matters.
- **`implied_move` fails closed** when decontamination would remove >50% of the straddle's variance
  ("an estimate whose correction exceeds its result is not a measurement"). On 2026-07-29 that
  refused 4 of 10 names whose only expiry was +17 trading days out.

---

## 12. IMMEDIATE NEXT STEPS

1. **Nothing is pending scoring.** Ledger 93 rows, zero awaiting an outcome.
2. ✅ **§9.1 and §9.2 approved and shipped 2026-07-30** (edge-score v1.5.0, 178 tests).
   Measured impact: 0 of 40 recorded verdicts move — see the box in §9.
3. **SOURCE GG — now the single blocking item.** Per §9.2.3 this is the highest-value action in
   the system: the only directional term that is not analyst opinion, and the reason the short
   leg is still dead after §9.1 landed. It is a data-sourcing job, not a modelling one. Until it
   exists the model runs at 2/4 completeness with two signals forever.
4. **Re-run the C13-hardened stack on the NEXT AMC batch, registering BEFORE the print.** The
   pipeline is built and green; the 07-29 attempt was voided on timing alone (§14), not on
   substance. Pull inputs AND freeze verdicts inside the same pre-print window next time.
5. Un-audited by the mechanism standard: `CONF_FLOOR 0.55` (never binds), `EDGE_MIN 0.08`, tier
   boundaries, the 0.71/0.29 split, the 13-param skew overlay (logged, never used).

### 12.6 `catalyst/` PUBLIC REPO — AUDITED 2026-07-30, **NOT SYNCED, NOT PUSHED**
Read-only inspection only. Nothing was committed, pushed, or scrubbed — publishing is Jacob's
call, and a history rewrite is destructive.

| Finding | Detail |
|---|---|
| **Behind by 6 versions** | Public HEAD carries engine **v1.5.0**; local is **v1.5.6**. |
| **Missing the entire live layer** | `pre_edgescore.py` (THE production scorer), `pre_impliedmove.py`, `pre_expectations.py`, `run_tests.py`, `INDEX.md`, `docs/POSTMORTEM_SOP.md` are **absent from the public repo**. What is currently published is the *demoted* stack. |
| **Dirty working tree** | 9 tracked files modified + `calcrisk_selftest.py` untracked, all uncommitted. |
| **Real tickers in committed history** | Confirmed in `git log -p`: **AEHR** and **NKE** appear in `docs/PRE_UPGRADE_PLAN.md`, `docs/skew_overlay_design.md` and `pre_calcrisk.py` comments. Only **2 commits exist**, and both are contaminated — a scrub means rewriting 100% of history and force-pushing. |
| **Ledger safety** | `ledger.jsonl` is gitignored and absent from `git ls-files`. Clean — no live record has leaked. |

**Recommendation:** since both commits are contaminated, the cheapest honest fix is to **re-init
the public repo from a scrubbed snapshot** rather than surgically rewriting history. Either path
needs an explicit go-ahead; say the word and I will prepare the scrubbed tree for review *before*
anything is pushed.

## 14. THE 2026-07-29 AMC BATCH — VOID, AND WHAT SURVIVES IT

**8 names, all AMC 2026-07-29:** MSFT, META, ARM, HOOD, QCOM, LRCX, FTNT, FICO.
Owner brief: paper only, stress the model, find the loopholes. Driver:
`calc_run_2026_07_29b.py` (registration hard-disabled in code).

### 14.1 Why it is VOID — timing, and nothing else
```
_batch0729b.json / _opt.json   pulled 10:13–10:14 ET 07-29   INPUTS — genuinely pre-print
pre_engine.py C13              written      19:28 ET 07-29   3.5h AFTER the 16:00 prints
calc_run_2026_07_29b.py        written      19:39 ET 07-29   3.5h AFTER the prints
_variants0729b.json            written      19:39 ET 07-29   3.5h AFTER the prints
```
The inputs are clean; the **verdicts are not**. They came from code authored after the outcomes
were public, and C13 is verdict-changing (it refuses 2 of 8). Not having looked at the results is
not a defence — **§3.3: contamination applies to every output of a post-hoc function.** Registering
this would have been a deliberate repeat of the AMKR error. **Nothing was written to the ledger.**
Class: counterfactual preview, same as BE / TER / KLAC / V. It may never be cited as evidence.

### 14.2 What survives — C13, because it is a statement about the INPUT FEED
Truth-value independent of any outcome. From the 10:13 ET pull, **2 of 8 revision feeds are corrupt**:
- **MSFT** — `up_7d = 10` against `up_30d = 8`. The 7-day window is a *subset* of the 30-day
  window, so this is arithmetically impossible, not noisy.
- **FTNT** — `38 up / 0 down` against **37 covering analysts** → R = **+1.03**, outside the domain
  of a net-fraction-of-panel metric. The signature of a vendor period-roll re-basing. Ungated it
  scores **REV = +2, the maximum bullish fundamental read the model can produce** — and FTNT was
  simultaneously **+63pts extended vs XLK**, the most stretched name in the batch. The corrupt
  input was pointing the model long into the worst possible name.

**Shipped as C13** (`pre_engine.rev_feed_integrity`, engine **v1.5.6**): two definitional rules,
**0 new parameters**, fails closed to `INPUT_INVALID`. It refuses the name rather than nulling REV
— because at the edge-score layer merely *zeroing* a rejected REV is **not** conservative: if REV
opposed the other terms, removing it can *increase* |edge| and manufacture a trade. Refusing cannot.
**Checked against all 93 ledger rows: zero violations, so no historical winner is disturbed.**
15 new assertions; suite 151 → **166 pass**.

> The gap this closes: after v1.5.5, the four revision counts are the *only* surviving fundamental
> input, feeding 71% of the live score — and they were the one decision-carrying input with **no
> validation of any kind**. C1 bounded `covering_analysts` and `implied_move`; the numbers that
> actually move the score were unchecked.

### 14.3 The other loopholes the batch exposed (all outcome-independent)
1. **The model had ONE opinion on eight mega-cap prints** (META, EXPLORATORY, 0.39% risk). With
   GG and VEL unsourced, `directional = REV/4`, and the 0.08 dead-band absorbs everything else.
   The 81% trade rate of the previous batch was an artifact of *which inputs happened to be
   populated*, not of a calibrated threshold. See §9.3.
2. **The SHORT leg is structurally unreachable, and the richness veto is not why.** FICO: edge
   **−0.225**, `positioning = −1`, refused because `directional = 0`. Full argument in §9.1.
3. **C4 reconciliation was a no-op** — `Truth` was populated from the same pull as `Judgment`.
   A self-consistency check is not a cross-source check. Declared in the run header; genuinely
   fixing it needs a *second, independent* feed.
4. **The model cannot see the most striking data in the batch.** LRCX front-expiry put/call OI
   **14.89**, ARM **7.07** with 12% of float short. Logged into the Stage-1 skew diagnostic and
   used for nothing, per design.
5. **3 of 8 implied moves REFUSED** by the decontamination guard (ARM 58% of variance stripped,
   QCOM 90%, FICO 89%). The guard is working; the coverage is the problem.

---

## 15. GG SOURCING — BUILT 2026-07-30 (`pre_guidance.py` + `pre_edgar.py`, 64 assertions)

Owner asked: **python or outsource?** Answer: **Python, via SEC EDGAR** — and it beats
outsourcing on every axis. EDGAR *is* the primary source; a vendor's guidance field is that
vendor's READING of this document. It is free, needs no key, and every record carries the
accession URL so a GG can be re-derived years later. A paid feed gives a number you cannot
re-check. Verified working end-to-end on 2026-07-30.

### 15.1 THE DEFINITION
```
GG = direction of the company's OWN latest guidance vs the company's OWN PRIOR guidance
     for the SAME period.       +1 RAISED · 0 MAINTAINED · -1 CUT · None UNSOURCED
```
**Never against consensus.** A guide below the street but above the company's own prior guide
is a **RAISE**. Comparing to consensus would rebuild §9.2 inside its own fix, so
`comparison` must be `OWN_PRIOR_GUIDANCE` and every analyst-flavoured basis (`CONSENSUS`,
`ESTIMATE_REVISIONS`, `ANALYST`, `STREET`, `WHISPER`, `BUYSIDE`) is **refused by name**.

**Mechanism (why the term deserves to exist):** a company revising its OWN outlook is
management acting on private information about its own order book, pricing and costs. That is
the issuer, not an observer; a decision, not an estimate; and it is legally required to be
truthful. The argument depends on no sample — which is the point.

**Ranges are handled parameter-free:** compare MIDPOINTS; exact equality → MAINTAINED, any
difference → its sign. A narrowed range around an unchanged midpoint correctly reads 0. **This
module adds ZERO scoring parameters** — like `pre_impliedmove` it builds an input, it doesn't score.

### 15.2 THE PERIOD-MATCHING PROBLEM (found while building; it changed the definition)
Most US issuers guide **one quarter ahead**: the Q3 release guides Q4, the Q4 release guides Q1.
So each QUARTER is guided exactly once and has **no same-period predecessor to compare against**.
Confirmed on QUALCOMM's 2026-07-29 8-K — Q4 FY26 guidance only, no annual outlook.

The comparison that DOES exist is the **FULL-YEAR guide, re-issued at every quarterly release
for the same fiscal year**. That is what "raised full-year guidance" means, and it is what the
market reacts to.

| priority | source | note |
|---|---|---|
| PRIMARY | full-year guide vs the same FY's guide in the prior release | always available *if* the issuer guides annually |
| STRONGEST | any mid-quarter revision / pre-announcement | rare; flagged FRESH |
| UNUSABLE | next-quarter guide with no same-period prior | GG stays None |

**GG coverage is PARTIAL BY CONSTRUCTION.** Annual guiders (most large caps) yield a GG;
one-quarter-at-a-time issuers (QCOM, much of semis) do not. Already handled correctly — an
absent GG lowers completeness and shrinks the position rather than fabricating a zero.

### 15.3 WHAT IS AUTOMATED vs WHAT IS NOT — deliberately
- **Automated:** locate the earnings 8-K (Item **2.02** = Results of Operations — an exact
  filter, not a date guess), or a **6-K** for foreign private issuers; pull the EX-99 press
  release; extract the outlook section; detect revision language ("raising our full year
  guidance"); return everything **with its citation pre-filled from the fetch**.
- **NOT automated:** parsing the numbers into a verdict. Guidance prose is not reliably
  machine-parseable (ranges, GAAP vs non-GAAP, segment tables, footnoted exclusions), and a
  regex that silently mis-reads a range would inject a fabricated value into the one term built
  to be unfabricated. The numbers are read from the returned excerpt; because the provenance
  fields come from the fetch, **the citation cannot be typed by hand**.

### 15.4 MEASURED COVERAGE (all 8 names of the 07-29 batch, 2026-07-30)
**8 / 8 retrieve two releases; 7 / 8 reach a named guidance section** (ARM's 6-K primary doc
carries no recognised heading — reported, not fabricated). FICO's revision language was
auto-detected: *"raising our full year guidance"*. Two real bugs were found and fixed by this
test, both of which had been failing **silently**:
- **Exhibit naming is not standardised.** `msft-ex99_1.htm` · `exhibit991erq32026.htm` ·
  `qcom062826erex991.htm` · `lrcx_exhibitx991xq4x2026.htm` are all the same thing. The obvious
  `r"ex-?99"` matches **two of four** — FICO and LRCX returned "no EX-99 exhibit" on filings
  that plainly had one.
- **Foreign private issuers file 6-K, which carries no item codes at all.** Filtering on
  8-K Item 2.02 was silently dropping **every non-US name** (ARM) from GG coverage entirely.

### 15.5 FIRST LIVE GG RUN — 8 names, 2026-07-30 (`gg_run_2026_07_30.py`)
Comparison: the FY guide in each name's 2026-07-29 release vs the FY guide in its prior
(April/May) release. **This is the guidance now STANDING, so it is the GG for each name's NEXT
print (late Oct).** It is forward-looking for that purpose and must NEVER be attached to the
voided 07-29 batch. Every figure is transcribed from the cited accession URL.

| ticker | GG | driver (verbatim from the filing) |
|---|---|---|
| **FICO** | **+1** | FY26 revenue $2.45B → **$2.53B**, non-GAAP EPS $40.45 → **$42.43**. The release prints a two-column *"Previous / Updated Fiscal 2026 Guidance"* table — both sides in ONE document. Cleanest case in the batch. |
| **FTNT** | **+1** | FY26 revenue $7.71-7.87B → **$8.02-8.18B**, EPS $3.10-3.16 → **$3.41-3.47**, billings $8.80-9.10B → **$9.35-9.55B**. Three metrics, all raised. |
| **HOOD** | **+1** | FY26 adj. opex+SBC $2.700-2.825B → **$2.675-2.775B**. *"we are lowering and tightening"*. **Costs down = bullish** — only correct because of the polarity fix. |
| **META** | **−1** | FY26 total expenses $162-169B → **$165-169B** (*"raising the lower-end of our expense outlook"* for $2.4B legal charges); tax rate 13-16% → **15-17%**. CAPEX $125-145B → $130-145B was **refused as two-sided**. |
| MSFT | None | Guidance is **not in the 8-K**: *"Microsoft will provide forward-looking guidance … on its earnings conference call and webcast."* Delivered orally; EDGAR does not carry it. |
| QCOM | None | Guides **one quarter ahead only** (Q3 FY26, then Q4 FY26). No same-period prior, no annual outlook. Exactly the §15.2 case. |
| LRCX | None | Same shape as QCOM — quarter-ahead only. **Semis as a group guide this way.** |
| ARM | None | Foreign private issuer (6-K); no recognised outlook section in either retrieved doc. Needs the IR deck, not EDGAR. |

**GG obtained on 4 of 8 (50%).** Every miss has a stated, specific reason — an absent GG lowers
completeness and shrinks the position; it never fabricates a zero.

> **THE POLARITY BUG, found by running this on real filings.** `bucket()` originally read
> "midpoint up → +1" for *every* metric. That is right for revenue and **backwards for costs**.
> META's only same-period FY guides are EXPENSES and CAPEX, so the naive rule would have scored
> a $2.4B legal-charge cost overrun as a **bullish company raise**. HOOD is the mirror: it
> LOWERED opex, which is bullish. Fixed with an explicit `POLARITY` table; unknown metrics and
> two-sided ones (CAPEX) **fail closed** rather than defaulting to higher-is-better. 16 new
> assertions, both pinned to these two real filings. This is the third silent sign error the
> model has found in itself, and the first one caught *before* it ever priced a trade.

### 15.6 WHAT REMAINS
Reading the guidance numbers per name at run time and filling in `GuidanceRecord`. That is a
research step inside each batch run, not a build step. Freshness is computed and **never gates**
— the freshness gate failed both limbs of the Abstraction Test and stays reverted.

---

## 16. THE BATCH RUNNER — `pre_batch.py` v1.0.0 (2026-07-30). **READY.**

One command, one path. Replaces the copy-a-dated-run-file workflow that let the 07-29 batch be
scored after its own prints.

```bash
python pre_batch.py --tickers META,FICO --event-date 2026-10-27 --session amc --gg-fetch
#   -> writes gg_inbox_2026-10-27.json : EDGAR excerpts + citations. READ it,
#      transcribe the numbers into gg_2026-10-27.json (schema printed by the command).
python pre_batch.py --tickers META,FICO --event-date 2026-10-27 --session amc
#   -> dry run; picks the GG file up automatically
python pre_batch.py --tickers META,FICO --event-date 2026-10-27 --session amc --register
#   -> freezes to the ledger. REFUSED if the cutoff has passed.
```

### 16.1 THE CLOCK GUARD — the reason this module exists
`--register` is **refused outright** once the session cutoff (16:00 ET AMC / 09:30 ET BMO) has
passed, with a message naming the batch as a counterfactual and citing §14. Verified: it refuses
a 07-29 AMC registration attempted on 07-30. Cutoffs are computed in **exchange time via
`zoneinfo`**, so DST is handled — a fixed −4 offset would put every January cutoff an hour wrong,
and that is asserted. A **dry** run on a past event is still allowed: that is how a legitimate
counterfactual gets built. **This is no longer "remember to check the clock".**

### 16.2 THE GG HANDOFF
`--gg-fetch` → read → `gg_<event_date>.json` → picked up automatically. If that file is absent
the batch still runs, with **GG = None DECLARED** per name — never silently 0, which would read
as "guidance is flat" when the truth is "not looked at". Polarity, the provenance contract and
the consensus refusal all apply through the runner (asserted end-to-end).

### 16.3 FIRST WIRED RUN — GG changes verdicts, exactly where predicted
Dry run, 5 names, GG loaded from `gg_2026-10-27.json`:

| name | GG | edge | stance | note |
|---|---|---|---|---|
| **META** | **−1** | **−0.315** | **SHORT** (STANDARD) | **the first SHORT the model has produced since §9.1 shipped** |
| HOOD | +1 | +0.158 | BUY | conf **0.89**, 3/4 complete |
| QCOM | None | +0.138 | BUY | conf 0.78 — no GG available (semis guide one quarter ahead) |
| FICO | +1 | −0.100 | NO_TRADE | GG lifts `exp` to +0.25 but the name is EXTENDED (pos −1); lands inside the asymmetric short band |
| FTNT | +1 | — | NO_TRADE | **C13 INPUT_INVALID** — verified guidance cannot rescue a corrupt revisions feed. Fails closed, correctly. |

> **This closes the §9.1 loop.** Cutting the richness veto moved 0 of 40 verdicts because the
> binding clause was `expectations < 0`, and `expectations` was REV/4 — which is almost never
> negative. **GG is what makes that clause reachable.** META shorts on a company-issued expense
> raise and tax-rate raise, not on analyst opinion and not on vol richness. §9.1 was inert until
> §9.2's fix landed; now it isn't.

**Confidence rises 0.78 → 0.89 (completeness 2/4 → 3/4) on GG-sourced names — the first time the
model has run above half information.**

⚠️ Those numbers are a WIRING TEST: current market data against a placeholder October event
date. They are not a tradeable output and were not registered.

### 16.4 STATUS
All four legs now source. See §17 for VEL.

---

## 17. VEL SOURCING — `pre_vel.py` v1.0.0 (2026-07-30). **DONE, and FULLY AUTOMATED.**

**Why this one automates when GG could not:** GG lives in press-release PROSE and needs a human
read. VEL lives in the company's own **XBRL facts** — structured, typed, dated, SEC-filed. There
is no parsing ambiguity for a fabrication to hide in, so this module fetches *and* buckets end
to end. Source: `data.sec.gov/api/xbrl/companyconcept` — free, official, no key.

### 17.1 THE DEFINITION
```
VEL = the ACCELERATION of the company's contracted forward book (RPO, ASC 606).

  g_now  = RPO(t)   / RPO(t-4q) - 1        g_prev = RPO(t-1q) / RPO(t-5q) - 1
  delta  = (g_now - g_prev) in bp    ->    +1 if >= +400 · -1 if <= -400 · else 0
```
Acceleration, not level, for two reasons: the ±400bp band in `PARAMS` is already a band on a
*change* in growth, and the AEHR lesson was exactly that a book can accelerate while trailing
revenue collapses. **Reuses `VEL_UP_BPS`/`VEL_DN_BPS` — ZERO new parameters.** Basis is
`BACKLOG`, which C12 accepts as forward even on order-driven names.

### 17.2 THE CONCEPT-MEANING TRAP — availability is not meaning
`ContractWithCustomerLiabilityCurrent` resolves for **ROBINHOOD at $12-16 BILLION**. Those are
**broker customer balances**, not a forward revenue book. Feeding that in would have produced a
confident, enormous, meaningless VEL. So exactly ONE concept is trusted by default —
**`RevenueRemainingPerformanceObligation`**, which is *defined* as consideration on contracts not
yet recognised and means the same thing for every filer. Deferred-revenue variants are a weaker
proxy, valid only for subscription/contract businesses and meaningless for brokers/banks/insurers;
they require a per-name opt-in **with a stated reason**. Everything else fails closed.

### 17.3 TWO GUARDS, BOTH ADDED BECAUSE THE FIRST REAL RUN GOT THEM WRONG
- **RETRO** — every XBRL fact carries its `filed` date; anything filed on/after the event is
  discarded. A 10-Q lands after the 8-K, so pre-print the newest available RPO is the *prior*
  quarter's, which is correct. History is de-duplicated to the **earliest** filing per period,
  so a later restatement can never rewrite what was knowable at decision time.
- **STALENESS** — **QUALCOMM stopped reporting RPO in 2022**, and the first build cheerfully
  computed a VEL from a four-year-old series. A dead series does not announce itself; it just
  returns its final value forever. Limit is `183 + 60` days — two fiscal quarters plus filing
  lag. Derived, not tuned.

### 17.4 FIRST LIVE VEL RUN (event 2026-10-27)
| ticker | VEL | forward book YoY |
|---|---|---|
| **MSFT** | **−1** | +97.2% → +82.4% (−1,480bp) — decelerating off an extraordinary base |
| **FICO** | **−1** | +40.0% → +14.7% (−2,536bp) |
| FTNT | 0 | +11.8% → +14.8% (+295bp — inside the band) |
| LRCX | 0 | +10.8% → +10.5% (−30bp) |
| ARM | 0 | −6.9% → −4.9% (+201bp) |
| QCOM | None | series DEAD since 2022-12-25 |
| META / HOOD | None | no RPO; proxy needs an explicit opt-in |

**VEL verified on 5 of 8 — better coverage than GG (4 of 8), and it needs no human step.**

> **FICO is the payoff case: GG +1 (guidance RAISED) against VEL −1 (forward book DECELERATING
> hard).** Those are both company-reported and they genuinely disagree — management is guiding up
> while the contracted book slows. Neither REV nor `wash` can see that. **FICO now runs at 4/4
> completeness, confidence 1.00 — the first time the model has had full information on any name.**
>
> ⚠️ **CORRECTION (added after the 07-30 post-mortem, §18).** That VEL −1 rests on the RPO for
> period-end 2026-06-30, which was **FILED 2026-07-29 — with the print itself.** It was NOT
> knowable before the 07-29 print, and the retro guard correctly refuses it for that event.
> Pre-print, FICO's VEL was **0** (book still accelerating, +37.5% → +40.0%). So this
> disagreement is an input for FICO's NEXT print, exactly as §17.4 is dated — it did not and
> could not have called the −20% move on 07-30. Do not read it as a predictive hit.

### 17.5 THE RUNNER
`pre_batch.py` now runs **[3/5] GG** (human-read) then **[4/5] VEL** (automated) and reports
`GG verified n/N · VEL verified n/N · BOTH n/N`. Optional
`vel_overrides_<event_date>.json` opts a name into a proxy concept:
`{"TICKER": {"concept": "...", "reason": "..."}}` — never for a broker/bank/insurer.

---

## 18. POST-MORTEM — 8 names, AMC 2026-07-29 → open 2026-07-30 (`postmortem_0729b.py`)

**COUNTERFACTUAL. Nothing was written to the ledger; the record stays at 93 rows / 3-of-8.**
The batch was VOID (§14), so these stances were never pre-registrations and cannot score.
Gap and beta methods are imported from `pre_postmortem` — the same ones the real record uses.

| ticker | stock | ETF | β | **IDIO** | close | void stance |
|---|---|---|---|---|---|---|
| LRCX | +26.13 | SMH +5.08 | 1.35 | **+19.25** | +11.36 | NO_TRADE |
| MSFT | +12.28 | XLK +3.75 | 0.22 | **+11.47** | +14.27 | NO_TRADE (C13 refused) |
| ARM | +15.43 | SMH +5.08 | 1.42 | **+8.21** | −3.37 | NO_TRADE |
| FTNT | +7.04 | XLK +3.75 | 0.46 | **+5.32** | +1.35 | NO_TRADE (C13 refused) |
| HOOD | +1.19 | XLF +0.25 | 1.95 | +0.70 | −0.43 | NO_TRADE |
| META | −10.22 | XLC −2.78 | 1.72 | **−5.44** | −3.87 | **BUY** ❌ |
| QCOM | −5.90 | SMH +5.08 | 0.94 | **−10.66** | −9.54 | NO_TRADE |
| FICO | −16.25 | XLK +3.75 | 1.00* | **−20.00** | −19.46 | NO_TRADE |

`*` FICO's beta failed the clean-window estimate and fell back to 1.0, FLAGGED.

### 18.1 THE UNCOMFORTABLE FINDING — this was not prudent abstention
**6 of the 7 abstentions moved ≥5% idio**, three of them ≥10%, on a night of enormous
dispersion (−20.0 to +19.3). The earlier claim that "the abstentions remain better than the
bets" (§7) does **not** survive this batch. The model was not being careful; **it was blind.**
The single bet it did place, META BUY, lost (−5.44).

### 18.2 GG AND VEL, COMPUTED PRE-PRINT — both wrong, on n=2
Recomputed with `event_date=2026-07-29` so the retro guards bite and only pre-print filings are
visible. Between them the two new legs produced exactly **two** directional calls:

| leg | name | pre-print call | realized idio | |
|---|---|---|---|---|
| VEL | MSFT | **−1** (book +107.6% → +97.2%) | **+11.47** | ❌ |
| GG | FICO | **+1** (FY26 rev guide $2.35B → $2.45B, raised April) | **−20.00** | ❌ |

Everything else was 0 or unsourced. **n=2, so this is not evidence — but it is the first
forward-ish reading on both legs and it points against them.** Contamination is weak-but-real:
the modules were built after the 07-29 prints, though before the 07-30 opens. The result being
*unfavourable* is the direction that is hard to fake, so it is reported prominently.

### 18.3 FICO — the sharpest lesson in the batch
FICO fell **−20.00% idio**. Traced through every configuration:

| configuration | expectations | edge | stance |
|---|---|---|---|
| as run (REV 0, no GG/VEL) | 0.00 | −0.225 | NO_TRADE — `expectations < 0` unmet |
| fully sourced (REV 0, **GG +1**, VEL 0, wash −1) | **+0.25** | −0.113 | NO_TRADE — GG pushed the edge *up*, further from a short |
| **`wash` only (V2 variant)** | — | **−0.225** | **SHORT** ✅ |

**`wash` alone called it; every fundamental leg blocked it, and GG actively made it worse.**
FICO was unshortable under all four-leg configurations because `expectations` was never
negative. This is §9.2 biting from the opposite side to §10's evidence: on this event the only
term *not* sourced from expectations was the only one that was right.

### 18.4 C13 COST TWO WINNERS — stated, not buried
C13 refused MSFT (**+11.47**) and FTNT (**+5.32**), both up. FTNT's corrupt feed was maximally
BULLISH (REV +2 from the re-basing artifact) and FTNT rose. **On this night the corrupt input
would have been right.** The mechanism argument is unchanged — an arithmetically impossible
feed is not a measurement, and being accidentally right once does not make it one — but the
cost is real and belongs in the record, not in a footnote.

### 18.5 SOP CLASSIFICATION
- **META BUY (−5.44) — Type B.** Revenue guided to $61-64B and expenses raised for a $2.4B
  legal charge; the deciding variable arrived in the print. **Patching FORBIDDEN.**
- **FICO abstention (−20.00) — Type A.** Observable pre-print: the name was +29.8pts EXTENDED
  vs XLK and `wash` scored it −1 correctly. The model *had* the signal and the fundamental
  legs overrode it. This is a live design question, not bad luck — it is §9.2 §9.1 territory
  and it needs Jacob's call, not a unilateral patch.
- **MSFT / FTNT (C13 refusals) — Type D for the outcome, but the gate is Type-A-proof:** the
  inputs were genuinely broken; the up-moves were not caused by the model being wrong about
  them.

---

## 19. THE FORECAST LAYER — `pre_forecast.py` v1.0.0. **IT NEVER ABSTAINS.**
**Owner directive, 2026-07-30, after the 07-29 post-mortem. Not optional, not a shadow.**

### 19.1 THE DIAGNOSIS
The stack had ONE output answering TWO questions:

| question | kind | may it abstain? |
|---|---|---|
| *what do I think will happen?* | **prediction** | **NO** |
| *should I put money on it?* | **bet** | yes |

Collapsing them meant that whenever the bet was unjustified, **the prediction vanished too**.
A prediction never made is never scored; a model whose predictions are never scored **cannot
improve** — which is precisely why version after version changed the verdicts and never the
outcomes. On a PAPER book abstention protects nothing and teaches nothing: it is pure cost.

The trade gates are UNCHANGED (they exist to protect real capital later). This layer runs
alongside and is graded on every event. **It never feeds the trade verdict** (asserted).

### 19.2 WHY 7 OF 8 WERE SILENT — the mechanical cause, per name
| name | idio | cause |
|---|---|---|
| LRCX | **+19.25** | excess −10.1 vs a **−15** bar. Missed by 4.9pts → positioning 0 |
| ARM | +8.21 | excess +13.8 vs a **+15** bar. Missed by 1.2pts |
| MSFT | +11.47 | C13 voided the feed → **silent**, not neutral |
| FTNT | +5.32 | C13 voided the feed |
| QCOM | −10.66 | REV 0, no GG (semis), VEL series dead → literally nothing |
| FICO | −20.00 | `wash` said SHORT; `expectations` overrode it |
| HOOD | +0.70 | correctly quiet |

**Three were threshold misses of 1–5 points on a ±15 bar that has never been audited, and two
were gates producing silence instead of a fallback.** That is not caution; it is a scoring
system whose default is mute.

### 19.3 WHAT THE FORECAST USES THAT THE TRADE LAYER THROWS AWAY
- **continuous** washout/extension distance instead of the ±15 step (recovers LRCX, ARM);
- **flow** — put/call OI and short interest, logged for weeks and never allowed to speak;
- a **direction-only REV read on C13-voided names** — refusing to *bet* on a broken feed is
  right, refusing to have an *opinion* is what made MSFT silent into +11.5%;
- **implied move as MAGNITUDE only** — never as direction; that category error is cut twice
  already and is not returning through this door.

### 19.4 HONEST FIRST RESULT — replay of 07-29, pre-print inputs only
**3 / 8 directional. That is coin-flip and is not dressed up.** Weights (0.55/0.35/0.10) mirror
the trade layer and were fixed BEFORE the replay; tuning them on n=8 is forbidden.

| basis | record | |
|---|---|---|
| EVIDENCED | **2/3** | called BOTH extremes: LRCX +19.25 ✅ and FICO −20.00 ✅ |
| WEAK | 1/3 | |
| COINFLIP | 0/2 | |

The gradient (EVIDENCED > WEAK > COINFLIP) is the right *shape* and is the first the model has
ever produced — but n=8 makes it meaningless as evidence. **Two misses worth watching, NOT
patching:** ARM and FTNT were both called DOWN on extension and both rose. "Extended →
mean-reverts down" failed twice out of two.

### 19.5 THE STANDING QUESTION THIS EXISTS TO ANSWER
*In what circumstances does a name gap >5%, and which way?* Every forecast carries a **regime**
label (`WASHED/SOFT/NEUTRAL/FIRM/EXTENDED` × `HIGH_MOVE/LOW_MOVE`), so
`pre_forecast.score()` slices accuracy by regime, conviction and basis. That question becomes
answerable only once every event carries a labelled call — which is what this layer guarantees.

Log is `forecasts.jsonl`, **separate from `ledger.jsonl`** so paper predictions can never
contaminate the capital track record.

---

## 20. FORECAST BACKTEST — 31 events. **THE CORE THESIS DOES NOT HOLD.**
`backtest_forecast.py`, run 2026-07-30. Largest sample PRE has ever had.

**CONTAMINATED — `pre_forecast` post-dates every outcome (§3.3). Not evidence, not an edge.**
It is run anyway because a *negative* result survives contamination: a signal that is flat, or
worse than a constant, cannot be rescued by the contamination running in its favour.

```
BASE RATE  15/31 gapped UP -> always guessing DOWN scores 51.6%
FORECAST   45.2% (n=31)                            -6.4pp  DOES NOT BEAT A CONSTANT
```

### 20.1 THE STRUCTURAL FINDING — a long bias, and it is NOT an outcome artifact
**The layer called UP 22 times and DOWN 9**, on a sample that split 15 up / 16 down. It calls
UP **71%** of the time on a coin-flip tape. That is a property of the scoring function, not of
the outcomes, so **this one finding is not contaminated at all.** `wash` is the dominant term
and `wash` is structurally long: beaten-down names get bought.

### 20.2 THE BUCKET THAT MATTERS — `WASHED/HIGH_MOVE`, **5/12**
The largest bucket, and **all 12 were called UP.** In its core regime the model has exactly one
idea — *buy the washout* — and it is a coin flip at best.

| result | names |
|---|---|
| miss (7) | NFLX −10.64 · AMKR −10.15 · BSX −7.30 · VRT −6.93 · SOFI −6.59 · NVTS −4.55 · RMBS −0.26 |
| hit (5) | AEHR **+35.04** · TER +15.95 · APLD +5.20 · SAP +3.66 · CLS +0.02 |

**Remove AEHR and the bucket is 4/11.** AEHR is the single trade that has carried the entire
narrative of this model since inception, and it is one observation inside its worst regime.

### 20.3 `NEUTRAL/LOW_MOVE` — **0/5.** Never once right.
KLAC −5.80 · PG −4.20 · SPGI −1.26 · CDNS −0.11 all called UP and all fell; VZ called DOWN and
rose. Small n, but 0-for-5 with a consistent long bias is the same disease as §20.1.

### 20.4 WHAT THIS MEANS — stated plainly
The model's central thesis is **"buy names that have been beaten down into a print."** Across
its own 31-event history that thesis is **5/12 in its strongest form and 45.2% overall, against
a 51.6% constant.** It is not a small calibration problem. Either:
1. `wash` has the **wrong sign** (a washed name into a print is falling for a reason), or
2. `wash` measures something real but **needs a discriminator** — a filter separating the
   washouts that bounce (AEHR, TER) from those that keep falling (NFLX, AMKR, SOFI), or
3. there is no edge here at all.

**This is premise-level and it is Jacob's call — I am not flipping a sign on a contaminated
backtest.** The forward log (`forecasts.jsonl`) is the instrument that will settle it, and as
of 2026-07-30 it holds 14 genuinely pre-registered forecasts.

### 20.5 IMMEDIATE RELEVANCE TO THE LIVE BATCH
Of the 14 names registered 2026-07-30, **COIN, TEM and BBAI sit in `WASHED/HIGH_MOVE`** — the
5/12 bucket — and all three are called UP. MSTR is `WASHED/LOW_MOVE` (3/4). **Roughly a third
of the live batch is concentrated in the model's worst-performing regime**, which is exactly
the thing to know before the results come in rather than after.

---

## 13. CLAIMS THAT MUST NOT BE MADE
❌ Black-Scholes / option pricing / IV modelling (implied_move is an INPUT; IRM is a ratio).
❌ "Event study" with statistical significance (market-model AR, estimated beta, no test statistic).
❌ Any ML / learned weights — every threshold is hand-set.
❌ Any backtested edge (n=8; a full-pipeline backtest is impossible without look-ahead).
❌ Programming proficiency by the owner (AI-assisted from written spec).
