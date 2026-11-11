# Health 2026-11-10 19:04 ET - **AMBER**

check.py: PASS - 1 warning(s)

## RED - events or decisions being lost, or about to be
- none

## AMBER - look at
- T2R missing: ZETA_2026-11-09 (D013 shadow; the budget may have skipped it)
- T2O missing: ZETA_2026-11-09 (D013 shadow; the budget may have skipped it)
- T2R missing: ACHR_2026-11-09 (D013 shadow; the budget may have skipped it)
- T2O missing: ACHR_2026-11-09 (D013 shadow; the budget may have skipped it)
- T2R missing: CRWV_2026-11-10 (D013 shadow; the budget may have skipped it)
- T2O missing: CRWV_2026-11-10 (D013 shadow; the budget may have skipped it)
- T2R missing: MARA_2026-11-09 (D013 shadow; the budget may have skipped it)
- T2O missing: MARA_2026-11-09 (D013 shadow; the budget may have skipped it)
- T2R missing: RGTI_2026-11-10 (D013 shadow; the budget may have skipped it)
- T2O missing: RGTI_2026-11-10 (D013 shadow; the budget may have skipped it)
- Actions failure: Earnings experiment - paper options at 2026-11-10T23:50:33Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42926629787
- Actions failure: Earnings experiment - paper options at 2026-11-10T23:37:24Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42924884366
- Actions failure: Earnings experiment - paper options at 2026-11-10T23:07:54Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42920729986
- Actions failure: Earnings experiment - paper options at 2026-11-10T23:07:32Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42920675572
- Actions failure: Earnings experiment - paper options at 2026-11-10T22:14:29Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42912700779
- Actions failure: Earnings experiment - paper options at 2026-11-10T21:45:42Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42908150311
- Actions failure: Earnings experiment - paper options at 2026-11-10T21:15:16Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42903220580
- Actions failure: Earnings experiment - paper options at 2026-11-10T20:59:35Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42900613661
- Actions failure: Earnings experiment - paper window runner (routine push) at 2026-11-10T15:46:20Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42847830961
- Actions failure: Earnings experiment - paper options at 2026-11-10T12:08:35Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42813234591
- Actions failure: Earnings experiment - paper options at 2026-11-10T04:29:51Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42756222257
- Actions failure: Earnings experiment - paper options at 2026-11-10T02:35:05Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42743771983
- Actions failure: Earnings experiment - paper options at 2026-11-10T01:49:09Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42738449089
- Actions failure: Earnings experiment - paper options at 2026-11-10T01:41:58Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42737626209
- Actions failure: Earnings experiment - paper options at 2026-11-10T01:25:58Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42735740235
- Actions failure: Earnings experiment - paper options at 2026-11-10T01:25:30Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42735685983
- Actions failure: Earnings experiment - paper options at 2026-11-10T00:37:55Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42729769420
- Actions failure: Earnings experiment - paper options at 2026-11-10T00:08:16Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42725961203
- paper/options_ledger.json: alerts ['seasonA-DPZ-2026-10-13-F', 'seasonA-CIFR-2026-11-02-F', 'seasonA-BWXT-2026-11-02-F', 'seasonA-DOCN-2026-11-03-F', 'seasonA-BETA-2026-11-03-F', 'seasonA-DT-2026-11-03-F', 'seasonA-IPGP-2026-11-03-F', 'seasonA-LSCC-2026-11-02-F', 'seasonA-MTCH-2026-11-02-F', 'seasonA-ON-2026-11-02-F', 'seasonA-PAY-2026-11-02-F', 'seasonA-PLTR-2026-11-02-F', 'seasonA-SHOP-2026-11-03-F', 'seasonA-VRTX-2026-11-02-F', 'seasonA-VVX-2026-11-02-F', 'seasonA-YUMC-2026-11-03-F']

## KNOWN - acknowledged in ops/health_known.json, reads exactly as acknowledged; not in the status
- none

