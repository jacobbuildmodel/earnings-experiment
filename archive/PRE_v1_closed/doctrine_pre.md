# PRE-CHAT DOCTRINE — **CLOSED 2026-09-13**

> ## 🔴 THERE IS NO LONGER A PRE-EARNINGS CHAT.
>
> The five-chat model is now **four**. The blind pre-earnings forecaster was retired on
> **2026-09-13** by the owner's decision, after four independent external reviews all reached the
> same verdict. **This file exists so the trigger phrase `pre earnings model` lands on the closure
> and its reason, rather than on a boot sequence for a model that no longer runs.**
>
> Full reasoning: **`PRE/pre_closed.py`.** Final record and the closure decision: **`PRE/STATE.md`.**
> Command tombstones: `.claude/skills/pre/SKILL.md` and `.claude/skills/post/SKILL.md`.

## If someone opens a chat with `pre earnings model` or `PRE`

Say it is closed, give the one-line reason, and point at `/earnings`. **Do not boot a batch, do
not read `PRE/METHOD.md`, do not offer to run one forecast.** There is nothing to resume.

## The final record

**27 blind, pre-registered, integrity-hashed directional forecasts. 14 correct = 51.9%**, which is
**p = 1.00** against a pre-specified 50% null. Mean idiosyncratic separation between UP and DOWN
calls **−1.86pp at t = −0.50**. No directional skill demonstrated, and no inverted signal either.
**Out-of-sample n for the final scoring stack: 5.**

That is a clean negative result, honestly obtained under blind pre-registration. It is kept, not
deleted, because it is worth more than a flattering one.

## Why it closed, and the reason is not the hit rate

**The scoring stack was edited four times inside its own measurement window** — 2026-08-09,
08-12, and twice on 09-05 — each time in response to observed misses. `value`, `vrich` and
`SAT`-in-directional were cut mid-sample; on 2026-09-02 the `DEFAULT_ETF` change altered the
**benchmark used to compute idio** for 6 of 7 names in that batch. So 51.9% is the blended
in-sample score of a sequence of different models, and the history cannot be replayed because
`rev_raw`/`gg`/`vel` were null on every row before 2026-09-12.

**Waiting would have made it worse, not better.** The error ledger existed to detect mechanisms
and demand changes; every change it extracted reset the out-of-sample clock and destroyed the
frozen specification a record requires. Against pure noise the 3-confirmation firing rule reached
a "RIPE" class **~68% of the time** over 13 misses with author-chosen mechanism labels. **The
governance layer was not merely disproportionate to the evidence — it was the thing preventing
evidence from existing.**

⚠ **Not the reasons, recorded so they don't become folklore.** Two of the three arguments in the
original audit brief were overturned on external review and re-verified from source:
- *not* "always-DOWN beats it by 3.7pp" — the two rules make **identical** predictions on 16 of
  27 events and differ on 11, 5 right vs 6. **McNemar exact p = 1.00.** The benchmark was also
  chosen after seeing the data.
- *not* "the effective sample is 6 event-dates" — that assumed perfect within-night redundancy.
  **Tarone/Pearson χ² = 4.92 on 5 df, dispersion 0.98**; cluster bootstrap 33–70% vs naive
  33–70%. Correctness is not measurably clustered, because the model's own calls vary within a
  night.
- *not* the Singapore time zone — 21:30 SGT is 9:30pm, and a genuine 2pp edge on 10pp σ at ~5
  prints a week is a per-trade Sharpe near 0.2.
- *not* the "inverted conviction gradient", which was noise on cells of n=2 and n=6 and was
  wrongly reported as a finding for three sessions.

## What survived

**Two rules, moved into `.claude/skills/earnings/SKILL.md`** — the guidance-qualifier diff (a
raise on a changed basis is not a raise) and the `OCF/NI` earnings-quality ratio. They are rules
in the chat that already reads prints, not a new subsystem.

**Deliberately NOT salvaged:** the blindness protocol, the clock guard, integrity hashing. They
were the best-built part of PRE, and they are entangled across ~2,000 lines of scoring code in
`pre_batch` / `pre_calcrisk` / `pre_edgescore` / `pre_ledger`. Refactoring to rescue them is how
a retirement quietly becomes a rebuild. **Do not build "PRE-Forensics"** — three of four external
reviewers proposed it, and it duplicates `/earnings` while re-creating the overhead that closed PRE.

## The binding rule

The ledgers are **read-only**, guarded in code (`PRE/pre_closed.py`) and asserted by
`baseline/check.py`, which checks their frozen line counts on **every run of every chat**.
Reopening is a deliberate act: delete `PRE/CLOSED` **and** record that decision in `PRE/STATE.md`.
It is never done by importing a module or running an old command.
