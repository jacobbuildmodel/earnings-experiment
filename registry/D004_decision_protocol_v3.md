# D004 · Decision protocol · v3 — FROZEN 2026-09-29 (ET) · applies from Season A

> v2 was frozen for Season A on 2026-09-21 and has never governed a decision: no Season A event exists
> yet. v3 replaces it before its first use. **v1 stays LIVE for the pilot.** Machine-readable twin:
> `D004_decision_protocol_v3.json`; this file wins on any disagreement. **Everything not listed here is
> v2 unchanged** (T2 decides by the snapshot-session close; timed inputs; BUY ⇔ confidence > 0.5).
>
> Sources:
> - the history study (D006 v1, run 2026-09-29), which produced T1 rule v0
> - a Season A preview of 2026-09-28, which showed ~80 eligible events on the busiest snapshot days
> - CHARTER backlog items I3 (outside view first) and I7 (leak probe)

## Change 1 — T1 is rule v0, computed by code

- **What.** `registry/T1_rule_v0.json` (R-LIT, **FAILED VALIDATION** in history).
  - The snapshot stores H1–H10 in `factors.json`, computed by `pipeline/history_factors.py`, the same
    code as the history study.
  - `freeze.py` computes T1 with `pipeline/t1_rule.py` and writes it into `decision.json`. If the AI
    wrote a `t1`, it is replaced, and the replacement is noted in the manifest.
  - More than 5 of the 10 factors missing → T1 = null with the reason, never guessed.
- **Why "failed validation" is still scored.** D006 pre-committed to it: a zero-snooping mechanical
  track is the honest control for T2, and its failure in history is itself the prior to beat.

## Change 2 — T2 may not see T1

T2 must not read `registry/T1_rule_v0.json` or `analysis/history/`. Neither is on disk in the T2
job: sparse checkout, like `archive/` and `outcomes/`. T2 stays an independent judge. D004 v1 already
forbade reading other tracks' decisions; this closes the route of recomputing T1.

## Change 3 — capacity: a fair order, never a chosen one

- **The problem.** Each event gets its own T2 job (up to 5 in parallel; model `claude-opus-5` through
  `anthropics/claude-code-action@v1`; 120 turns and 45 minutes per event). On a peak day not every
  event may be decided before the deadline.
- **The rule.** Events start in the order of `sha256("<season>|<TICKER>|<date>")`, ascending. An event
  not decided by its deadline is frozen T2 **MISSING**, reason `capacity`.
- **Why.** The order is fixed, random with respect to every outcome and factor, and chosen by no one.
  Missing T2s are then missing at random, and D005's paired evaluation (T0 recomputed on the events a
  track decided) stays unbiased. Any "smart" order — easiest first, biggest first — would select events.

## Change 4 — the outside view first (CHARTER I3)

- Before any event-specific research, T2 reads `registry/D004_base_rates_v3.json`: the history
  study's buy-everything hit rates, overall, by cluster and by session.
- It then writes `t2.prior`: the probability it starts from, before anything about this company, and
  one line on which base rate it used.
- Its final `confidence` may move away from the prior. `thesis.md` says what moved it and by how much.
- Why: forecasters, and language models, are better calibrated when they anchor on a base rate first
  (Schoenegger et al. 2024; superforecasting practice). The history study says the opponent wins 54%;
  a T2 that ignores that number starts from a worse place.

## Change 5 — the leak probe (CHARTER I7)

- As its first act, before reading any file about the event, T2 writes `t2.leak_probe`: its answer,
  from memory alone, to "What did <TICKER>'s stock do after its earnings report of <date>?"
- It is recorded, never used. Every Season A print is after the model's training cutoff, so the
  answer should be "I don't know". Any specific answer is evidence of leakage and is reported in D005's
  disclosures.
- `freeze.py` refuses a v3 decision that lacks `prior` or `leak_probe`.

## Change 6 — business stage: one more revenue tag

- D004 §4's revenue tags gain `RevenueFromContractWithCustomerIncludingAssessedTax` (4th in priority).
  AAR (AIR) reports revenue only under that tag and read `unknown` on 2026-09-28.
- `OperatingIncomeLoss` stays the only operating-income source. Companies without it (NIKE) stay
  `unknown`: a proxy would be a guess, which §4 forbids.
