# D011 · report views · v1 — the paper report's promised views (descriptive, decides nothing)

> **Frozen 2026-10-16 ET (Fri evening)**, before the first D011 v3 close (Mon 2026-10-19 from 14:30 ET), so before any v3 round
> trip has a result.
> **Why now:** these views were promised on 2026-10-14 (D011 v3 §3; `ops/incidents/2026-10-13_DPZ_exit.md` Part 4,
> "ideas not adopted yet"). The 2026-10-15 session review found none of them built.
> **Disclosed:** written after seeing the first v3 opens of 2026-10-16. Options account: 3 of 3 filled at attempt 0.
> Long account: 2 filled at attempt 0, NOC `open_failed: platform`. Also seen: one dry pass of the real prints, which
> fetched and compared the orders and committed nothing. No P&L of any v3 trade exists yet.
> It changes nothing in D011 v1–v3, in the frozen report (`pipeline/paper_options_report.py`, implementation v3,
> byte-identical, still the D011 report of record), in the exit audit, in the open-fill trigger or in any result.
> **It adds no test.**

## What it adds (`pipeline/paper_options_report_v2.py`)

`python pipeline/paper_options_report_v2.py [SEASON] [--write]` covers both accounts: options (PX-F,
`paper/options_ledger.json`) and long (PX-L, `paper/long_ledger.json`). With `--write` it writes
`outcomes/paper/options_report_v2_<season>_<date>.json` and `.md`.
- The markdown holds the headline tables.
- The JSON holds everything: each-price blocks, gate-status and session splits, every `exit_late` cut, and every
  order's execution and real-print rows.

**Every block appears three times:**
- all trades;
- v3 only (`"exec": "v3"`);
- all trades without DPZ (`seasonA-DPZ-2026-10-13-F`, the v1 trade whose exit failed).

While DPZ is the only v1 trade, "v3 only" and "without DPZ" are the same set. Both are kept so neither cut looks
chosen.

| view | what it shows |
|---|---|
| **1. Fill rate as an outcome** | Read from order records only, never from the result, P&L or a grade. `orders_view()` drops `result` and reduces `close_sim` to a flag. A test changes every result and every fill price and checks that these views and the trigger do not move. **Opens:** filled at attempt 0, filled at attempt 1, `open_failed: platform`, other failures, or pending. **Closes:** for v3, the concession step of the order that completed the fill: 0%, 5% … 25%. The frozen ladder counts the orders sent, so the 25% step covers the 6th order sent and every later one (`sent_before` ≥ 5; the `attempt` shown is the client-id suffix, which differs after a refused record). A step outside the ladder counts as "other". A fill whose step was not recorded is "step unknown". The other outcomes are unfilled by expiry, rejected and pending. v1 closes are counted apart (no ladder). Every trade with a real opening fill lands in exactly one bucket. Each attempt shows its status and minutes live |
| **Open-fill trigger counts** | `registry/D011_open_fill_trigger_v1.md` per account. The population is the first 6 trades with `snapshot_session` ≥ 2026-10-16 that sent an opening order. They are ordered by their first opening send (UTC). One run stamps all its sends with the same time, so ties go by the trade's place in the ledger. That is the order the frozen `sync()` walks and sends in. The trigger note fixed no order, so this one is disclosed here. **If the 6th place falls inside such a tie,** the platform failures over every admissible choice of 6 are shown too (`tie_at_cut`, `platform_failures_range`, counting a pending trade as not failed). When another choice would change FIRED, the state says so. When a tied trade is still pending (`pending_in_tie`), the state says that too. Trades that sent no opening order (`held_by_cap`, `halt`, `never_sent`, skipped) are outside the population and tallied apart. The state reads FIRED once 2 are `open_failed: platform`, "not fired" once all 6 are decided, and open otherwise |
| **2. P&L at three prices** | Next to the actual fill: **mid**, **halfway** (half-way from the mid to the far side, i.e. paying half the half-spread) and **far side** (natural). Per $1 of spot and in dollars. **Headline = the common set**: the trades priced at all four, so the columns compare like with like. `each_price` keeps every trade priced at a given price, with its n and missing count. Covered: real round trips and all trades with a result (simulated legs labelled), each with and without `exit_late`, each with the frozen report's gate-status and session splits. Also covered: the SH-X pairing and the PX-L/PX-F pairing at each price. Rule 7 status on each block |
| **3. Execution** | Each filled order against its own recorded quotes. Fill − mid, fill − natural and fill − limit (+ = worse for us). The **share of the half-spread paid**: 0 = filled at the mid, 1 = at the far side. Each order also shows its minutes from send to fill |
| **4. Real prints** | Each order against Alpaca's historical OPRA bars and trades (below) |

## Pricing definitions

D011 conventions apply: per unit, debit +, credit −, P&L = −(open net + close net).

