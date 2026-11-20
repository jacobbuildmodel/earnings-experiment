# Health 2026-11-20 07:03 ET - **RED**

check.py: PASS - 1 warning(s)

## RED - events or decisions being lost, or about to be
- DATES STALE (seasonA): no date confirmed or retired since Fri 13 Nov 07:38 ET (over 30 h), while 1 PENDING name(s) have a calendar date within 7 days, 1 within 3 sessions ['BKE']; newest re-check Thu 19 Nov 22:47 ET - the re-checks run but confirm nothing

## AMBER - look at
- T2R missing: GAP_2026-11-19 (D013 shadow; the budget may have skipped it)
- T2O missing: GAP_2026-11-19 (D013 shadow; the budget may have skipped it)
- T2R missing: NVDA_2026-11-17 (D013 shadow; the budget may have skipped it)
- T2O missing: NVDA_2026-11-17 (D013 shadow; the budget may have skipped it)
- T2R missing: PANW_2026-11-18 (D013 shadow; the budget may have skipped it)
- T2O missing: PANW_2026-11-18 (D013 shadow; the budget may have skipped it)
- Actions failure: Earnings experiment - paper options at 2026-11-20T03:49:31Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/44670303800
- Actions failure: Earnings experiment - paper options at 2026-11-20T01:41:35Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/44655459764
- Actions failure: Earnings experiment - paper options at 2026-11-20T00:58:38Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/44650082924
- Actions failure: Earnings experiment - paper options at 2026-11-20T00:45:37Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/44648398930
- Actions failure: Earnings experiment - paper options at 2026-11-20T00:32:24Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/44646668053
- Actions failure: Earnings experiment - paper options at 2026-11-20T00:31:53Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/44646598329
- Actions failure: Earnings experiment - paper options at 2026-11-19T23:27:57Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/44637872031
- Actions failure: Earnings experiment - paper options at 2026-11-19T23:00:01Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/44633726119
- Actions failure: Earnings experiment - paper options at 2026-11-19T22:38:11Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/44630470595
- Actions failure: Earnings experiment - paper options at 2026-11-19T22:25:53Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/44628550190
- Actions failure: Earnings experiment - paper options at 2026-11-19T15:48:25Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/44558942535
- Actions failure: Earnings experiment - paper window runner (routine push) at 2026-11-19T15:46:11Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/44558531303
- Actions failure: Earnings experiment - paper options at 2026-11-19T14:46:37Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/44547420123
- paper/options_ledger.json: alerts ['seasonA-DPZ-2026-10-13-F', 'seasonA-CIFR-2026-11-02-F', 'seasonA-BWXT-2026-11-02-F', 'seasonA-DOCN-2026-11-03-F', 'seasonA-BETA-2026-11-03-F', 'seasonA-DT-2026-11-03-F', 'seasonA-IPGP-2026-11-03-F', 'seasonA-LSCC-2026-11-02-F', 'seasonA-MTCH-2026-11-02-F', 'seasonA-ON-2026-11-02-F', 'seasonA-PAY-2026-11-02-F', 'seasonA-PLTR-2026-11-02-F', 'seasonA-SHOP-2026-11-03-F', 'seasonA-VRTX-2026-11-02-F', 'seasonA-VVX-2026-11-02-F', 'seasonA-YUMC-2026-11-03-F']

## KNOWN - acknowledged in ops/health_known.json, reads exactly as acknowledged; not in the status
- none

