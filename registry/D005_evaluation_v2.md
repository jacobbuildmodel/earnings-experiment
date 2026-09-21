# D005 · Evaluation protocol · v2 — FROZEN 2026-09-21 (ET) · applies to every season, pilot included

> Frozen **before any outcome of this experiment exists**, the same day as v1. The earliest exit A is the
> open of 2026-09-23. **v1 is still computed and printed beside v2** (rule 5): `report.py` emits
> `verdict_D005_v1` next to the v2 `verdict`. Everything not listed here is v1 unchanged, word for word.
>
> Source: two external evaluations on 2026-09-21, one by a Sonnet reviewer and one by an Opus
> reviewer, each starting cold (`reviews/evaluations/2026-09-21_external.md`). Their headline: the
> blindness machinery is strong, but low power combined with many printed verdicts is the main
> threat. A p < 0.05 at ~100 events is quite likely a false positive, and even a true positive
> overstates the edge several times (Gelman & Carlin 2014; Ioannidis 2005).

## 1. What counts as a success: hit-rate lift AND return lift ≥ 0

The primary test is unchanged (D005 v1 §2–§3: lift in WIN_raw, tested through β). **The verdict
wording now requires both halves of "profits from the result":**

| condition (sample sufficient) | the only words allowed |
|---|---|
| p ≥ 0.05 | "no evidence of directional lift (p = …)" |
| p < 0.05 **and** return lift ≥ 0 | "evidence of directional lift, return lift non-negative (exploratory, p = …)" |
| p < 0.05 **and** return lift < 0 | "directional lift WITHOUT return lift — not a success (p = …)" |

The "insufficient", pilot and confirmatory rows of v1 §4 are unchanged. In a confirmatory season a
registered lift hypothesis counts as "confirmed" only if its Holm-adjusted p < 0.05 **and** its return
lift ≥ 0. Hit rates can win while returns lose, because growth names are punished hard on misses
(Skinner & Sloan 2002).

## 2. Only the full sample gets a verdict

The robustness cuts (without `price_dispute`, `timing_unverified`, `confound_8k`) are printed as
**"robustness cut — descriptive, no verdict"**. v1 gave them verdict wording, which invites picking
the best-looking cut.

## 3. New statistics — always computed, never promoted to primary

- **T2 confidence test:** `WIN_raw = a + b·confidence`, clustered by entry session, one-sided
  restricted wild cluster bootstrap on b. It uses the probability, not just the BUY/NO_BUY split, so
  its power does not collapse when T2's BUY share drifts. In the evaluator's simulation, power held
  near 40% where the binary test fell from 28% to 15%. It may be registered as a confirmatory
  hypothesis (test id `T2_confidence`, see §7).
- **Within-date estimate:** separation with entry-session fixed effects, so a result cannot come from
  simply buying more on up-market days. Descriptive robustness.
- **Leave-one-date-out:** the lift recomputed with each entry session dropped, reporting its range and
  how many drops flip its sign. Descriptive robustness.
- **Exit A in two legs** (secondary): pre-print (entry open → entry-session close) and print gap
  (entry-session close → exit-A open), for T0 and for each BUY and NO_BUY set. A "win" earned in the
  session before the print is pre-announcement drift, not a read of the result (Barber et al. 2013).
- **Gate selectivity:** over every gated event, including the INELIGIBLE ones, the pass rate and mean
  implied move per cluster and per business stage. The ≥ 4% gate bites unevenly (mature names
  rarely clear it), so a cluster comparison is also a comparison of how selective the gate was.

## 4. Grading changes (`grade.py`, implementation v2)

- **Print before the frozen window:** an Item 2.02 8-K accepted before the frozen release window opens
  → **VOID `print_date_differs`**. An 8-K can lag its release, but never precede it. A 2.02 filing
  after the window stays `timing_unverified`, because 8-Ks lag. D003 v2 also refuses such events at
  the gate from Season A.
- **Exit A without a price**, even delayed five sessions → VOID `no_price`. v1 code let such an event
  drop silently.
- **Prices are fetched from 06:00 ET the next calendar day,** after the vendor's overnight revision of
  the daily bar. v1 fetched at the close + 15 min.
- **An independent random stream per test,** seeded from 20260921 and the test's name. Adding or
  removing one test never changes another's p-value.

## 5. Disclosures added to every report

- **Test size.** Measured by the evaluator: 4.3% with 25 equal clusters, **6.5% with very unequal
  clusters** (27% of events on one date), and 6.0% with date-varying BUY share under a 3% market
  shock. The test mildly over-rejects when clusters are very unequal.
- **Timestamp proof.** `check.py` verifies that each token covers its manifest and pre-dates the entry
  open. It does **not** validate the authorities' certificate chains. Two independent authorities are
  required so that a single bad token cannot carry the proof.
- **Partial pooling.** A cluster's standard error comes from its own few entry dates, so it runs small
  and the shrinkage puts too much weight on the cluster's own estimate. Per-cluster answers are
  descriptive until a cluster clears the rule 7 minimum.
- **Power.** The v1 §7 table stands. A significant result at that power overstates the true edge. The
  report says so beside any "evidence" verdict.

## 6. Read-only guarantees for the AI step (workflow, recorded here as part of the evidence chain)

- Before any code step runs after the AI step, the workflow checks that the AI changed nothing under
  `pipeline/`, `check.py`, `.github/`, `registry/`, `requirements.txt` or its own prompt. Any change is
  restored from the pre-AI commit, and the run fails.
- `logs/actions/` flags any git command that can print file contents from history (`git show`,
  `git log -p`, …) for review, alongside the path fences.
- `check.py` fails if any file under `events/`, `universe/` or `registry/` was ever deleted, or if an
  append-only hash list ever lost or changed a line.

## 7. Requirements any T1 rule must meet before it can be scored (the history study, rule v0)

1. The rule-building **procedure and its search log** are frozen before the rule, including every
   factor and specification tried, so the number of tests is countable (rule 7).
2. It is built **by code only**, never by an AI's judgment. An AI's training data covers the history
   quarters, which is look-ahead.
3. It uses only factors **reconstructible as of each past date**. yfinance `info`, `eps_trend` and
   `earnings_estimate` are current-only values and are excluded from history. Source match holds
   (v1 §5).
4. **Survivorship:** the history universe is rebuilt as of each past date, not from today's tickers.
   Where that is impossible, the rule and its report say so.
5. The history window **ends before the pilot starts** (2026-09-21).

Season A remains exploratory. The first confirmatory file (`D005_confirmatory_seasonB.json`) is
registered before Season B's screening date. Its family should include `T2_confidence`.
