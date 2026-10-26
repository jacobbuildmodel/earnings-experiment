# D016 gate audit - seasonA - decision

Run 2026-10-26T08:50 ET by `pipeline/gate_audit.py` under `registry/D016_gate_audit_v1.md`. Counts only: it read `gate.json` and `option_chain.json` and nothing else. No outcome, P&L, grade or shadow figure is here.

- Events with a chain reading: **31**. Failed before the chain: 0. Not live (dry or outside the window), skipped: 0.
- Reproduction of the stored gate: 31 of 31.

## A. Every check on every event (D003 v4)

| check | events failing | the only failing check |
|---|---|---|
| `no_quote` | 0 | 0 |
| `low_implied_move` | 0 | 0 |
| `wide_spread` | 22 | 11 |
| `thin_oi` | 12 | 1 |

| combination | events |
|---|---|
| wide_spread + thin_oi | 11 |
| wide_spread | 11 |
| PASS | 8 |
| thin_oi | 1 |

## B. Pass rate by share price

| bucket | events | PASS | rate | `no_quote` | `low_implied_move` | `wide_spread` | `thin_oi` |
|---|---|---|---|---|---|---|---|
| $100-<$300 | 10 | 4 | 40.0% | 0 | 0 | 6 | 4 |
| < $100 | 13 | 2 | 15.4% | 0 | 0 | 10 | 6 |
| >= $300 | 8 | 2 | 25.0% | 0 | 0 | 6 | 2 |

## B. Pass rate by expiry gap after the reaction day

| bucket | events | PASS | rate | `no_quote` | `low_implied_move` | `wide_spread` | `thin_oi` |
|---|---|---|---|---|---|---|---|
| <= 5 sessions | 16 | 7 | 43.8% | 0 | 0 | 9 | 4 |
| > 5 sessions (monthly) | 15 | 1 | 6.7% | 0 | 0 | 13 | 8 |

## C. Alternatives the stored chains support

| id | rule | PASS | adds | drops | median straddle spread | max straddle spread | max leg spread |
|---|---|---|---|---|---|---|---|
| A0 | D003 v4 as run | 8 of 31 | - | - | 5.2% | 9.6% | 9.8% |
| A1 | better of the two nearest strikes | 9 of 31 | TTMI | - | 5.2% | 9.6% | 9.8% |
| A2 | dollar floor $0.10 a leg | 8 of 31 | - | - | 5.2% | 9.6% | 9.8% |
| A3 | straddle spread <= 10% | 10 of 31 | RTX, TTMI | - | 6.1% | 9.6% | 12.8% |
| A4 | A1 + A3 | 10 of 31 | RTX, TTMI | - | 5.4% | 9.6% | 12.8% |

Sensitivity (raises the friction ceiling; never recommended by §5):

| cap | PASS | adds | median straddle spread | max leg spread |
|---|---|---|---|---|
| leg 0.125 | 9 of 31 | TTMI | 5.7% | 11.3% |
| leg 0.15 | 12 of 31 | APPF, DECK, RTX, TTMI | 7.4% | 14.4% |
| leg 0.2 | 14 of 31 | APPF, DECK, RTX, TSCO, TTMI, VRSN | 8.4% | 18.2% |
| straddle 0.125 | 12 of 31 | APPF, DECK, RTX, TTMI | 7.4% | 14.4% |
| straddle 0.15 | 13 of 31 | APPF, DECK, RTX, TTMI, VRSN | 8.3% | 16.3% |

## D. The §5 decision rule

