# PRE — SUPERSEDED STATE BLOCKS
Moved out of `STATE.md` so the file the blind chat reads at every boot stays small.
Nothing here is retracted; it is history, not current state.

---

## Archived 2026-09-02 — from the 2026-08-09 session

## 🟢 SHIPPED 2026-08-09 (evening) — OWNER DECISIONS ON REVIEW #3

**1. UNITS — normalised by the legs actually populated.** `/4` was never arbitrary: it is the correct
normaliser for three populated legs and we run one, so this was **the GG/VEL sourcing gap expressing
itself as a silent gain error**, not an independent bug. A static /2 would hard-code the outage; a
doc restatement changes nothing. Now `sum(range of VERIFIED legs)` — self-correcting, no parameter.
**Sold honestly: it makes REV louder to demote washout, and REV is not validated either. It
reallocates authority between two unvalidated terms.** The claim is only that the model was doing
something other than what it said.
- 🔴 **Unanticipated side-effect, NOT silently corrected:** a lone ±1-range leg (GG or VEL alone) now
  **saturates the term on one notch** — APLD/AZN go HIGH → **MAXIMUM** on VEL=+1. Harm is limited
  because conviction does not size, but the label is inflated. **Owner's call. A third correction in
  one session is how the guide-freshness gate happened.**

**2. NEW GOVERNANCE TIER — `DEFECT`.** The LOGIC tier's 2-holdout bar is designed for *edge* claims,
and holdouts are years away — so **an arithmetic correction inherited an evidence bar it could never
clear, and the model became uncorrectable.** DEFECT: sole claim is "behaviour now matches
documentation", no edge asserted, holdouts waived, **full ledger re-score mandatory and published.**
The moment a DEFECT filing says "this should improve the hit rate", it is LOGIC and the holdouts return.

**3. LIMB 2 RE-AIMED — it protected the wrong OBJECT, not the wrong strength.** It vetoed **P&L
winners** inside a system whose own table says *"a winning trade can be a wrong thesis."* Now it
protects **theses CONFIRMED BY ATTRIBUTION**, reports the flip set **both ways**, and vetoes only
when a change breaks a confirmed thesis **and repairs nothing**. Unattributed winners get
**disclosure, not veto**. Hard clause: **at n=11 the flip set IS the training set — the net count is
COST evidence, never the reason to ship.** `dispose()` refuses a filing with no named mechanism.
- 🔴 **`thesis_confirmed` is a MANDATORY SOP field written on ZERO of 60 outcome rows.** Not
  "recorded and never consulted" — **never recorded.** `observe()` now carries it.

**4. KILL SWITCHES — sign × expectancy, never one replacing the other.** PAUSE only when **both**
are bad. **REVIEW** when they disagree: `sign<50% + expectancy>0` is the *expected* gap-capture
profile and must not auto-pause; `sign>=50% + expectancy<=0` is pennies-in-front-of-a-roller and is
the more dangerous, because the dashboard reads green. Plus: **expectancy −1.13% → −4.75% excluding
the largest winner.** The edge is one trade.

**5. QUEUED, NOT BUILT — one gate over BOTH B and D.** Not a D-gate: B and D are the same claim
(*"no action warranted"*) and gating them separately migrates the abuse a third time — to **Type C**,
already open and whose response explicitly *shields the signal*. At a one-open horizon there is
almost no expression to fix, **so C claims should be near-zero; if they are not, that is the tell.**
D limbs: inside-distribution (limb 3 inverted) · **not nameable** (naming it makes it A or B) ·
not-recurrent (limb 4 verbatim — the limb that lets D ripen) · a budget **tighter** than B's 30%.

**4/11 vs 5/15 was the VOID exclusion (CTSH), not attribution.** Pinned; not the thesis distinction.

**TESTS: 485 assertions, 11 suites, all pass.** Both gates green.

---

## 🔴🔴 EXTERNAL REVIEW #3 — THE MODEL IS LOSING MONEY AND HAD NO STATISTIC THAT COULD SAY SO

Verified in code, not accepted on assertion: `python verify_claims.py` (re-runnable, read-only).
**6 of 8 claims CONFIRMED, 2 REFUTED, 1 new finding produced by the verification itself.**

```
THE CLEAN RECORD  (void rows now excluded IN THE DATA, from pre_ledger.stats())
  n = 11 trades over 5 event-days     hit 4/11 = 36.4%
  avg win +10.51%   avg loss -7.79%   payoff 1.35
  EXPECTANCY -1.13%/trade             cumulative idio -12.47%   (before slippage)
  quoted-everywhere "5/15" INCLUDED 4 void rows and no expectancy at all
```

**Every statistic this model ever quoted about itself was a SIGN statistic.** 5/15 at 3:1 is a fine
model; 5/15 at 1.18:1 is dead. Nothing here could tell those apart — and the kill switch inherits it:
`idio-sign <50% -> PAUSE` fires on a profitable model and stays silent on an unprofitable one.
**Expectancy was computable from these rows the whole time.** Now in `stats()`.

