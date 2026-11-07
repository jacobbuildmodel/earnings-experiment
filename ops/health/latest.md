# Health 2026-11-07 05:37 ET - **AMBER**

check.py: PASS - 1 warning(s)

## RED - events or decisions being lost, or about to be
- paper/options_ledger.json: HALT - fill anomaly - new opens stopped until a person clears 'halt' in the ledger
- DATES STALE (seasonA): no date confirmed or retired since Fri 30 Oct 22:12 ET (over 30 h), while 30 PENDING name(s) have a calendar date within 7 days, 23 within 3 sessions ['ADEA', 'CALX', 'CORT', 'CPNG', 'DBD', 'EBAY', 'IBRX', 'KTB', 'MARA', 'MCD', 'MDGL', 'PCOR', 'PEN', 'PPLI', 'RAMP', 'RDW', 'ROG', 'SHOO', 'SLAB', 'TECH', 'WK', 'YUM', 'ZBRA']; newest re-check Fri 30 Oct 22:06 ET - the re-checks are not running

## AMBER - look at
- T2R missing: LYFT_2026-11-05 (D013 shadow; the budget may have skipped it)
- T2O missing: LYFT_2026-11-05 (D013 shadow; the budget may have skipped it)
- T2R missing: WULF_2026-11-06 (D013 shadow; the budget may have skipped it)
- T2O missing: WULF_2026-11-06 (D013 shadow; the budget may have skipped it)
- T2R missing: IREN_2026-11-05 (D013 shadow; the budget may have skipped it)
- T2O missing: IREN_2026-11-05 (D013 shadow; the budget may have skipped it)
- Actions failure: Earnings experiment - paper options at 2026-11-07T03:12:58Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42332956168
- Actions failure: Earnings experiment - paper options at 2026-11-07T02:32:21Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42329746362
- Actions failure: Earnings experiment - paper options at 2026-11-06T23:58:34Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42315318590
- Actions failure: Earnings experiment - paper options at 2026-11-06T23:36:04Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42312994358
- Actions failure: Earnings experiment - paper options at 2026-11-06T23:22:20Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42311452049
- Actions failure: Earnings experiment - paper options at 2026-11-06T22:58:38Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42308629430
- Actions failure: Earnings experiment - paper options at 2026-11-06T22:58:02Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42308560576
- Actions failure: Earnings experiment - paper options at 2026-11-06T21:59:28Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42301155730
- Actions failure: Earnings experiment - paper options at 2026-11-06T21:26:23Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42296725891
- Actions failure: Earnings experiment - paper options at 2026-11-06T20:48:28Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42291453067
- Actions failure: Earnings experiment - paper window runner (routine push) at 2026-11-06T15:45:36Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42246022814
- Actions failure: Earnings experiment - paper options at 2026-11-06T14:48:02Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42237150713
- paper/options_ledger.json: alerts ['seasonA-DPZ-2026-10-13-F', 'seasonA-CIFR-2026-11-02-F', 'seasonA-BWXT-2026-11-02-F', 'seasonA-DOCN-2026-11-03-F', 'seasonA-BETA-2026-11-03-F', 'seasonA-DT-2026-11-03-F', 'seasonA-IPGP-2026-11-03-F', 'seasonA-LSCC-2026-11-02-F', 'seasonA-MTCH-2026-11-02-F', 'seasonA-ON-2026-11-02-F', 'seasonA-PAY-2026-11-02-F', 'seasonA-PLTR-2026-11-02-F', 'seasonA-SHOP-2026-11-03-F', 'seasonA-VRTX-2026-11-02-F', 'seasonA-VVX-2026-11-02-F', 'seasonA-YUMC-2026-11-03-F']

## KNOWN - acknowledged in ops/health_known.json, reads exactly as acknowledged; not in the status
- none

