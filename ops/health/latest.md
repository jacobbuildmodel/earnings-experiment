# Health 2026-11-13 06:26 ET - **AMBER**

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
- T2R missing: CBRS_2026-11-12 (D013 shadow; the budget may have skipped it)
- T2O missing: CBRS_2026-11-12 (D013 shadow; the budget may have skipped it)
- T2R missing: MARA_2026-11-09 (D013 shadow; the budget may have skipped it)
- T2O missing: MARA_2026-11-09 (D013 shadow; the budget may have skipped it)
- T2R missing: CSCO_2026-11-12 (D013 shadow; the budget may have skipped it)
- T2O missing: CSCO_2026-11-12 (D013 shadow; the budget may have skipped it)
- T2R missing: RGTI_2026-11-10 (D013 shadow; the budget may have skipped it)
- T2O missing: RGTI_2026-11-10 (D013 shadow; the budget may have skipped it)
- Actions failure: Earnings experiment - paper options at 2026-11-13T03:04:17Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/43356446081
- Actions failure: Earnings experiment - paper options at 2026-11-13T00:55:52Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/43340963662
- Actions failure: Earnings experiment - paper options at 2026-11-12T23:56:14Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/43332971820
- Actions failure: Earnings experiment - paper options at 2026-11-12T23:44:26Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/43331371699
- Actions failure: Earnings experiment - paper options at 2026-11-12T23:28:12Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/43329112234
- Actions failure: Earnings experiment - paper options at 2026-11-12T23:27:28Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/43329013364
- Actions failure: Earnings experiment - paper options at 2026-11-12T22:39:55Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/43321980919
- Actions failure: Earnings experiment - paper options at 2026-11-12T22:11:26Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/43317573434
- Actions failure: Earnings experiment - paper options at 2026-11-12T21:48:28Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/43313858938
- Actions failure: Earnings experiment - paper options at 2026-11-12T21:34:54Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/43311653880
- Actions failure: Earnings experiment - paper options at 2026-11-12T15:46:45Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/43251469236
- Actions failure: Earnings experiment - paper window runner (routine push) at 2026-11-12T15:46:30Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/43251426154
- Actions failure: Earnings experiment - paper options at 2026-11-12T15:45:23Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/43251224537
- Actions failure: Earnings experiment - paper options at 2026-11-12T14:46:39Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/43240711676
- Actions failure: Earnings experiment - paper options at 2026-11-12T14:45:46Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/43240556733
- paper/options_ledger.json: alerts ['seasonA-DPZ-2026-10-13-F', 'seasonA-CIFR-2026-11-02-F', 'seasonA-BWXT-2026-11-02-F', 'seasonA-DOCN-2026-11-03-F', 'seasonA-BETA-2026-11-03-F', 'seasonA-DT-2026-11-03-F', 'seasonA-IPGP-2026-11-03-F', 'seasonA-LSCC-2026-11-02-F', 'seasonA-MTCH-2026-11-02-F', 'seasonA-ON-2026-11-02-F', 'seasonA-PAY-2026-11-02-F', 'seasonA-PLTR-2026-11-02-F', 'seasonA-SHOP-2026-11-03-F', 'seasonA-VRTX-2026-11-02-F', 'seasonA-VVX-2026-11-02-F', 'seasonA-YUMC-2026-11-03-F']

## KNOWN - acknowledged in ops/health_known.json, reads exactly as acknowledged; not in the status
- none

