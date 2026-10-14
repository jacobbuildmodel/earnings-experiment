# D014 v2 - pre-print state and the sector's week, first hour after the print (EXPLORATION)

Frozen procedure `registry/D014_exploration_postprint_v2.md`. Gap-up events only (s = +1). Positive y = the gap kept going after the open.

Step 1: {'events': 2885, 'with_ret5': 2885, 'with_rel5': 2884, 'gap_up_train': 1042, 'group_sizes_train': {'C7_washed_out': 73, 'C8_ran_up': 79, 'C9_sector_sold': 474, 'C10_sector_bought': 568}}

## Verdict

- no pre-print-state or sector-week pattern clears the bar (|t| > 3 and BH q < 0.10 on TRAIN)

## TRAIN family (18 tests)

| test | n | mean / diff | t | q | survivor |
|---|---|---|---|---|---|
| C7_washed_out|5 | 70 | -0.372% | -0.75 | 0.957 |  |
| C7_washed_out|30 | 73 | -0.417% | -0.65 | 0.957 |  |
| C7_washed_out|60 | 73 | -0.042% | -0.05 | 0.957 |  |
| C8_ran_up|5 | 78 | -0.022% | -0.07 | 0.957 |  |
| C8_ran_up|30 | 79 | -0.052% | -0.09 | 0.957 |  |
| C8_ran_up|60 | 79 | +0.415% | +0.79 | 0.957 |  |
| C7_minus_C8|5 | 70 vs 78 | -0.350% | -0.58 | 0.957 |  |
| C7_minus_C8|30 | 73 vs 79 | -0.365% | -0.42 | 0.957 |  |
| C7_minus_C8|60 | 73 vs 79 | -0.457% | -0.48 | 0.957 |  |
| C9_sector_sold|5 | 456 | -0.103% | -0.72 | 0.957 |  |
| C9_sector_sold|30 | 474 | -0.085% | -0.42 | 0.957 |  |
| C9_sector_sold|60 | 474 | +0.159% | +0.70 | 0.957 |  |
| C10_sector_bought|5 | 555 | -0.214% | -1.91 | 0.957 |  |
| C10_sector_bought|30 | 568 | -0.028% | -0.16 | 0.957 |  |
| C10_sector_bought|60 | 568 | -0.018% | -0.10 | 0.957 |  |
| C9_minus_C10|5 | 456 vs 555 | +0.111% | +0.65 | 0.957 |  |
| C9_minus_C10|30 | 474 vs 568 | -0.057% | -0.22 | 0.957 |  |
| C9_minus_C10|60 | 474 vs 568 | +0.177% | +0.63 | 0.957 |  |

## Secondary: small-ticket costs (13 bp vs 2 bp)

- v1 C1_big_gap|5 fade: TRAIN net +1.436% / +1.326%; VALIDATION net +0.286% / +0.176%
- v1 C1_big_gap|10 fade: TRAIN net +1.647% / +1.537%; VALIDATION net +0.393% / +0.283%
- v1 C1_big_gap|30 fade: TRAIN net +1.803% / +1.693%; VALIDATION net +0.651% / +0.541%
- v1 C1_big_gap|60 fade: TRAIN net +1.973% / +1.863%; VALIDATION net +0.642% / +0.532%
- v1 C1_big_gap|c fade: TRAIN net +1.993% / +1.883%; VALIDATION net +0.855% / +0.745%
- v1 C6_high_attention|5 fade: TRAIN net +0.057% / -0.053%; VALIDATION net -0.207% / -0.317%
- v1 all|d follow: TRAIN net -0.418% / -0.528%; VALIDATION net -0.663% / -0.773%
