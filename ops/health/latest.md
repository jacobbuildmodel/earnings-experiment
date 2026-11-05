# Health 2026-11-05 10:47 ET - **AMBER** (1 known)

check.py: PASS - 1 warning(s)

## RED - events or decisions being lost, or about to be
- none

## AMBER - look at
- T2R missing: IREN_2026-11-05 (D013 shadow; the budget may have skipped it)
- T2O missing: IREN_2026-11-05 (D013 shadow; the budget may have skipped it)
- T2R missing: WULF_2026-11-06 (D013 shadow; the budget may have skipped it)
- T2O missing: WULF_2026-11-06 (D013 shadow; the budget may have skipped it)
- T2R missing: LYFT_2026-11-05 (D013 shadow; the budget may have skipped it)
- T2O missing: LYFT_2026-11-05 (D013 shadow; the budget may have skipped it)

## KNOWN - acknowledged in ops/health_known.json, reads exactly as acknowledged; not in the status
- paper/options_ledger.json: alerts ['seasonA-DPZ-2026-10-13-F', 'seasonA-CIFR-2026-11-02-F', 'seasonA-BWXT-2026-11-02-F', 'seasonA-DOCN-2026-11-03-F', 'seasonA-BETA-2026-11-03-F', 'seasonA-DT-2026-11-03-F', 'seasonA-IPGP-2026-11-03-F', 'seasonA-LSCC-2026-11-02-F', 'seasonA-MTCH-2026-11-02-F', 'seasonA-ON-2026-11-02-F', 'seasonA-PAY-2026-11-02-F', 'seasonA-PLTR-2026-11-02-F', 'seasonA-SHOP-2026-11-03-F', 'seasonA-VRTX-2026-11-02-F', 'seasonA-VVX-2026-11-02-F', 'seasonA-YUMC-2026-11-03-F'] - DPZ's held_past_expiry flag (set once, never cleared) and 15 gates the 2026-10-28 fill halt blocked, never opened (paper_options_alerts below); the gates the D019 stop blocks are not in this line (health.py reads them as information) (the 15: STATE.md Log 2026-11-02 07:40 ET; the stop: registry/D019_reframe_v1.md §1) (ops/incidents/2026-10-13_DPZ_exit.md; acknowledged 2026-10-28, laptop chat (the new-RED marker owed in STATE.md NOW, 2026-10-27); the 15 gates 2026-11-05, Jacob ("Yes, acknowledge") in the D019 owed-items chat, until 2026-11-06)

