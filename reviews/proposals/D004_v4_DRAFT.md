# D004 · Decision protocol · v4 — FROZEN 2026-10-05 (ET) · applies from Season A

> v3 was frozen for Season A on 2026-09-29 and has never governed a decision: no Season A event exists
> yet. v4 replaces it before its first use, as v3 replaced v2. **v1 stays LIVE for the pilot.**
> - Machine-readable twin: `D004_decision_protocol_v4.json`; this file wins on any disagreement.
> - **The method is frozen with it.** `D004_implementation_v4.sha256` lists the files that carry the
>   method: `dossier.py`, `t2_stage2.py` (including the exact prompts, whose hash is `system_sha256`
>   in the JSON), `freeze.py`, `due.py`, `grade.py` and `t2-queue.yml`. `check.py` FAILS if any of them
>   differs from its latest registered hash. A change is an appended, dated line, never a silent edit
>   (rule 5).
> - **Everything not listed here is v3 unchanged:**
>   - T1 is rule v0, computed by code
>   - T2 is fenced from T1
>   - the outside-view prior and the leak probe are required
>   - BUY ⇔ confidence > 0.5
>   - the base-rate card
>   - the stage revenue tags
> - An independent review (Sonnet, 2026-10-05) found no look-ahead path. Its fixes are in the code and in
>   the text below.

## Why — capacity, measured

- **v3's T2 researched on its own.** NKE (pilot, v1 rules) took 50 turns and about $3.14 of usage.
- **The account behind the Actions token can afford very little of that.** Load tests on 2026-10-02/03
  showed **one or two such runs per 5-hour window**, on a weekly cap shared with Jacob's chats.
- **Demand is far higher.** Season A brings up to ~50 eligible events on a peak day. Under v3 most T2
  decisions would be MISSING.
- **Jacob (2026-10-05):** no paid API for now; find a free workaround.

## Change 1 — the dossier: code gathers T2's inputs at the snapshot (stage 1)

`pipeline/dossier.py` writes `dossier.json` right after the gate and factor snapshot. It contains:

| item | content | cut at |
|---|---|---|
| gate | the frozen gate | — |
| factors | every factor with its value **and source** | — |
| base rates | the base-rate card | — |
| release | the latest earnings release: EX-99.1 of the latest Item 2.02 8-K, found through the filing index's Type column | 14,000 characters |
| periodic | the **MD&A** of the latest 10-Q / 10-K, anchored on its "Item 2." / "Item 7." heading | 12,000 characters |
| 8-Ks | the other 8-Ks of the last 90 days (at most 6), each with its body and, where filed, its EX-99.1 | 2,500 characters each |
| headlines | Yahoo Finance RSS headlines with their one-line summaries | 20 |

How the MD&A is found:
- Cross-references and table-of-contents lines are skipped.
- The section ends at the next real heading.
- It was correct on 18 of 18 recent filings tested on 2026-10-05. Before the review the rule was wrong on
  6 of 10.
- If no heading is found, the MD&A is recorded as missing, never guessed.

Timestamps:
- Every item carries its source and publication time.
- SEC items are filtered on their **acceptance** time, so a filing accepted after the snapshot cannot
  enter.
- Headlines must be at least **15 minutes** before `captured_et`. The raw feed's hash and fetch time are
  kept.
- The gate and factor items carry `captured_et` itself.
- Code refuses any other item not published before `captured_et`.

Failures:
- A failed fetch is listed under `missing`, never filled.
- **A transient failure** (an SEC 429/503 or a network error) marks the dossier `transient`. Stage 1 then
  waits: `due.py finalize` rebuilds the dossier at every run. An incomplete dossier is frozen as it is
  only at the evening last chance, or from 18:00 ET on the snapshot session.

**The stage-1 freeze** covers the gate, factors, option chain, dossier, T0 and T1, and `decision.json`
with `t2.stage2` set. It happens at the snapshot, before any model reads anything. So **T0 and T1 can no
longer be lost to an AI failure**.

## Change 2 — T2 decides with NO tools, from the frozen dossier (stage 2)

`pipeline/t2_stage2.py` makes two calls per event, through the Claude Code CLI, **only on the Actions
runner**.

**The call itself:**
- model **`claude-sonnet-5-5`**
- `claude -p --safe-mode --strict-mcp-config --setting-sources "" --disable-slash-commands --tools ""
  --max-turns 1`, with a replaced system prompt, from a scratch directory
- the CLI's own init line must show **no tools and no MCP servers**, and the result **one turn and no
  server-side tool use**. Otherwise the reply is rejected.

**The two calls:**
1. **The leak probe, with nothing in context:** "What did <TICKER>'s stock do after its earnings report
   of <DATE>?" The answer is recorded verbatim, as v3 requires: before anything about the event is read.
