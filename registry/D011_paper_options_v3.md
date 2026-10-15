# D011 · v3 — how the closing order is placed (paper options, both accounts)

> **Frozen 2026-10-14 ET, before the first Season A gate (Fri 2026-10-16).** Reviewed before freezing by an Opus 5.5
> agent: FREEZE WITH FIXES, all applied (§4). v1's DPZ trade is the only paper
> options trade that exists.
> **D011 v1 and v2 are not edited** (rule 5). v1's rules keep governing every trade whose snapshot session is
> before 2026-10-15: today, DPZ only.
> v3 governs every PX-F and PX-L trade whose **snapshot session is on or after 2026-10-15**. `open_event`
> stamps those trades `"exec": "v3"`. It changes **only how the closing order is priced and resent**: no event,
> size, entry, exit window, label or grading rule changes.

## 0. Why (ops/incidents/2026-10-13_DPZ_exit.md)

- **What happened:** DPZ's close, a 4-leg limit at v1's natural, did not fill on Oct 13 (14:46 ET) or on
  Oct 14 (10:45 ET). The position stayed open into a further 4% fall. That moved the trade from about +$32
  (the on-time natural) to about −$770.
- **The research (2026-10-14, sources in the incident file):**
  1. **The price feed.** Our quotes come from Alpaca's free "indicative" options feed, which Alpaca staff
     describe as real-time OPRA "randomized a bit" and not meant for strategy testing. Paper fills are
     judged against real quotes, so a limit at the indicative natural can sit inside the real market and
     never fill. Alpaca has a documented case of exactly that (GOOG, Jan 2026).
  2. **Zero-bid wings.** Both closes asked to sell two zero-bid wings at 0.00. Whether that blocks a
     multi-leg paper fill is not documented. An active open-source Alpaca earnings bot reports paper
     spreads not filling below the ask, and closes only legs that have a bid.
  3. **Scheduling** is fixed separately and with no rule change (`paper-window.yml`, every 2 minutes).
- **The real-time OPRA feed costs money**, so this rule has to work with the indicative feed (no new money
  before results).

## 1. The v3 close (everything else is v1)

| item | v1 | **v3** |
|---|---|---|
| legs of the close | every leg reversed | every leg reversed, **except a leg we would SELL to close (a long leg) whose quote is present with bid = 0 and an ask.** That leg is left to expire and valued at **0**; its bid and ask are recorded (`dropped_legs`). **A missing quote is never read as worthless:** v1's rule applies, and nothing is sent this run. If every leg would be dropped (only bad data can do that), the full close is sent |
| order type | one `mleg` limit order | `mleg` while 2 or more legs remain. **One leg left** (a long straddle with a worthless leg): a simple limit order on that leg, at the positive price |
| limit price | the natural (the far side of every leg) | **the natural plus a concession that grows with each attempt:** limit = natural + c_k × \|natural\|, with c_k = **0%**, 5%, 10%, 15%, 20%, 25% for k = 0 … 5 and later. Debit positive, so a debit pays more and a credit receives less. Rounded to the cent on the marketable side. **c never exceeds 25%.** Attempt 0 is the natural itself, so the first try separates "a zero-bid wing blocked the fill" from "the indicative price was not marketable" |
| attempt count k | — | the close records that have an Alpaca order id: sent and adopted orders count, refused ones do not |
| cancel a live close after | 15 minutes | **2 minutes**. The resend still happens on a LATER run, never in the same run, so a cancel that loses the race with a fill cannot double the position. With the 2-minute window runner that is about 5 minutes per attempt, so the full walk takes about 30 minutes |
| last close sent | 15:55 ET | 15:55 ET, and **15:10 ET on the expiry date**. A live close is left to fill until Alpaca's 15:15 cut-off |
| recorded per attempt | quotes, natural, limit | the same, plus `concession`, `dropped_legs`, `all_sides`, `order_class` (simple or mleg), each leg quote's age in seconds |
| after expiry | — | each dropped leg's intrinsic value on the expiry close is recorded (`dropped_at_expiry`), and is **never added to the result**. **Above 0 is an alert** (`dropped_itm`): Alpaca exercises an in-the-money long option into shares |

