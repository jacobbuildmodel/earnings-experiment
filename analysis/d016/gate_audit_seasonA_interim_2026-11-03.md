# D016 gate audit - seasonA - interim_2026-11-03

Run 2026-11-03T11:02 ET by `pipeline/gate_audit.py` under `registry/D016_gate_audit_v1.md`. Counts only: it read `gate.json` and `option_chain.json` and nothing else. No outcome, P&L, grade or shadow figure is here.

- Events with a chain reading: **143**. Failed before the chain: 5. Not live (dry or outside the window), skipped: 0.
- Reproduction of the stored gate: 143 of 143.

## A. Every check on every event (D003 v4)

| check | events failing | the only failing check |
|---|---|---|
| `no_quote` | 1 | 0 |
| `low_implied_move` | 1 | 0 |
| `wide_spread` | 106 | 46 |
| `thin_oi` | 65 | 4 |

| combination | events |
|---|---|
| wide_spread + thin_oi | 59 |
| wide_spread | 46 |
| PASS | 32 |
| thin_oi | 4 |
| low_implied_move + wide_spread + thin_oi | 1 |
| no_quote + thin_oi | 1 |

## B. Pass rate by share price

| bucket | events | PASS | rate | `no_quote` | `low_implied_move` | `wide_spread` | `thin_oi` |
|---|---|---|---|---|---|---|---|
| $100-<$300 | 50 | 13 | 26.0% | 0 | 0 | 36 | 24 |
| < $100 | 69 | 12 | 17.4% | 1 | 0 | 54 | 30 |
| >= $300 | 24 | 7 | 29.2% | 0 | 1 | 16 | 11 |

## B. Pass rate by expiry gap after the reaction day

| bucket | events | PASS | rate | `no_quote` | `low_implied_move` | `wide_spread` | `thin_oi` |
|---|---|---|---|---|---|---|---|
| <= 5 sessions | 63 | 24 | 38.1% | 0 | 1 | 38 | 18 |
| > 5 sessions (monthly) | 80 | 8 | 10.0% | 1 | 0 | 68 | 47 |

## C. Alternatives the stored chains support

| id | rule | PASS | adds | drops | median straddle spread | max straddle spread | max leg spread |
|---|---|---|---|---|---|---|---|
| A0 | D003 v4 as run | 32 of 143 | - | - | 4.6% | 9.6% | 9.8% |
| A1 | better of the two nearest strikes | 36 of 143 | COHU, HUT, TTMI, UCTT | - | 4.8% | 9.6% | 9.8% |
| A2 | dollar floor $0.10 a leg | 33 of 143 | NVTS | - | 4.7% | 11.6% | 15.6% |
| A3 | straddle spread <= 10% | 38 of 143 | ENTG, KLAC, RTX, TOST, TTMI, XYZ | - | 5.1% | 9.9% | 12.8% |
| A4 | A1 + A3 | 43 of 143 | COHU, ENTG, ETSY, GEHC, HUT, KLAC, RTX, TOST, TTMI, UCTT, XYZ | - | 5.7% | 9.9% | 12.8% |

Sensitivity (raises the friction ceiling; never recommended by §5):

| cap | PASS | adds | median straddle spread | max leg spread |
|---|---|---|---|---|
| leg 0.125 | 38 of 143 | ENTG, HUT, KLAC, TOST, TTMI, XYZ | 5.1% | 12.4% |
| leg 0.15 | 49 of 143 | APPF, COHU, DECK, DOCN, ENTG, ETSY, GEHC, HUT, KLAC, NXPI, PINS, RTX, SBUX, TOST, TTMI, VFC, XYZ | 6.5% | 14.9% |
| leg 0.2 | 57 of 143 | APPF, BSX, COHU, CROX, DECK, DOCN, ENTG, ETSY, GEHC, GEN, HUT, INCY, KLAC, NVTS, NXPI, PINS, RTX, SBUX, TOST, TSCO, TTMI, VFC, VRSN, W, XYZ | 8.0% | 19.1% |
| straddle 0.125 | 46 of 143 | APPF, CROX, DECK, DOCN, ENTG, ETSY, HUT, KLAC, NVTS, RTX, SBUX, TOST, TTMI, XYZ | 5.9% | 17.3% |
| straddle 0.15 | 53 of 143 | APPF, COHU, CROX, DECK, DOCN, ENTG, ETSY, GEHC, HUT, INCY, KLAC, NVTS, NXPI, PINS, RTX, SBUX, TOST, TTMI, VFC, VRSN, XYZ | 7.1% | 17.3% |

