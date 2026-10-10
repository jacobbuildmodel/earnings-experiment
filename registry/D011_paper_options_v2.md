# D011 · Paper options · v2 — FROZEN 2026-10-10 (ET) · adds the LONG straddle on a second paper account

> **What v2 is:** v1 plus one new track, **PX-L**, the long earnings straddle, traded on a second Alpaca paper
> account.
> **v1 is unchanged and keeps running.** The short iron butterfly (PX-F) still runs under
> `D011_paper_options_v1.md`; neither its code (`pipeline/paper_options.py`, `paper-options.yml`) nor its
> hashes are edited. v1 §10 named this exact change ("the long straddle in a second account") as a v2.
> Jacob approved the second account on 2026-10-10 ("yes").
> Implementation: `pipeline/paper_long.py`, `.github/workflows/paper-long.yml`, `tests/test_paper_long.py`,
> hashed in `D011_implementation_v2.sha256`. It runs v1's frozen code, so v1's hashes cover the logic.
> **Descriptive execution track.** It adds no hypothesis to any test family.

## 1. Why

The literature disagrees on which side of the earnings straddle wins. Pre-announcement straddle buyers
earned +3.34% (Gao, Xing & Zhang 2018). Retail buyers lose (de Silva, Smith & So 2025).

D009 SH-X and D011 v1 measure the short side. PX-L measures the long side on **the same events**, with real
order mechanics. Each PX-L / PX-F pair shows what each side paid in spreads and earned from the print.

## 2. Exactly what differs from v1

Everything in v1 §3–§8 applies to PX-L word for word, except:

| | v1 PX-F | v2 PX-L |
|---|---|---|
| structure | sell the ATM call + put, buy wings at ±2M | **buy the ATM call + put** (v1 `legs_for` structure `L`) |
| opening limit | a credit, sent negative | a debit, sent positive (Alpaca's documented convention; v1's sign guard applies on this account too) |
| account | `APCA_API_KEY_ID` / `APCA_API_SECRET_KEY` | **`APCA_L_API_KEY_ID` / `APCA_L_API_SECRET_KEY`**, a second paper account |
| ledger | `paper/options_ledger.json` | `paper/long_ledger.json` |
| first events | gates from 2026-10-09 | **gates whose snapshot session is on or after 2026-10-12** |
| held past expiry | settled at the butterfly's intrinsic value | settled at **\|S − K\|** on the expiry close (the straddle's value) |

**Same as v1:**
- events (every live-season gate SH-X takes, any gate status)
- size n
- entry: the snapshot session, before 15:55 ET
- the one primary exit: the reaction session, first close sent 14:30–15:00 ET, `exit_late` after
- order mechanics, retries and id adoption
- failure labels and simulation
- the reported quantities, and the "insufficient" rule

**PX-L skips an event exactly when PX-F does.** That includes `no_wing_strike`, although PX-L has no wings,
so the two tracks are paired event by event.

Without the two secrets `paper_long.py` does nothing (it prints "not configured"). The track starts on the
first eligible gate after the keys exist.

## 3. What is reported (in addition to v1 §8)

- **Per event, PX-L + PX-F:** the two P&Ls side by side. Their sum is roughly minus the round-trip spread
  cost of the shared body plus the wings' P&L. That isolates what the market charged.
- PX-L's mean `pnl_on_spot`, on real-fill round trips, with the same splits as v1.

Under 30 round trips **or** 10 entry dates the verdict is "insufficient".

## 4. What changes this rule

Nothing in v2 is ever edited. A further change is a v3 with its own start date.