2. **The decision.** It sees the event line and the dossier, and nothing else. It returns:
   - the prior and which base rate it used
   - confidence with two decimals
   - the thesis, 2–5 reasons, and what moved it from the prior
   - the deciding variable
   - three theses (expected · mechanism · wrong if)
   - what to watch in the print
   - the dossier items used

**What code does with the reply:**
- **Code sets the decision: BUY ⇔ confidence > 0.50.** A reply of exactly 0.50 is NO_BUY.
- The reply's shape is checked, and the decision is validated by `freeze.decision_problems`.
- `inputs_read` = the dossier items used, with their publication times. `decided_et` = the runner clock.
- At most **3 failed attempts** per event, each logged. After that, T2 is MISSING for the event.
- Every attempt is logged and committed in `logs/t2/`: the replies, hashes, isolation check and usage.
  Rejected and failed attempts are on the record too.

**The stage-2 freeze:**
- `t2.json`, `t2_thesis.md` and `manifest_t2.json`, which holds their hashes, the stage-1 dossier hash
  and `system_sha256`.
- RFC 3161 tokens named `manifest_t2.tsr_*`, which never touch stage-1 files.
- It must be committed **and pushed before the deadline**. A push failure is an error, not "done".
- `check.py` verifies:
  - the hashes and tokens
  - that the dossier hash equals stage 1's
  - that the commit precedes the entry open

**Measured** (dry runs on a copy of NKE, 2026-10-05): **$0.083** a decision, against $3.14 for the
agentic run, about 38× less. Two calls gave the same answer.

This is anecdotal. The comparison was with the pilot's v1 agentic card, and it was made after NKE's
outcome was known.

## Change 3 — the deadline moves to 15 minutes before the entry open

- **Why v2 set the deadline at the snapshot-session close:** after 16:00 an agentic T2 could read
  after-hours prints and same-day news that T1's snapshot never had.
- **Why that no longer applies:** a v4 T2 has **no tools**. Its information set is the frozen dossier
  plus its pre-cutoff training, so waiting adds nothing it can see. The fairness the v2 change protected
  is kept by construction.
- **What is gained:** decisions spread over the night, across several usage windows.
- **The rule:** `decided_et` ≥ `captured_et`, and the stage-2 freeze is committed before entry open −
  15 min. With no frozen `t2.json`, T2 is MISSING for the event.
- **Queue order:** earliest deadline first, then `sha256("<season>|<TICKER>|<date>")`. It is
  outcome-blind; within a deadline, whatever capacity misses is missed at random.
- `.github/workflows/t2-queue.yml` runs the queue every 30 minutes, from after the gate to the next
  morning.

## Change 4 — T2G (Gemini) and T2E (their average): SHADOWS, registered now (CHARTER I2)

**T2G.**
- **What:** the same prompts, through the Gemini API free tier, model **`gemini-3.8-flash`**. No tools
  and no grounding are sent.
- **Auth and probe:** `GEMINI_API_KEY`, set by Jacob on 2026-10-05.
  - The key works and lists the model.
  - On 2026-10-05 the free tier answered **HTTP 503 "high demand"** for every 3.x Flash model, so a
    503 counts as a usage limit: this run stops and a later run retries.
  - The 2.5 models are closed to new users.
  - One model, fixed, so T2G is one consistent track.
- **Files:** `t2g.json` and `manifest_t2g.json`, frozen the same way.
- **Privacy:** Google may use free-tier prompts. The dossier holds only public company information.

**T2E**, pre-registered now so it is not chosen after seeing results (review finding 15):
- the mean of T2's and T2G's confidence
- BUY ⇔ > 0.50
- on events where **both** were frozen

**How the shadows are reported:**
- T2G and T2E get T2's statistics: the hit rate against T0, the confidence test, Brier score and
  calibration.
- Descriptive and labelled SHADOW.
- Never part of T2, never in a confirmatory family, and never shown to T2.
- Compared with T2 only on the intersection of events.
- Gemini's training cutoff is not published here. Its leak probe is the check, and any specific answer
  is reported.

## What is lost, said plainly

- **T2 no longer chases sources itself.** It has no call transcript and no guidance beyond what the
  release and MD&A state. It sees headlines, not articles, and long documents are truncated (limits
  above).
- **The model changes from Opus to Sonnet.**
- **Pilot T2 (v1, agentic Opus) is not comparable** with Season A T2 and is never pooled with it. The
  pilot was always "bugs, not findings". Seasons are kept apart by the season key in every report.
- **What is gained:**
  - T2 decisions on (nearly) every event
  - an information set that is exactly reproducible and timestamp-verified by code
  - a frozen method
  - a free second model
