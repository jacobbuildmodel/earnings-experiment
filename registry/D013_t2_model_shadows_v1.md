# D013 · T2 model shadows · v1 — FROZEN 2026-10-13 (ET) · Opus 5.5, a Sonnet replicate, and their ensemble

> **Frozen before any Season A T2 decision exists.** The first Season A dossiers are built from the gates of
> Fri 2026-10-16, and no Season A event has a `t2.json` yet.
> Jacob upgraded to the Max plan on 2026-10-13 and asked that the capacity be used. **This is CHARTER I2,
> which D009 v1 §7 deferred for capacity.**
> Implementation: `pipeline/t2_models.py` and `tests/test_t2_models.py`, hashed in
> `D013_implementation_v1.sha256`. It reuses `pipeline/t2_stage2.py` (D004 v4), which is **not edited**.
> **Every D013 track is a SHADOW:** never scored as T2, never in a confirmatory family, never shown to T2 or
> to each other.
> **Independent review (Opus 5.5, read-only), 2026-10-13:** FREEZE WITH FIXES. Fixes 1, 2, 3, 5 and 6 are in
> the frozen code below, fix 4 is in `check.py`, and the notes are disclosed in §6.

## 1. Why

- **The charter's core asset** is a clean, post-cutoff, pre-registered record of an LLM's pre-earnings
  judgment. T2 runs on Sonnet 5.5, chosen in D004 v4 to save capacity. Three questions now have
  capacity:
  1. **Does a stronger model judge better?** T2O, Claude Opus 5.5, on the identical dossier and prompt.
  2. **How noisy is T2 itself?** T2R is a second, independent Sonnet 5.5 run. The T2 vs T2R agreement is
     T2's test–retest reliability, the ceiling on any signal T2 can carry.
  3. **Do ensembles help calibration?** T2M, the mean of three Claude runs. The forecasting literature
     says they do (Halawi et al. 2024; Schoenegger et al. 2024; CHARTER I2).
- **T2 itself does not change.** Switching T2's model would end its pooled A + B record (rule 5).
- **Claude Fable 5.1 is not a track.** On 2026-10-13 the account refused it through the same isolated call
  with "Fable 5.1 requires usage credits", which is paid extra usage. Adding it later is a D013 v2 with its
  own start date.

## 2. Probe (2026-10-13, laptop, T2's exact CLI flags, a one-word prompt)

| model | init tools | MCP | turns | result |
|---|---|---|---|---|
| claude-opus-5-5 | [] | [] | 1 | OK |
| claude-sonnet-5-5 | [] | [] | 1 | OK |
| claude-fable-5-1 | [] | [] | 1 | refused: requires usage credits |

## 3. The tracks

| track | backend | model | files |
|---|---|---|---|
| **T2O** | `opus` | `claude-opus-5-5` | `t2o.json`, `t2o_thesis.md`, `manifest_t2o.json` + tokens |
| **T2R** | `sonnet_r` | T2's own model, `rule["t2_model"]` (`claude-sonnet-5-5`) | `t2r.json`, `t2r_thesis.md`, `manifest_t2r.json` + tokens |
| **T2M** | — (code) | mean of T2, T2R and T2O confidences | none (computed at grading) |

**T2O and T2R each run exactly D004 v4 stage 2**, through `t2_stage2.py`'s own functions:
- the same leak probe, system prompt (`SYSTEM_SHA256`), dossier (hash-checked against `manifest.json`),
  isolation checks, `--max-turns 1` and no tools
- the same `MAX_ATTEMPTS` = 3 and usage-limit handling
- the same deadline: the freeze committed before entry open − 15 min
- the same freeze: its own manifest, RFC 3161 tokens and git commit

**Which events:** exactly T2's (a PASS manifest with a frozen dossier). The queue order is the same.

**T2 comes first:**
- A D013 run does nothing while any T2 decision is still waiting in T2's own queue (`waiting("claude")` is
  non-empty).
- A D013 run never touches T2's files. This is tested: the real write path stages only `t2o*`, its
  manifest, tokens and `*_opus_*` logs.
- **This protects T2's place in the queue, not its share of the allowance.**

**Budget, enforced by code** (it protects the shared Max allowance from the shadows):
- At most **12 new decisions per backend per run**.
- At most **80 per backend over the trailing 7 days**, counted from that backend's own `decided` logs.
- Over budget, the event's shadow stays missing for that run. Nothing is logged as an attempt.

