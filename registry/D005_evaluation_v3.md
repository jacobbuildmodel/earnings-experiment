# D005 · Evaluation · v3 — FROZEN 2026-10-06 (ET) · one confirmatory hypothesis, pooled over Seasons A + B

> Frozen **before any Season A data exist**: no Season A screen (slot 2026-10-08 16:00 ET → 2026-10-09
> 09:30 ET), no gate, no T2 decision, no outcome. The commit timestamp is the proof.
> Machine-readable twin: `D005_confirmatory_pooled_AB.json`. This file wins on any disagreement.
> **v1 and v2 stay live and are scored as written.** v3 adds H-T2C. It supersedes exactly one sentence of
> v2, quoted under "Family". Everything else is v2 unchanged.
> Draft and review: `reviews/proposals/D005_v3_pooled_T2_confidence_DRAFT.md`. An independent review
> (Sonnet) said FREEZE WITH FIXES; every finding is applied below, findings 1 and 2 being critical.

## Why

- **v1 §7:** one season detects only a ~12-point lift. "The pre-registered answer to that is to pool
  seasons (a new D005 version that says so, before the pooled data is seen), never to loosen the test."
- **v2 §3:** the T2 confidence test keeps ~40% power in the evaluator's simulation, where the binary BUY
  test falls to 15–28%. "It may be registered as a confirmatory hypothesis (test id `T2_confidence`)."
- Registered only for Season B, the AI question would be tested on one season. It would throw away
  Season A's decisions, made under D004 v4, a protocol already frozen that will not change during Season A.
- Pooling roughly doubles the sample for the one test that keeps its power. It costs no rigour only if it
  is registered before Season A data exist.

## H-T2C — T2's stated confidence predicts the win

- **Claim:** in `WIN_raw = a_A·[season A] + a_B·[season B] + b · confidence`, **b > 0**.
  - `WIN_raw` is D001's primary WIN (exit A raw return > 0).
  - `confidence` is T2's two-decimal confidence, as frozen in `t2.json`.
  - There is one intercept per season, so a difference in base rate between A and B cannot pass as signal.
- **Only the sign of b is claimed.** Its size is not a calibration measure (Brier and calibration stay
  descriptive, per v2). The BUY threshold of 0.50 plays no part in this test. Ties are left in the OLS as
  they are.
- **Test:** `pipeline/report.py` `wild_p_k`, the restricted wild cluster bootstrap-t.
  - The restricted fit drops `confidence` and **keeps both season intercepts**.
  - Clusters are entry sessions. Sessions are distinct across seasons, nested within one season.
  - Weights are Rademacher at 12 or more clusters, Webb six-point below that. B = 9,999.
  - **One-sided, α = 0.05.**
  - The two-sided 95% interval is always printed. A b significantly below 0 at two-sided 0.05 is called
    **"anti-informative"**, never "no effect".
- **Disclosed size risk:** v2 records 6.5% size with very unequal clusters. If one entry session holds more
  than 25% of the pooled sample, the verdict carries that disclosure.

## Sample

Every `seasonA` and `seasonB` event that meets all three conditions:
1. its S2 gate status is **PASS**
2. it has a stage-2 T2 frozen under **the H-T2C protocol** (below): `t2.json` + `manifest_t2.json`,
   committed before entry open − 15 min
3. it is graded on exit A under D001, and is not VOID

**Not in the sample. Counted and reported:**
- **T2 MISSING.** It is fixed before the entry open, so it cannot depend on the outcome.
  - MISSING and non-MISSING PASS events are compared on cluster, entry session and implied move.
  - If MISSING exceeds 20% of PASS events in either season, the verdict word carries
    "(missing-data caveat)".
  - A protocol-shadow event (see Continuity) that goes MISSING for capacity counts in this tally.
- **VOID and ungraded.** A pre-registered sensitivity run codes every `no_price` VOID (delisting, halt)
  as WIN = 0 and is reported beside the verdict. If the sensitivity result and the primary result
  disagree on the verdict, the disagreement is carried as a stated threat.
