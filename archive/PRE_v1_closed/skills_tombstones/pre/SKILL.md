---
name: pre
description: DECOMMISSIONED 2026-09-13. The PRE directional pre-earnings forecast is a CLOSED EXPERIMENT and this command no longer produces a forecast. Still triggers on "/pre", "pre-register <TICKERS>", "PRE batch", "run pre-earnings on X", "freeze the forecast", or naming a stock reporting soon and wanting a directional call BEFORE the print - so that those trained phrases get the closure and the reason, instead of silently doing nothing. Post-print work now belongs to /earnings. Do not re-implement a directional forecast here.
---

# `/pre` — DECOMMISSIONED

> ## 🔴 DO NOT RUN A PRE-EARNINGS FORECAST. THERE ISN'T ONE ANY MORE.
>
> The PRE directional model was **retired on 2026-09-13** by the owner's decision, after four
> independent external reviews all reached the same verdict. Its ledgers are **read-only** and
> guarded in code. **This file is a tombstone, not a runbook.**

## What to say when this triggers

State the closure, in one short paragraph, then offer the thing that replaced it. Do not
re-derive the reasoning — it is written up in full in **`PRE/pre_closed.py`** and summarised in
**`PRE/STATE.md`**. Do not pitch a rebuild.

**The final record:** 27 blind, pre-registered, integrity-hashed forecasts. **14 correct =
51.9%**, which is **p = 1.00** against a pre-specified 50% null. Mean idiosyncratic separation
between UP and DOWN calls **−1.86pp at t = −0.50**. No skill demonstrated — and no inverted
signal either. **Out-of-sample n for the final scoring stack: 5.**

## Why it closed — the short version

The hit rate is not the reason. **The scoring stack was edited four times inside its own
measurement window** (2026-08-09, 08-12, 09-05 ×2), each time in response to observed misses.
`value`/`vrich`/`SAT` were cut mid-sample; on 2026-09-02 the `DEFAULT_ETF` change altered the
*benchmark* used to compute idio for 6 of 7 names in that batch. So 51.9% is the blended
in-sample score of a sequence of different models.

**And waiting could not fix it.** The error ledger's job was to detect mechanisms and demand
changes; every change it extracted reset the out-of-sample clock and destroyed the frozen
specification a record requires. Against pure noise the 3-confirmation firing rule reached a
"RIPE" class ~68% of the time over 13 misses with author-chosen labels. **The governance layer
was not disproportionate to the evidence — it was what prevented evidence from existing.**

⚠ **Reasons that were NOT the cause, recorded so they don't become folklore:** *not* "always-DOWN
beat it" (McNemar exact **p = 1.00**; the two rules differ on only 11 of 27 events, 5 right vs 6,
and that benchmark was picked after seeing the data) · *not* "the effective sample is 6
event-dates" (Tarone/Pearson **χ² = 4.92 on 5 df, dispersion 0.98** — no block structure in
correctness; cluster bootstrap 33–70% vs naive 33–70%) · *not* the Singapore time zone (21:30 SGT
is 9:30pm, and a real 2pp edge on 10pp σ is a per-trade Sharpe near 0.2) · *not* the "inverted
conviction gradient", which was noise on cells of n=2 and n=6.

## What to do instead

| the ask | where it goes |
|---|---|
| read a print, re-rate a name, cross-stock read-through | **`/earnings`** — chat 2. It inherited PRE's two surviving rules. |
| is this name worth owning | **`/evaluate`** — chat 3, DRIVE v3.2 |
| what do I buy now | **`/buy`** — chat 4 |

**The two rules that survived** live in `.claude/skills/earnings/SKILL.md`: the
**guidance-qualifier diff** (a raise on a changed basis is not a raise — the AEO catch) and the
**OCF/NI earnings-quality ratio**. Nothing else was salvaged, deliberately: the blindness protocol
and clock guard are entangled across ~2,000 lines of scoring code, and refactoring to rescue them
is how a retirement quietly becomes a rebuild.

## 🔴 If asked to reopen it

Reopening is a deliberate act and it is the owner's alone. It requires deleting `PRE/CLOSED`
**and** recording that decision in `PRE/STATE.md`. `baseline/check.py` asserts the frozen ledger
line counts on every run, so rows cannot be added to a closed sample quietly.

**If asked to "just run one forecast" — refuse and say why.** A single new row appended to a
closed sample makes an honestly-obtained negative result uninterpretable, which is the same
defect, one layer up, that closed the model. The frozen record is worth more than one more
datapoint.