**Order:** `sonnet_r` first, then `opus`, so under pressure the cheaper replicate and T2M survive first.

**Model check:**
- A reply whose CLI init line names a model other than the requested one is rejected and never frozen.
- The report counts a shadow only if its frozen file names the registered model. Exclusions are listed.

**Drift check:**
- `run` refuses if `t2_models.py` or `t2_stage2.py` differs from `D013_implementation_v1.sha256`.
- `report` prints any drift.
- So a later D004 implementation change stops the shadows visibly. Resuming them is a D013 v2 or a
  registered addendum.

**`check.py`:** a D013 shadow file or token problem is a labelled WARN, never a FAIL. A FAIL would stop T2's
own queue (`t2-queue.yml` gates on `check.py`). The grader excludes any shadow not frozen in time.

**T2M:**
- the mean of the confidences of T2, T2R and T2O, on events where **all three** froze before the entry open
- BUY ⇔ > 0.50
- **T2E (D004 v4: the mean of T2 and T2G) is unchanged.** T2G is not in T2M, because the free Gemini tier is
  too often unavailable to require it.

**Runner:**
- cloud routine **`earnings-t2-models`**, at 30 minutes past each T2 routine fire (`50 1,5,10,21 * * *` UTC)
- it runs `T2_ALLOW_LOCAL=1 python3 pipeline/t2_models.py run --backend all`
- `CLAUDE.md` gets a guard line for it, like `earnings-t2-cloud`

**Missing:** a shadow that does not freeze in time is missing for that event. Missing shadows never affect
T2, T0 or T1.

## 4. Grading

- **Code only.** `t2_models.py report SEASON` reads the graded outcome rows written by `grade.py` (D005).
- A shadow counts for an event only if **its own manifest's commit precedes the entry open**: grade.py's
  test for T2 and T2G.
- WIN is exit A's `WIN_raw`, the D001 primary, as for T2.

## 5. What is reported (descriptive, labelled SHADOW; rule 7 applies)

- **For each of T2O, T2R and T2M, T2's statistics**, computed by D005's `report.evaluate` unchanged (through
  its T2G slot):
  - the BUY hit rate and lift over T0
  - the confidence test
  - Brier score, Brier skill, log loss, AUC and the calibration table
- **Paired with T2, on the intersection of events:**
  - the mean Brier difference (track − T2; < 0 means better than T2), with a CR1 t by entry session once
    sufficient
  - decision agreement, the confidence correlation, and the mean |confidence difference|
  - **T2 vs T2R agreement is T2's test–retest reliability**
- **Under 30 events or 10 entry dates the result is "insufficient".** A verdict is never "works" or "no
  effect".
- **What a result can do:** at Gate 1, support registering a T2 model or ensemble change as a new D004
  version with its own clock, scored beside the old one. Nothing else.

## 6. Disclosed

- **Leak:** each shadow runs the same leak probe. The report lists every shadow's answer per event. Opus 5.5's
  training cutoff precedes Season A.
- **Capacity:** every shadow draws on the same Max allowance as T2 and the laptop chats.
  - The code budget above caps the shadows' share.
  - **If the weekly limit still binds, this registration lets an operator pause `earnings-t2-models`.**
  - A paused night leaves those events' shadows missing; it never edits a shadow.
- **Mislabelled commits:** shadow freezes reuse `t2_stage2.py`'s commit text ("D004 v4, pipeline/
  t2_stage2.py"), and their logs reuse "T2 queue: … attempt log(s)". Count T2 activity by track (the
  manifest name), never from commit messages. Fixing this would mean editing the frozen `t2_stage2.py`.
- **Aborts:** a run that dies inside a git or `write_once` call does not record the attempt, so the next
  fire can repeat that call. This was already true for T2.
- **Shared Monte Carlo seeds:** T2O, T2R and T2M reuse the T2G slot of `report.evaluate`, and so share its
  random streams. The results are reproducible, but their bootstrap noise is correlated.
- **T2M contains T2**, so T2M-vs-T2 agreement and the Brier difference are partly mechanical.
- **T2 vs T2R is model plus environment noise.** T2 may run on the cloud routine or on Actions, under
  different CLI versions and defaults, so "test–retest" is not pure model sampling.
- **Dependence:** T2, T2R and T2O see the same dossier, so their errors are correlated by construction. T2M
  measures what averaging buys on top of that.

## 7. What changes this rule

Nothing in v1 is ever edited. Adding Fable, changing a model or changing T2M's membership is a v2 with its own
start date.