## Information
- ZETA_2026-11-09: T2 deadline Mon 09 Nov 09:15 ET - frozen so far: T2, T2G
- ACHR_2026-11-09: T2 deadline Mon 09 Nov 09:15 ET - frozen so far: T2, T2G
- MARA_2026-11-09: T2 deadline Mon 09 Nov 09:15 ET - frozen so far: T2, T2G
- ops/health_known.json: paper/options_ledger.json: alerts ['seasonA-DPZ-2026-10-13-F', 'seasonA-CIFR-2026-11-02-F', 'seasonA-BWXT-2026-11-02-F', 'seasonA-DOCN-2026-11-03-F', 'seasonA-BETA-2026-11-03-F', 'seasonA-DT-2026-11-03-F', 'seasonA-IPGP-2026-11-03-F', 'seasonA-LSCC-2026-11-02-F', 'seasonA-MTCH-2026-11-02-F', 'seasonA-ON-2026-11-02-F', 'seasonA-PAY-2026-11-02-F', 'seasonA-PLTR-2026-11-02-F', 'seasonA-SHOP-2026-11-03-F', 'seasonA-VRTX-2026-11-02-F', 'seasonA-VVX-2026-11-02-F', 'seasonA-YUMC-2026-11-03-F'] lapsed on 2026-11-06 - it alarms again until re-acknowledged
- ops/health_known.json: seasonA-DPZ-2026-10-13-F lapsed on 2026-11-06 - it alarms again until re-acknowledged
- 11 paper run(s) in 24 h failed only on the D019 stop (halt True, errors 0, every alert acknowledged or a gate the stop blocked), each read from its job logs; newest 2026-11-07T03:12:58Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42332956233
- paper/options_ledger.json: stopped by D019 since 2026-11-04T08:39 (registry/D019_reframe_v1.md §1) - no new opens; open positions close under D011's own exits
- paper/options_ledger.json: 35 gate(s) not opened under the D019 stop ['seasonA-ACHR-2026-11-09-F', 'seasonA-ALRM-2026-11-05-F', 'seasonA-ATEN-2026-11-05-F', 'seasonA-AVPT-2026-11-05-F', 'seasonA-AXON-2026-11-05-F', 'seasonA-BILL-2026-11-05-F', 'seasonA-CARG-2026-11-05-F', 'seasonA-DIOD-2026-11-05-F', 'seasonA-FIVN-2026-11-05-F', 'seasonA-FROG-2026-11-05-F', 'seasonA-GRND-2026-11-05-F', 'seasonA-HALO-2026-11-05-F', 'seasonA-IONQ-2026-11-05-F', 'seasonA-KRMN-2026-11-05-F', 'seasonA-LYFT-2026-11-05-F', 'seasonA-MARA-2026-11-09-F', 'seasonA-MRNA-2026-11-06-F', 'seasonA-NET-2026-11-05-F', 'seasonA-PCTY-2026-11-05-F', 'seasonA-PDFS-2026-11-05-F', 'seasonA-QBTS-2026-11-10-F', 'seasonA-QLYS-2026-11-09-F', 'seasonA-ROIV-2026-11-09-F', 'seasonA-SANM-2026-11-09-F', 'seasonA-SARO-2026-11-05-F', 'seasonA-SOUN-2026-11-05-F', 'seasonA-TDC-2026-11-05-F', 'seasonA-TDG-2026-11-10-F', 'seasonA-TEAM-2026-11-05-F', 'seasonA-TXG-2026-11-05-F', 'seasonA-TXRH-2026-11-05-F', 'seasonA-UA-2026-11-06-F', 'seasonA-VSAT-2026-11-05-F', 'seasonA-WULF-2026-11-06-F', 'seasonA-ZETA-2026-11-09-F']
- paper/long_ledger.json: stopped by D019 since 2026-11-04T08:39 (registry/D019_reframe_v1.md §1) - no new opens; open positions close under D011's own exits
- paper/long_ledger.json: 35 gate(s) not opened under the D019 stop ['seasonA-ACHR-2026-11-09-L', 'seasonA-ALRM-2026-11-05-L', 'seasonA-ATEN-2026-11-05-L', 'seasonA-AVPT-2026-11-05-L', 'seasonA-AXON-2026-11-05-L', 'seasonA-BILL-2026-11-05-L', 'seasonA-CARG-2026-11-05-L', 'seasonA-DIOD-2026-11-05-L', 'seasonA-FIVN-2026-11-05-L', 'seasonA-FROG-2026-11-05-L', 'seasonA-GRND-2026-11-05-L', 'seasonA-HALO-2026-11-05-L', 'seasonA-IONQ-2026-11-05-L', 'seasonA-KRMN-2026-11-05-L', 'seasonA-LYFT-2026-11-05-L', 'seasonA-MARA-2026-11-09-L', 'seasonA-MRNA-2026-11-06-L', 'seasonA-NET-2026-11-05-L', 'seasonA-PCTY-2026-11-05-L', 'seasonA-PDFS-2026-11-05-L', 'seasonA-QBTS-2026-11-10-L', 'seasonA-QLYS-2026-11-09-L', 'seasonA-ROIV-2026-11-09-L', 'seasonA-SANM-2026-11-09-L', 'seasonA-SARO-2026-11-05-L', 'seasonA-SOUN-2026-11-05-L', 'seasonA-TDC-2026-11-05-L', 'seasonA-TDG-2026-11-10-L', 'seasonA-TEAM-2026-11-05-L', 'seasonA-TXG-2026-11-05-L', 'seasonA-TXRH-2026-11-05-L', 'seasonA-UA-2026-11-06-L', 'seasonA-VSAT-2026-11-05-L', 'seasonA-WULF-2026-11-06-L', 'seasonA-ZETA-2026-11-09-L']
- paper/options: 66 position(s), 3 open order(s) - they match the ledgers
- paper/long: 5 position(s), 0 open order(s) - they match the ledgers
- Mon 09 Nov: 7 snapshot(s) - ATRO, CRWV, FLY, MRCY, RGTI, RUM, STUB
- Tue 10 Nov: 7 snapshot(s) - DGII, DPC, LUNR, MBGL, OCTV, ONDS, TWST
- Wed 11 Nov: 3 snapshot(s) - AMAT, CBRS, CSCO
- Fri 13 Nov: 1 snapshot(s) - INFQ
- seasonA: 9 name(s) still PENDING a confirmed date

