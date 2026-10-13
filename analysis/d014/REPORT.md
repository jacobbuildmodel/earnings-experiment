# D014 - the first hour after the print (EXPLORATION)

Frozen procedure `registry/D014_exploration_postprint_v1.md`. The gap's sign is read before 09:27 from pre-market trades; entry at the official opening auction. Positive y = the stock kept going the gap's way; negative = it reversed.

Events 2885 with a pre-market gap of at least 1% (TRAIN 1973 on 351 dates, VALIDATION 912 on 132 dates); 429 below the floor. Coverage: {'im': 868, 'surprise': 2882, 'pmv': 2885, 'spy_g': 2885}. Quotes: {'0935': 2884, '0940': 2885, '1000': 2885, '1030': 2885}.

## Verdict

- C1_big_gap|5: failed validation
- C1_big_gap|10: failed validation
- C1_big_gap|30: failed validation
- C1_big_gap|60: failed validation
- C1_big_gap|c: failed validation
- C6_high_attention|5: failed validation

## TRAIN family (42 tests)

| test | n | dates | mean y | t | q | survivor | complement mean |
|---|---|---|---|---|---|---|---|
| all|5 | 1918 | 343 | -0.131% | -1.87 | 0.272 |  | - |
| all|10 | 1970 | 350 | -0.081% | -0.95 | 0.684 |  | - |
| all|30 | 1973 | 351 | -0.022% | -0.22 | 0.959 |  | - |
| all|60 | 1973 | 351 | +0.016% | +0.15 | 0.959 |  | - |
| all|c | 1973 | 351 | +0.161% | +1.19 | 0.614 |  | - |
| C1_big_gap|5 | 65 | 42 | -1.988% | -4.70 | 0.0 | **yes** | -0.066% |
| C1_big_gap|10 | 70 | 45 | -1.956% | -4.21 | 0.001 | **yes** | -0.012% |
| C1_big_gap|30 | 70 | 45 | -2.011% | -4.06 | 0.001 | **yes** | +0.051% |
| C1_big_gap|60 | 70 | 45 | -2.130% | -4.11 | 0.001 | **yes** | +0.095% |
| C1_big_gap|c | 70 | 45 | -2.013% | -3.20 | 0.01 | **yes** | +0.241% |
| C2_surprise_disagrees|5 | 773 | 264 | -0.029% | -0.26 | 0.959 |  | -0.201% |
| C2_surprise_disagrees|10 | 789 | 269 | +0.038% | +0.31 | 0.959 |  | -0.160% |
| C2_surprise_disagrees|30 | 789 | 269 | +0.074% | +0.52 | 0.904 |  | -0.086% |
| C2_surprise_disagrees|60 | 789 | 269 | -0.011% | -0.07 | 0.959 |  | +0.034% |
| C2_surprise_disagrees|c | 789 | 269 | +0.039% | +0.19 | 0.959 |  | +0.242% |
| C3_market_against|5 | 852 | 258 | -0.151% | -1.40 | 0.507 |  | -0.115% |
| C3_market_against|10 | 872 | 260 | +0.041% | +0.32 | 0.959 |  | -0.178% |
| C3_market_against|30 | 873 | 260 | +0.080% | +0.53 | 0.904 |  | -0.102% |
| C3_market_against|60 | 873 | 260 | +0.139% | +0.80 | 0.717 |  | -0.082% |
| C3_market_against|c | 873 | 260 | +0.391% | +1.69 | 0.344 |  | -0.022% |
| C4_bad_news|5 | 907 | 275 | -0.095% | -0.87 | 0.704 |  | -0.164% |
| C4_bad_news|10 | 930 | 278 | +0.017% | +0.14 | 0.959 |  | -0.169% |
| C4_bad_news|30 | 931 | 279 | +0.014% | +0.09 | 0.959 |  | -0.054% |
| C4_bad_news|60 | 931 | 279 | -0.036% | -0.21 | 0.959 |  | +0.063% |
| C4_bad_news|c | 931 | 279 | +0.192% | +0.84 | 0.704 |  | +0.133% |
| C5_mid_cap|5 | 837 | 242 | -0.235% | -1.85 | 0.272 |  | -0.051% |
| C5_mid_cap|10 | 858 | 247 | -0.219% | -1.46 | 0.507 |  | +0.026% |
| C5_mid_cap|30 | 858 | 247 | -0.162% | -0.96 | 0.684 |  | +0.086% |
| C5_mid_cap|60 | 858 | 247 | -0.117% | -0.65 | 0.833 |  | +0.118% |
| C5_mid_cap|c | 858 | 247 | +0.049% | +0.22 | 0.959 |  | +0.247% |
| C6_high_attention|5 | 961 | 311 | -0.327% | -3.42 | 0.005 | **yes** | +0.065% |
| C6_high_attention|10 | 985 | 316 | -0.221% | -1.89 | 0.272 |  | +0.059% |
| C6_high_attention|30 | 986 | 317 | -0.187% | -1.33 | 0.517 |  | +0.143% |
| C6_high_attention|60 | 986 | 317 | -0.129% | -0.86 | 0.704 |  | +0.161% |
| C6_high_attention|c | 986 | 317 | -0.009% | -0.05 | 0.959 |  | +0.330% |
| all|d | 1918 | 343 | +0.086% | +1.38 | 0.507 |  | - |
| C1_big_gap|d | 65 | 42 | -0.112% | -0.33 | 0.959 |  | +0.092% |
| C2_surprise_disagrees|d | 773 | 264 | +0.090% | +0.95 | 0.684 |  | +0.082% |
| C3_market_against|d | 852 | 258 | +0.214% | +2.01 | 0.266 |  | -0.017% |
| C4_bad_news|d | 907 | 275 | +0.098% | +0.95 | 0.684 |  | +0.074% |
| C5_mid_cap|d | 837 | 242 | +0.034% | +0.30 | 0.959 |  | +0.125% |
| C6_high_attention|d | 961 | 311 | +0.102% | +1.09 | 0.683 |  | +0.069% |

## Survivors: costs and VALIDATION

| test | side | TRAIN net | VALIDATION mean y | Holm p | VALIDATION net | verdict |
|---|---|---|---|---|---|---|
| C1_big_gap|5 | fade | +1.436% | -0.716% | 0.3107 | +0.286% | failed validation |
| C1_big_gap|10 | fade | +1.647% | -0.762% | 0.3911 | +0.393% | failed validation |
| C1_big_gap|30 | fade | +1.803% | -0.901% | 0.4778 | +0.651% | failed validation |
| C1_big_gap|60 | fade | +1.973% | -0.869% | 0.4778 | +0.642% | failed validation |
| C1_big_gap|c | fade | +1.993% | -0.875% | 0.4778 | +0.855% | failed validation |
| C6_high_attention|5 | fade | +0.057% | -0.115% | 0.4778 | -0.207% | failed validation |

## Descriptive (no tests)

- |pre-market gap| quantiles: {'0.1': 0.018197681665212517, '0.25': 0.030410993765110028, '0.5': 0.05582922824302128, '0.75': 0.09507445589919816, '0.9': 0.14995811225914535}
- |gap| / implied move: {'n': 868, '0.25': 0.3113604505946098, '0.5': 0.5265116125236727, '0.75': 0.8183486027245995}
- the open gap has the pre-market gap's sign in 94.4% of events
- share of the reaction day's move reached by minute h (median): {'5': 0.87, '10': 0.88, '30': 0.92, '60': 0.93}
- sources: {'open_from_bar': 0, 'close_from_bar': 0}

