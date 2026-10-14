# D014 v3 - the retail entry (cost addendum, no new test)

Frozen `registry/D014_exploration_postprint_v3.md`. Retail entry = the first regular minute's VWAP worsened by half the first post-open quoted spread (moomoo SG has no opening-auction order).

Coverage: {'events': 2885, 'with_retail_entry': 2865}

## Survivors

- v1 C1_big_gap|5: **auction-only** - retail net TRAIN +0.283% / VALIDATION -0.553% at 2 bp; -0.663% at 13 bp (VALIDATION)
- v1 C1_big_gap|10: **auction-only** - retail net TRAIN +0.497% / VALIDATION -0.444% at 2 bp; -0.554% at 13 bp (VALIDATION)
- v1 C1_big_gap|30: **auction-only** - retail net TRAIN +0.649% / VALIDATION -0.196% at 2 bp; -0.306% at 13 bp (VALIDATION)
- v1 C1_big_gap|60: **auction-only** - retail net TRAIN +0.820% / VALIDATION -0.181% at 2 bp; -0.291% at 13 bp (VALIDATION)
- v1 C1_big_gap|c: **auction-only** - retail net TRAIN +0.855% / VALIDATION -0.020% at 2 bp; -0.130% at 13 bp (VALIDATION)
- v1 C6_high_attention|5: **auction-only** - retail net TRAIN -0.296% / VALIDATION -0.909% at 2 bp; -1.019% at 13 bp (VALIDATION)

## Unconditional, net at 2 bp by entry (descriptive)

| cell | segment | auction | retail (primary) | plain VWAP | far side |
|---|---|---|---|---|---|
| all|5 follow | train | -0.486% | -1.322% | -0.530% | -1.148% |
| all|5 follow | validation | -0.602% | -1.464% | -0.569% | -1.380% |
| all|5 fade | train | -0.222% | -0.951% | -0.178% | -1.123% |
| all|5 fade | validation | -0.373% | -1.299% | -0.406% | -1.382% |
| all|10 follow | train | -0.353% | -1.186% | -0.397% | -1.013% |
| all|10 follow | validation | -0.399% | -1.264% | -0.367% | -1.179% |
| all|10 fade | train | -0.198% | -0.928% | -0.154% | -1.100% |
| all|10 fade | validation | -0.359% | -1.283% | -0.391% | -1.368% |
| all|30 follow | train | -0.217% | -1.053% | -0.261% | -0.880% |
| all|30 follow | validation | -0.308% | -1.178% | -0.276% | -1.093% |
| all|30 fade | train | -0.176% | -0.904% | -0.133% | -1.076% |
| all|30 fade | validation | -0.214% | -1.130% | -0.246% | -1.215% |
| all|60 follow | train | -0.128% | -0.962% | -0.171% | -0.790% |
| all|60 follow | validation | -0.181% | -1.054% | -0.147% | -0.970% |
| all|60 fade | train | -0.158% | -0.889% | -0.115% | -1.060% |
| all|60 fade | validation | -0.212% | -1.122% | -0.246% | -1.205% |
| all|c follow | train | +0.141% | -0.686% | +0.098% | -0.514% |
| all|c follow | validation | +0.216% | -0.653% | +0.249% | -0.567% |
| all|c fade | train | -0.181% | -0.916% | -0.138% | -1.087% |
| all|c fade | validation | -0.256% | -1.176% | -0.289% | -1.261% |
