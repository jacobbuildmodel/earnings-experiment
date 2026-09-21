# D005 · Evaluation protocol v1 — how graded outcomes become a verdict — FROZEN 2026-09-21 (ET)

> Frozen **before any outcome of this experiment could be known**: the earliest possible exit A is the
> open of 2026-09-23, and nothing had been graded. D001 fixes *what* a win is; D005 fixes *how* wins are
> counted, tested and worded, so none of those choices can be made after seeing results (rules 2, 5–8).
> A change creates `D005_…_v2` with its own start date; v1 keeps being computed and reported beside it.
> Where FRAMEWORK §5 and this file differ, this file wins.

## 1. What is counted

- **Graded event:** passed the D003 S2 gate, frozen before its entry open, and not VOID under D001 §6.
  VOID and INELIGIBLE events keep their rows and are counted beside every result (D001 §6, D003 §1).
- **Event-date (the cluster):** the event's **entry session**. For exit A, every event entering on
  session X is held over the *same* window, from X's open to the next session's open: a BMO print on
  X+1 and an AMC print on X both enter at X's open and exit at X+1's open. Consecutive windows do not
  overlap. So events that share an entry session share one market move, and no other events do. Every
  standard error, p-value and interval below is clustered on it. "10 event-dates" in rule 7 means 10
  distinct entry sessions. Secondary exits B and C hold longer; their windows can overlap across
  entry sessions, and their clustered numbers are therefore approximate. That is one more reason they
  are secondary.
- **Samples are never mixed.**

  | sample | role |
  |---|---|
  | `pilot` (prints 2026-09-21 → 10-09) | pipeline test. Labelled **PILOT — bugs, not findings** on every output. Never confirmatory. |
  | `seasonA` | first out-of-sample read of rule v0 and of T2. **Exploratory**, whatever the p-value. |
  | `seasonB` onwards | confirmatory, for hypotheses registered before that season's screening date (§4). |

- **A track is evaluated only on events where it made a decision**, and T0 is recomputed on exactly
  those events. A T2 frozen as MISSING (`freeze.py --t2-missing`) is excluded from T2's numbers and
  counted as `t2_missing`. T1 is null in the pilot (D004 §2), so the pilot has no T1 result.

## 2. The primary statistic — per track, against T0, on the primary outcome (D001: exit A, WIN_raw)

| quantity | definition |
|---|---|
| T0 hit rate `H0` | share of the track's graded events with WIN_raw |
| BUY-set hit rate `HB`, NO_BUY-set `HN` | the same share within the track's BUYs / NO_BUYs |
| **lift** (PRIMARY, D001 §5) | `HB − H0` |
| separation `β` | `HB − HN` |

With BUY share `f`, **lift = (1 − f) · β**, so lift > 0 exactly when β > 0 (0 < f < 1). The **point
estimate reported is the lift**; the **test is on β**, estimated as the slope of a linear probability
regression `WIN_raw = α + β·BUY + ε`. A track that buys everything or nothing has lift 0 by definition
and is reported as "no selection".

Always beside it (never promoted to primary): mean raw return of each set, **return lift**
(`mean_BUY − mean_all`) and return separation with the same test, NO_BUY accuracy, void and missing
counts, and the three robustness cuts: without `price_dispute`, without `timing_unverified`, without
`confound_8k`.

## 3. The test

- **Hypothesis (per track):** H0: β ≤ 0 against H1: β > 0. One-sided, because the experiment asks only
  whether selection *beats* buying everything.
- **Method:** cluster-robust (CR1) t-statistic for β, clustered by entry session, with its p-value
  from the **restricted wild cluster bootstrap-t** (Cameron, Gelbach & Miller 2008): the null imposed,
  9,999 draws. Rademacher weights with ≥ 12 clusters, Webb six-point weights below 12. Seed 20260921.
  *Why:* the number of event-dates is small, and conventional cluster-robust t-tests over-reject with
  few clusters; the wild cluster bootstrap holds its size with as few as ~6 clusters. It is the
  regression form of a directional-accuracy test against the base rate, in the spirit of
  Pesaran–Timmermann (1992); the return version plays the role of Anatolyev–Gerko's (2005)
  excess-profitability test.
