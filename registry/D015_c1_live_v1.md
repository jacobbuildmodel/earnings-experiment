# D015 · C1 live · v1 — fade a pre-market gap beyond the implied move, confirmed on fresh market-wide events

> **CONFIRMATORY SHADOW. Frozen before the first reaction session it counts.** Graded after the fact from Alpaca
> history; no order is ever sent. Code: `pipeline/shadow_c1.py`, workflow `.github/workflows/c1-shadow.yml`,
> hashes `registry/D015_implementation_v1.sha256`. It changes nothing in D001–D014.
> **Reviewed before freezing** by an independent Opus 5.5 agent: FREEZE WITH FIXES, 11 findings, all applied. The
> critical one: D014's implied move came from **monthly** expiries, so the live one does too (§3).

## 0. Where it came from (disclosed)

- **D014 v1** (exploration, `analysis/d014/REPORT.md`) tested 42 first-hour cells on 2022-09 → 2025-08. One
  group survived TRAIN: **C1, a pre-market gap bigger than the options-implied move** (|g| > IM).
  - TRAIN, y_30: −2.01%, t −4.06, n 70 on 45 dates (it reversed).
  - VALIDATION: the same sign, −0.90%, n 62 on 36 dates, Holm p 0.48. **It failed validation.**
- **Rule 6:** a failed validation leaves C1 a hunch, not a finding. This registration is its one clean test, on
  data neither TRAIN nor VALIDATION touched.
- **Origin of the question:** Jacob, via a DRIVE note on 2026-10-13 (ideas only; rule 9 intact). Rule 10: no
  archive file was read.
- **Why the market-wide set:** C1 flags only ~15% of events with an implied move. On the ~300 gated events a
  season, power would stay near 35% even pooled. On SH-M (~1,300 a season) it is ~85% (§9).
- **Planning value:** −0.9% (VALIDATION), not −2.0%. y_30 had the largest VALIDATION effect of the five horizons;
  it is chosen as the single primary before any fresh data exists, so the error rate holds.

## 1. Hypothesis (one, one-sided)

**H-C1:** among earnings events whose pre-market gap is at least 1% **and** larger than the options-implied move
priced on the prior afternoon, the return from the reaction session's official opening auction to 10:00 ET,
signed in the gap's direction, is **negative** on average. The gap partly reverses.

## 2. Events

- **Population:** every **SH-M** event (D009 §3.1–3.2, unchanged) of **Season A and Season B**.
  - That means: a name of the season's frozen S1 raw capture; a US-listed common stock of ≥ $2B; any industry;
    dated by the Nasdaq calendar captured on its snapshot session; one event per SEC CIK.
  - D009's voids carry over:
    - `not_committed_before_entry`
    - `print_contradicted` / `print_early` (Item 2.02 8-K, `shadow.sec_timing`)
    - `not_domestic_foreign` / `not_domestic_no_cik`
- **Sessions:** R = the D001 exit-A session (the reaction session). P = the D001 entry session, the session
  before R.
- **Counted from the registration:** an event counts only if R's 09:30 ET open is **after** the later of the
  first commits of this file and `registry/D015_implementation_v1.sha256`. Earlier events are VOID
  `before_registration`, listed but never tested.
- **Not counted:** the off-season SH-MO windows (D009 v2) and the pilot. Adding them is a new version.

## 3. The implied move, captured live on P

- **When:** from 35 to 5 minutes before P's official close (15:25–15:55 ET on a normal day, 12:25–12:55 on a
  13:00 close). The code waits inside one job; GitHub cron is not trusted (CLAUDE.md).