- **Leg prices.** Mid = (bid + ask) / 2. It needs a bid, a positive ask and ask ≥ bid.
  - The far side is the ask to buy and the bid to sell, which is the frozen `natural()` for every order that was
    sent. Recomputed, it equals the recorded natural on all 36 order records at freeze (tested).
  - Halfway = (mid + far side) / 2.
  - **A missing quote is never priced:** that price is missing for the trade, and the reason is listed. A wing with
    a zero bid and no ask has a far side but no mid, so expect n to be smaller at mid and halfway (`each_price`).
- **The quotes are those recorded when each order was sent.** An order that rested before filling is compared with
  older quotes. DPZ's open filled 32 minutes after its send. The minutes are shown per order.
- **A chain's price** is the quantity-weighted price of its filled records, as `fill_net()` weights the fills.
- **A v3 close's dropped legs** (zero bid, left to expire) are outside the order.
  - They are valued at 0 at every price (v3 §1).
  - Their mid at the close is shown separately.
  - Their value at expiry stays the frozen code's `dropped_at_expiry`.
- **Simulated legs:**
  - An entry simulated for a platform reason is priced from the record `settle()` books: the first opening record
    with a natural.
  - A position held past expiry closes at intrinsic, the same at every price.
  - A close simulated because the entry was simulated recorded only its natural. Its mid and halfway are missing.
- **An adopted order** carries the quotes of the run that adopted it, not of its send. It is counted and flagged.
- **A one-leg v3 close** is a simple order whose `limit_price` is always positive. For a sell, the credit sign is
  restored before comparing.

## Real prints (`pipeline/paper_fill_recheck.py`, `.github/workflows/paper-fill-recheck.yml`)

**Probed 2026-10-16 20:38 ET** on the options account's plan (`ops/probes/alpaca_options_history_2026-10-16.json`,
run 38987238984):

| call | answer |
|---|---|
| historical 1-minute bars, `/v1beta1/options/bars` | **200**, real prints, also for an expired contract (DPZ 2026-10-16) |
| historical trades, `/v1beta1/options/trades` | **200**: price, size, exchange, condition code |
| historical quotes, `/v1beta1/options/quotes` | **404**: no such endpoint. **What the quote was cannot be checked after the fact** |
| daily bars reaching into the current session | **403** "OPRA agreement is not signed", for a 10-day range ending on the current date. Why is not known: the same evening, 1-minute bars around a 14:43 ET fill answered 200. The 2026-10-14 research says free OPRA bars are available once older than 15 minutes. The 12-hour wait below makes the code independent of it |
| latest trade, `feed=opra` | **403**, same message. `feed=indicative`: 200 |
| bars with a `feed` parameter | **400**: the parameter does not exist |

**What is stored.** Per order record that reached Alpaca (it has an order id) and is final, per leg, raw and
write-once in `paper/fill_recheck/<season>/<client_order_id>.json`:
- **filled:** the 1-minute bars from 30 minutes before to 30 minutes after the fill, and the trades from 15 minutes
  before to 15 minutes after;
- **ended unfilled:** the 1-minute bars while it was live. That is from the send to the cancel request + 2 minutes,
  never past that session's 16:00 ET close. With no cancel request, it runs to that close.
- **filled with no fill time recorded:** not fetched; the report says so.

**When:**
- **12-hour wait.** A window is fetched once it ended 12 or more hours ago. The probe saw only data hours old, so a
  same-day answer that may not have settled is never stored.
- **Failed requests.** A failed request writes nothing, so a later run retries. The one exception: a request error about the contract
  or window itself (400, 404, 422) for a window more than 3 days old is stored as that leg's error, so one bad
  contract cannot turn every run red. Auth, plan and rate answers (401, 403, 408, 429) and 5xx are never stored: they
  are about the account or the moment, so the run stays red until a person looks.
- **Empty answers** are stored empty: missing, never filled in.
- **Red runs.** A failed request or a failed push turns the run red.
- **Schedule.** The workflow runs at 16:50 EST / 17:50 EDT and at 07:30 EST / 08:30 EDT. Neither is inside the
  14:27–15:56 ET paper window in either clock. Each run catches up on everything not yet stored, and the morning run
  does most of the work. It can also be run by hand (`fetch`, `probe`, `dry`).
- **Guards.** A committing fetch refuses to run 14:00–16:05 ET on a weekday, which also covers a hand dispatch. The
  Alpaca keys reach only the three data steps. The workflow checks this file's implementation hashes with
  `sha256sum -c` before it fetches.

**Compared:**
- **Filled, per leg:** the nearest real trade (price, time gap, condition, exchange), the fill minute's bar, and the
  bars' low–high. `worse_by` > 0 means the paper fill was worse for us than the print.
  - **Headline:** legs with a trade within 60 seconds of the fill, and the order's net at those prints when every leg
    has one.
  - Prints up to 15 minutes away are shown apart (`max_leg_dt_s`), labelled not simultaneous.