- **T2 vs T1** (from Season A, when T1 exists): stack the two tracks' rows,
  `WIN_raw = α + γ·T2 + β·BUY + δ·BUY×T2 + ε`, clustered by entry session. δ > 0 means T2 separates
  better than T1. The test is the same wild cluster bootstrap on δ.
- **T2's probabilities** — reported for every season, never used to re-score a decision:
  - Brier score and **Brier skill score** against the constant forecast equal to the sample's own T0
    hit rate. That reference knows the base rate in hindsight, which makes it harder to beat, not easier.
  - Log loss, with confidence clipped to [0.01, 0.99].
  - AUC, with a 90% interval from resampling whole entry sessions (2,000 draws, same seed).
  - A calibration table in bins 0–.40 · .40–.50 · .50–.60 · .60–1.
  - The share of confidences within 0.45–0.55, which shows whether T2 is hedging.

## 4. Verdict wording — fixed, so a result cannot be talked up or down

| condition | the only words allowed |
|---|---|
| fewer than 30 graded events **or** fewer than 10 event-dates | **"insufficient"**. The code produces no lift, separation or p-value to quote; only the descriptive hit rates and mean returns appear |
| pilot | "PILOT — bugs, not findings", then the descriptive numbers |
| Season A, p < 0.05 | "evidence of lift (exploratory, p = …)" |
| Season A, p ≥ 0.05 | "no evidence of lift (p = …)" — never "no effect" |
| confirmatory season, registered hypothesis | "confirmed" / "not confirmed", after the Holm correction below |

**Confirmatory family (Season B onwards):** H1 T1 lift > 0 · H2 T2 lift > 0 · H3 T2 separates better
than T1 (δ > 0), plus any hypothesis registered in writing before that season's screening date. The
family is tested at α = 0.05 with the **Holm** step-down correction over the number registered. Nothing
unregistered can be "confirmed".

The hypotheses are registered in `registry/D005_confirmatory_<season>.json`, frozen and hash-listed
before that season's screening date. `report.py` refuses a file that is not in `FROZEN.sha256`. With no
such file it prints no confirmatory verdict at all. A hypothesis that cannot be tested (for example,
a track that bought everything) counts as p = 1, not confirmed.

## 5. Exploration — the findings table (FRAMEWORK §5)

- **Effect of a factor:** the WIN_raw rate in the top third of the factor minus the bottom third
  (terciles within the season, per group), and the same difference in mean raw return. The t-statistic
  comes from the §3 regression on a top-vs-bottom indicator, clustered by entry session. The p-value is
  two-sided, from the same wild cluster bootstrap. Groups: all events, and each sector cluster. A test
  needs at least 9 events with the factor; fewer is not run.
- **Multiple testing (rule 7):** every factor × cluster × outcome test that is run is logged and
  counted. Benjamini–Hochberg q-values are computed across all of them. A factor becomes a
  **CANDIDATE** only if q < 0.10, **and** |t| > 3, **and** the effect has the same sign in both halves of
  the sample (split at the median entry date).
- **Per-cluster and per-stage answers:** partial pooling by normal–normal empirical Bayes. Each
  cluster's β is shrunk towards the pooled β with the DerSimonian–Laird between-cluster variance τ²,
  weight on its own estimate = τ² / (τ² + se²). A cluster under the rule 7 minimum is "insufficient"
  whatever its shrunk value.
- **Known truncation:** every event already has implied move ≥ 4% (D003 §6). Any B-family (options)
  finding holds only for that range and must say so.
