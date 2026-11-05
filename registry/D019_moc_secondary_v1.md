# D019 §3(a) · The MOC secondary on SH-M and SH-W · v1 — FROZEN 2026-11-04 (ET)

> Registered under `registry/D019_reframe_v1.md` §3(a) (committee REPORT §12.3) **before any of its numbers is
> computed**, on any season. Its code, `pipeline/moc_secondary.py`, comes in a later commit and is hashed in
> `registry/D019_implementation_v1.sha256`. The commit timestamps are the proof.

## 1. What it measures

The trade Jacob can place: **buy at the close before the print, sell at the close of the reaction day**, both by
market-on-close (MOC) order. D009's SH-M and SH-W trade open → open (D001 exit A); this is their close → close twin.

## 2. Events

- Every SH-M and SH-W event exactly as `pipeline/shadow.py` (D009) builds it in
  `outcomes/shadow/<season>/graded.json`: the same names, dates, sessions, VOID rules and 2.02 8-K timing check.
  Nothing is added or removed here.
- An event counts when D009 graded it (`graded` true) and both MOC prices and the dividend field below are present.
  A split between the entry and exit sessions makes it VOID (`split_in_window`), as in D009.
- Events flagged `late_8k` or `timing_unverified` are included and flagged, as in D009. The report also gives the
  figure without them (descriptive).

## 3. Prices

- **Entry:** the official close of D009's entry session (D001: D − 1 for a BMO print on D, D for an AMC print). It is
  the last close before the print.
- **Exit:** the official close of the reaction day (D001's exit-B session: D for BMO, D + 1 for AMC).
- Both from yfinance daily bars, `auto_adjust=False`, field `Close`: the official closing-auction price, which is what
  an MOC order is filled at. On an early-close day it is that day's official close.
- Fetched once the exit session is settled (06:00 ET the next day, as D009), stored write-once in
  `outcomes/shadow/<season>/moc_prices.jsonl`. D009's own `prices.jsonl` is never written. A failed fetch leaves the
  field missing and the event ungraded; it is never filled.
- Dividends with an ex-date after the entry session, up to and including the exit session, are added to the exit.

## 4. Return and costs

- **raw** = (exit + dividends) / entry − 1.
- **Fees:** US$0.99 per order, two orders, at a stated notional of US$1,000: **0.198% a round trip**.
  **net** = raw − 0.00198.
- **The MOC spread:** an MOC order fills at the closing-auction price, and that price is the one used, so no quoted
  spread is crossed. v1 deducts nothing for it. This is a stated assumption, not a measurement: no MOC fill exists in
  the record. Real MOC fills are measured in the paper pilot (D019 §5: Season C, ≥ 50 MOC round trips). A measured
  figure enters only as a new version with its own clock.
- Reported beside it, descriptive: net minus a further 0.10% a round trip (a stress line, not an estimate).

## 5. The statistic, and where it counts

- **Per track and season:**
  - n events and n clusters (the entry session, as D009);
  - the raw mean, the net mean and the win rate (raw > 0);
  - the net mean's cluster-robust SE (CR1, `report.ols_k`) and its 95% interval with t on clusters − 1 df;
  - the one-sided p of net mean > 0 (the D005 restricted wild cluster bootstrap, as `shadow.mean_test`).
- **The Gate 2 statistic (D019 §5): SH-M's net mean on Season B only. It passes if the point estimate is ≥ +0.50%.**
  SH-W's figure is a secondary.
- Any other season (Season A, the pilot, an off-season window) may be computed only labelled **DESCRIPTIVE, not
  evidence**: Season A was read before this file, and the others are not Season B.
- Under 30 events or 10 sessions the status is "insufficient", never "works" or "no effect" (rule 7).
- The bar does not move. A change is a new version with its own clock (rule 5).

## 6. Code

`pipeline/moc_secondary.py`, tested on synthetic rows in `tests/test_moc_secondary.py`. Both are committed after this
file and before any run on real data. Both are hashed in `registry/D019_implementation_v1.sha256`.
