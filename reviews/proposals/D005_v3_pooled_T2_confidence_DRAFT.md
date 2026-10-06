# D005 · Evaluation · v3 — DRAFT: one confirmatory hypothesis pooled over Seasons A and B

> **DRAFT, not a rule.** To be frozen (registry + `FROZEN.sha256`) only after an independent review,
> and **before the first Season A T2 decision** (the Season A screen is captured 2026-10-08 16:00 ET →
> 2026-10-09 09:30 ET; the first stage-2 decisions run the night of 2026-10-09). Nothing about Season A
> exists when this is written: no screen, no gate, no decision, no outcome.
> v1 and v2 stay live and are scored as written. **Everything not listed here is v2 unchanged.**

## Why now

- **v1 §7:** one season of ~100 events detects only a ~12-point lift, so "no evidence" after one season is
  the expected result even if an edge exists. "The pre-registered answer to that is to pool seasons (a new
  D005 version that says so, before the pooled data is seen), never to loosen the test."
- **v2 §3:** the T2 confidence test keeps ~40% power in the evaluator's simulation, where the binary BUY
  test falls to 15–28%. "It may be registered as a confirmatory hypothesis (test id `T2_confidence`)."
- **v2, end:** "Season A remains exploratory." The first confirmatory file is Season B's, and it should
  include `T2_confidence`. Registered that way, the AI question would be tested on **Season B alone**. It
  would throw away a season of T2 decisions made under a protocol (D004 v4) that is already frozen and
  will not change during Season A.
- CHARTER §6: power comes first. Pooling is the only lever on this question that costs nothing in rigour,
  **provided it is registered before Season A data exist**. After 2026-10-09 the chance is gone.

## H-T2C — T2's stated confidence predicts the win

- **Claim:** in `WIN_raw = a_season + b · confidence`, **b > 0**.
  - `WIN_raw` is D001's primary WIN (exit A raw return > 0).
  - `confidence` is T2's two-decimal confidence, as frozen in `t2.json`.
  - `a_season` is one intercept per season, so a difference in base rate between A and B cannot pass as
    signal.
- **Test:** v2 §3's T2 confidence test, extended only by the season intercepts.
  - OLS slope, clustered by **entry session**; the clusters are the entry sessions of both seasons together.
  - D005's restricted wild cluster bootstrap-t, imposing b = 0.
  - One-sided, α = 0.05 (before Holm, see Family).
- **Sample:** every event in `seasonA` and `seasonB` that meets all three:
  1. its S2 gate status is PASS
  2. it has a stage-2 T2 frozen under D004 v4: `t2.json` + `manifest_t2.json`, committed before entry
     open − 15 min, model `claude-sonnet-5-5`, with the D004 v4 implementation hashes
  3. it is graded on exit A under D001 and is not VOID
- **Counted and reported, not in the sample:** T2 MISSING, VOID, ungraded. If T2 is MISSING on more than
  20% of PASS events in either season, the verdict carries that as a stated threat.
- **Leak probe:** as D004 v3 change 5, recorded and never used. Every specific answer is listed in the
  disclosures. The test includes every event: code cannot judge text (rule 4), and a judged exclusion
  would be a choice made after seeing outcomes.
- **T2G and T2E** stay shadows (D004 v4), never in this family.

## Continuity across seasons

- Season B events enter H-T2C only if they were decided by **the same stage-2 protocol**: D004 v4's model
  and system prompt, matching its implementation hashes.
- If T2 changes for Season B (a D004 v5), D004 v4 stage 2 keeps running on every Season B PASS event as a
  frozen shadow track, so H-T2C keeps its sample. That track is a measurement, not a decision.
- If that is impossible (for example the model is retired), H-T2C is tested on Season A alone, at the same
  α, labelled "Season A only — protocol discontinued".

## When and how it is decided

- **Once**, at Gate 2, after Season B is fully graded. That is the same point as D008's H-S0 and D009's
  pooled tests.
- **Season A's interim estimate is reported but is not a result.** It is labelled INTERIM, with no
  verdict word. The Gate 1 report may show b and its interval, never "confirmed" or "rejected".
- **"Insufficient"** (v1): under 30 events or 10 entry sessions in the pooled sample. Then no effect size
  is called a finding.

## Family

- H-T2C is a member of the **Gate 2 confirmatory family**.
  - `D005_confirmatory_seasonB.json`, registered before Season B's screening date, must list H-T2C and
    count it in Holm's m. It must not register `T2_confidence` a second time, on Season B alone.
  - If that file is never registered, H-T2C stands alone: Holm m = 1, α = 0.05.
- D008's H-S0 and D009's H-M, H-X and H-VOL keep the families their own registrations set.

## What this does NOT change

- Season A stays exploratory for everything else: T1, T2 lift, factors and clusters.
- T2's BUY/NO_BUY lift (v1 primary) is still reported per season, and pooled descriptively.
- No rule of D001–D004 changes. No live rule is edited. v2's statement that Season A is exploratory still
  holds for every test except this one.

## Implementation (method fixed here, code later)

- `report.py` today runs a confirmatory family for one season (`D005_confirmatory_<season>.json`).
- The pooled run will be written, tested on synthetic data (size near 5%, power at a planted slope) and
  independently reviewed **before Season B's screening date**. Its hash is registered then.
- The method is fully fixed by this file, so the code cannot choose it.
- The machine-readable twin `D005_confirmatory_pooled_AB.json` has a name that the per-season lookup will
  never load, so Season A stays exploratory in code.

```json
{
  "id": "D005_confirmatory_pooled_AB_v1",
  "rule": "D005_evaluation_v3",
  "hypotheses": [
    {"id": "H-T2C", "test": "T2_confidence", "seasons": ["seasonA", "seasonB"], "pooled": true,
     "model": "WIN_raw ~ season intercepts + b * confidence", "cluster": "entry_session",
     "bootstrap": "D005 restricted wild cluster bootstrap-t, null b = 0", "sided": "greater",
     "alpha": 0.05, "family": "Gate 2 confirmatory family (Holm m set by D005_confirmatory_seasonB.json; m = 1 if none)",
     "sample": "PASS + frozen D004 v4 stage-2 T2 + graded exit A, not VOID",
     "verdict_at": "Gate 2, after Season B grading; Season A interim is descriptive only"}
  ]
}
```