- **Source match:** a factor may enter a T1 rule only if its live value (captured at the snapshot) and
  its history (used to build the rule) come from the same source and basis, or from a reconciliation
  written down before the rule is frozen. Two vendors disagree on EPS consensus basis (STATE #2).

## 6. How D001 is applied by the grader (`pipeline/grade.py`) where D001 leaves a choice

- **Corrections (D001 §2):** a price row is never rewritten. A correction is a new row that carries a
  reason, and the newest row for a key is the one in force.
- **Prices:** yfinance `history(auto_adjust=False)`. Yahoo's series is already split-adjusted, so a
  split between entry and exit is already applied (D001 §3); it is flagged `split_in_window`. A cash
  dividend with entry < ex-date ≤ exit is added to the exit price, flag `dividend_adjusted`. Prices
  are fetched only after the session's close + 15 min. Each is stored once with its fetch time and
  never rewritten.
- **Check source:** Alpha Vantage `TIME_SERIES_DAILY`, which needs the `ALPHAVANTAGE_API_KEY`
  secret. Without it every price is flagged `single_source` (D001 §2). Alpha Vantage prices are
  as-traded while Yahoo's are split-adjusted, so the Alpha Vantage value is divided by the splits
  recorded after that session before the tolerance test.
- **"Print date or session differs" (D001 §6)** is checked against the company's **Item 2.02 8-K**
  acceptance time on SEC EDGAR:
  - inside the frozen release window (BMO: previous close → open of D · AMC: close of D → next open)
    → `verified`
  - inside the opposite window → **VOID `print_session_differs`**
  - accepted during market hours, or no 2.02 8-K within D−3…D+3 → `timing_unverified`, because an 8-K
    can lag its press release. The result is reported with and without these events.
- **Confounds:** every 8-K from three days before the print to three days after exit C is stored. Any
  item other than 2.02, 7.01 or 9.01 sets `confound_8k` (CLAUDE.md: read every filing in the event
  window). This is a robustness cut, never a VOID.
- **Leave-one-out benchmark:** no issuer holdings file is captured (the iShares and SPDR files are not
  machine-fetchable), so every WIN_excess carries `bench_weight_missing`, the D003 §8 fallback.
  WIN_excess is secondary.
- **Rule 1:** an event whose manifest commit is timestamped at or after the entry open is VOID
  `freeze_after_entry_open`. The RFC 3161 tokens are verified by `check.py`.

## 7. Power — what this experiment can and cannot see (registered so it cannot be forgotten later)

The smallest true effect detectable with 80% power, one-sided α = 0.05. This assumes a 55% base rate,
half the events bought, and **independent events**. Clustering on event-dates makes every number
larger; ×1.14 at a design effect of 1.3.

| graded events | detectable separation β | detectable lift |
|---|---|---|
| 30 | 45.2 pp | 22.6 pp |
| 100 (≈ Season A) | 24.7 pp | 12.4 pp |
| 200 | 17.5 pp | 8.7 pp |
| 400 | 12.4 pp | 6.2 pp |
| 800 | 8.7 pp | 4.4 pp |

A season of ~100 events can only detect a selection edge of ~12 points of hit rate over buying
everything. Published earnings-window edges are far smaller than that, so **"no evidence of lift"
after one season is the expected result even if a modest edge exists.** The pre-registered answer to
that is to pool seasons (a new D005 version that says so, before the pooled data is seen), never to
loosen the test.

## 8. Implementation

- `pipeline/grade.py` applies D001 + §6; `pipeline/report.py` computes §1–§5, all of it: per-track
  lift, the stacked T2-vs-T1 test, Holm confirmatory verdicts, T2 probability scores, partial pooling,
  and the findings table with BH, |t| > 3 and split halves.
- Both were tested on synthetic data before this freeze:
  - the vectorised bootstrap equals a per-draw loop
  - the size is 5.5% at the 5% level (1,000 simulations, 25 clusters)
  - a planted real factor is promoted, and a noise factor and a noise rule are not
  - grade.py graded real past prints and voided a deliberately mislabelled session
  - independent review by a second model (Sonnet) found defects, and they were fixed before the freeze
- The SHA-256 of both files at this freeze is recorded in `registry/D005_implementation_v1.sha256`,
  and `report.py` prints whether the running code still matches it. A later change to either is a new
  implementation version, logged there, and results are reported under both versions until a new
  D005 retires the old one.
- Outcomes and reports are written under `outcomes/`, which is never on disk for the AI step (D004 §3).
