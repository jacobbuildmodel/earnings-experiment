# Health 2026-11-03 10:46 ET - **AMBER**

check.py: PASS - 1 warning(s)

## RED - events or decisions being lost, or about to be
- none

## AMBER - look at
- Actions failure: Earnings experiment - paper options at 2026-11-03T14:47:07Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41657109564
- Actions failure: Earnings experiment - paper options at 2026-11-03T04:03:59Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41575882842
- Actions failure: Earnings experiment - paper options at 2026-11-03T02:02:31Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41563598606
- Actions failure: Earnings experiment - paper options at 2026-11-03T01:25:03Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41559603872
- Actions failure: Earnings experiment - paper options at 2026-11-03T01:08:15Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41557714310
- Actions failure: Earnings experiment - paper options at 2026-11-03T00:52:24Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41555922689
- Actions failure: Earnings experiment - paper options at 2026-11-03T00:51:29Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41555817177
- Actions failure: Earnings experiment - paper options at 2026-11-02T23:49:43Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41548365936
- Actions failure: Earnings experiment - paper options at 2026-11-02T23:25:04Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41545263414
- Actions failure: Earnings experiment - paper options at 2026-11-02T23:04:10Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41542444999
- Actions failure: Earnings experiment - paper options at 2026-11-02T22:52:48Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41540924277
- Actions failure: Earnings experiment - paper options at 2026-11-02T19:37:40Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41511693360
- paper/options_ledger.json: alerts ['seasonA-DPZ-2026-10-13-F', 'seasonA-CIFR-2026-11-02-F', 'seasonA-BWXT-2026-11-02-F', 'seasonA-DOCN-2026-11-03-F', 'seasonA-BETA-2026-11-03-F', 'seasonA-DT-2026-11-03-F', 'seasonA-IPGP-2026-11-03-F', 'seasonA-LSCC-2026-11-02-F', 'seasonA-MTCH-2026-11-02-F', 'seasonA-ON-2026-11-02-F', 'seasonA-PAY-2026-11-02-F', 'seasonA-PLTR-2026-11-02-F', 'seasonA-SHOP-2026-11-03-F', 'seasonA-VRTX-2026-11-02-F', 'seasonA-VVX-2026-11-02-F', 'seasonA-YUMC-2026-11-03-F']
- no C1 implied-move capture for 2026-11-02 (D015): that session's events can never be C1

## KNOWN - acknowledged in ops/health_known.json, reads exactly as acknowledged; not in the status
- none

