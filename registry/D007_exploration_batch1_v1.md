# D007 · Exploration batch 1 — new signals on the history sample · v1 — FROZEN 2026-09-30 (ET)

> **Exploration, not confirmation (rules 6–7).** This batch looks for **candidates** in the D006
> history sample. Nothing it finds is a result. A survivor becomes a pre-registered hypothesis for
> Season B and is tested only on data it has never seen.
>
> Written and frozen **before any of the data below was downloaded**. On 2026-09-30 the sources were
> probed for format only (FINRA one day, Wikipedia one article, DoltHub schemas and one ticker).
> **No signal was computed against any outcome.**
>
> Sample: `analysis/history/graded_events.json` (D006), prints 2023-09-01 → 2026-09-18, one per
> issuer. Code: `pipeline/explore_d007.py`, implementation hash appended below at the run.

## 1. The signals — each fixed now, with its sign

All are **as of the snapshot-session close**, from data dated on or before it (point in time).

| id | signal | definition | expected sign | source |
|---|---|---|---|---|
| E1 | **Short-selling pressure** | mean daily ShortVolume ÷ TotalVolume over the 5 sessions to the snapshot, minus the same over the 60 sessions before those | − | Christophe, Ferri & Angel 2004 (LR09) · FINRA Reg SHO daily files (CNMS), free |
| E2 | **Peer read-through** | mean exit-A raw return of other sample events of the **same cluster** whose exit-A session is within the 10 sessions up to the snapshot; missing if fewer than 2 | − (early reporters' news is over-extrapolated, then corrected) | Thomas & Zhang 2008 (LR21) · own event table |
| E3 | **Market fear** | VIX close on the snapshot session | two-sided | Baker & Wurgler; Mian & Sankaraguruswamy 2012 (LR25) · yfinance `^VIX` |
| E4 | **Market trend** | S&P 500 ETF (SPY) return over the 20 sessions to the snapshot | two-sided | LR25 · yfinance |
| E5 | **Retail attention** | mean daily English-Wikipedia pageviews of the company's article over the 5 days to the snapshot ÷ the mean over the 60 days before; missing if no article or < 30 views/day | + | Da, Engelberg & Gao 2011 (LR05) · Wikimedia pageviews API; ticker → article via Wikidata P249 |
| E6 | **Early reporter** | calendar days from the end of the last completed calendar quarter to the print date; the sign is on *days*, so early = few days | − | Savor & Wilson (LR03); Johnson & So 2018 |
| E7 | **Rich options** | DoltHub `iv_current` ÷ `hv_current` on the snapshot session | two-sided | the vol-selling literature; the repos reviewed 2026-09-30 |
| E8 | **Implied-volatility run-up** | DoltHub `iv_current` ÷ `iv_month_ago` on the snapshot session | two-sided | Dubinsky et al.; the earnings IV build-up |
| E9 | **Calls rich vs puts** | at the strike nearest the snapshot close, on the nearest expiry in DoltHub `option_chain` for the snapshot date: IV(call) − IV(put) | + | Cremers & Weinbaum 2010; Jin, Livnat & Zhang 2012 (LR12) |
| E10 | **Put skew** | same chain: IV of the put with strike nearest 0.9 × close, minus IV of the ATM call | − | Xing, Zhang & Zhao 2010 (LR13) |

**Not tested here, and why:**
- **Busy-day effect** (+1.0% on dates with ≥ 10 prints): it was *seen* in this very sample on
  2026-09-30. It is registered **for live confirmation only** (Season B), never tested here.
- **Semis' weak reaction:** likewise seen here; described (§4), confirmed only live.
- **The option "crush":** it needs post-print prices, so it is not point in time.

## 2. The test — one per signal, 10 in all

For each signal, events with the signal present:
1. **Score:** the signal's percentile rank within the events of the four calendar quarters **before**
   the event's quarter (the D006 §5.2 method), flipped for a − sign. For a two-sided signal, the
   unflipped rank.
2. **Split:** "high" = score > 0.5.
3. **Primary:** hit-rate lift = WIN rate of the high group − WIN rate of all scored events. Its t: the
   D005 implementation (OLS of WIN on the high indicator, clustered by entry session), one-sided for
   a signed signal and two-sided otherwise.
4. **Secondary**, reported: the return lift, and both halves separately — TRAIN (2023-09-01 →
   2025-08-31) and VALIDATION (2025-09-01 → 2026-09-18).

**A candidate must pass all of:**
- BH q < 0.10 across the 10 tests
- |t| > 3 on the full period
- the same sign in both halves
- at least 300 scored events and 50 entry dates

**Everything else is recorded as negative or insufficient knowledge.** Coverage (the share of events
with the signal present) is reported per signal, per cluster.

## 3. What happens to a survivor

It is written into `D005_confirmatory_seasonB.json` before the Season B screening date. Only then can
it be scored on Season B's live events, out of sample. It never enters T1 rule v0, and it never
enters T2's inputs until confirmed.

## 4. Descriptive only, never tested here

- The semis mechanism: pre-print run-up (H2), the IV run-up (E8) and the peer read-through (E2),
  within semis, against their reaction.
- The busy-day split.

These are pictures that suggest the Season B hypotheses. They are not evidence.

## 5. Pitfalls declared in advance

- **Survivorship** (D006 §8).
- **DoltHub coverage** is partial and its methodology undocumented. A missing value is missing, never
  filled.
- **Wikipedia:** article mapping errors (a wrong or ambiguous article) are counted.
- **FINRA** short volume includes market-maker hedging. It is a noisy proxy for informed shorting.
- **Multiple testing:** 10 tests under BH; the bar is t > 3, not 2.
