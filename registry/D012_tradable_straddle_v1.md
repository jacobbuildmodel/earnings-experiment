# D012 · The tradable short straddle · v1 — FROZEN 2026-10-12 (ET) · one confirmatory hypothesis, H-XT

> **Frozen before any Season A event it covers has an outcome.** The only Season A gate so far, DPZ
> (2026-10-09), is `wide_spread`, so H-XT excludes it, and it is ungraded anyway.
> **Origin, disclosed:** a candidate found by looking at D010, which is exploration. It came from a cut that
> D010 did not pre-register (`analysis/d010/REVIEW_2026-10-12.md`). Under rule 6 that history is the reason
> to test, never evidence. Season A + B are out of sample: D010's data ends 2026-09-18.

## 1. The candidate (D010 history, 2020–2026, 2025–26-heavy; exploration only)

D010 found that across all 1,249 events neither side paid after costs:
- short −3.22%, t −19
- long −4.03%, t −20

Its end-of-day quotes are wide, with a median spread of 21–31% of the option price. Restricted after the
fact to the events whose ATM legs **both** had a relative spread ≤ 10% at the entry close (the D003 S2 gate's
own `max_rel_spread_each_leg`), the picture changes:

| n = 168 events, 114 dates | mean per $1 of spot | t (clustered by date) |
|---|---|---|
| short, at the bid, bought back at the reaction-day close ask | +0.05% | 0.17 |
| short, at mid | **+1.13%** | **3.44** |
| long, both spreads paid | −2.20% | −6.42 |

These numbers are post hoc, so the winner's curse applies. Exiting at the reaction-day close also pays a
second spread. The live SH-X trade does not pay it: it holds to expiry and settles at intrinsic.

## 2. The hypothesis

| id | hypothesis (one-sided) | sample |
|---|---|---|
| **H-XT** | mean SH-X P&L on spot (bid) > 0 | graded SH-X events whose `gate.json` records `options.rel_spread` **≤ 0.10 on both the call and the put** |

- **SH-X is exactly D009 §4**, graded by the same code, with the same voids (including `print_late`), the
  same timing checks and the same existence-before-entry rule. Only the filter is new.
- **The filter** reads the gate's recorded `rel_spread` and nothing else. It is computed at the snapshot,
  before entry. It holds whatever the gate's status: a gate INELIGIBLE for another reason is in, and one
  missing `rel_spread` is out.

## 3. Test and verdict — the D009 §5 method, its own family

- One-sided cluster-robust t by entry session, plus D005's restricted wild cluster bootstrap: 9,999 draws,
  Rademacher weights at ≥ 12 clusters and Webb below, with the seed per test name `H-XT`.
- **Its own family, m = 1, α = 0.05.** D009's Holm family (H-M, H-X, H-VOL, m = 3) is unchanged.
- The rule 7 minimum applies: under 30 events or 10 entry sessions, the result is "insufficient".
- It reports the MDE, (1.645 + 0.842) × clustered se. It is also reported without `timing_unverified` and
  `late_8k` events.
- **Verdict timing:**
  - before a season's end, results are interim and for monitoring only
  - Season A's season-end result is an interim to Gate 1
  - **the registered verdict is on Seasons A + B pooled, at Season B's end**
- **Wording:** "p < 0.05 (shadow, confirmatory for H-XT)", or "no evidence (shadow) — an effect smaller than
  <MDE> would usually be missed". Never "works", never "no effect".

## 4. Reported beside it (descriptive, no test)

- SH-X at mid on the same subset.
- D011 PX-F (the short iron butterfly) and PX-L (the long straddle) on the same subset. This shows whether
  real paper fills keep what the bid assumption gives.
- The excluded events: SH-X on gates with `rel_spread` > 0.10.

## 5. Implementation

- **The code is added later:** an H-XT path in D009's report code. It applies the §2 filter to the existing
  SH-X rows and reuses the H-X test unchanged.
- It is written and hashed as `D012_implementation_v1.sha256` **before the first report that shows H-XT,
  and in any case before Season A's season end**. It may not change §2–§3.

## 6. What changes this rule

Nothing in v1 is ever edited. A different threshold, exit or sample is a v2 with its own clock.