**D003 v5 = A4 from the Season B screen (Jacob's call).** A4 has the most PASS (10 vs A0 8); ties by median straddle spread, then A2, A1, A3, A4 (D016 §5.3).

Gains over A0: A1 +1, A2 +0, A3 +2, A4 +2.

## Events

| event | spot | expiry gap | stored | all failing checks | straddle spread | A1 | A2 | A3 | A4 |
|---|---|---|---|---|---|---|---|---|---|
| ABT 2026-10-21 | 104.36 | 2 | PASS | PASS | 9.6% | PASS | PASS | PASS | PASS |
| AGYS 2026-10-26 | 121.88 | 18 | wide_spread | wide_spread, thin_oi | 27.2% | - | - | - | - |
| AMKR 2026-10-26 | 39.50 | 3 | wide_spread | wide_spread, thin_oi | 10.5% | - | - | - | - |
| APPF 2026-10-22 | 223.15 | 20 | wide_spread | wide_spread | 11.3% | - | - | - | - |
| CDNS 2026-10-26 | 316.55 | 3 | wide_spread | wide_spread, thin_oi | 13.3% | - | - | - | - |
| CLS 2026-10-26 | 260.98 | 3 | wide_spread | wide_spread, thin_oi | 10.8% | - | - | - | - |
| CVLT 2026-10-27 | 171.10 | 18 | wide_spread | wide_spread, thin_oi | 17.9% | - | - | - | - |
| DECK 2026-10-22 | 85.62 | 0 | wide_spread | wide_spread | 11.6% | - | - | - | - |
| DPZ 2026-10-13 | 307.39 | 3 | wide_spread | wide_spread, thin_oi | 16.3% | - | - | - | - |
| EEFT 2026-10-27 | 65.62 | 18 | wide_spread | wide_spread | 33.5% | - | - | - | - |
| GLXY 2026-10-27 | 14.72 | 3 | PASS | PASS | 6.5% | PASS | PASS | PASS | PASS |
| HXL 2026-10-21 | 92.20 | 21 | wide_spread | wide_spread, thin_oi | 39.1% | - | - | - | - |
| KN 2026-10-22 | 34.93 | 20 | wide_spread | wide_spread, thin_oi | 58.9% | - | - | - | - |
| LMT 2026-10-22 | 550.26 | 1 | wide_spread | wide_spread | 23.0% | - | - | - | - |
| LRCX 2026-10-21 | 265.30 | 1 | PASS | PASS | 4.7% | PASS | PASS | PASS | PASS |
| META 2026-10-21 | 690.00 | 1 | PASS | PASS | 1.7% | PASS | PASS | PASS | PASS |
| MXL 2026-10-22 | 75.99 | 20 | PASS | PASS | 3.6% | PASS | PASS | PASS | PASS |
| NOC 2026-10-20 | 514.28 | 23 | wide_spread | wide_spread | 16.3% | - | - | - | - |
| PEGA 2026-10-20 | 35.18 | 22 | thin_oi | thin_oi | 8.8% | - | - | - | - |
| RMBS 2026-10-26 | 87.00 | 18 | wide_spread | wide_spread, thin_oi | 12.9% | - | - | - | - |
| RNG 2026-10-22 | 83.30 | 0 | wide_spread | wide_spread | 23.4% | - | - | - | - |
| ROP 2026-10-22 | 395.17 | 21 | wide_spread | wide_spread | 19.3% | - | - | - | - |
| RTX 2026-10-20 | 192.27 | 3 | wide_spread | wide_spread | 8.5% | - | - | PASS | PASS |
| SPCX 2026-10-20 | 147.24 | 0 | PASS | PASS | 2.3% | PASS | PASS | PASS | PASS |
| SSNC 2026-10-22 | 87.15 | 20 | wide_spread | wide_spread, thin_oi | 42.9% | - | - | - | - |
| TSCO 2026-10-22 | 32.97 | 1 | wide_spread | wide_spread | 16.8% | - | - | - | - |
| TTMI 2026-10-22 | 95.84 | 21 | wide_spread | wide_spread | 8.9% | PASS | - | PASS | PASS |
| TXN 2026-10-21 | 280.08 | 1 | PASS | PASS | 5.7% | PASS | PASS | PASS | PASS |
| VICR 2026-10-20 | 195.98 | 23 | wide_spread | wide_spread, thin_oi | 13.8% | - | - | - | - |
| VRSN 2026-10-22 | 307.55 | 20 | wide_spread | wide_spread | 14.2% | - | - | - | - |
| WDC 2026-10-22 | 379.06 | 0 | PASS | PASS | 8.4% | PASS | PASS | PASS | PASS |
