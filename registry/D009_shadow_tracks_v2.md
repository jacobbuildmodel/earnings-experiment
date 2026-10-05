# D009 · Shadow tracks · v2 — the year-round market-wide shadow — FROZEN 2026-10-02 (ET)

> Drafted 2026-10-03 by a claude.ai cloud session (`ops/cloud_session_prompt.md`, T2). CHARTER I11.
> Machine part: `registry/D009_shadow_tracks_v2.json`.
>
> **v2 changes nothing in v1.** SH-W, SH-M and SH-X, v1's family (H-M, H-X, H-VOL; Holm m = 3) and
> its pooled A+B verdict are scored untouched (rule 5). v2 adds one track and one test with their own
> clock.

> **Laptop review and freeze, 2026-10-02 ~22:45 ET.** Drafted in a cloud session (PR #1); reviewed,
> merged and frozen here, before Season A's first entry.
> - **Code:** its 30 tests pass; no look-ahead found. Grading reuses `shadow.grade_one` unchanged.
> - **§5.1:** the Nasdaq screener was probed from the laptop. One call returned **7,073 listings**, with
>   `symbol` and `marketCap`. It works.
> - **§5.2, measured** from the laptop's Nasdaq calendar counts of 2026-10-02:
>   - 2025-11-24 → 2026-01-09: 21 of 35 weekdays carried a print ≥ $2B, **165 prints, ~7.9 per such day**
>   - 2026-08-24 → 09-18: 15 of 20 weekdays, **134 prints, ~8.9 per such day**
>   - So the k ≈ 8 column of §0 applies: **about +24–40% information a year**
> - **§5.3:** `clock_start_entry_session` = **2026-10-05**, the first open after this freeze commit.
>   Every Season A SH-M event is therefore inside H-MY.
> - **§5.4:** `shadow.yml` runs `shadow_offseason.py due --commit` each evening. It screens a window once
>   on or after its screen date, then grades. Job timeout 150 min.
> - **Kept as the draft says:** H-MY is its own family (m = 1) and shares data with v1's H-M. Neither may
>   be cited without the other (§3).

## 0. The answer first: what it buys, and the uncomfortable part

Exploratory, on the D006 history (`analysis/d009v2/info_gain.py` → `info_gain.txt`; 3,536 allowlist
prints, 2022-09 → 2026-09; "in-season" = a 6-week window from the 2nd Monday of Jan/Apr/Jul/Oct).

**Variance split by entry session.**

| sample | events | sessions | events per session (median) | sd shared by the session | sd stock-specific |
|---|---|---|---|---|---|
| in-season | 3,141 | 345 | 7 | 1.80% | 9.14% |
| off-season | 395 | 164 | 1 | not estimable (≈ 0) | 9.74% |

An entry session with *k* events carries information 1 / (1.80%² + 9.14%²/*k*) about the mean.
Against an in-season market-wide session (~45 events), one off-season session is worth:

| events that session | 1 | 2 | 3 | 5 | 8 | 15 |
|---|---|---|---|---|---|---|
| share of an in-season session | 6% | 11% | 16% | 26% | 37% | 58% |

**Information added per year** (~127 off-season sessions a year; in-season 4 × 29 sessions):

| share of off-season sessions with a print ≥ $2B | k = 2 | k = 3 | k = 5 | k = 8 |
|---|---|---|---|---|
| 40% | +5 to +8% | +7 to +12% | +11 to +18% | +16 to +27% |
| **60%** (JOURNAL 2026-10-02, last year's Nasdaq calendar) | +7 to +12% | +11 to +18% | +17 to +28% | +24 to +40% |
| 80% | +10 to +16% | +14 to +24% | +22 to +37% | +33 to +54% |

The low end of each cell assumes a flat 45 events on every one of 29 in-season sessions. The high end
scales the history's in-season sessions instead: fewer sessions carry a print, and their sizes are
uneven, so the in-season side carries less information and the off-season share is larger. Scaling the history's own off-season sessions the same way gives **+15 to
+25%**.

- **Uncomfortable 1: the gain is modest, and smallest exactly where it is wanted.** For the A+B pooled
  verdict, the off-season between A and B (~35 sessions) moves H-M's expected t from **2.19 to
  2.26–2.34** at the history premium (+0.65% net), and from **1.01 to 1.04–1.08** at +0.30%. Year-round
  is a +10–25% a year accumulator, not a fix for Gate 1 or Gate 2. Its real value is through Sep 2027,
  when ~4 off-season windows have accrued.
- **Uncomfortable 2: the off-season is a different population.** Off-season reporters are mostly
  non-calendar fiscal years (retailers, and Dec/Mar/Jun/Sep fiscal-quarter firms). In history their net
  mean is **+0.27%** (t 0.51, 395 prints, hit 50.4%), against **+0.59%** in-season (t 2.69). The
  difference, −0.32 pts (t −0.56), is not significant, but pooling may dilute the premium. So v2 reports the
  off-season alone and the difference beside the pooled test.
- **Uncomfortable 3: the brief's suggested universe does not work.** Using last season's S1 capture
  (the calendar union of names that print *in* the season window) would miss almost every off-season
  reporter: **only 5 of 389 (1%) off-season prints in history came from a ticker that printed in the
  preceding season window.** Firms report on a fixed lag from their own quarter end, so off-season
  reporters stay off-season. v2 therefore needs its own fixed-date screen (§2).
- **Not done (network blocked, `ops/cloud_probe_2026-10.md`):** recounting last year's off-season
  prints ≥ $2B per weekday from the Nasdaq calendar. The 60% figure is the laptop's count from
  2026-10-02 and was not re-verified here. One live point: the 2026-10-02 capture lists **1, 5, 2, 3 and
  1** names ≥ $2B (Nasdaq's cap) for Oct 5–9, the quiet week before Season A. That is k ≈ 2–3, so the
  low end of the table.

**Recommendation: freeze v2.** It costs no AI, about 40 minutes of Yahoo calls per window, and one
code file. It adds information every off-season week that would otherwise be lost, and it measures the
off-season premium on its own (negative knowledge if it is ~0). It should not be sold as a power fix.

## 1. Track SH-MO — market-wide, off-season

**Event:** a print of a name in the window's universe (§2) with D inside a registered off-season window,
dated exactly as SH-M (D009 v1 §3.2): (name, D, session) **as listed in the shadow calendar capture
taken on its snapshot session** (BMO: D−2 sessions; AMC: D−1; the D003 S2 offsets of the season the
window follows). With no capture that day or no session, there is no event. Share classes of one CIK
on one date are one event.

**Grading:** D009 v1 §1 verbatim, through the same code (`shadow.grade_one`, the event graded as SH-M
and then labelled SH-MO):
- the D001 trade, exit A
- net = raw − 0.20%
- dividends and splits
- the 2.02 8-K timing check (verified / VOID contradicted or early / flag late or unverified)
- the domestic test (`not_domestic_*` VOID)
- existence before entry: the calendar capture **and** the window's screen file must be committed
  before the entry open

Outputs go to `outcomes/shadow/<window>/`, fenced from T2 like v1's.

**Windows (registered explicitly, never inferred):**

| window | follows | sessions | screen date |
|---|---|---|---|
| `off_seasonA` | seasonA (ends 2026-11-20) | D in 2026-11-23 → 2027-01-08 | 2026-11-18 |

- The code refuses any window that overlaps a registered D003 season window. A print is either v1
  SH-M or v2 SH-MO, never both.
- **Disclosed gap:** if D003 v5 starts Season B later than 2027-01-11, prints from 2027-01-11 to the
  day before Season B are in neither track. The next window (after Season B) is registered by v2.1,
  before its screen date, once Season B's window is known.
- **Why the screen is on 11-18, not 11-20:** the earliest event, BMO 2026-11-23, enters at the
  2026-11-20 open. The screen file must be committed before that (§1 existence rule). The 11-18 date
  leaves 11-19 as a retry day. A screen that is late voids only the events whose entry came before it.

## 2. Universe (rule 8): one fixed-date screen per window

On the window's screen date (a later session is allowed, and voids mechanically as above), write-once
`shadow/offseason/<window>/market.json`:
1. **Ticker list:**
   - **Nasdaq's stock screener** (`api.nasdaq.com/api/screener/stocks`, every NYSE / Nasdaq / NYSE
     American listing with Nasdaq's market cap)
   - **united with** the Nasdaq earnings calendar for every weekday of the window, as of the screen
     date
   - The screener makes the list independent of who has announced a date yet. The calendar is a
     backstop if the screener fails, and the failure is recorded.
2. **Pre-filter:** keep names Nasdaq sizes at ≥ $1.5B, or does not size. This only saves Yahoo calls;
   the decisive cut is step 4.
3. **Market data:** Yahoo `Ticker.info` for each name, with the same fields as S1's
   `yfinance_market.json`. A failed name is recorded as an error, never filled.
4. **Filters:** D003's S1 block of the preceding season, verbatim, as D009 v1 §3.1:
   - EQUITY
   - NYSE / Nasdaq / NYSE American
   - USD
   - **≥ $2B at capture**
   - not a D003-excluded ticker
   - not "Shell Companies"
   - any industry, no options condition

The domestic-filer test runs at grading (SEC), as in v1.

## 3. Hypothesis, test and verdict — v2's own family, m = 1

| id | hypothesis (one-sided) | sample |
|---|---|---|
| **H-MY** | the mean net return of every market-wide event from v2's clock is > 0 | v1's graded SH-M of seasonA and seasonB with entry ≥ the clock, **plus** graded SH-MO of `off_seasonA` |

- **Clock:** `clock_start_entry_session` = the first session whose 09:30 ET open falls after the commit
  that freezes v2.
  - **If v2 is frozen before Season A's first entry open (2026-10-12 09:30 ET), Season A's SH-M is in.**
  - If later, Season A's SH-M events before the clock are out. Its outcomes would already exist, so
    including them would let the result choose the sample.
- **Test:** v1 §5 mechanics:
  - cluster-robust t by entry session
  - D005 restricted wild cluster bootstrap, 9,999 draws, seed `report.R("H-MY")`
  - rule 7 minimum (30 events, 10 sessions) → "insufficient"
  - MDE = 2.487 × clustered se
  - also reported without `timing_unverified` / `late_8k`
- **Verdict date:** the same as v1's pooled verdict (Season B's last report date + 10 days). Earlier runs
  are "interim (monitoring only)". Wording as v1: "p < 0.05 (shadow, secondary; v2 family m = 1)" or
  "no evidence (shadow) — an effect smaller than <MDE> would usually be missed". Never "works", never
  "no effect".
- **Descriptive, not tests:** H-MO, the SH-MO mean alone; MO−M, the off- minus in-season difference
  (OLS dummy, same bootstrap).
- **Disclosed — one question asked twice:** H-MY shares most of its data with v1's H-M. The two are
  not independent evidence, and neither may be cited without the other. H-MY is the better-powered
  version; H-M is the one registered first. If both are wanted in one family, that is a v1 change,
  which rule 5 forbids. A Gate 1 decision may instead register H-MY as the confirmatory market-wide
  test for later seasons.
- **What a result can do:** the same as v1 §5. At Gate 1, register it as a confirmatory hypothesis for
  a later season. Nothing else.

## 4. Code (on the cloud branch, behind new commands; v1's commands unchanged)

`pipeline/shadow_offseason.py` — `windows` · `screen <window>` · `grade <window> [--no-fetch]` ·
`report <window> [--with seasonA seasonB] [--write] [--final]`. Tests:
`tests/test_shadow_offseason.py`, covering:
- the dating rule
- the overlap guard
- existence before entry
- the S1 filters
- end-to-end grading on fake prices / timing
- the clock filter
- seeds by name
- insufficient
- refusing an unfrozen rule, an unset clock, and the pilot

## 5. For the laptop session before freezing

1. **Probe the Nasdaq screener endpoint** from the laptop. This session's network is blocked, so it is
   untested here. Confirm the row fields (`symbol`, `marketCap`) and that one call returns every
   listing (several thousand rows). If it fails, decide whether the calendar union alone is
   acceptable, and say so in the frozen text.
2. Count last year's off-season prints ≥ $2B per weekday (Nasdaq calendar) and replace the k-range in
   §0 with the measured one. It was not possible here.
3. Set `clock_start_entry_session`. Copy the .md/.json to `registry/` and add both hashes to
   `FROZEN.sha256`. Register `pipeline/shadow_offseason.py` and the new `pipeline/shadow.py` (T1
   refactor) in a `D009_implementation_v2.sha256`.
4. Workflow (`shadow.yml`, which this session may not touch):
   - an evening step on/after 2026-11-18 that runs `python pipeline/shadow_offseason.py screen
     off_seasonA --commit` (≈ 40 min of Yahoo calls; give it its own timeout)
   - add `python pipeline/shadow_offseason.py grade off_seasonA` to the evening grade loop, then
     `commit-grade`
5. Decide the gap question (§1) when D003 v5 fixes Season B's window.