- **Unfilled, per leg:** did any print reach the recorded indicative far side (to buy: a low ≤ the ask; to sell: a
  high ≥ the bid)? **Per order:** the best net the prints allowed against the limit. The legs are taken at their
  best minute, so this is **not simultaneous**: a ceiling on how marketable the limit was, suggestive only.

**Honest limits:**
- These are **trades, not quotes**. Paper fills against quotes no one shows us, so this is a check, not a fill
  model.
- Thin contracts often print nothing near the fill. "Missing" will be common, and it is the honest answer.
- Multi-leg (complex-order) prints can sit outside the single-leg market. Their condition code is recorded and not
  filtered: the code table was not verified.

## Use

- **The frozen report stays the D011 report of record.** These views sit next to it, labelled descriptive, as the
  exit audit does.
- From the first v3 round trip (closes from 2026-10-19), every D011 P&L number in STATE.md or JOURNAL.md is given at
  the fill and at all three prices, and for all trades vs v3 only, with DPZ in and out.
- The open-fill trigger's counts come from view 1, with the trigger's own definitions.
- Nothing here changes a rule. A change to how D011 trades or grades is a new D011 version (rule 5).

## Independent review (Sonnet 5.5, read-only, 2026-10-16 evening ET): SHIP WITH FIXES, all applied

**Verified clean by the reviewer:**
- 3,000 random round trips through the frozen `settle()`, with 0 mismatches: the fill column = the frozen result,
  halfway = (mid + natural) / 2, and mid ≥ halfway ≥ natural.
- A matched PX-F/PX-L round trip equals the frozen `both_sides`, `paired_shx` and `summary` exactly.

**Applied:**
1. **The evening cron was inside the paper window in EST.** It is now 16:50 EST / 17:50 EDT, with a 14:00–16:05 ET
   no-commit guard.
2. **A print at 0.0 s was not counted** as within 60 s.
3. **A v3 fill with no recorded step fell out of every bucket.** There is now a "step unknown" bucket, and a test
   that every real trade lands in one.
4. **Ties at the trigger's cut** now go by the frozen send order (ledger order), not by key. The admissible range is
   shown, no-order trades are tallied, and each attempt's status is listed.
5. Each trigger row shows every attempt's terminal status. An order Alpaca accepted and later rejected would be
   labelled `platform` by the frozen code, and this makes it visible. The frozen code is not changed.
6. **Per-order nets mixed prints up to 15 minutes apart.** The headline now uses prints within 60 s; the rest is
   labelled not simultaneous.
7. **A same-day empty answer could become permanent.** Fetching now waits 12 hours.
8. **A failed push exited 0,** and one refused contract could turn every run red. A failed push now exits red, and
   request errors about the contract (400, 404, 422) are stored after 3 days.
9. **A fill with no fill time** is no longer treated as unfilled.
10. The quotes' staleness is stated, with minutes to fill per order.
11. **The columns used different n.** The headline is now the common set.
12. **The fill-rate test was too weak.** It now changes results and fill prices through `build()`.

**Second pass (the same reviewer, on the fixes): SHIP WITH FIXES, all applied.**
- The 4,000-ledger brute force of the tie range matched exactly.
- Fixed: a 403 (an account problem) could have been stored as a permanent refusal; now only 400/404/422 are.
- Fixed: a pending trade tied at the cut is now named in the state.
- Fixed: the probe is behind the same quiet guard.
- Fixed: an empty set prints "-" for dollars, and a step outside the ladder counts as "other".
- The probe row's 15-minute reading is reworded to what was observed.
- The change procedure is written down below.

**Also applied:**
- attempt numbering (the client id suffix, plus the frozen `k`);
- "pending" wording;
- splits on both samples;
- pairings in the markdown;
- the Alpaca keys moved onto the data steps;
- a test that no workflow has a `pull_request` trigger;
- this spec's corrections (the cron times, the 25% step's attempts, the unfilled window's fallback, and an unsourced
  count of legs dropped).

## Files (hashes in `registry/D011_report_views_implementation_v1.sha256`)

- `pipeline/paper_options_report_v2.py`
- `pipeline/paper_fill_recheck.py`
- `.github/workflows/paper-fill-recheck.yml`
- `tests/test_paper_options_report_v2.py`
- `tests/test_paper_fill_recheck.py`
- `tests/fixtures/paper_ledgers_2026-10-16.json`: both real ledgers as committed at `c3eb852`
- this file

A test fails if any listed file drifts from its hash, and the workflow refuses to fetch. A change is a new list (v2),
never an edited line. **The procedure, in one commit:** write
`D011_report_views_implementation_v2.sha256`, point the workflow's hash step and the registration test at it, and add
it to `FROZEN.sha256`. Until then the workflow refuses to fetch. That is safe, because fetching is descriptive and
catches up. Another test checks that the frozen report and its test still match
`D011_implementation_v3.sha256`.
