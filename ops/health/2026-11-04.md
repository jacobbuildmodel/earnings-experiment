# Health 2026-11-04 10:46 ET - **RED**

check.py: PASS - 1 warning(s)

## RED - events or decisions being lost, or about to be
- paper/options_ledger.json: HALT - D019 §1 (registry/D019_reframe_v1.md): the committee's §12 REFRAME, approved by Jacob 2026-11-03 - paper options stopped. No new opens; open positions close under D011's own exit rules. Not a fill anomaly: do not clear.
- paper/long_ledger.json: HALT - D019 §1 (registry/D019_reframe_v1.md): the committee's §12 REFRAME, approved by Jacob 2026-11-03 - paper options stopped. No new opens; open positions close under D011's own exit rules. Not a fill anomaly: do not clear.

## AMBER - look at
- Actions failure: Earnings experiment - paper options at 2026-11-04T14:47:04Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41851017921
- Actions failure: Earnings experiment - paper long straddle at 2026-11-04T14:47:04Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41851017816
- Actions failure: Earnings experiment - paper options at 2026-11-04T03:04:52Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41764827525
- Actions failure: Earnings experiment - paper options at 2026-11-04T00:26:18Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41746811706
- Actions failure: Earnings experiment - paper options at 2026-11-03T23:49:43Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41742180661
- Actions failure: Earnings experiment - paper options at 2026-11-03T23:33:21Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41740072629
- Actions failure: Earnings experiment - paper options at 2026-11-03T23:10:48Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41737054993
- Actions failure: Earnings experiment - paper options at 2026-11-03T23:10:15Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41736977726
- Actions failure: Earnings experiment - paper options at 2026-11-03T22:15:49Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41729242094
- Actions failure: Earnings experiment - paper options at 2026-11-03T21:40:54Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41723986280
- Actions failure: Earnings experiment - paper options at 2026-11-03T20:52:36Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41716577417
- paper/options_ledger.json: alerts ['seasonA-DPZ-2026-10-13-F', 'seasonA-CIFR-2026-11-02-F', 'seasonA-BWXT-2026-11-02-F', 'seasonA-DOCN-2026-11-03-F', 'seasonA-BETA-2026-11-03-F', 'seasonA-DT-2026-11-03-F', 'seasonA-IPGP-2026-11-03-F', 'seasonA-LSCC-2026-11-02-F', 'seasonA-MTCH-2026-11-02-F', 'seasonA-ON-2026-11-02-F', 'seasonA-PAY-2026-11-02-F', 'seasonA-PLTR-2026-11-02-F', 'seasonA-SHOP-2026-11-03-F', 'seasonA-VRTX-2026-11-02-F', 'seasonA-VVX-2026-11-02-F', 'seasonA-YUMC-2026-11-03-F']

## KNOWN - acknowledged in ops/health_known.json, reads exactly as acknowledged; not in the status
- none