## Information
- paper/options_ledger.json: open ['seasonA-ALAB-2026-11-03-F', 'seasonA-AMD-2026-11-03-F', 'seasonA-ANET-2026-11-03-F', 'seasonA-DDOG-2026-11-04-F', 'seasonA-FLYW-2026-11-03-F', 'seasonA-FRSH-2026-11-03-F', 'seasonA-HUT-2026-11-04-F', 'seasonA-NVTS-2026-11-03-F', 'seasonA-OUST-2026-11-03-F', 'seasonA-Q-2026-11-04-F', 'seasonA-RAL-2026-11-04-F', 'seasonA-RIOT-2026-11-04-F', 'seasonA-RPRX-2026-11-04-F', 'seasonA-SWKS-2026-11-03-F', 'seasonA-TOST-2026-11-03-F', 'seasonA-VSH-2026-11-04-F', 'seasonA-W-2026-11-04-F', 'seasonA-XYZ-2026-11-03-F', 'seasonA-YOU-2026-11-04-F', 'seasonA-ZBH-2026-11-04-F']
- paper/long_ledger.json: open ['seasonA-DOCN-2026-11-03-L', 'seasonA-BETA-2026-11-03-L', 'seasonA-DT-2026-11-03-L', 'seasonA-IPGP-2026-11-03-L', 'seasonA-MTCH-2026-11-02-L', 'seasonA-ON-2026-11-02-L', 'seasonA-PAY-2026-11-02-L', 'seasonA-PLTR-2026-11-02-L', 'seasonA-SHOP-2026-11-03-L', 'seasonA-VVX-2026-11-02-L', 'seasonA-YUMC-2026-11-03-L', 'seasonA-AMD-2026-11-03-L', 'seasonA-ANET-2026-11-03-L', 'seasonA-DDOG-2026-11-04-L', 'seasonA-DUOL-2026-11-03-L', 'seasonA-FLYW-2026-11-03-L', 'seasonA-FRSH-2026-11-03-L', 'seasonA-NVTS-2026-11-03-L', 'seasonA-OUST-2026-11-03-L', 'seasonA-Q-2026-11-04-L', 'seasonA-RAL-2026-11-04-L', 'seasonA-RIOT-2026-11-04-L', 'seasonA-SWKS-2026-11-03-L', 'seasonA-TOST-2026-11-03-L', 'seasonA-UBER-2026-11-04-L', 'seasonA-VSH-2026-11-04-L', 'seasonA-W-2026-11-04-L', 'seasonA-XYZ-2026-11-03-L', 'seasonA-YOU-2026-11-04-L', 'seasonA-ZBH-2026-11-04-L']
- paper/options: ALAB: the account holds +7, the ledgers show +0 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: AMD: the account holds +6, the ledgers show +0 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: ANET: the account holds +15, the ledgers show +0 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: BETA: the account holds +0, the ledgers show +88 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: DT: the account holds +0, the ledgers show +40 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: PLTR: the account holds +0, the ledgers show +11 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: RIOT: the account holds +136, the ledgers show +0 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: SHOP: the account holds +0, the ledgers show +13 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: UBER: the account holds +49, the ledgers show +0 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: YOU: the account holds +38, the ledgers show +0 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: ['seasonA-BETA-2026-11-03-sell', 'seasonA-DT-2026-11-03-sell', 'seasonA-PLTR-2026-11-02-sell', 'seasonA-SHOP-2026-11-03-sell', 'seasonA-ALAB-2026-11-03-buy', 'seasonA-AMD-2026-11-03-buy', 'seasonA-ANET-2026-11-03-buy', 'seasonA-RIOT-2026-11-04-buy', 'seasonA-UBER-2026-11-04-buy', 'seasonA-YOU-2026-11-04-buy'] live in the ledger, no longer open at Alpaca (the next paper run records how they ended)
- paper/options: 129 position(s), 0 open order(s) - they match the ledgers
- paper/long: 62 position(s), 0 open order(s) - they match the ledgers
- Tue 03 Nov: 48 snapshot(s) - ACIW, ACLS, ACMR, APPN, BROS, BSY, CAVA, CHYM, CORZ, CPAY, CRUS, CW, DASH, DAVE, DCO, EW, FICO, FIG, FOUR, FSLY, HUBS, KTB, KVYO, LOAR, MELI, MTSI, NTCT, ONC, OTEX, PAYC, PAYO, POWI, PTC, PTRN, QCOM, RDW, RELY, RVMD, SHAK, SITM, SNAP, STE, U, VECO, VERX, VIAV, VSEC, Z
- Wed 04 Nov: 35 snapshot(s) - AKAM, ALRM, ATEN, AVPT, AXON, BILL, CARG, CART, DBX, DIOD, FIGS, FIVN, FROG, GRND, HALO, IONQ, IREN, KRMN, LASR, LITE, LYFT, MRNA, NET, PCTY, PDFS, QNT, SARO, SOUN, TDC, TEAM, TXG, TXRH, UA, VSAT, WULF
- Thu 05 Nov: 2 snapshot(s) - ROIV, VIA
- Fri 06 Nov: 9 snapshot(s) - ACHR, ASTS, CSQR, MARA, ONTO, QBTS, QLYS, SANM, ZETA
- Mon 09 Nov: 7 snapshot(s) - ATRO, CRWV, FLY, MRCY, RGTI, RUM, STUB
- seasonA: 42 name(s) still PENDING a confirmed date

