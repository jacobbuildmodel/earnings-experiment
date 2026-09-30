# D003 · Universe screening rule · v3 — FROZEN 2026-09-29 (ET) · applies from Season A

> v2 was frozen for Season A on 2026-09-21. No Season A calendar has been pulled yet (the capture slot
> opens 2026-10-08 16:00 ET), so v2 has never governed a screen and v3 replaces it before its first use.
> v1 stays LIVE for the pilot. Machine-readable twin: `D003_universe_screen_v3.json`. This file wins on
> any disagreement. **Everything not listed below is v2 unchanged, word for word.**

## Change 1 — one event per issuer

- **The defect.** A Season A preview (2026-09-28, D003 v2 on that day's data) admitted both **GOOG and
  GOOGL**, and both **Z and ZG**. Two share classes of one company report one set of results. Two
  events would count one print twice, and the two outcomes are nearly identical, which inflates n and
  understates the standard errors.
- **v3:** the S1 screen and the mid-season screen keep **one ticker per SEC CIK**, the alphabetically
  first. The other classes are excluded with reason `second_share_class`.
- A mechanical choice, fixed before any Season A data exists. Found while building the history study
  (D006 §2 applies the same rule).