- **Leak probe:** as D004 v3 change 5, recorded and never used. Every specific answer is listed in the
  disclosures. No event is excluded on it, because code cannot judge text (rule 4) and a judged exclusion
  would be made after the outcomes are known.

**Minimums, else "insufficient"** (no effect size called a finding):
- pooled: at least 30 events and 10 entry sessions
- **and in each season:** at least 10 events and 5 entry sessions, so one season alone cannot meet the
  pooled minimum

**Degenerate confidence:** if the pooled SD of `confidence` is below 0.05, or it takes fewer than 5
distinct values, the verdict is **DEGENERATE**. That is p = 1, reported as such.

## The H-T2C protocol, and continuity across seasons

**"Same protocol"** means all five of these match D004 v4 as frozen:
1. the model id `claude-sonnet-5-5`
2. the system prompt (`system_sha256` in `manifest_t2.json`)
3. the dossier builder, `pipeline/dossier.py`
4. the call, parse and decision code, `pipeline/t2_stage2.py`
5. the call parameters fixed in D004 v4

Items 3 and 4 are judged against `registry/D004_implementation_v4.sha256`. Its dated lines are
append-only, and each one starts a new protocol version.

- **Any change to these five ends pooling** for events decided after the change. That covers a bug fix
  to the dossier or parse code, a data-source change and a model change.
- The old protocol must then continue as a **shadow**, on every PASS event from the change on, under the
  same entry open − 15 min freeze rule. Shadow events enter the sample only if they meet sample rule 2.
- A shadow's output is **never shown to the live T2 step**, as with T2G/T2E.
- **Capacity assumption:** about $0.085 a decision (D004 v4, measured), on the shared subscription. The
  shadow doubles T2 load from the change on. That is why it competes for capacity, and why its MISSING
  events count.
- **If no H-T2C-protocol track can run on Season B, H-T2C is UNTESTABLE.** There is no verdict word, and
  Season A is reported as exploratory. **H-T2C is never tested on Season A alone:** by Gate 1 its interim
  has been seen, and testing it then would judge discovery data as proof (rule 6).

## When it is decided

- **Once**, at Gate 2, after Season B is fully graded.
- **Season A interim:** b and its interval may be shown at Gate 1, labelled INTERIM, with no verdict
  word.
  - The interim may inform whether a D004 v5 is adopted for Season B. That does not touch H-T2C, because
    the H-T2C protocol is fixed above and continues as a shadow if replaced.
  - The interim is **never** used to choose Season B's screen, universe or BUY rule.

## Family

- **H-T2C is a family of one: Holm m = 1, one-sided α = 0.05.** It is fixed now and moved by nothing
  registered later.
- `D005_confirmatory_seasonB.json` runs its own, separate family. It **must not** register
  `T2_confidence` again, neither on Season B alone nor pooled.
- **v3 supersedes this sentence of v2:** "Its family should include `T2_confidence`." Nothing else of v2
  is superseded.
- D008's H-S0 and D009's H-M, H-X and H-VOL keep the families their own registrations set.

## What does not change

- v2's statement that "Season A remains exploratory" still holds for every test other than H-T2C: T1,
  T2's BUY/NO_BUY lift, factors and clusters.
- T2's lift is reported per season, and pooled descriptively.
- No rule of D001–D004 changes, and no live rule is edited (rule 5).
- T2G and T2E stay shadows, never in this family (D004 v4).

## Implementation

- `report.py` runs today's per-season families from `D005_confirmatory_<season>.json`. The twin's name,
  `D005_confirmatory_pooled_AB.json`, is one that lookup never loads, so Season A stays exploratory in
  code.
- **The pooled H-T2C run is written before Season B's screening date.** It must be:
  - built on `wild_p_k` as specified above
  - tested on synthetic data: size near 5%, and power at a planted slope, including the per-season
    minimums, the degeneracy rule and the `no_price` sensitivity
  - independently reviewed
- Its hash is registered then. The method is fully fixed by this file, so the code cannot choose it.