## Information
- 22 paper run(s) in 24 h failed only on the D019 stop (halt True, errors 0, every alert acknowledged or a gate the stop blocked), each read from its job logs; newest 2026-11-05T14:48:05Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/42048519765
- paper/options_ledger.json: stopped by D019 since 2026-11-04T08:39 (registry/D019_reframe_v1.md §1) - no new opens; open positions close under D011's own exits
- paper/options_ledger.json: 27 gate(s) not opened under the D019 stop ['seasonA-ALRM-2026-11-05-F', 'seasonA-ATEN-2026-11-05-F', 'seasonA-AVPT-2026-11-05-F', 'seasonA-AXON-2026-11-05-F', 'seasonA-BILL-2026-11-05-F', 'seasonA-CARG-2026-11-05-F', 'seasonA-DIOD-2026-11-05-F', 'seasonA-FIVN-2026-11-05-F', 'seasonA-FROG-2026-11-05-F', 'seasonA-GRND-2026-11-05-F', 'seasonA-HALO-2026-11-05-F', 'seasonA-IONQ-2026-11-05-F', 'seasonA-KRMN-2026-11-05-F', 'seasonA-LYFT-2026-11-05-F', 'seasonA-MRNA-2026-11-06-F', 'seasonA-NET-2026-11-05-F', 'seasonA-PCTY-2026-11-05-F', 'seasonA-PDFS-2026-11-05-F', 'seasonA-SARO-2026-11-05-F', 'seasonA-SOUN-2026-11-05-F', 'seasonA-TDC-2026-11-05-F', 'seasonA-TEAM-2026-11-05-F', 'seasonA-TXG-2026-11-05-F', 'seasonA-TXRH-2026-11-05-F', 'seasonA-UA-2026-11-06-F', 'seasonA-VSAT-2026-11-05-F', 'seasonA-WULF-2026-11-06-F']
- paper/options_ledger.json: open ['seasonA-ACIW-2026-11-05-F', 'seasonA-ACLS-2026-11-05-F', 'seasonA-BROS-2026-11-04-F', 'seasonA-BSY-2026-11-05-F', 'seasonA-CAVA-2026-11-04-F', 'seasonA-CHYM-2026-11-04-F', 'seasonA-CORZ-2026-11-05-F', 'seasonA-CPAY-2026-11-04-F', 'seasonA-SNAP-2026-11-04-F', 'seasonA-U-2026-11-05-F', 'seasonA-VERX-2026-11-04-F', 'seasonA-VIAV-2026-11-04-F']
- paper/long_ledger.json: stopped by D019 since 2026-11-04T08:39 (registry/D019_reframe_v1.md §1) - no new opens; open positions close under D011's own exits
- paper/long_ledger.json: 27 gate(s) not opened under the D019 stop ['seasonA-ALRM-2026-11-05-L', 'seasonA-ATEN-2026-11-05-L', 'seasonA-AVPT-2026-11-05-L', 'seasonA-AXON-2026-11-05-L', 'seasonA-BILL-2026-11-05-L', 'seasonA-CARG-2026-11-05-L', 'seasonA-DIOD-2026-11-05-L', 'seasonA-FIVN-2026-11-05-L', 'seasonA-FROG-2026-11-05-L', 'seasonA-GRND-2026-11-05-L', 'seasonA-HALO-2026-11-05-L', 'seasonA-IONQ-2026-11-05-L', 'seasonA-KRMN-2026-11-05-L', 'seasonA-LYFT-2026-11-05-L', 'seasonA-MRNA-2026-11-06-L', 'seasonA-NET-2026-11-05-L', 'seasonA-PCTY-2026-11-05-L', 'seasonA-PDFS-2026-11-05-L', 'seasonA-SARO-2026-11-05-L', 'seasonA-SOUN-2026-11-05-L', 'seasonA-TDC-2026-11-05-L', 'seasonA-TEAM-2026-11-05-L', 'seasonA-TXG-2026-11-05-L', 'seasonA-TXRH-2026-11-05-L', 'seasonA-UA-2026-11-06-L', 'seasonA-VSAT-2026-11-05-L', 'seasonA-WULF-2026-11-06-L']
- paper/long_ledger.json: open ['seasonA-ACIW-2026-11-05-L', 'seasonA-ACLS-2026-11-05-L', 'seasonA-BROS-2026-11-04-L', 'seasonA-BSY-2026-11-05-L', 'seasonA-CAVA-2026-11-04-L', 'seasonA-CHYM-2026-11-04-L', 'seasonA-CORZ-2026-11-05-L', 'seasonA-CPAY-2026-11-04-L', 'seasonA-CRUS-2026-11-04-L', 'seasonA-CW-2026-11-04-L', 'seasonA-DCO-2026-11-05-L', 'seasonA-EW-2026-11-04-L', 'seasonA-FICO-2026-11-04-L', 'seasonA-FIG-2026-11-04-L', 'seasonA-FOUR-2026-11-05-L', 'seasonA-KVYO-2026-11-04-L', 'seasonA-LOAR-2026-11-05-L', 'seasonA-MELI-2026-11-04-L', 'seasonA-MTSI-2026-11-05-L', 'seasonA-NTCT-2026-11-05-L', 'seasonA-ONC-2026-11-05-L', 'seasonA-OTEX-2026-11-05-L', 'seasonA-PAYC-2026-11-04-L', 'seasonA-POWI-2026-11-04-L', 'seasonA-PTRN-2026-11-04-L']
- paper/options: CHYM: the account holds +0, the ledgers show +62 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: CORZ: the account holds +0, the ledgers show +137 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: FOUR: the account holds +0, the ledgers show +32 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: IREN: the account holds +69, the ledgers show +0 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: KVYO: the account holds +0, the ledgers show +57 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: LYFT: the account holds +132, the ledgers show +0 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: QCOM: the account holds +0, the ledgers show +16 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: SNAP: the account holds +0, the ledgers show +307 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: WULF: the account holds +184, the ledgers show +0 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: Z: the account holds +0, the ledgers show +54 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: ['seasonA-CHYM-2026-11-04-sell', 'seasonA-CORZ-2026-11-05-sell', 'seasonA-FOUR-2026-11-05-sell', 'seasonA-KVYO-2026-11-04-sell', 'seasonA-QCOM-2026-11-04-sell', 'seasonA-SNAP-2026-11-04-sell', 'seasonA-Z-2026-11-04-sell', 'seasonA-IREN-2026-11-05-buy', 'seasonA-LYFT-2026-11-05-buy', 'seasonA-WULF-2026-11-06-buy'] live in the ledger, no longer open at Alpaca (the next paper run records how they ended)
- paper/options: 119 position(s), 0 open order(s) - they match the ledgers
- paper/long: 56 position(s), 0 open order(s) - they match the ledgers
- Thu 05 Nov: 2 snapshot(s) - ROIV, VIA
- Fri 06 Nov: 10 snapshot(s) - ACHR, ASTS, CSQR, MARA, ONTO, QBTS, QLYS, SANM, TDG, ZETA
- Mon 09 Nov: 7 snapshot(s) - ATRO, CRWV, FLY, MRCY, RGTI, RUM, STUB
- Tue 10 Nov: 7 snapshot(s) - DGII, DPC, LUNR, MBGL, OCTV, ONDS, TWST
- Wed 11 Nov: 3 snapshot(s) - AMAT, CBRS, CSCO
- seasonA: 16 name(s) still PENDING a confirmed date

