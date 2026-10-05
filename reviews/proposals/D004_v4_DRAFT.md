# D004 · Decision protocol · v4 — FROZEN 2026-10-05 (ET) · applies from Season A

> v3 was frozen for Season A on 2026-09-29 and has never governed a decision: no Season A event exists
> yet. v4 replaces it before its first use, as v3 replaced v2. **v1 stays LIVE for the pilot.**
> Machine-readable twin: `D004_decision_protocol_v4.json`; this file wins on any disagreement.
> **Everything not listed here is v3 unchanged:**
> - T1 is rule v0, computed by code
> - T2 is fenced from T1
> - the hash order
> - the outside-view prior and the leak probe are required
> - BUY ⇔ confidence > 0.5
> - the base-rate card
> - the stage revenue tags

## Why — capacity, measured

- **The cost of v3's T2.** It researched on its own: NKE took 50 turns, about $3.14 of usage.
- **The account's capacity.** Load tests on 2026-10-02/03 found that the account behind the Actions token
  carries **one or two such runs per 5-hour window**, on a weekly cap shared with Jacob's chats.
- **The demand.** Season A brings up to ~50 eligible events on a peak day.
- **The result under v3:** most T2 decisions would be MISSING, at random but useless for power.
- **Jacob's decision (2026-10-05):** no paid API for now. Find a free workaround.

## Change 1 — the dossier: code gathers T2's inputs at the snapshot (stage 1)

`pipeline/dossier.py` writes `dossier.json` right after the gate and factor snapshot. It holds:
- the gate
- the factor sheet
- the base-rate card
- the company's latest earnings release (EX-99.1 of its latest Item 2.02 8-K)
- the MD&A of its latest 10-Q/10-K
- the other 8-Ks of the last 90 days (opening text)
- news **headlines** with their publication times

Rules for the items:
- Every item carries its source and publication time. Code **refuses** any item not published before
  `captured_et`; the gate and factor items carry `captured_et` itself.
- A failed fetch is listed under `missing`, never filled.

**Stage-1 freeze.** The event is frozen at once, before any model reads anything. That covers the gate,
factors, option chain, dossier, T0 and T1, and `decision.json` with `t2.stage2` set. So **T0 and T1 can
no longer be lost to an AI failure**.

## Change 2 — T2 decides in ONE call with NO tools, from the frozen dossier (stage 2)

- **Model `claude-sonnet-5-5`**, through the Claude Code CLI:
  - `claude -p --tools "" --max-turns 1`
  - a fixed system prompt (`pipeline/t2_stage2.py` `SYSTEM`)
  - run from a scratch directory, so no project file is loaded
  - authenticated by the Actions OAuth token, or by `ANTHROPIC_API_KEY` if that secret ever exists
- **The prompt asks for the same things as v3:**
  - the leak probe first, from memory
  - the outside-view prior from the base-rate card
  - confidence
  - BUY ⇔ > 0.5
  - the thesis, 2–5 reasons, the deciding variable
  - three theses (expected · mechanism · wrong if)
  - what to watch
  - the dossier items used
- **Code** writes `t2.json` and `t2_thesis.md` from the reply:
  - `inputs_read` = the dossier items used, with their publication times
  - `decided_et` = the runner clock
  - it validates them with `freeze.decision_problems`
- Every call is logged in `logs/t2/`: the reply, the prompt hash, the dossier hash and the usage.
- **The stage-2 freeze:** `manifest_t2.json` (hashes of `t2.json` and `t2_thesis.md`, plus the dossier
  hash it used) and RFC 3161 tokens over it, committed and pushed before the entry open.

**Measured on NKE (2026-10-05, dry run):**
- cost: **$0.083** a decision against $3.14 for v3's agentic run, about 38× less
- the same substance as v3's agentic NKE card: China/Converse, the one-off tariff recovery, −10%
  reactions, a new CFO
- the same answer on two calls: 0.50

## Change 3 — the deadline moves to 15 minutes before the entry open

- **Why v2 tied T2 to the snapshot-session close:** after 16:00 an agentic T2 could read after-hours
  prints, the stock's own after-hours trading, and same-day news that T1's snapshot never had.
- **Why that reason no longer applies:** a v4 T2 has **no tools**, and its information set is the
  frozen dossier plus its pre-cutoff training. Waiting adds nothing it can see. The fairness the v2
  change protected is kept by construction.
- **What is gained:** decisions can be spread over the night, across several 5-hour usage windows,
  instead of 90 minutes.
- **The rule:** `decided_et` must be ≥ `captured_et` and < entry open − 15 min. A later decision is not
  valid. With no frozen `t2.json`, T2 is MISSING for that event (reason: no stage-2 decision). The hash
  order of v3 change 3 decides who goes first, so what capacity misses is missed at random.

## Change 4 — T2G, a free second model, as a SHADOW (CHARTER I2)

- **What:** the same dossier and system prompt sent to `gemini-3.8-flash` through the Gemini API free
  tier. No tools and no Google Search grounding.
- **Auth:** `GEMINI_API_KEY`, created by Jacob at no cost. Google may use free-tier prompts to improve
  its products; the dossier holds only public company information.
- **Files:** `t2g.json`, `manifest_t2g.json`, the same stage-2 freeze.
- **Status:** **SHADOW.**
  - It is reported beside T2: the hit rate against T0, the confidence test, and calibration.
  - It is never part of T2, never in a confirmatory family, and never shown to T2.
  - At Gate 1 the T2/T2G average (the ensemble) may be registered for later seasons.
- If the model id is refused when the key first runs, a v4.1 fixes it before T2G's first decision.

## What is lost, said plainly

- **T2 no longer chases sources itself.** No call transcript, no live web page, and only headlines
  rather than full articles.
- **The model changes from Opus to Sonnet.**
- For both reasons, **pilot T2 (v1, agentic Opus) is not comparable with Season A T2**, and is never
  pooled with it. The pilot was always "bugs, not findings".
- **What is gained:**
  - T2 decisions on (nearly) every event rather than 1–2 a day
  - an information set that is exactly reproducible and timestamp-verified by code
  - a free second model