- **Primary contract (D014's instrument):** the first **monthly** expiration strictly after R.
  - Monthly means the third Friday, or the Thursday before it when that Friday is not a session.
  - Why: D010's chains held mostly monthlies. 82% of D014's 868 implied moves (84% of D010's events) used a
    third-Friday expiry, a median 15 days after R. A weekly a few days out prices a much smaller move, so it
    would lower the C1 bar for large caps only.
- **Strike:** the strike listed for both calls and puts **nearest to spot** (yfinance `fast_info["last_price"]`),
  the lower one on a tie.
- **IM** = (call mid + put mid) / spot. It needs both bids > 0 and neither quote crossed. Otherwise IM is
  missing.
- **Secondary contract:** the first listed expiration strictly after R, often a weekly, read in the same pass,
  with its days after R.
- **Retries:** an event without a primary IM is retried every 60 s until the window closes. `no_expiry` is final.
- **Write-once file:** `shadow/c1/im/<P>.json`, committed and pushed at once. A failed push fails the job loudly.
  A day with no due event writes an empty file.
- **An event's IM is missing (never C1, still graded) when:**
  - `no_capture`: no file for P
  - `im_late`: the file's first commit is at or after 09:27 ET on R
  - `pre_registration`: the file was committed at or before the registration
  - `mismatch`: the capture's R differs, or its expiry is not after R
  - the fetch failed (its status)
- **Deviations from D014's IM, disclosed:**
  - Timing: D010 used end-of-day quotes on P; this uses quotes about 15 minutes delayed, near 15:25–15:55.
  - Strike: nearest to spot, not the call delta closest to 0.50. They are the same strike on most chains.
  - Expiry: monthly always; D010 used a weekly for the ~18% of events where its chain held one.
  - Source: yfinance (the S2 gate's source), not DoltHub.
  - Universe: market-wide ≥ $2B, not D006's 329 allowlist names.

  The question is the same; the instrument is close but not identical. If H-C1 fails, these are listed as
  possible reasons, never as excuses.

## 4. Prices (identical code)

- The live grader **imports** `analysis/d014/fetch.py` (`build_date`) and `analysis/d014/fetch_v3.py`
  (`build_date`) unchanged. So every definition of D014 v1 §3 and v3 §1 applies:
  - C0, the R−1 closing auction
  - PM, the last trade before 09:27 ET on R, floored at the release's SEC acceptance minute
  - O, the official opening auction
  - P_h and P_c, the last trade before 09:30 + h and the closing auction
  - the NBBO quotes at 09:35, 09:40, 10:00 and 10:30
  - the split check, and voids `no_c0`, `no_open`, `split`, `no_premarket`
  - the first-minute VWAP and the first post-open quote
- **SEC acceptance:** the earliest Item 2.02 8-K accepted inside the event's own session window
  (`shadow.sec_timing`); otherwise unknown (no floor, as in D014).
- **Fetched once per R,** from 17:00 ET on R. The output is write-once:
  `outcomes/shadow/<season>/c1/prices_<R>.json`, derived prices only. A failed request writes nothing, and the
  next run retries.
- **SEC lookup failures:**
  - Prices for R wait while any event's SEC lookup is unresolved (failed or not yet run), for up to 10 days after
    its report date.
  - After that, prices are fetched for the rest. Every event still unresolved, and every row priced under an
    unresolved status, is VOID `sec_unresolved`.
  - This is decided by network failures, never by an outcome. A lookup exception never stops the grade.

## 5. Returns

- g = PM / C0 − 1, s = sign(g). Only |g| ≥ 1% counts (the D014 floor).
- **C1 flag:** primary IM present and |g| > IM, known before 09:27 ET.
- y_h = s · (P_h / O − 1) for h = 5, 10, 30, 60; y_c to the close; the delayed variant y_d. Positive means the
  move continued; negative means it reversed. y_30 is missing when the official open came at or after 10:00
  (D014 §3); that count is reported.
- The net fade at the auction entry, D014 §4 (`run_d014.net`, fee 2 bp): mid less the half spread at 10:00,
  and the closing auction.
- The net fade at the retail entry, D014 v3 (`run_d014_v3.retail_net`, primary kind, fee 2 bp). Entry: the
  first-minute VWAP worsened by half the first post-open spread. Exit: 10:00 at mid less the half spread, and
  the closing auction.
- Market-adjusted y: minus s · SPY's return over the same window.

## 6. The test

- **Primary statistic:** the mean of y_30 over C1 events, with a CR1 standard error clustered by R
  (`run_d014.cr1`). t = mean / SE.
  - **One-sided p** = P(T ≤ t) for Student's t with **G − 1** degrees of freedom, where G is the number of R
    dates. Few clusters make the normal too liberal.
- **Insufficient:** fewer than 30 events or fewer than 10 R dates. No effect size is claimed then (rule 7).
- **Two looks, α = 0.05 split by Bonferroni.** Each look is taken once, by code, and written once
  (`outcomes/shadow/c1_looks/`); a second run refuses.

  | look | data | when | CONFIRMED if |
  |---|---|---|---|
  | 1 | Season A alone | on or after **2026-12-07**, once every Season A timing check is final and every R date is priced | p < **0.005** |
  | final | Season A + B pooled | once every timing check of both seasons is final and every R date is priced | p < **0.045** |

  - At look 1, anything else reads "not yet". The test continues, and no other conclusion is drawn.
  - At the final look, anything else is **NOT CONFIRMED**.
- **Blinding:** until a look is taken, no C1 return statistic is printed, written or reported (no mean, t or p).
  `status` shows counts and coverage only. Nobody sees the effect while the code or Season B could still change.
- **Season B:** its registration (the main experiment's D003 version) is decided without reference to D015.
  - If the experiment runs no Season B, the final look runs on Season A alone, at p < 0.045, on or after
    2027-03-31.
  - Choosing not to run Season B because of a D015 number is forbidden, and no such number can be seen
    (blinding).
- **Family:** H-C1 is its own family, m = 1. D014's exploration family is closed. D009's H-M/H-X/H-VOL and
  D012's H-XT are unaffected.

## 7. Secondary (reported at the looks, descriptive, decide nothing)

- y at 5, 10, 60 and the close, and the delayed variant. The market-adjusted y at every horizon.
- The net fade at the auction and at the retail entry, at 10:00 and at the close.
- C1 restricted to implied moves from tight quotes: both legs' (ask − bid) / mid ≤ 0.10, the S2 gate's own
  spread rule.
- C1 restricted to SEC timing `verified` (excluding `late` and `unverified`).
- C1 among companies under $10B.
- C1 defined with the **nearest-expiry** IM instead of the monthly.
- The complement (gap ≥ 1%, IM present, not C1) and all gaps ≥ 1%. These replicate D014's unconditional
  result.
- Counts:
  - voids by reason, and the IM status of graded events
  - the C1 rate and the quantiles of |g| / IM
  - C1 events missing y_30 (a delayed open)
  - IM coverage (the 0.85 assumed in §9 rests on a 12-name dry run)

## 8. What a result means

- **CONFIRMED, and the net retail fade at the close is > 0 on the same data:** propose a live paper track in
  shares (Alpaca paper, at the open). It gets its own registration, then goes to D008/Gate 2 as a candidate
  sleeve.
- **CONFIRMED, but the retail net ≤ 0:** the reversal is real but not capturable through moomoo SG, which has no
  opening-auction order. It is auction-only; a broker with MOO is Jacob's call, and no new money flows before
  results.
- **NOT CONFIRMED:** negative knowledge for the charter. D014's TRAIN result was a chance pattern, or it decayed.
- **Insufficient:** says nothing; the power assumption was wrong. Report it.

## 9. Power (from D014's own C1 rows, frozen here so the outcome can be compared to it)

- C1 return spread: SD of y_30 = 4.5% (TRAIN) and 4.7% (VALIDATION). The CR1 design effect is about 1.0 on
  TRAIN and 1.6 on VALIDATION.
- **Expected count:**
  - about 1,300 SH-M events a season (D009)
  - × ~0.8 with a gap ≥ 1% (D014: 2,885 of 3,536)
  - × ~0.85 with an IM (a dry capture on 2026-10-14: 10 of 12 names)
  - × ~0.15 C1 (D014: 13–18% of events with an IM)
  - → **~130 C1 events a season**, less the foreign and void events.
- Assuming SD 4.6% and a design effect of 1.3, with about 27 R dates in Season A and 55 pooled (Student t):

  | true mean | look 1 (A, n ≈ 130): expected t · power at p < 0.005 | final (A + B, n ≈ 260): expected t · power at p < 0.045 |
  |---|---|---|
  | −0.9% (VALIDATION) | 2.0 · ≈ 20% | 2.8 · ≈ 85% |
  | −2.0% (TRAIN) | 4.3 · ≈ 94% | 6.2 · ≈ 100% |

## 10. Files and guards

| file | role |
|---|---|
| `pipeline/shadow_c1.py` | capture, grade, status (blind), look1, final, probe (coverage-only check of a pre-registration R) |
| `.github/workflows/c1-shadow.yml` | capture (routine pushes + cron backups, one job waits inside the window), evening grade + blind status, manual probe |
| `tests/test_shadow_c1.py` | expiry and strike choice, window, voids, the C1 flag and y's sign, Student t, blinding, write-once looks, end-to-end on a fake Alpaca |
| `shadow/c1/im/<P>.json` | the write-once captures (no outcome) |
| `outcomes/shadow/<season>/c1.json`, `c1_timing.json`, `c1/prices_<R>.json` | graded rows, timing checks, prices (fenced from T2) |
| `outcomes/shadow/c1_looks/` | the two looks, each written once |

- `check.py` fails if a file under `shadow/c1/im/` changes after its first commit.
- `check.py` fails if any file in `D015_implementation_v1.sha256` differs from its latest line. That covers the C1
  code, the D014 code it imports, and the shared code that defines the sample: `shadow.py`, `sessions.py`,
  `common.py`, `s1_screen.py`. The list is append-only.
- `shadow_c1.py` refuses to capture, grade or take a look if its own code or the D014 code drifts.
- `health.py` raises AMBER when the latest closed session has no C1 capture.
- A change to the C1 code is D015 v2, with its own clock (rule 5). A change to shared code needs a dated line in
  the list saying why the C1 sample is unaffected.