## Information
- paper/options_ledger.json: open ['seasonA-ALAB-2026-11-03-F', 'seasonA-AMD-2026-11-03-F', 'seasonA-ANET-2026-11-03-F', 'seasonA-DDOG-2026-11-04-F', 'seasonA-FLYW-2026-11-03-F', 'seasonA-FRSH-2026-11-03-F', 'seasonA-HUT-2026-11-04-F', 'seasonA-NVTS-2026-11-03-F', 'seasonA-OUST-2026-11-03-F', 'seasonA-Q-2026-11-04-F', 'seasonA-RAL-2026-11-04-F', 'seasonA-RIOT-2026-11-04-F', 'seasonA-RPRX-2026-11-04-F', 'seasonA-SWKS-2026-11-03-F', 'seasonA-TOST-2026-11-03-F', 'seasonA-VSH-2026-11-04-F', 'seasonA-W-2026-11-04-F', 'seasonA-XYZ-2026-11-03-F', 'seasonA-YOU-2026-11-04-F', 'seasonA-ZBH-2026-11-04-F', 'seasonA-ACIW-2026-11-05-F', 'seasonA-ACLS-2026-11-05-F', 'seasonA-BROS-2026-11-04-F', 'seasonA-BSY-2026-11-05-F', 'seasonA-CAVA-2026-11-04-F', 'seasonA-CHYM-2026-11-04-F', 'seasonA-CORZ-2026-11-05-F', 'seasonA-CPAY-2026-11-04-F', 'seasonA-SNAP-2026-11-04-F', 'seasonA-U-2026-11-05-F', 'seasonA-VERX-2026-11-04-F', 'seasonA-VIAV-2026-11-04-F']
- paper/long_ledger.json: open ['seasonA-AMD-2026-11-03-L', 'seasonA-ANET-2026-11-03-L', 'seasonA-DDOG-2026-11-04-L', 'seasonA-DUOL-2026-11-03-L', 'seasonA-FLYW-2026-11-03-L', 'seasonA-FRSH-2026-11-03-L', 'seasonA-NVTS-2026-11-03-L', 'seasonA-OUST-2026-11-03-L', 'seasonA-Q-2026-11-04-L', 'seasonA-RAL-2026-11-04-L', 'seasonA-RIOT-2026-11-04-L', 'seasonA-SWKS-2026-11-03-L', 'seasonA-TOST-2026-11-03-L', 'seasonA-UBER-2026-11-04-L', 'seasonA-VSH-2026-11-04-L', 'seasonA-W-2026-11-04-L', 'seasonA-XYZ-2026-11-03-L', 'seasonA-YOU-2026-11-04-L', 'seasonA-ZBH-2026-11-04-L', 'seasonA-ACIW-2026-11-05-L', 'seasonA-ACLS-2026-11-05-L', 'seasonA-BROS-2026-11-04-L', 'seasonA-BSY-2026-11-05-L', 'seasonA-CAVA-2026-11-04-L', 'seasonA-CHYM-2026-11-04-L', 'seasonA-CORZ-2026-11-05-L', 'seasonA-CPAY-2026-11-04-L', 'seasonA-CRUS-2026-11-04-L', 'seasonA-CW-2026-11-04-L', 'seasonA-DCO-2026-11-05-L', 'seasonA-EW-2026-11-04-L', 'seasonA-FICO-2026-11-04-L', 'seasonA-FIG-2026-11-04-L', 'seasonA-FOUR-2026-11-05-L', 'seasonA-KVYO-2026-11-04-L', 'seasonA-LOAR-2026-11-05-L', 'seasonA-MELI-2026-11-04-L', 'seasonA-MTSI-2026-11-05-L', 'seasonA-NTCT-2026-11-05-L', 'seasonA-ONC-2026-11-05-L', 'seasonA-OTEX-2026-11-05-L', 'seasonA-PAYC-2026-11-04-L', 'seasonA-POWI-2026-11-04-L', 'seasonA-PTRN-2026-11-04-L']
- paper/options: ALAB: the account holds +0, the ledgers show +7 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: AMD: the account holds +0, the ledgers show +6 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: ANET: the account holds +0, the ledgers show +15 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: CHYM: the account holds +62, the ledgers show +0 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: CORZ: the account holds +137, the ledgers show +0 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: FOUR: the account holds +32, the ledgers show +0 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: KVYO: the account holds +57, the ledgers show +0 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: QCOM: the account holds +16, the ledgers show +0 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: RIOT: the account holds +0, the ledgers show +136 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: SNAP: the account holds +307, the ledgers show +0 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: UBER: the account holds +0, the ledgers show +49 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: YOU: the account holds +0, the ledgers show +38 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: Z: the account holds +54, the ledgers show +0 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: ['seasonA-ALAB-2026-11-03-sell', 'seasonA-AMD-2026-11-03-sell', 'seasonA-ANET-2026-11-03-sell', 'seasonA-RIOT-2026-11-04-sell', 'seasonA-UBER-2026-11-04-sell', 'seasonA-YOU-2026-11-04-sell', 'seasonA-CHYM-2026-11-04-buy', 'seasonA-CORZ-2026-11-05-buy', 'seasonA-FOUR-2026-11-05-buy', 'seasonA-KVYO-2026-11-04-buy', 'seasonA-QCOM-2026-11-04-buy', 'seasonA-SNAP-2026-11-04-buy', 'seasonA-Z-2026-11-04-buy'] live in the ledger, no longer open at Alpaca (the next paper run records how they ended)
- paper/options: 178 position(s), 0 open order(s) - they match the ledgers
- paper/long: 91 position(s), 0 open order(s) - they match the ledgers
- Wed 04 Nov: 35 snapshot(s) - AKAM, ALRM, ATEN, AVPT, AXON, BILL, CARG, CART, DBX, DIOD, FIGS, FIVN, FROG, GRND, HALO, IONQ, IREN, KRMN, LASR, LITE, LYFT, MRNA, NET, PCTY, PDFS, QNT, SARO, SOUN, TDC, TEAM, TXG, TXRH, UA, VSAT, WULF
- Thu 05 Nov: 2 snapshot(s) - ROIV, VIA
- Fri 06 Nov: 10 snapshot(s) - ACHR, ASTS, CSQR, MARA, ONTO, QBTS, QLYS, SANM, TDG, ZETA
- Mon 09 Nov: 7 snapshot(s) - ATRO, CRWV, FLY, MRCY, RGTI, RUM, STUB
- Tue 10 Nov: 7 snapshot(s) - DGII, DPC, LUNR, MBGL, OCTV, ONDS, TWST
- seasonA: 29 name(s) still PENDING a confirmed date

