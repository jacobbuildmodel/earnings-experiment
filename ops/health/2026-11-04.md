# Health 2026-11-04 22:34 ET - **AMBER**

check.py: PASS - 1 warning(s)

## RED - events or decisions being lost, or about to be
- none

## AMBER - look at
- Actions failure: Earnings experiment - paper options at 2026-11-05T03:11:14Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41959990961
- Actions failure: Earnings experiment - paper options at 2026-11-05T00:45:51Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41943735920
- Actions failure: Earnings experiment - paper options at 2026-11-05T00:04:02Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41938520468
- Actions failure: Earnings experiment - paper options at 2026-11-04T23:51:09Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41936927688
- Actions failure: Earnings experiment - paper options at 2026-11-04T23:32:17Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41934495038
- Actions failure: Earnings experiment - paper options at 2026-11-04T23:31:20Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41934365752
- Actions failure: Earnings experiment - paper options at 2026-11-04T22:30:18Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41925835034
- Actions failure: Earnings experiment - paper options at 2026-11-04T21:48:24Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41919490365
- Actions failure: Earnings experiment - paper options at 2026-11-04T21:14:03Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41914151961
- Actions failure: Earnings experiment - paper options at 2026-11-04T20:55:14Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41911148453
- Actions failure: Earnings experiment - paper window runner (routine push) at 2026-11-04T15:46:12Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41861174301
- Actions failure: Earnings experiment - paper options at 2026-11-04T14:47:04Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41851017921
- Actions failure: Earnings experiment - paper window runner (routine push) at 2026-11-04T14:46:33Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41850934058
- paper/options_ledger.json: alerts ['seasonA-DPZ-2026-10-13-F', 'seasonA-CIFR-2026-11-02-F', 'seasonA-BWXT-2026-11-02-F', 'seasonA-DOCN-2026-11-03-F', 'seasonA-BETA-2026-11-03-F', 'seasonA-DT-2026-11-03-F', 'seasonA-IPGP-2026-11-03-F', 'seasonA-LSCC-2026-11-02-F', 'seasonA-MTCH-2026-11-02-F', 'seasonA-ON-2026-11-02-F', 'seasonA-PAY-2026-11-02-F', 'seasonA-PLTR-2026-11-02-F', 'seasonA-SHOP-2026-11-03-F', 'seasonA-VRTX-2026-11-02-F', 'seasonA-VVX-2026-11-02-F', 'seasonA-YUMC-2026-11-03-F']

## KNOWN - acknowledged in ops/health_known.json, reads exactly as acknowledged; not in the status
- none

