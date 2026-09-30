# D003 · Universe screening rule · v4 — FROZEN 2026-09-29 (ET) · applies from Season A

> v3 was frozen earlier the same day and has never governed a gate: no Season A event exists yet. v4
> replaces it before its first use. **v1 stays LIVE for the pilot**, and MU's pilot record stands as
> gated. Machine-readable twin: `D003_universe_screen_v4.json`. This file wins on any disagreement.
> **Everything not listed here is v3 unchanged.**

## Change 1 — open interest over a ±2% band, not one strike

- **The defect.** The pilot's first gate ever (MU, 2026-09-29 14:31 ET) was rejected `thin_oi`.
  - 260 contracts at the single strike nearest spot ($1,072.50).
  - The same expiry held **309,771** contracts; 18,820 lay within ±2% of spot.
  - The spread test, the real measure of tradability, passed at 0.85% a leg.
  - A single-strike floor scales with share price: a $1,000 stock lists strikes $2.50 apart, so its
    open interest is spread over many more strikes than a $30 stock's.
- **The check.** On 2026-09-29, 19 of the first 20 Season A preview names priced over $250 failed the
  single-strike floor on their earnings expiry (weeks out, when open interest is still building).
- **v4:** the 500-contract floor applies to call + put open interest summed over every strike within
  **±2% of spot** in the gate expiry, **always including the nearest strike**. So v4 is never stricter
  than v3. The single-strike sum is still recorded as `oi_atm`, so the two can be compared on every
  event.
- **Decided on the gate evidence only.** MU prints on 2026-09-30 after this freeze; no outcome was seen.