**Unchanged from v1:** the primary exit (first close sent 14:30–15:00 ET on the reaction session), `exit_late`,
`held_past_expiry`, `close_rejected`, the platform simulation, every opening order, and sizing.

## 2. What it measures, and the honest limits

- **The execution number stays** "fill − the indicative natural when sent". Under v3 it also contains any
  concession needed.
- **The concession is a ceiling, not a cost.** The only paper options fill so far (DPZ's opening order)
  came 4 cents BETTER than its limit, which suggests Alpaca fills a marketable limit at the real quote.
  Every fill's price is compared with its limit, so the data show which is true.
- **A ceiling that scales with premium:** 25% of the natural is about 2% of spot on an at-the-money
  straddle, and on DPZ it would have been 6.3 per unit, against an edge of about 3. The cap prevents an
  absurd fill. It does not keep a fill cheap.
- **Paper is still paper:** no queue, no size check, about 10% random partial fills, no fees
  (docs.alpaca.markets/docs/paper-trading).
- **Dropped wings valued at 0** understate the P&L when a wing ends in the money. That value is recorded
  separately and raises an alert.
- **Simulated closes pay no concession.** A close simulated because the opening order failed on the
  platform (v1 rule, unchanged) is booked at the natural with no concession. v3's real and simulated closes
  are therefore not comparable. Simulated trades are already labelled and kept out of the real sample.

## 3. Pooling and reporting

- **Season A PX-F and PX-L are v3 from the first gate.** DPZ (v1, an INELIGIBLE gate, before the season) is
  the only v1 trade.
- **Every D011 number is shown twice:** all trades including DPZ, and v3 only. Leaving out the one loser
  alone would look selective.
- The frozen report (implementation v3) pools by structure. The v3-only and all-trades splits are computed
  by filtering the ledgers on `exec`.
- The exit audit (`registry/D011_exit_audit_v1.md`) lists every trade's on-time counterfactual. Its rows do
  not carry `exec`, so a v3-only split joins them back to the ledger by `key`.

## 4. Pre-freeze review (Opus 5.5, 2026-10-14): FREEZE WITH FIXES, all applied

1. A missing quote was read as a worthless leg, and could book a long straddle as lost while it was still
   open. **Fixed:** a leg is dropped only when its quote is present with bid 0 and an ask. A missing quote
   means nothing is sent this run.
2. A long straddle with one worthless leg would have sent a one-leg `mleg`, which Alpaca does not document.
   **Fixed:** a simple order.
3. Adopted orders could lose leg sides when the legs changed between runs. **Fixed:** `all_sides` is
   recorded and used.
4. Dropped wings had no record at expiry and no alarm. **Fixed:** `dropped_at_expiry`, with `dropped_itm`
   as an alert.
5. **Cadence:** 2-minute cancel, 2-minute runner, and c₀ = 0 so the first attempt is diagnostic.
6. **Runner:** exits non-zero when a sync fails; a 13:55 EDT start, before the frozen crons.
7. **Health:** partial closes, the v3 expiry-day 15:10 send, and `close_sim` are handled.
8. **Disclosed side effect on OPENING orders (no v3 change):** the reliable 2-minute runner means v1's
   15-minute cancel of an unfilled opening order now always happens. That rule was already in force but had
   effectively been skipped. DPZ's open took 32 minutes to fill. Expect more opens to cancel, resend once,
   and if still unfilled be simulated as `platform` (labelled, outside the execution sample). **The opening
   fill rate is watched in the first Season A week.** A change to opens would be a new version.
9. **The v1 implementation hash no longer matches the live file.** `D011_implementation_v1.sha256` names
   the v1 file as it stood at commit `f84849d` (2026-10-09). The live `pipeline/paper_options.py` is
   implementation v4 (`registry/D011_implementation_v4.sha256`), and runs v1's code paths for trades
   without `exec`.