## Information
- ops/health_known.json: paper/options_ledger.json: alerts ['seasonA-DPZ-2026-10-13-F', 'seasonA-CIFR-2026-11-02-F', 'seasonA-BWXT-2026-11-02-F', 'seasonA-DOCN-2026-11-03-F', 'seasonA-BETA-2026-11-03-F', 'seasonA-DT-2026-11-03-F', 'seasonA-IPGP-2026-11-03-F', 'seasonA-LSCC-2026-11-02-F', 'seasonA-MTCH-2026-11-02-F', 'seasonA-ON-2026-11-02-F', 'seasonA-PAY-2026-11-02-F', 'seasonA-PLTR-2026-11-02-F', 'seasonA-SHOP-2026-11-03-F', 'seasonA-VRTX-2026-11-02-F', 'seasonA-VVX-2026-11-02-F', 'seasonA-YUMC-2026-11-03-F'] lapsed on 2026-11-06 - it alarms again until re-acknowledged
- ops/health_known.json: seasonA-DPZ-2026-10-13-F lapsed on 2026-11-06 - it alarms again until re-acknowledged
- 17 paper run(s) in 24 h failed only on the D019 stop (halt True, errors 0, every alert acknowledged or a gate the stop blocked), each read from its job logs; newest 2026-11-10T23:50:33Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42926629888
- paper/options_ledger.json: stopped by D019 since 2026-11-04T08:39 (registry/D019_reframe_v1.md §1) - no new opens; open positions close under D011's own exits
- paper/options_ledger.json: 46 gate(s) not opened under the D019 stop ['seasonA-ACHR-2026-11-09-F', 'seasonA-ALRM-2026-11-05-F', 'seasonA-ATEN-2026-11-05-F', 'seasonA-ATRO-2026-11-10-F', 'seasonA-AVPT-2026-11-05-F', 'seasonA-AXON-2026-11-05-F', 'seasonA-BILL-2026-11-05-F', 'seasonA-CARG-2026-11-05-F', 'seasonA-CRWV-2026-11-10-F', 'seasonA-DIOD-2026-11-05-F', 'seasonA-FIVN-2026-11-05-F', 'seasonA-FLY-2026-11-10-F', 'seasonA-FROG-2026-11-05-F', 'seasonA-GRND-2026-11-05-F', 'seasonA-HALO-2026-11-05-F', 'seasonA-IONQ-2026-11-05-F', 'seasonA-KRMN-2026-11-05-F', 'seasonA-LUNR-2026-11-12-F', 'seasonA-LYFT-2026-11-05-F', 'seasonA-MARA-2026-11-09-F', 'seasonA-MBGL-2026-11-12-F', 'seasonA-MRCY-2026-11-10-F', 'seasonA-MRNA-2026-11-06-F', 'seasonA-NET-2026-11-05-F', 'seasonA-OCTV-2026-11-12-F', 'seasonA-ONDS-2026-11-12-F', 'seasonA-PCTY-2026-11-05-F', 'seasonA-PDFS-2026-11-05-F', 'seasonA-QBTS-2026-11-10-F', 'seasonA-QLYS-2026-11-09-F', 'seasonA-RGTI-2026-11-10-F', 'seasonA-ROIV-2026-11-09-F', 'seasonA-RUM-2026-11-11-F', 'seasonA-SANM-2026-11-09-F', 'seasonA-SARO-2026-11-05-F', 'seasonA-SOUN-2026-11-05-F', 'seasonA-STUB-2026-11-10-F', 'seasonA-TDC-2026-11-05-F', 'seasonA-TDG-2026-11-10-F', 'seasonA-TEAM-2026-11-05-F', 'seasonA-TXG-2026-11-05-F', 'seasonA-TXRH-2026-11-05-F', 'seasonA-UA-2026-11-06-F', 'seasonA-VSAT-2026-11-05-F', 'seasonA-WULF-2026-11-06-F', 'seasonA-ZETA-2026-11-09-F']
- paper/long_ledger.json: stopped by D019 since 2026-11-04T08:39 (registry/D019_reframe_v1.md §1) - no new opens; open positions close under D011's own exits
- paper/long_ledger.json: 46 gate(s) not opened under the D019 stop ['seasonA-ACHR-2026-11-09-L', 'seasonA-ALRM-2026-11-05-L', 'seasonA-ATEN-2026-11-05-L', 'seasonA-ATRO-2026-11-10-L', 'seasonA-AVPT-2026-11-05-L', 'seasonA-AXON-2026-11-05-L', 'seasonA-BILL-2026-11-05-L', 'seasonA-CARG-2026-11-05-L', 'seasonA-CRWV-2026-11-10-L', 'seasonA-DIOD-2026-11-05-L', 'seasonA-FIVN-2026-11-05-L', 'seasonA-FLY-2026-11-10-L', 'seasonA-FROG-2026-11-05-L', 'seasonA-GRND-2026-11-05-L', 'seasonA-HALO-2026-11-05-L', 'seasonA-IONQ-2026-11-05-L', 'seasonA-KRMN-2026-11-05-L', 'seasonA-LUNR-2026-11-12-L', 'seasonA-LYFT-2026-11-05-L', 'seasonA-MARA-2026-11-09-L', 'seasonA-MBGL-2026-11-12-L', 'seasonA-MRCY-2026-11-10-L', 'seasonA-MRNA-2026-11-06-L', 'seasonA-NET-2026-11-05-L', 'seasonA-OCTV-2026-11-12-L', 'seasonA-ONDS-2026-11-12-L', 'seasonA-PCTY-2026-11-05-L', 'seasonA-PDFS-2026-11-05-L', 'seasonA-QBTS-2026-11-10-L', 'seasonA-QLYS-2026-11-09-L', 'seasonA-RGTI-2026-11-10-L', 'seasonA-ROIV-2026-11-09-L', 'seasonA-RUM-2026-11-11-L', 'seasonA-SANM-2026-11-09-L', 'seasonA-SARO-2026-11-05-L', 'seasonA-SOUN-2026-11-05-L', 'seasonA-STUB-2026-11-10-L', 'seasonA-TDC-2026-11-05-L', 'seasonA-TDG-2026-11-10-L', 'seasonA-TEAM-2026-11-05-L', 'seasonA-TXG-2026-11-05-L', 'seasonA-TXRH-2026-11-05-L', 'seasonA-UA-2026-11-06-L', 'seasonA-VSAT-2026-11-05-L', 'seasonA-WULF-2026-11-06-L', 'seasonA-ZETA-2026-11-09-L']
- paper window (options): paper-window-push.yml afternoon step since 10:49 ET (done)
- paper window (long): paper-window-push.yml afternoon step since 10:49 ET (done)
- paper/options: 68 position(s), 0 open order(s) - they match the ledgers
- paper/long: 5 position(s), 0 open order(s) - they match the ledgers
- Tue 10 Nov: 7 snapshot(s) - DGII, DPC, LUNR, MBGL, OCTV, ONDS, TWST
- Wed 11 Nov: 3 snapshot(s) - AMAT, CBRS, CSCO
- Fri 13 Nov: 1 snapshot(s) - INFQ
- Mon 16 Nov: 2 snapshot(s) - NVDA, TJX
- seasonA: 6 name(s) still PENDING a confirmed date