## Information
- ops/health_known.json: paper/options_ledger.json: alerts ['seasonA-DPZ-2026-10-13-F', 'seasonA-CIFR-2026-11-02-F', 'seasonA-BWXT-2026-11-02-F', 'seasonA-DOCN-2026-11-03-F', 'seasonA-BETA-2026-11-03-F', 'seasonA-DT-2026-11-03-F', 'seasonA-IPGP-2026-11-03-F', 'seasonA-LSCC-2026-11-02-F', 'seasonA-MTCH-2026-11-02-F', 'seasonA-ON-2026-11-02-F', 'seasonA-PAY-2026-11-02-F', 'seasonA-PLTR-2026-11-02-F', 'seasonA-SHOP-2026-11-03-F', 'seasonA-VRTX-2026-11-02-F', 'seasonA-VVX-2026-11-02-F', 'seasonA-YUMC-2026-11-03-F'] lapsed on 2026-11-06 - it alarms again until re-acknowledged
- ops/health_known.json: seasonA-DPZ-2026-10-13-F lapsed on 2026-11-06 - it alarms again until re-acknowledged
- 14 paper run(s) in 24 h failed only on the D019 stop (halt True, errors 0, every alert acknowledged or a gate the stop blocked), each read from its job logs; newest 2026-11-13T03:04:17Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/43356446112
- paper/options_ledger.json: stopped by D019 since 2026-11-04T08:39 (registry/D019_reframe_v1.md §1) - no new opens; open positions close under D011's own exits
- paper/options_ledger.json: 49 gate(s) not opened under the D019 stop ['seasonA-ACHR-2026-11-09-F', 'seasonA-ALRM-2026-11-05-F', 'seasonA-AMAT-2026-11-12-F', 'seasonA-ATEN-2026-11-05-F', 'seasonA-ATRO-2026-11-10-F', 'seasonA-AVPT-2026-11-05-F', 'seasonA-AXON-2026-11-05-F', 'seasonA-BILL-2026-11-05-F', 'seasonA-CARG-2026-11-05-F', 'seasonA-CBRS-2026-11-12-F', 'seasonA-CRWV-2026-11-10-F', 'seasonA-CSCO-2026-11-12-F', 'seasonA-DIOD-2026-11-05-F', 'seasonA-FIVN-2026-11-05-F', 'seasonA-FLY-2026-11-10-F', 'seasonA-FROG-2026-11-05-F', 'seasonA-GRND-2026-11-05-F', 'seasonA-HALO-2026-11-05-F', 'seasonA-IONQ-2026-11-05-F', 'seasonA-KRMN-2026-11-05-F', 'seasonA-LUNR-2026-11-12-F', 'seasonA-LYFT-2026-11-05-F', 'seasonA-MARA-2026-11-09-F', 'seasonA-MBGL-2026-11-12-F', 'seasonA-MRCY-2026-11-10-F', 'seasonA-MRNA-2026-11-06-F', 'seasonA-NET-2026-11-05-F', 'seasonA-OCTV-2026-11-12-F', 'seasonA-ONDS-2026-11-12-F', 'seasonA-PCTY-2026-11-05-F', 'seasonA-PDFS-2026-11-05-F', 'seasonA-QBTS-2026-11-10-F', 'seasonA-QLYS-2026-11-09-F', 'seasonA-RGTI-2026-11-10-F', 'seasonA-ROIV-2026-11-09-F', 'seasonA-RUM-2026-11-11-F', 'seasonA-SANM-2026-11-09-F', 'seasonA-SARO-2026-11-05-F', 'seasonA-SOUN-2026-11-05-F', 'seasonA-STUB-2026-11-10-F', 'seasonA-TDC-2026-11-05-F', 'seasonA-TDG-2026-11-10-F', 'seasonA-TEAM-2026-11-05-F', 'seasonA-TXG-2026-11-05-F', 'seasonA-TXRH-2026-11-05-F', 'seasonA-UA-2026-11-06-F', 'seasonA-VSAT-2026-11-05-F', 'seasonA-WULF-2026-11-06-F', 'seasonA-ZETA-2026-11-09-F']
- paper/long_ledger.json: stopped by D019 since 2026-11-04T08:39 (registry/D019_reframe_v1.md §1) - no new opens; open positions close under D011's own exits
- paper/long_ledger.json: 49 gate(s) not opened under the D019 stop ['seasonA-ACHR-2026-11-09-L', 'seasonA-ALRM-2026-11-05-L', 'seasonA-AMAT-2026-11-12-L', 'seasonA-ATEN-2026-11-05-L', 'seasonA-ATRO-2026-11-10-L', 'seasonA-AVPT-2026-11-05-L', 'seasonA-AXON-2026-11-05-L', 'seasonA-BILL-2026-11-05-L', 'seasonA-CARG-2026-11-05-L', 'seasonA-CBRS-2026-11-12-L', 'seasonA-CRWV-2026-11-10-L', 'seasonA-CSCO-2026-11-12-L', 'seasonA-DIOD-2026-11-05-L', 'seasonA-FIVN-2026-11-05-L', 'seasonA-FLY-2026-11-10-L', 'seasonA-FROG-2026-11-05-L', 'seasonA-GRND-2026-11-05-L', 'seasonA-HALO-2026-11-05-L', 'seasonA-IONQ-2026-11-05-L', 'seasonA-KRMN-2026-11-05-L', 'seasonA-LUNR-2026-11-12-L', 'seasonA-LYFT-2026-11-05-L', 'seasonA-MARA-2026-11-09-L', 'seasonA-MBGL-2026-11-12-L', 'seasonA-MRCY-2026-11-10-L', 'seasonA-MRNA-2026-11-06-L', 'seasonA-NET-2026-11-05-L', 'seasonA-OCTV-2026-11-12-L', 'seasonA-ONDS-2026-11-12-L', 'seasonA-PCTY-2026-11-05-L', 'seasonA-PDFS-2026-11-05-L', 'seasonA-QBTS-2026-11-10-L', 'seasonA-QLYS-2026-11-09-L', 'seasonA-RGTI-2026-11-10-L', 'seasonA-ROIV-2026-11-09-L', 'seasonA-RUM-2026-11-11-L', 'seasonA-SANM-2026-11-09-L', 'seasonA-SARO-2026-11-05-L', 'seasonA-SOUN-2026-11-05-L', 'seasonA-STUB-2026-11-10-L', 'seasonA-TDC-2026-11-05-L', 'seasonA-TDG-2026-11-10-L', 'seasonA-TEAM-2026-11-05-L', 'seasonA-TXG-2026-11-05-L', 'seasonA-TXRH-2026-11-05-L', 'seasonA-UA-2026-11-06-L', 'seasonA-VSAT-2026-11-05-L', 'seasonA-WULF-2026-11-06-L', 'seasonA-ZETA-2026-11-09-L']
- paper/options: 68 position(s), 2 open order(s) - they match the ledgers
- paper/long: 5 position(s), 0 open order(s) - they match the ledgers
- Fri 13 Nov: 1 snapshot(s) - INFQ
- Mon 16 Nov: 2 snapshot(s) - NVDA, TJX
- Tue 17 Nov: 5 snapshot(s) - BBWI, KLIC, P, PANW, WWD
- Wed 18 Nov: 4 snapshot(s) - ESTC, GAP, INTU, ROST
- seasonA: 2 name(s) still PENDING a confirmed date

