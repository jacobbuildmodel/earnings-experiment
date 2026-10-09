# D011 · Paper options · v1 — FROZEN 2026-10-09 (ET) · the short earnings straddle with real order mechanics

> **Frozen before the first options order and before the first Season A gate** (gates run from 14:30 ET
> 2026-10-09).
> Implementation: `pipeline/paper_options.py`, `.github/workflows/paper-options.yml` and
> `tests/test_paper_options.py` (20 offline tests), hashed in `D011_implementation_v1.sha256`.
> **This is a DESCRIPTIVE execution track.** It adds no hypothesis to any test family; D009's Holm family
> (H-M, H-X, H-VOL) and every other family are unchanged.
> Asked for by Jacob 2026-10-08 ("add paper straddles now"). Reviewed before the freeze by an independent model
> (Sonnet, read-only): first DO NOT FREEZE with 3 blockers; on re-review FREEZE WITH FIXES. Those fixes are
> applied.

## 1. Why

D009 SH-X assumes the straddle is sold **at the gate's bids** and held to expiry. Nothing has tested that
against a real order yet. D011 sends a real paper order shortly after each gate and records three things:
1. **Execution:** the fill against the natural price that Alpaca quoted when the order was sent.
2. **Tradeable P&L:** the P&L of a form Jacob could actually trade.
3. **Capacity:** whether the account can carry a peak day (~50 prints a day around Nov 3–5).

## 2. What the account allows (probed 2026-10-08, closed market, every order cancelled)

- Options level 3, with options buying power of about $98k.
- **A naked short straddle is refused:** "account not eligible to trade uncovered option contracts".
- Multi-leg (`mleg`) limit orders are accepted while the market is closed. Options **market** orders are
  refused outside hours.
- A sell on contracts that have an opposite open order is refused as a "potential wash trade".
- The free `indicative` feed returns bid and ask.
- **The sign of an `mleg` limit is not confirmed:** both signs were accepted for the same credit structure.
  The code uses Alpaca's documented convention, debit positive and credit negative, and guards it (§5).

So SH-X's exact trade cannot be placed. **The traded form is the short iron butterfly (PX-F):** SH-X's naked
short straddle plus two bought wings.

The **long straddle is not traded.** It uses the same contracts on the opposite side, which one account nets
and Alpaca refuses. It would need a second paper account, a question for Jacob and not a blocker.

## 3. Events

- **Eligible:** every `gate.json` of a live season (the pilot is excluded), **of any gate status**, that SH-X
  takes:
  - spot, expiry and strike are recorded
  - both ATM legs have a bid
  - it is not a dry run
  - D011 also needs both asks
- **When:** the gate's snapshot session is today, the market is open, and the time is before **15:55 ET**.
- **Committed first:** `git log` shows the gate committed in the Actions checkout of `main` before the trade
  record is made.
- **Every eligible-or-not gate gets a record with its reason.** The reasons:

| reason | meaning |
|---|---|
| `not_in_shx` | SH-X does not take the gate |
| `not_eligible_vs_shx (no ask)` | SH-X takes it, D011 cannot |
| `dry_gate` | the gate was a dry run |
| `expiry_before_reaction` | the option expires before the reaction session |
| `contract_not_listed_at_alpaca` | Alpaca does not list the contract |
| `no_wing_strike` | no listed strike sits far enough out for a wing |
| `missed_entry_window` | the gate was first seen at or after 15:55 ET, or on a later day, and Alpaca has no order with its id |
| `orphan_order` | as above, but Alpaca HAS an order with its id (a lost ledger): an alert |
| `never_sent` | no order was ever sent: quotes were never readable before the cutoff |
| `held_by_cap` | blocked by the sign-guard cap (§5): an alert |
| `halt` | blocked by a halt (§5): an alert |

- **Contracts:** only standard 100-share contracts. A strike that lists two contracts of one type (an
  adjusted series) is dropped.

## 4. The structure and its size

- **Body:** sell the gate's ATM call and put, at its strike and expiry.
- **Wings:**
  - M = the gate's straddle mid = (call bid + call ask + put bid + put ask) / 2
  - buy the call at the **lowest listed strike ≥ K + 2M**
  - buy the put at the **highest listed strike ≤ K − 2M**
- **Size:** n = max(1, floor(equity × 0.5% / (100 × M))).
  - n is 1 when M > $2.50 at $100k equity, and larger for cheap straddles (M = $1.10 gives n = 4).
  - The primary metric is per $1 of spot, so the size does not enter it.

## 5. Orders

- **One `mleg` DAY limit order** at the natural price: the far side of every leg, from Alpaca's quotes at
  that moment.
  - The limit is rounded to the cent on the marketable side.
  - Debits are sent as positive limits, credits as negative ones.
- **Fills are read leg by leg.** The side of each leg is the side we SENT, never the one in the response.
  - A leg whose filled quantity differs from its order's makes the net unknown.
  - The recorded net never depends on the sign convention.
- **Alpaca is the source of truth:**
  - Before any order is sent, its `client_order_id` is looked up, and an existing order is **adopted, never
    resent**.
  - A duplicate-id refusal is adopted the same way.
  - The ledger is written after every send.
  - The ids are `<season>-<TICKER>-<date>-F-open[-r1]` and `-close[-rk]`.