### 🔴 THE TRIVIAL SHADOW WAS RUN FOR THE FIRST TIME AND IT IS THE WORST RESULT IN THE FILE
`REV>=+1 AND GG>=0 -> BUY` fires on 11 of 38 graded events: **2/11 up, mean idio −4.38%.**
**The only surviving fundamental signal is not uninformative in its own ledger — it points the wrong
way.** n=11 over few event-days, not conclusive. But with expectancy at −1.13%, the honest summary is
**no evidence either signal works, and weak evidence one is inverted.**

### 🔴 THE UNITS DEFECT — the published weighting is not the actual weighting
`expectations` spans **[−0.5,+0.5]** (REV/4, integer buckets); `positioning` spans **{−1,0,+1}**.
So 0.71/0.29 realizes as **0.1775 per REV notch vs 0.2900 for the washout flag — washout is worth
1.63 notches.** Verified: **a WASHED name with DETERIORATING revisions scores +0.0872 and BUYS.**
The system §2 claims to have dismantled was **not dismantled** — cutting SAT removed the double-count,
not the dominance. And it is the **same normalisation bug** the sector weights were killed for, still
live in the production scorer. Consequence: **MAXIMUM conviction is unreachable** on any REV-only
name (max 0.4999 vs 0.55) — that is the whole pharma/financial/consumer universe.

### 🔴 VOID STATUS EXISTED ONLY IN PROSE — the signature failure, in its purest form
STATE.md has said for weeks that the 07-29 batch and AMKR are void. **`ledger.jsonl` had no void
field.** Every statistic silently included them, including the kill-switch dashboard. Now fixed:
append-only `{"type":"void"}` rows, `stats()` excludes them **and reports how many**. 19 rows marked.
**A fact that lived in a document and not in the data plane, with every gate green the whole time.**

### REFUTED — do not carry these forward
- `corr(REV, positioning) = +0.026` over 53 entries. The reviewer's hypothesis that the score is a
  disguised value/mean-reversion construct is **not supported**; the two terms are near-orthogonal.
- **"COINFLIP 80% is just the up-drift"** is wrong: of 5 graded COINFLIPs, **2 UP / 3 DOWN**.
  `basis=COINFLIP` means |signal|<0.10, not signal=0; the UP default never fired. **The n=5 objection
  stands, the mechanism does not.**

