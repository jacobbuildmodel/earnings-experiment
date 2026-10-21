# D016 gate audit - seasonA - interim_2026-10-21

Run 2026-10-21T13:30 ET by `pipeline/gate_audit.py` under `registry/D016_gate_audit_v1.md`. Counts only: it read `gate.json` and `option_chain.json` and nothing else. No outcome, P&L, grade or shadow figure is here.

- Events with a chain reading: **15**. Failed before the chain: 0. Not live (dry or outside the window), skipped: 0.
- Reproduction of the stored gate: 15 of 15.

## A. Every check on every event (D003 v4)

| check | events failing | the only failing check |
|---|---|---|
| `no_quote` | 0 | 0 |
| `low_implied_move` | 0 | 0 |
| `wide_spread` | 9 | 6 |
| `thin_oi` | 4 | 1 |

| combination | events |
|---|---|
| wide_spread | 6 |
| PASS | 5 |
| wide_spread + thin_oi | 3 |
| thin_oi | 1 |

## B. Pass rate by share price

| bucket | events | PASS | rate | `no_quote` | `low_implied_move` | `wide_spread` | `thin_oi` |
|---|---|---|---|---|---|---|---|
| $100-<$300 | 6 | 4 | 66.7% | 0 | 0 | 2 | 1 |
| >= $300 | 5 | 1 | 20.0% | 0 | 0 | 4 | 1 |
| < $100 | 4 | 0 | 0.0% | 0 | 0 | 3 | 2 |

## B. Pass rate by expiry gap after the reaction day

| bucket | events | PASS | rate | `no_quote` | `low_implied_move` | `wide_spread` | `thin_oi` |
|---|---|---|---|---|---|---|---|
| <= 5 sessions | 9 | 5 | 55.6% | 0 | 0 | 4 | 1 |
| > 5 sessions (monthly) | 6 | 0 | 0.0% | 0 | 0 | 5 | 3 |

## C. Alternatives the stored chains support

| id | rule | PASS | adds | drops | median straddle spread | max straddle spread | max leg spread |
|---|---|---|---|---|---|---|---|
| A0 | D003 v4 as run | 5 of 15 | - | - | 4.7% | 9.6% | 9.8% |
| A1 | better of the two nearest strikes | 6 of 15 | TTMI | - | 5.0% | 9.6% | 9.8% |
| A2 | dollar floor $0.10 a leg | 5 of 15 | - | - | 4.7% | 9.6% | 9.8% |
| A3 | straddle spread <= 10% | 7 of 15 | RTX, TTMI | - | 5.7% | 9.6% | 12.8% |
| A4 | A1 + A3 | 7 of 15 | RTX, TTMI | - | 5.2% | 9.6% | 12.8% |

Sensitivity (raises the friction ceiling; never recommended by §5):

| cap | PASS | adds | median straddle spread | max leg spread |
|---|---|---|---|---|
| leg 0.125 | 6 of 15 | TTMI | 5.2% | 11.3% |
| leg 0.15 | 7 of 15 | RTX, TTMI | 5.7% | 12.8% |
| leg 0.2 | 8 of 15 | RTX, TSCO, TTMI | 7.1% | 18.2% |
| straddle 0.125 | 7 of 15 | RTX, TTMI | 5.7% | 12.8% |
| straddle 0.15 | 7 of 15 | RTX, TTMI | 5.7% | 12.8% |

## D. The §5 decision rule

**D003 v5 = A4 from the Season B screen (Jacob's call).** A4 has the most PASS (7 vs A0 5); ties by median straddle spread, then A2, A1, A3, A4 (D016 §5.3).

Gains over A0: A1 +1, A2 +0, A3 +2, A4 +2.

_Interim: this decides nothing. The decision run is the first at or after Fri 2026-10-23 16:00 ET._

## Events

| event | spot | expiry gap | stored | all failing checks | straddle spread | A1 | A2 | A3 | A4 |
|---|---|---|---|---|---|---|---|---|---|
| ABT 2026-10-21 | 104.36 | 2 | PASS | PASS | 9.6% | PASS | PASS | PASS | PASS |
| DPZ 2026-10-13 | 307.39 | 3 | wide_spread | wide_spread, thin_oi | 16.3% | - | - | - | - |
| HXL 2026-10-21 | 92.20 | 21 | wide_spread | wide_spread, thin_oi | 39.1% | - | - | - | - |
| LMT 2026-10-22 | 550.26 | 1 | wide_spread | wide_spread | 23.0% | - | - | - | - |
| LRCX 2026-10-21 | 265.30 | 1 | PASS | PASS | 4.7% | PASS | PASS | PASS | PASS |
| META 2026-10-21 | 690.00 | 1 | PASS | PASS | 1.7% | PASS | PASS | PASS | PASS |
| NOC 2026-10-20 | 514.28 | 23 | wide_spread | wide_spread | 16.3% | - | - | - | - |
| PEGA 2026-10-20 | 35.18 | 22 | thin_oi | thin_oi | 8.8% | - | - | - | - |
| ROP 2026-10-22 | 395.17 | 21 | wide_spread | wide_spread | 19.3% | - | - | - | - |
| RTX 2026-10-20 | 192.27 | 3 | wide_spread | wide_spread | 8.5% | - | - | PASS | PASS |
| SPCX 2026-10-20 | 147.24 | 0 | PASS | PASS | 2.3% | PASS | PASS | PASS | PASS |
| TSCO 2026-10-22 | 32.97 | 1 | wide_spread | wide_spread | 16.8% | - | - | - | - |
| TTMI 2026-10-22 | 95.84 | 21 | wide_spread | wide_spread | 8.9% | PASS | - | PASS | PASS |
| TXN 2026-10-21 | 280.08 | 1 | PASS | PASS | 5.7% | PASS | PASS | PASS | PASS |
| VICR 2026-10-20 | 195.98 | 23 | wide_spread | wide_spread, thin_oi | 13.8% | - | - | - | - |