## Information
- LYFT_2026-11-05: T2 deadline Thu 05 Nov 09:15 ET - frozen so far: T2, T2G
- WULF_2026-11-06: T2 deadline Thu 05 Nov 09:15 ET - frozen so far: T2, T2G
- IREN_2026-11-05: T2 deadline Thu 05 Nov 09:15 ET - frozen so far: T2, T2G
- 11 paper run(s) in 24 h failed only on the D019 stop (halt True, errors 0, every alert acknowledged or a gate the stop blocked), each read from its job logs; newest 2026-11-05T03:11:14Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/41959990775
- paper/options_ledger.json: stopped by D019 since 2026-11-04T08:39 (registry/D019_reframe_v1.md §1) - no new opens; open positions close under D011's own exits
- paper/options_ledger.json: 27 gate(s) not opened under the D019 stop ['seasonA-ALRM-2026-11-05-F', 'seasonA-ATEN-2026-11-05-F', 'seasonA-AVPT-2026-11-05-F', 'seasonA-AXON-2026-11-05-F', 'seasonA-BILL-2026-11-05-F', 'seasonA-CARG-2026-11-05-F', 'seasonA-DIOD-2026-11-05-F', 'seasonA-FIVN-2026-11-05-F', 'seasonA-FROG-2026-11-05-F', 'seasonA-GRND-2026-11-05-F', 'seasonA-HALO-2026-11-05-F', 'seasonA-IONQ-2026-11-05-F', 'seasonA-KRMN-2026-11-05-F', 'seasonA-LYFT-2026-11-05-F', 'seasonA-MRNA-2026-11-06-F', 'seasonA-NET-2026-11-05-F', 'seasonA-PCTY-2026-11-05-F', 'seasonA-PDFS-2026-11-05-F', 'seasonA-SARO-2026-11-05-F', 'seasonA-SOUN-2026-11-05-F', 'seasonA-TDC-2026-11-05-F', 'seasonA-TEAM-2026-11-05-F', 'seasonA-TXG-2026-11-05-F', 'seasonA-TXRH-2026-11-05-F', 'seasonA-UA-2026-11-06-F', 'seasonA-VSAT-2026-11-05-F', 'seasonA-WULF-2026-11-06-F']
- paper/options_ledger.json: open ['seasonA-ACIW-2026-11-05-F', 'seasonA-ACLS-2026-11-05-F', 'seasonA-BROS-2026-11-04-F', 'seasonA-BSY-2026-11-05-F', 'seasonA-CAVA-2026-11-04-F', 'seasonA-CHYM-2026-11-04-F', 'seasonA-CORZ-2026-11-05-F', 'seasonA-CPAY-2026-11-04-F', 'seasonA-SNAP-2026-11-04-F', 'seasonA-U-2026-11-05-F', 'seasonA-VERX-2026-11-04-F', 'seasonA-VIAV-2026-11-04-F']
- paper/long_ledger.json: stopped by D019 since 2026-11-04T08:39 (registry/D019_reframe_v1.md §1) - no new opens; open positions close under D011's own exits
- paper/long_ledger.json: 27 gate(s) not opened under the D019 stop ['seasonA-ALRM-2026-11-05-L', 'seasonA-ATEN-2026-11-05-L', 'seasonA-AVPT-2026-11-05-L', 'seasonA-AXON-2026-11-05-L', 'seasonA-BILL-2026-11-05-L', 'seasonA-CARG-2026-11-05-L', 'seasonA-DIOD-2026-11-05-L', 'seasonA-FIVN-2026-11-05-L', 'seasonA-FROG-2026-11-05-L', 'seasonA-GRND-2026-11-05-L', 'seasonA-HALO-2026-11-05-L', 'seasonA-IONQ-2026-11-05-L', 'seasonA-KRMN-2026-11-05-L', 'seasonA-LYFT-2026-11-05-L', 'seasonA-MRNA-2026-11-06-L', 'seasonA-NET-2026-11-05-L', 'seasonA-PCTY-2026-11-05-L', 'seasonA-PDFS-2026-11-05-L', 'seasonA-SARO-2026-11-05-L', 'seasonA-SOUN-2026-11-05-L', 'seasonA-TDC-2026-11-05-L', 'seasonA-TEAM-2026-11-05-L', 'seasonA-TXG-2026-11-05-L', 'seasonA-TXRH-2026-11-05-L', 'seasonA-UA-2026-11-06-L', 'seasonA-VSAT-2026-11-05-L', 'seasonA-WULF-2026-11-06-L']
- paper/long_ledger.json: open ['seasonA-ACIW-2026-11-05-L', 'seasonA-ACLS-2026-11-05-L', 'seasonA-BROS-2026-11-04-L', 'seasonA-BSY-2026-11-05-L', 'seasonA-CAVA-2026-11-04-L', 'seasonA-CHYM-2026-11-04-L', 'seasonA-CORZ-2026-11-05-L', 'seasonA-CPAY-2026-11-04-L', 'seasonA-CRUS-2026-11-04-L', 'seasonA-CW-2026-11-04-L', 'seasonA-DCO-2026-11-05-L', 'seasonA-EW-2026-11-04-L', 'seasonA-FICO-2026-11-04-L', 'seasonA-FIG-2026-11-04-L', 'seasonA-FOUR-2026-11-05-L', 'seasonA-KVYO-2026-11-04-L', 'seasonA-LOAR-2026-11-05-L', 'seasonA-MELI-2026-11-04-L', 'seasonA-MTSI-2026-11-05-L', 'seasonA-NTCT-2026-11-05-L', 'seasonA-ONC-2026-11-05-L', 'seasonA-OTEX-2026-11-05-L', 'seasonA-PAYC-2026-11-04-L', 'seasonA-POWI-2026-11-04-L', 'seasonA-PTRN-2026-11-04-L']
- paper window (options): paper-window-push.yml afternoon step since 12:00 ET (done)
- paper window (long): paper-window-push.yml afternoon step since 12:00 ET (done)
- paper/options: 123 position(s), 10 open order(s) - they match the ledgers
- paper/long: 56 position(s), 0 open order(s) - they match the ledgers
- Wed 04 Nov: 35 snapshot(s) - AKAM, ALRM, ATEN, AVPT, AXON, BILL, CARG, CART, DBX, DIOD, FIGS, FIVN, FROG, GRND, HALO, IONQ, IREN, KRMN, LASR, LITE, LYFT, MRNA, NET, PCTY, PDFS, QNT, SARO, SOUN, TDC, TEAM, TXG, TXRH, UA, VSAT, WULF
- Thu 05 Nov: 2 snapshot(s) - ROIV, VIA
- Fri 06 Nov: 10 snapshot(s) - ACHR, ASTS, CSQR, MARA, ONTO, QBTS, QLYS, SANM, TDG, ZETA
- Mon 09 Nov: 7 snapshot(s) - ATRO, CRWV, FLY, MRCY, RGTI, RUM, STUB
- Tue 10 Nov: 7 snapshot(s) - DGII, DPC, LUNR, MBGL, OCTV, ONDS, TWST
- seasonA: 27 name(s) still PENDING a confirmed date