## Information
- ops/health_known.json: paper/options_ledger.json: alerts ['seasonA-DPZ-2026-10-13-F', 'seasonA-CIFR-2026-11-02-F', 'seasonA-BWXT-2026-11-02-F', 'seasonA-DOCN-2026-11-03-F', 'seasonA-BETA-2026-11-03-F', 'seasonA-DT-2026-11-03-F', 'seasonA-IPGP-2026-11-03-F', 'seasonA-LSCC-2026-11-02-F', 'seasonA-MTCH-2026-11-02-F', 'seasonA-ON-2026-11-02-F', 'seasonA-PAY-2026-11-02-F', 'seasonA-PLTR-2026-11-02-F', 'seasonA-SHOP-2026-11-03-F', 'seasonA-VRTX-2026-11-02-F', 'seasonA-VVX-2026-11-02-F', 'seasonA-YUMC-2026-11-03-F'] lapsed on 2026-11-06 - it alarms again until re-acknowledged
- ops/health_known.json: seasonA-DPZ-2026-10-13-F lapsed on 2026-11-06 - it alarms again until re-acknowledged
- 12 paper run(s) in 24 h failed only on the D019 stop (halt True, errors 0, every alert acknowledged or a gate the stop blocked), each read from its job logs; newest 2026-11-20T03:49:31Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/44670303789
- paper/options_ledger.json: stopped by D019 since 2026-11-04T08:39 (registry/D019_reframe_v1.md §1) - no new opens; open positions close under D011's own exits
- paper/options_ledger.json: 62 gate(s) not opened under the D019 stop ['seasonA-ACHR-2026-11-09-F', 'seasonA-ALRM-2026-11-05-F', 'seasonA-AMAT-2026-11-12-F', 'seasonA-ATEN-2026-11-05-F', 'seasonA-ATRO-2026-11-10-F', 'seasonA-AVPT-2026-11-05-F', 'seasonA-AXON-2026-11-05-F', 'seasonA-BBWI-2026-11-19-F', 'seasonA-BILL-2026-11-05-F', 'seasonA-CARG-2026-11-05-F', 'seasonA-CBRS-2026-11-12-F', 'seasonA-CRWV-2026-11-10-F', 'seasonA-CSCO-2026-11-12-F', 'seasonA-DIOD-2026-11-05-F', 'seasonA-ESTC-2026-11-19-F', 'seasonA-FIVN-2026-11-05-F', 'seasonA-FLY-2026-11-10-F', 'seasonA-FROG-2026-11-05-F', 'seasonA-GAP-2026-11-19-F', 'seasonA-GRND-2026-11-05-F', 'seasonA-HALO-2026-11-05-F', 'seasonA-INFQ-2026-11-16-F', 'seasonA-INTU-2026-11-19-F', 'seasonA-IONQ-2026-11-05-F', 'seasonA-KLIC-2026-11-18-F', 'seasonA-KRMN-2026-11-05-F', 'seasonA-LUNR-2026-11-12-F', 'seasonA-LYFT-2026-11-05-F', 'seasonA-MARA-2026-11-09-F', 'seasonA-MBGL-2026-11-12-F', 'seasonA-MRCY-2026-11-10-F', 'seasonA-MRNA-2026-11-06-F', 'seasonA-NET-2026-11-05-F', 'seasonA-NVDA-2026-11-17-F', 'seasonA-OCTV-2026-11-12-F', 'seasonA-ONDS-2026-11-12-F', 'seasonA-P-2026-11-18-F', 'seasonA-PANW-2026-11-18-F', 'seasonA-PCTY-2026-11-05-F', 'seasonA-PDFS-2026-11-05-F', 'seasonA-QBTS-2026-11-10-F', 'seasonA-QLYS-2026-11-09-F', 'seasonA-RGTI-2026-11-10-F', 'seasonA-ROIV-2026-11-09-F', 'seasonA-ROST-2026-11-19-F', 'seasonA-RUM-2026-11-11-F', 'seasonA-SANM-2026-11-09-F', 'seasonA-SARO-2026-11-05-F', 'seasonA-SOUN-2026-11-05-F', 'seasonA-STUB-2026-11-10-F', 'seasonA-TDC-2026-11-05-F', 'seasonA-TDG-2026-11-10-F', 'seasonA-TEAM-2026-11-05-F', 'seasonA-TJX-2026-11-18-F', 'seasonA-TXG-2026-11-05-F', 'seasonA-TXRH-2026-11-05-F', 'seasonA-UA-2026-11-06-F', 'seasonA-VSAT-2026-11-05-F', 'seasonA-WSM-2026-11-19-F', 'seasonA-WULF-2026-11-06-F', 'seasonA-WWD-2026-11-18-F', 'seasonA-ZETA-2026-11-09-F']
- paper/long_ledger.json: stopped by D019 since 2026-11-04T08:39 (registry/D019_reframe_v1.md §1) - no new opens; open positions close under D011's own exits
- paper/long_ledger.json: 62 gate(s) not opened under the D019 stop ['seasonA-ACHR-2026-11-09-L', 'seasonA-ALRM-2026-11-05-L', 'seasonA-AMAT-2026-11-12-L', 'seasonA-ATEN-2026-11-05-L', 'seasonA-ATRO-2026-11-10-L', 'seasonA-AVPT-2026-11-05-L', 'seasonA-AXON-2026-11-05-L', 'seasonA-BBWI-2026-11-19-L', 'seasonA-BILL-2026-11-05-L', 'seasonA-CARG-2026-11-05-L', 'seasonA-CBRS-2026-11-12-L', 'seasonA-CRWV-2026-11-10-L', 'seasonA-CSCO-2026-11-12-L', 'seasonA-DIOD-2026-11-05-L', 'seasonA-ESTC-2026-11-19-L', 'seasonA-FIVN-2026-11-05-L', 'seasonA-FLY-2026-11-10-L', 'seasonA-FROG-2026-11-05-L', 'seasonA-GAP-2026-11-19-L', 'seasonA-GRND-2026-11-05-L', 'seasonA-HALO-2026-11-05-L', 'seasonA-INFQ-2026-11-16-L', 'seasonA-INTU-2026-11-19-L', 'seasonA-IONQ-2026-11-05-L', 'seasonA-KLIC-2026-11-18-L', 'seasonA-KRMN-2026-11-05-L', 'seasonA-LUNR-2026-11-12-L', 'seasonA-LYFT-2026-11-05-L', 'seasonA-MARA-2026-11-09-L', 'seasonA-MBGL-2026-11-12-L', 'seasonA-MRCY-2026-11-10-L', 'seasonA-MRNA-2026-11-06-L', 'seasonA-NET-2026-11-05-L', 'seasonA-NVDA-2026-11-17-L', 'seasonA-OCTV-2026-11-12-L', 'seasonA-ONDS-2026-11-12-L', 'seasonA-P-2026-11-18-L', 'seasonA-PANW-2026-11-18-L', 'seasonA-PCTY-2026-11-05-L', 'seasonA-PDFS-2026-11-05-L', 'seasonA-QBTS-2026-11-10-L', 'seasonA-QLYS-2026-11-09-L', 'seasonA-RGTI-2026-11-10-L', 'seasonA-ROIV-2026-11-09-L', 'seasonA-ROST-2026-11-19-L', 'seasonA-RUM-2026-11-11-L', 'seasonA-SANM-2026-11-09-L', 'seasonA-SARO-2026-11-05-L', 'seasonA-SOUN-2026-11-05-L', 'seasonA-STUB-2026-11-10-L', 'seasonA-TDC-2026-11-05-L', 'seasonA-TDG-2026-11-10-L', 'seasonA-TEAM-2026-11-05-L', 'seasonA-TJX-2026-11-18-L', 'seasonA-TXG-2026-11-05-L', 'seasonA-TXRH-2026-11-05-L', 'seasonA-UA-2026-11-06-L', 'seasonA-VSAT-2026-11-05-L', 'seasonA-WSM-2026-11-19-L', 'seasonA-WULF-2026-11-06-L', 'seasonA-WWD-2026-11-18-L', 'seasonA-ZETA-2026-11-09-L']
- paper/options: 67 position(s), 1 open order(s) - they match the ledgers
- paper/long: 5 position(s), 0 open order(s) - they match the ledgers
- seasonA: 1 name(s) still PENDING a confirmed date