## D. The §5 decision rule

**D003 v5 = A4 from the Season B screen (Jacob's call).** A4 has the most PASS (43 vs A0 32); ties by median straddle spread, then A2, A1, A3, A4 (D016 §5.3).

Gains over A0: A1 +4, A2 +1, A3 +6, A4 +11.

_Interim: this decides nothing. The decision run is the first at or after Fri 2026-10-23 16:00 ET._

## Events

| event | spot | expiry gap | stored | all failing checks | straddle spread | A1 | A2 | A3 | A4 |
|---|---|---|---|---|---|---|---|---|---|
| ABT 2026-10-21 | 104.36 | 2 | PASS | PASS | 9.6% | PASS | PASS | PASS | PASS |
| AEHR 2026-11-02 | 52.00 | 3 | wide_spread | wide_spread, thin_oi | 17.0% | - | - | - | - |
| AGYS 2026-10-26 | 121.88 | 18 | wide_spread | wide_spread, thin_oi | 27.2% | - | - | - | - |
| ALAB 2026-11-03 | 233.15 | 2 | PASS | PASS | 2.3% | PASS | PASS | PASS | PASS |
| ALNY 2026-10-29 | 224.92 | 16 | wide_spread | wide_spread, thin_oi | 11.7% | - | - | - | - |
| AMD 2026-11-03 | 473.63 | 0 | PASS | PASS | 2.0% | PASS | PASS | PASS | PASS |
| AMKR 2026-10-26 | 39.50 | 3 | wide_spread | wide_spread, thin_oi | 10.5% | - | - | - | - |
| AMZN 2026-10-29 | 253.00 | 0 | PASS | PASS | 2.5% | PASS | PASS | PASS | PASS |
| ANET 2026-11-03 | 164.32 | 2 | PASS | PASS | 7.1% | PASS | PASS | PASS | PASS |
| APPF 2026-10-22 | 223.15 | 20 | wide_spread | wide_spread | 11.3% | - | - | - | - |
| ARXS 2026-10-28 | 52.47 | 16 | wide_spread | wide_spread, thin_oi | 29.5% | - | - | - | - |
| AXTI 2026-10-29 | 63.69 | 0 | wide_spread | wide_spread | 24.1% | - | - | - | - |
| BBIO 2026-10-29 | 70.93 | 15 | wide_spread | wide_spread, thin_oi | 64.9% | - | - | - | - |
| BDC 2026-10-29 | 107.23 | 16 | wide_spread | wide_spread, thin_oi | 29.0% | - | - | - | - |
| BETA 2026-11-03 | 19.57 | 13 | PASS | PASS | 6.1% | PASS | PASS | PASS | PASS |
| BHE 2026-10-28 | 70.54 | 16 | wide_spread | wide_spread, thin_oi | 67.5% | - | - | - | - |
| BLKB 2026-10-28 | 55.22 | 17 | wide_spread | wide_spread, thin_oi | 63.5% | - | - | - | - |
| BOOT 2026-10-28 | 111.69 | 16 | wide_spread | wide_spread, thin_oi | 21.0% | - | - | - | - |
| BSX 2026-10-28 | 45.38 | 2 | wide_spread | wide_spread | 16.0% | - | - | - | - |
| BWXT 2026-11-02 | 129.85 | 13 | wide_spread | wide_spread, thin_oi | 19.3% | - | - | - | - |
| CAKE 2026-10-27 | 108.36 | 17 | PASS | PASS | 5.7% | PASS | PASS | PASS | PASS |
| CDNS 2026-10-26 | 316.55 | 3 | wide_spread | wide_spread, thin_oi | 13.3% | - | - | - | - |
| CIFR 2026-11-02 | 8.05 | 4 | PASS | PASS | 4.8% | PASS | PASS | PASS | PASS |
| CLS 2026-10-26 | 260.98 | 3 | wide_spread | wide_spread, thin_oi | 10.8% | - | - | - | - |
| CMG 2026-10-28 | 27.94 | 1 | PASS | PASS | 5.7% | PASS | PASS | PASS | PASS |
| COHU 2026-10-28 | 51.18 | 16 | wide_spread | wide_spread | 14.3% | PASS | - | - | PASS |
| COLM 2026-10-29 | 60.51 | 15 | wide_spread | wide_spread, thin_oi | 125.3% | - | - | - | - |
| CROX 2026-10-29 | 119.00 | 16 | wide_spread | wide_spread | 12.3% | - | - | - | - |
| CVLT 2026-10-27 | 171.10 | 18 | wide_spread | wide_spread, thin_oi | 17.9% | - | - | - | - |
| DDOG 2026-11-04 | 219.84 | 2 | wide_spread | wide_spread, thin_oi | 10.1% | - | - | - | - |
| DECK 2026-10-22 | 85.62 | 0 | wide_spread | wide_spread | 11.6% | - | - | - | - |
| DOCN 2026-11-03 | 86.77 | 3 | wide_spread | wide_spread | 12.4% | - | - | - | - |
| DPZ 2026-10-13 | 307.39 | 3 | wide_spread | wide_spread, thin_oi | 16.3% | - | - | - | - |
| DT 2026-11-03 | 57.28 | 13 | PASS | PASS | 4.2% | PASS | PASS | PASS | PASS |
| DUOL 2026-11-03 | 135.92 | 2 | wide_spread | wide_spread, thin_oi | 20.1% | - | - | - | - |
| DXCM 2026-10-29 | 78.89 | 0 | wide_spread | wide_spread, thin_oi | 60.7% | - | - | - | - |
| EAT 2026-10-28 | 187.99 | 17 | wide_spread | wide_spread, thin_oi | 12.6% | - | - | - | - |
| EEFT 2026-10-27 | 65.62 | 18 | wide_spread | wide_spread | 33.5% | - | - | - | - |
| ENTG 2026-10-29 | 150.41 | 16 | wide_spread | wide_spread | 9.7% | - | - | PASS | PASS |
| ETSY 2026-10-28 | 84.54 | 2 | wide_spread | wide_spread | 10.9% | - | - | - | PASS |
| EXEL 2026-10-29 | 66.10 | 15 | wide_spread | wide_spread | 73.6% | - | - | - | - |
| EXTR 2026-10-28 | 22.97 | 17 | wide_spread | wide_spread, thin_oi | 13.7% | - | - | - | - |
| FFIV 2026-10-27 | 463.66 | 17 | PASS | PASS | 8.1% | PASS | PASS | PASS | PASS |
| FLEX 2026-10-28 | 78.05 | 17 | PASS | PASS | 6.9% | PASS | PASS | PASS | PASS |
| FLYW 2026-11-03 | 19.69 | 12 | wide_spread | wide_spread | 79.6% | - | - | - | - |
| FN 2026-11-02 | 318.96 | 13 | wide_spread | wide_spread, thin_oi | 17.2% | - | - | - | - |
| FORM 2026-10-28 | 106.75 | 16 | wide_spread | wide_spread, thin_oi | 8.3% | - | - | - | - |
| FRSH 2026-11-03 | 14.53 | 12 | wide_spread | wide_spread | 31.8% | - | - | - | - |
| FTAI 2026-10-29 | 157.40 | 1 | wide_spread | wide_spread, thin_oi | 18.3% | - | - | - | - |
| FTNT 2026-10-28 | 185.46 | 1 | wide_spread | wide_spread, thin_oi | 9.7% | - | - | - | - |
| GDDY 2026-10-29 | 106.22 | 0 | wide_spread | wide_spread, thin_oi | 86.7% | - | - | - | - |
| GD 2026-10-30 | 353.64 | 0 | low_implied_move | low_implied_move, wide_spread, thin_oi | 55.2% | - | - | - | - |
| GEHC 2026-10-28 | 71.83 | 2 | wide_spread | wide_spread | 13.0% | - | - | - | PASS |
| GEN 2026-10-28 | 23.99 | 16 | wide_spread | wide_spread | 16.8% | - | - | - | - |
| GLXY 2026-10-27 | 14.72 | 3 | PASS | PASS | 6.5% | PASS | PASS | PASS | PASS |
| GOOG 2026-10-28 | 318.05 | 1 | PASS | PASS | 3.3% | PASS | PASS | PASS | PASS |
| HII 2026-10-29 | 279.89 | 16 | wide_spread | wide_spread, thin_oi | 18.1% | - | - | - | - |
| HONA 2026-10-28 | 168.06 | 16 | wide_spread | wide_spread | 19.4% | - | - | - | - |
| HUT 2026-11-04 | 54.32 | 2 | wide_spread | wide_spread | 11.6% | PASS | - | - | PASS |
| HWM 2026-10-29 | 192.08 | 1 | wide_spread | wide_spread, thin_oi | 21.3% | - | - | - | - |
| HXL 2026-10-21 | 92.20 | 21 | wide_spread | wide_spread, thin_oi | 39.1% | - | - | - | - |
| ICHR 2026-11-02 | 38.12 | 13 | wide_spread | wide_spread, thin_oi | 12.7% | - | - | - | - |
| IDCC 2026-10-29 | 327.53 | 16 | wide_spread | wide_spread, thin_oi | 17.1% | - | - | - | - |
| INCY 2026-10-29 | 115.87 | 16 | wide_spread | wide_spread | 14.4% | - | - | - | - |
| INTA 2026-10-27 | 47.32 | 17 | wide_spread | wide_spread, thin_oi | 44.2% | - | - | - | - |
| INTC 2026-10-29 | 94.44 | 0 | PASS | PASS | 4.1% | PASS | PASS | PASS | PASS |
| IPGP 2026-11-03 | 71.51 | 13 | wide_spread | wide_spread, thin_oi | 45.4% | - | - | - | - |
| JMKE 2026-10-28 | 16.70 | 17 | wide_spread | wide_spread | 33.7% | - | - | - | - |
| KLAC 2026-10-28 | 153.55 | 1 | wide_spread | wide_spread | 9.2% | - | - | PASS | PASS |
| KN 2026-10-22 | 34.93 | 20 | wide_spread | wide_spread, thin_oi | 58.9% | - | - | - | - |
| LFUS 2026-10-28 | 365.19 | 17 | wide_spread | wide_spread, thin_oi | 11.8% | - | - | - | - |
| LHX 2026-10-29 | 258.46 | 1 | wide_spread | wide_spread, thin_oi | 10.0% | - | - | - | - |
| LMT 2026-10-22 | 550.26 | 1 | wide_spread | wide_spread | 23.0% | - | - | - | - |
| LOGI 2026-10-27 | 110.57 | 17 | wide_spread | wide_spread | 15.9% | - | - | - | - |
| LRCX 2026-10-21 | 265.30 | 1 | PASS | PASS | 4.7% | PASS | PASS | PASS | PASS |
| LSCC 2026-11-02 | 91.04 | 13 | wide_spread | wide_spread | 18.2% | - | - | - | - |
| MANH 2026-10-27 | 234.92 | 17 | wide_spread | wide_spread, thin_oi | 11.0% | - | - | - | - |
| META 2026-10-21 | 690.00 | 1 | PASS | PASS | 1.7% | PASS | PASS | PASS | PASS |
| MPWR 2026-10-29 | 1203.75 | 15 | wide_spread | wide_spread, thin_oi | 14.6% | - | - | - | - |
| MSFT 2026-10-28 | 530.66 | 1 | PASS | PASS | 1.7% | PASS | PASS | PASS | PASS |
| MSTR 2026-10-29 | 140.41 | 0 | PASS | PASS | 1.6% | PASS | PASS | PASS | PASS |
| MTCH 2026-11-02 | 41.47 | 13 | wide_spread | wide_spread | 15.4% | - | - | - | - |
| MUSA 2026-10-28 | 526.76 | 16 | wide_spread | wide_spread, thin_oi | 24.6% | - | - | - | - |
| MXL 2026-10-22 | 75.99 | 20 | PASS | PASS | 3.6% | PASS | PASS | PASS | PASS |
| NATL 2026-11-04 | 46.65 | 12 | no_quote | no_quote, thin_oi | - | - | - | - | - |
| NOC 2026-10-20 | 514.28 | 23 | wide_spread | wide_spread | 16.3% | - | - | - | - |
| NOW 2026-10-28 | 155.09 | 1 | PASS | PASS | 1.3% | PASS | PASS | PASS | PASS |
| NVTS 2026-11-03 | 8.07 | 2 | wide_spread | wide_spread | 11.6% | - | PASS | - | - |
| NXPI 2026-10-27 | 247.66 | 17 | wide_spread | wide_spread | 12.8% | - | - | - | - |
| OLED 2026-10-28 | 90.12 | 16 | wide_spread | wide_spread | 19.2% | - | - | - | - |
| ON 2026-11-02 | 69.82 | 3 | wide_spread | wide_spread, thin_oi | 13.0% | - | - | - | - |
| OSIS 2026-10-29 | 201.02 | 15 | wide_spread | wide_spread, thin_oi | 40.2% | - | - | - | - |
| OUST 2026-11-03 | 28.72 | 2 | wide_spread | wide_spread, thin_oi | 12.5% | - | - | - | - |
| PAY 2026-11-02 | 32.64 | 13 | wide_spread | wide_spread, thin_oi | 91.6% | - | - | - | - |
| PEGA 2026-10-20 | 35.18 | 22 | thin_oi | thin_oi | 8.8% | - | - | - | - |
| PINS 2026-10-29 | 20.83 | 0 | wide_spread | wide_spread | 13.1% | - | - | - | - |
| PI 2026-10-28 | 176.00 | 16 | wide_spread | wide_spread, thin_oi | 15.3% | - | - | - | - |
| PLTR 2026-11-02 | 184.37 | 3 | PASS | PASS | 1.0% | PASS | PASS | PASS | PASS |
| PLXS 2026-10-28 | 228.62 | 16 | wide_spread | wide_spread, thin_oi | 10.6% | - | - | - | - |
| QSR 2026-10-29 | 74.05 | 16 | PASS | PASS | 8.8% | PASS | PASS | PASS | PASS |
| QTWO 2026-10-28 | 68.41 | 16 | wide_spread | wide_spread, thin_oi | 33.9% | - | - | - | - |
| Q 2026-11-04 | 116.13 | 12 | wide_spread | wide_spread | 17.9% | - | - | - | - |
| RAL 2026-11-04 | 66.66 | 12 | wide_spread | wide_spread | 31.9% | - | - | - | - |
| RDDT 2026-10-29 | 135.37 | 0 | PASS | PASS | 4.6% | PASS | PASS | PASS | PASS |
| RIOT 2026-11-04 | 11.76 | 2 | PASS | PASS | 5.3% | PASS | PASS | PASS | PASS |
| RMBS 2026-10-26 | 87.00 | 18 | wide_spread | wide_spread, thin_oi | 12.9% | - | - | - | - |
| RNG 2026-10-22 | 83.30 | 0 | wide_spread | wide_spread | 23.4% | - | - | - | - |
| ROP 2026-10-22 | 395.17 | 21 | wide_spread | wide_spread | 19.3% | - | - | - | - |
| RPRX 2026-11-04 | 66.61 | 12 | wide_spread | wide_spread, thin_oi | 158.4% | - | - | - | - |
| RTX 2026-10-20 | 192.27 | 3 | wide_spread | wide_spread | 8.5% | - | - | PASS | PASS |
| SBUX 2026-10-29 | 104.03 | 0 | wide_spread | wide_spread | 10.9% | - | - | - | - |
| SHOP 2026-11-03 | 154.56 | 3 | PASS | PASS | 4.8% | PASS | PASS | PASS | PASS |
| SNDK 2026-10-29 | 1383.00 | 0 | PASS | PASS | 1.7% | PASS | PASS | PASS | PASS |
| SPCX 2026-10-20 | 147.24 | 0 | PASS | PASS | 2.3% | PASS | PASS | PASS | PASS |
| SPSC 2026-10-29 | 85.15 | 15 | wide_spread | wide_spread, thin_oi | 76.4% | - | - | - | - |
| SSNC 2026-10-22 | 87.15 | 20 | wide_spread | wide_spread, thin_oi | 42.9% | - | - | - | - |
| STX 2026-10-27 | 659.83 | 2 | wide_spread | wide_spread | 19.6% | - | - | - | - |
| SWKS 2026-11-03 | 85.32 | 12 | wide_spread | wide_spread, thin_oi | 11.4% | - | - | - | - |
| SYK 2026-10-29 | 304.38 | 15 | wide_spread | wide_spread | 28.1% | - | - | - | - |
| TEL 2026-10-28 | 215.10 | 17 | wide_spread | wide_spread, thin_oi | 14.5% | - | - | - | - |
| TENB 2026-10-28 | 48.79 | 16 | wide_spread | wide_spread, thin_oi | 36.1% | - | - | - | - |
| TER 2026-10-27 | 313.58 | 2 | thin_oi | thin_oi | 5.8% | - | - | - | - |
| TOST 2026-11-03 | 33.75 | 2 | wide_spread | wide_spread | 9.9% | - | - | PASS | PASS |
| TSCO 2026-10-22 | 32.97 | 1 | wide_spread | wide_spread | 16.8% | - | - | - | - |
| TTMI 2026-10-22 | 95.84 | 21 | wide_spread | wide_spread | 8.9% | PASS | - | PASS | PASS |
| TWLO 2026-10-29 | 252.49 | 0 | wide_spread | wide_spread | 20.6% | - | - | - | - |
| TXN 2026-10-21 | 280.08 | 1 | PASS | PASS | 5.7% | PASS | PASS | PASS | PASS |
| TYL 2026-10-28 | 378.95 | 16 | wide_spread | wide_spread, thin_oi | 21.9% | - | - | - | - |
| UBER 2026-11-04 | 66.78 | 2 | PASS | PASS | 2.7% | PASS | PASS | PASS | PASS |
| UCTT 2026-10-27 | 47.15 | 17 | thin_oi | thin_oi | 8.7% | PASS | - | - | PASS |
| VFC 2026-10-28 | 16.78 | 2 | wide_spread | wide_spread | 12.9% | - | - | - | - |
| VICR 2026-10-20 | 195.98 | 23 | wide_spread | wide_spread, thin_oi | 13.8% | - | - | - | - |
| VRSN 2026-10-22 | 307.55 | 20 | wide_spread | wide_spread | 14.2% | - | - | - | - |
| VRTX 2026-11-02 | 560.23 | 3 | wide_spread | wide_spread, thin_oi | 32.1% | - | - | - | - |
| VSH 2026-11-04 | 25.93 | 12 | wide_spread | wide_spread, thin_oi | 15.9% | - | - | - | - |
| VVX 2026-11-02 | 79.79 | 13 | wide_spread | wide_spread, thin_oi | 66.7% | - | - | - | - |
| WDC 2026-10-22 | 379.06 | 0 | PASS | PASS | 8.4% | PASS | PASS | PASS | PASS |
| WEX 2026-10-28 | 185.01 | 16 | thin_oi | thin_oi | 7.3% | - | - | - | - |
| W 2026-11-04 | 114.72 | 2 | wide_spread | wide_spread | 18.2% | - | - | - | - |
| XYZ 2026-11-03 | 77.59 | 2 | wide_spread | wide_spread | 8.0% | - | - | PASS | PASS |
| YOU 2026-11-04 | 48.12 | 12 | PASS | PASS | 7.4% | PASS | PASS | PASS | PASS |
| YUMC 2026-11-03 | 45.92 | 13 | wide_spread | wide_spread | 29.4% | - | - | - | - |
| ZBH 2026-11-04 | 96.62 | 12 | wide_spread | wide_spread, thin_oi | 53.3% | - | - | - | - |
