# D004 · Decision protocol v1 — T1 in the pilot, T2's rules, the business stage — FROZEN 2026-09-16 (ET)

> Fixes how decisions are made before the first one is made. A change creates `D004_…_v2` with its own
> start date, and events decided under v1 stay labelled v1.

## 1. T0

BUY every event that passes the D003 S2 gate.

## 2. T1 in the pilot (prints 2026-09-21 → 2026-10-09)

**No rule exists yet.** Rule v0 is built by the history study (Phase 2) and frozen before Season A
(FRAMEWORK §11). Every pilot event records `t1.decision = null` with the note `rule v0 not frozen —
pilot`. T1 is not back-filled for pilot events later: a rule scored on events it saw is not evidence.

## 3. T2 — the AI decision

**Who and when.** The Claude session running the experiment decides after the factor snapshot is
captured and before the freeze, which must be before the entry open.

**T2 may read — and must list in `inputs_read`:**
- the event's `confirm.json`, `gate.json`, `factors.json` and `option_chain.json`
- `reviews/literature_review.md`, as background on mechanisms
- company primary sources **published before the snapshot time**: the latest earnings release,
  10-Q/10-K and 8-Ks, guidance given for the quarter being reported, and the latest call transcript
- news and web pages **timestamped before the snapshot time**. Each one is listed with its URL and
  timestamp. Figures are verified against a primary source before they are relied on (CLAUDE.md).

**T2 must NOT read:**
- anything published after the snapshot time
- `archive/` (rule 10)
- the DRIVE repo, or anything about Jacob's holdings (rule 9)
- **any graded outcome of this experiment in the current season.** Outcomes of earlier seasons may
  be read only once a new D004 version says so. Within a season, T2 is a fixed judge, not a learning one.
- other tracks' decisions for the same event, except T0, which is always BUY

**T2 must write:**
- `decision.json` → `t2`:
  - `decision` — BUY or NO_BUY
  - `confidence` — the probability, 0–1, that the price rises from entry to exit A (D001 WIN_raw).
    **BUY if and only if confidence > 0.5.** The number and the decision can never disagree.
  - `thesis` — one sentence
  - `reasons` — the 2–5 things that decided it
  - `inputs_read` — as above
  - `deciding_variable` — what T2 expects will move the stock
- `thesis.md` — the FRAMEWORK §4 card, items 1–6:
  - identity, cluster and stage
  - the factor snapshot, by reference to `factors.json`
  - three theses, each as *expected · mechanism · what proves it wrong*
  - key observations to capture
  - predicted deciding variable
  - decisions

**T2 must never:**
- compute or judge an outcome (rule 4)
- change a decision after it is frozen
- write a decision for an event that failed the gate

## 4. Business stage — formula, never judgment (FRAMEWORK §6, axis 2)

**Source:** SEC XBRL `companyfacts`, 10-Q/10-K facts filed before the snapshot.

| field | definition |
|---|---|
| **revenue** | for **each quarter separately**, the first of `us-gaap:Revenues`, `RevenueFromContractWithCustomerExcludingAssessedTax`, `SalesRevenueNet` that has a value. Filers switch tags over time, so choosing one tag for the whole history would read stale quarters |
| **operating income** | `us-gaap:OperatingIncomeLoss` |
| **growth** | revenue of the latest quarter that has **both** revenue and operating income (a ~3-month duration fact, 80–100 days) ÷ the same fiscal quarter one year earlier − 1 |
| **margin** | operating income ÷ revenue, for that latest quarter |

**Stage:**
- growth ≥ 20% and margin < 0 → `unprofitable_growth`
- growth ≥ 20% and margin ≥ 0 → `profitable_growth`
- growth < 20% → `mature`
- any input missing, or the latest quarter with both inputs ending **more than 200 days** before the
  snapshot → `unknown`, which is never guessed (some filers stop using `OperatingIncomeLoss`)

Q4 is not always filed as a 3-month fact. Where only the annual figure exists, Q4 = annual − the three
reported quarters of that fiscal year, flag `q4_derived`.
