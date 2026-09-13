---
name: post
description: DECOMMISSIONED 2026-09-13 alongside /pre. The PRE directional model is a CLOSED EXPERIMENT, so there are no forecasts left to grade and no error ledger left to write to. Still triggers on "/post", "post-mortem", "score the batch", or a report that a pre-registered batch has printed - so those trained phrases get the closure and the reason instead of silently doing nothing. Post-print work now belongs to /earnings.
---

# `/post` — DECOMMISSIONED

> ## 🔴 THERE IS NOTHING LEFT TO GRADE.
>
> `/pre` no longer produces a forecast, so `/post` has no outcome to score, no conviction to
> judge, and no error class to file. **All three PRE ledgers are read-only and guarded in code**
> (`PRE/pre_closed.py`): `log_forecast`, `log_outcome`, `observe` and the ledger's `_append` all
> refuse writes to the production paths. **This file is a tombstone, not a runbook.**

## What to say when this triggers

State the closure and point at `/earnings`. The full reasoning is in **`PRE/pre_closed.py`**;
the final record and the closure decision are in **`PRE/STATE.md`**. Do not re-derive either,
and do not offer to grade "just this one".

**Final record: 27 graded forecasts, 14 correct = 51.9%, p = 1.00 against a pre-specified 50%
null.** Separation between UP and DOWN calls **−1.86pp, t = −0.50**. Out-of-sample n for the
final scoring stack: **5**.

## The seven steps are gone. Here is what happened to each.

| former step | disposition |
|---|---|
| 1 · score the outcome | **gone** — no forecasts are produced |
| 2 · post-mortem (A/B/C/D) | **gone** |
| 3 · surprise gate (4 limbs) | **decommissioned** — ceremony on n=6 |
| 4 · error ledger | **decommissioned** — the firing rule reached "RIPE" ~68% of the time against pure noise with author-chosen labels. It was manufacturing edits, and each edit destroyed the frozen spec a record needs. |
| 5 · the response | **gone** with the ledger |
| 6 · dossier | **frozen** — the 10 written dossiers stay readable; no new events are recorded |
| 7 · **scout → inbox** | ✅ **SURVIVED, and moved.** This was the step that produced real value. It now happens inside **`/earnings`**, which already wrote to the same inbox. |

## The part that was actually working

Step 7 and the forensic reading around it are what justified this command. In its final week
that produced the **AEO guidance basis change** (a ~4% underlying operating-income cut presented
as a +36% raise, because the prior guide excluded IEEPA tariff refunds and the new one included
them), the **CPRT read-through** (salvage names trade total loss frequency, not reported EPS —
the market looked through a 17% net-income decline), and a **stale ORCL card** whose own text had
requested re-underwriting at the exact print that had just happened.

**None of that required predicting a direction.** Two of those rules are now written into
`.claude/skills/earnings/SKILL.md` as rules rather than a subsystem — the guidance-qualifier diff
and `OCF/NI < 0.8` on an EPS beat.

## 🔴 Do not rebuild this as "PRE-Forensics"

It was proposed by three of the four external reviewers and it is the wrong move: chat 2
(`/earnings`) already exists to read prints forensically, and a parallel forensic engine
duplicates it while re-creating the governance overhead that closed PRE. **The rules belong in
the chat that already does the job.**

Reopening PRE requires deleting `PRE/CLOSED` and recording that decision in `PRE/STATE.md`.
`baseline/check.py` asserts the frozen ledger line counts on every run.
