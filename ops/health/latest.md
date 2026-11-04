# Health 2026-11-04 15:29 ET - **AMBER**

check.py: PASS - 1 warning(s)

## RED - events or decisions being lost, or about to be
- none

## AMBER - look at
- Actions failure: Earnings experiment - paper options at 2026-11-04T14:47:04Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41851017921
- Actions failure: Earnings experiment - paper window runner (routine push) at 2026-11-04T14:46:33Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41850934058
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
- IREN_2026-11-05: T2 deadline Thu 05 Nov 09:15 ET - frozen so far: none
- WULF_2026-11-06: T2 deadline Thu 05 Nov 09:15 ET - frozen so far: none
- LYFT_2026-11-05: T2 deadline Thu 05 Nov 09:15 ET - frozen so far: none
- 1 paper run(s) in 24 h failed only on the D019 stop (halt True, errors 0, every alert acknowledged or a gate the stop blocked), each read from its job logs; newest 2026-11-04T14:47:04Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41851017816
- paper/options_ledger.json: stopped by D019 since 2026-11-04T08:39 (registry/D019_reframe_v1.md §1) - no new opens; open positions close under D011's own exits
- paper/options_ledger.json: open ['seasonA-ACIW-2026-11-05-F', 'seasonA-ACLS-2026-11-05-F', 'seasonA-BROS-2026-11-04-F', 'seasonA-BSY-2026-11-05-F', 'seasonA-CAVA-2026-11-04-F', 'seasonA-CHYM-2026-11-04-F', 'seasonA-CORZ-2026-11-05-F', 'seasonA-CPAY-2026-11-04-F', 'seasonA-SNAP-2026-11-04-F', 'seasonA-U-2026-11-05-F', 'seasonA-VERX-2026-11-04-F', 'seasonA-VIAV-2026-11-04-F']
- paper/long_ledger.json: stopped by D019 since 2026-11-04T08:39 (registry/D019_reframe_v1.md §1) - no new opens; open positions close under D011's own exits
- paper/long_ledger.json: open ['seasonA-ACIW-2026-11-05-L', 'seasonA-ACLS-2026-11-05-L', 'seasonA-BROS-2026-11-04-L', 'seasonA-BSY-2026-11-05-L', 'seasonA-CAVA-2026-11-04-L', 'seasonA-CHYM-2026-11-04-L', 'seasonA-CORZ-2026-11-05-L', 'seasonA-CPAY-2026-11-04-L', 'seasonA-CRUS-2026-11-04-L', 'seasonA-CW-2026-11-04-L', 'seasonA-DCO-2026-11-05-L', 'seasonA-EW-2026-11-04-L', 'seasonA-FICO-2026-11-04-L', 'seasonA-FIG-2026-11-04-L', 'seasonA-FOUR-2026-11-05-L', 'seasonA-KVYO-2026-11-04-L', 'seasonA-LOAR-2026-11-05-L', 'seasonA-MELI-2026-11-04-L', 'seasonA-MTSI-2026-11-05-L', 'seasonA-NTCT-2026-11-05-L', 'seasonA-ONC-2026-11-05-L', 'seasonA-OTEX-2026-11-05-L', 'seasonA-PAYC-2026-11-04-L', 'seasonA-POWI-2026-11-04-L', 'seasonA-PTRN-2026-11-04-L']
- paper window (options): paper-window-push.yml afternoon step since 12:00 ET
- paper window (long): paper-window-push.yml afternoon step since 12:00 ET
- paper/options: 125 position(s), 0 open order(s) - they match the ledgers
- paper/long: 56 position(s), 0 open order(s) - they match the ledgers
- Wed 04 Nov: 35 snapshot(s) - AKAM, ALRM, ATEN, AVPT, AXON, BILL, CARG, CART, DBX, DIOD, FIGS, FIVN, FROG, GRND, HALO, IONQ, IREN, KRMN, LASR, LITE, LYFT, MRNA, NET, PCTY, PDFS, QNT, SARO, SOUN, TDC, TEAM, TXG, TXRH, UA, VSAT, WULF
- Thu 05 Nov: 2 snapshot(s) - ROIV, VIA
- Fri 06 Nov: 10 snapshot(s) - ACHR, ASTS, CSQR, MARA, ONTO, QBTS, QLYS, SANM, TDG, ZETA
- Mon 09 Nov: 7 snapshot(s) - ATRO, CRWV, FLY, MRCY, RGTI, RUM, STUB
- Tue 10 Nov: 7 snapshot(s) - DGII, DPC, LUNR, MBGL, OCTV, ONDS, TWST
- seasonA: 29 name(s) still PENDING a confirmed date