### ⛔ AWAITING JACOB — LOGIC tier, moves verdicts, NOT shipped unilaterally
1. **The units fix.** Rescale `expectations` to its realized range, or restate the weights honestly.
   Changes every verdict in the model. *(This also reframes the ±15 bar question: the bar is not the
   problem — the term's AUTHORITY relative to REV is.)*
2. **Abstraction Limb 2: veto → disclosure?** With 4 winners, almost any real fix breaks one, and the
   limb gives no credit for repairing losers. **It is a ratchet toward permanence, not a protection.**
3. **A gate on Type D.** The 4-limb gate closed Type B and left "normal variance" wide open next to
   it — the more comfortable claim, requiring proof of nothing. The abuse just migrates.
4. **Re-arm the kill switches on expectancy, not sign.** Half-done: reported, not yet triggering.


---
<!-- moved out of STATE.md 2026-09-12 -->
## 🔴 SESSION 2026-09-02 — THE 2026-08-26 BATCH GRADED **2 / 7**, AND THE MISS WAS ONE MECHANISM

Seven names frozen blind on 2026-08-25 (PLAB BMO; NVDA/CRM/CRWD/SNPS/NTNX/VEEV AMC 2026-08-26),
scored on the FIRST OPEN after the print. Nothing was registered — the trade pause held, so no
capital was touched.

| | fc | conv | idio open | dir | thesis |
|---|---|---|---|---|---|
| NVDA | UP | LOW | **+5.11%** | ✅ | ✅ |
| SNPS | UP | MEDIUM | **+1.98%** | ✅ | ❌ |
| PLAB | DOWN | LOW | **+27.52%** | ❌ | ❌ |
| VEEV | DOWN | LOW | **+12.12%** | ❌ | ❌ |
| CRM | DOWN | MEDIUM | **+11.57%** | ❌ | ❌ |
| CRWD | DOWN | LOW | **+9.56%** | ❌ | ❌ |
| NTNX | DOWN | LOW | **+8.85%** | ❌ | ❌ |

**Every name gapped UP and SPY gapped +0.32%** — this was not a tape effect absorbing the calls.
Five genuine idiosyncratic up-gaps that the model was short.

🔴 **ONE deciding variable, not five.** NVDA guided next-FY revenue growth ~70% and re-rated
the complex overnight — **IGV +6.0% on a +0.32% SPY day.** The model scored six names as
independent on a night when one of the six set the factor for the other five, **while forecasting
that name in the same batch.** The surprise gate was RUN and **FAILED** (limb 2 `not_sourceable`,
limb 3 `outside_distribution`) → reclassified **A / JUDGMENT**. The anti-excuse design worked:
this was a blind spot, not luck.

🔴 **THE INDEPENDENCE RULE HELD, AND IT MATTERS HERE.** Four wrong software calls collapse to
**ONE** confirmation — the board prints `raw 4, clustered to 1`. **A five-name wipeout is n=2 by
our own standard.** Nothing became ripe on direction; nothing was patched. Do not quote 5/7 as a
sample.

**PLAB is a SEPARATE miss** — BMO, and it gapped BEFORE NVDA printed. It beat above the guided
high end and the model was DOWN on it because **REV drove expectations to −1.00**. Adds to the
standing finding that REV is uninformative or inverted (trivial shadow 2/11, mean idio −4.38%).

✅ **THE GAP-CAPTURE EXIT GOT ITS CLEAREST LIVE VALIDATION YET: PLAB opened +27.1% and cooled to
~+4% within twenty minutes.** The entire move existed at the open.

### 🟢 SHIPPED — `benchmark-defaults-to-SPY-for-uncovered-sectors` (A / MECHANICAL, fired at 1)
**6 of 7 names benchmarked to SPY** because they were simply absent from `DEFAULT_ETF`. On an
IGV +6% / SPY +0.3% night, "beta-stripped idio" still carried a 3–6pt sector factor.
**Scope was deliberately narrowed to a TABLE EXTENSION, not a method change:** 43 of 61 existing
outcome rows have |idio| < 6%, so touching the benchmarking METHOD is sign-flip dangerous across the
whole record. Adding names to the table changes **zero historical rows** and flips **no direction**
in this batch (CRM +8.26, CRWD +6.65, NTNX +6.00, VEEV +9.34, SNPS +1.07, PLAB +27.33).
Software→IGV; PLAB + four semi-cap names→SMH. 4-line diff, no CRLF damage, 485 assertions pass.

### 🔴 THE SATURATION DEFECT TOOK ITS FIRST LIVE CASUALTY — AND IS STILL NOT PATCHED
**CRM was the highest-conviction wrong call in the batch** (MEDIUM / EVIDENCED, +11.57% against it).
Its revisions feed was corrupt at T−1 — the vendor reported `down_7d 12 > down_30d 11`,
arithmetically impossible — so **C13 fail-closed the TRADE layer while the FORECAST layer scored
the name anyway**, off a single positioning leg, and labelled the result EVIDENCED. That is precisely
the queued resolution fix (MAXIMUM/HIGH unreachable below two verified legs) doing the predicted
damage: **an inflated conviction label on a corrupt input, accruing during the pause.** Owner's call,
still open.

### THE ANALYST IS IN THE ERROR LEDGER TOO
A pre-print deep-dive argued the frozen SNPS UP call was wrong. **It was right.** The argument leaned
on CLOSE-day moves — which this model does not trade — and applied a months-horizon multiple
thesis to an event that resolves in one open.

> 🔴 **OWNER CORRECTION, STANDING (Jacob, 2026-09-02): the ONLY graded variable is the market
> OPEN immediately after the earnings date. Not the close, not the intraday drift, not pre-market.**

Logged as `analyst-override-uses-variable-outside-graded-horizon`, A/JUDGMENT, 1/3.
**SNPS was RIGHT on direction and WRONG on thesis** (`thesis_confirmed=False`): +1.07% vs IGV +6.0%,
the weakest gap in the batch. The washout did NOT mean-revert — the name was carried by the complex
and still lagged it. A winning call on a wrong thesis, recorded as such.

### ⛔ A `/pre` WAS REQUESTED IN THE `/post` CHAT AND WAS REFUSED
After the post-mortem, a request to pre-register a NEW name in the same conversation was refused.
That chat had read account files minutes earlier to resolve scout position-status, so the row would
have been `portfolio_aware` wearing a BLIND label — the AMKR failure mode, contaminated by
knowledge instead of by clock. **The refusal is the control working; it is recorded here as evidence
that it FIRES, not merely that it exists.** Findings reach the next chat as FILES — the code fix,
the dossiers, the standing notes, the error board — never as prose carried in a context window.

### STATE OF THE LEARNING LOOP — no longer empty
`errors.jsonl` 13 rows (10 observations, 3 dispositions) · `dossiers/` **7 names written**, plus
**4 standing notes** (NVDA, PLAB, NTNX, SNPS) which are exempt from the 5-event cap.
`ledger.jsonl` has **NO outstanding outcomes** — `NVT:2026-07-31` was cleared after 33 days.

```
🟢 SHIPPED   benchmark-defaults-to-SPY-for-uncovered-sectors       A/MECHANICAL, fired at 1
⏳ PENDING   gap-model-blind-to-same-night-complex-event      1/3   (raw 4, clustered to 1)
⏳ PENDING   rev-leg-points-against-the-print                 1/3   PLAB
⏳ PENDING   analyst-override-uses-variable-outside-graded-horizon  1/3
   SURPRISE RATE  0/10 = 0%  (budget 30%)
```

---