- **Retries:**
  - An order still live 15 minutes after it was sent is cancelled. The resend happens on a **later** run,
    and only once Alpaca reports the cancel as final, so a cancel that loses the race with a fill can never
    double the position.
  - The opening order is sent **at most twice**. The closing order is resent until it fills or the
    expiry passes.
  - **No order of any kind is sent at or after 15:55 ET.**
- **Transient errors are never decisions:**
  - A network, 429 or 5xx error, or quotes that cannot be read, consumes no id and decides nothing; the next
    run tries again.
  - An opening order whose quotes are never readable before the cutoff is `never_sent`, with no trade.
- **Sign guard:** until one real (not adopted) opening fill passes the check below, at most **3 trades** get an
  opening order. Their own retries are allowed. Every other gate that day is `held_by_cap`, an alert.
  - The check fails if the fill's net has a different sign from the natural, or
    |fill − natural| > max(25% × |natural|, $0.30).
  - A failure sets `halt`, which **stops all new opens** until a person clears it. Exits continue, and the
    run turns red.
  - The first passing fill is recorded as `convention_verified`.
  - A fill that cannot be read leg by leg is `fill_unreadable`, an alert.
- **Closing refusals:** a refused close is an alert. After 3 refused closes it is no longer resent
  (`close_rejected`).

## 6. Entry and exit — ONE primary exit, fixed now (rule 2)

- **Entry:** the snapshot session, at the first run after the gate is committed.
- **Runs:**
  - every 10 minutes through 14:00–16:50 EDT (13:00–15:50 EST)
  - after every S2-window run (the `claude/s2-trigger` routine starts those)
  - at 10:40 and 11:40 EDT
  - The run turns red on any alert, an unexpected error, a halt, or a failed push of the ledger.
- **Primary exit:** the reaction session, **with the first closing order sent between 14:30 and 15:00 ET**,
  as a buy-to-close at the natural with the same order mechanics.
  - `exit_first_sent_et` is recorded.
  - A first close sent at or after 15:00 ET, or on a later day, is **`exit_late`** and is reported both with
    and without these trades.
- **Never closed by expiry:** flagged `held_past_expiry` (Alpaca's exercise and assignment then apply). The
  open contracts are settled at the butterfly's intrinsic value on the expiry close, as SH-X settles, and
  labelled simulated.
- **No secondary exit.**
- **If `check.py` fails:** the run still refreshes and closes (`--exits-only`) but opens nothing.

## 7. Failed orders

| what happened | label | simulated? |
|---|---|---|
| opening order expired or cancelled unfilled after its attempts | `platform` | yes, at the natural recorded when it was first sent (Jacob, 2026-10-02) |
| refused for buying power | `capacity` | **no**: the account's real capacity |
| any other refusal (4xx: a wrong leg, a wash-trade or level refusal, a code bug) | `rejected_code` | **no**: an alert, and the run turns red |

- **With no real position**, the exit is simulated at the natural quoted at the first due exit run (its time is
  recorded, which may be after 14:30).
- **Simulated legs never enter the execution comparison** (§8.1).
- A partly filled opening order is flagged `partial_open`, and only the filled quantity is closed and scored.

## 8. What is reported (descriptive; rule 7 applies)

1. **Execution gap**, on real opening fills only:
   - `entry_vs_alpaca_natural` = fill net − natural, per unit. It is **negative when the fill beat the
     natural**.
   - `entry_credit_vs_gate_bid_sum` = the butterfly's net credit (wings included) − the gate's call bid + put
     bid (the SH-X assumption). It mixes the wing cost with execution, so it is NOT a pure execution gap.
   - Adopted orders (a lost ledger) are left out: their natural was read later than the send.
   - The gate's quotes come from yfinance and Alpaca's from another feed.
2. **P&L:** `pnl_on_spot` = (credit received − debit paid) / spot per unit, plus dollars.
   - On real-fill round trips, then on all trades with simulated legs labelled.
   - Split by gate status (PASS vs the rest) and by session (BMO/AMC).
3. **Paired with SH-X:** the same events' SH-X P&L. The difference is the wings + the earlier exit + real
   execution.
4. **Capacity:** `capacity` refusals by date.

Under 30 round trips **or** 10 entry dates the verdict is "insufficient", never "works" or "no effect".

The report code (`paper_options.py report`) is written and registered as implementation v2 **before the 10th
round trip**. It computes §8 only and may not change §3–§7.

## 9. Disclosed differences from SH-X and D010

| | SH-X (D009) | D010 (history) | **D011 (paper)** |
|---|---|---|---|
| structure | naked short straddle | straddle, both sides | short iron butterfly (wings at ±2M) |
| entry | gate quotes, bid | P close, bid | real order minutes after the gate, natural |
| exit | held to expiry, intrinsic at the close | R close, ask | R from 14:30 ET, natural |
| quotes | yfinance | DoltHub end of day | Alpaca indicative |

- **Expected, not yet shown:**
  - the wings cost a little in a quiet print and save a lot in a large one
  - closing on R gives up SH-X's theta after R and avoids assignment
- **Paper fills are simulated by Alpaca.** A paper fill at the natural does not prove a real order would
  fill there, and Gate 3 (real money) still has to show it.

## 10. What changes this rule

Nothing in v1 is ever edited. A change (wing width, exit time, the cap, the long straddle in a second account)
is a **D011 v2** with its own start date. v1's trades keep being reported untouched.
