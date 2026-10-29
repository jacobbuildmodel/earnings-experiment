# Health 2026-10-29 11:49 ET - **RED** (1 known)

check.py: PASS - 1 warning(s)

## RED - events or decisions being lost, or about to be
- paper/options_ledger.json: HALT - fill anomaly - new opens stopped until a person clears 'halt' in the ledger

## AMBER - look at
- Actions failure: Earnings experiment - paper options at 2026-10-29T02:21:24Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/40805850883
- Actions failure: Earnings experiment - paper options at 2026-10-28T23:54:49Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/40790558595
- Actions failure: Earnings experiment - paper options at 2026-10-28T22:55:28Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/40783606768
- Actions failure: Earnings experiment - paper options at 2026-10-28T22:44:20Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/40782242970
- Actions failure: Earnings experiment - paper options at 2026-10-28T22:28:11Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/40780197012
- Actions failure: Earnings experiment - paper options at 2026-10-28T22:27:50Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/40780152378
- Actions failure: Earnings experiment - paper options at 2026-10-28T21:35:02Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/40773147412
- Actions failure: Earnings experiment - paper options at 2026-10-28T20:56:49Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/40767739562
- Actions failure: Earnings experiment - paper options at 2026-10-28T20:11:35Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/40761051169
- Actions failure: Earnings experiment - paper options at 2026-10-28T19:51:12Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/40758009140

## KNOWN - acknowledged in ops/health_known.json, reads exactly as acknowledged; not in the status
- paper/options_ledger.json: alerts ['seasonA-DPZ-2026-10-13-F'] - the DPZ trade's flag held_past_expiry is set once and never cleared (pipeline/paper_options.py, hash-locked); no other alert is on the ledger (ops/incidents/2026-10-13_DPZ_exit.md; acknowledged 2026-10-28, laptop chat (the new-RED marker owed in STATE.md NOW, 2026-10-27), until 2026-11-06)

## Information
- paper/options_ledger.json: open ['seasonA-ALNY-2026-10-29-F', 'seasonA-ARXS-2026-10-28-F', 'seasonA-BDC-2026-10-29-F', 'seasonA-BHE-2026-10-28-F', 'seasonA-BOOT-2026-10-28-F', 'seasonA-CMG-2026-10-28-F', 'seasonA-COHU-2026-10-28-F', 'seasonA-CROX-2026-10-29-F', 'seasonA-ENTG-2026-10-29-F', 'seasonA-FTAI-2026-10-29-F', 'seasonA-GEN-2026-10-28-F', 'seasonA-AMZN-2026-10-29-F', 'seasonA-AXTI-2026-10-29-F', 'seasonA-BBIO-2026-10-29-F', 'seasonA-COLM-2026-10-29-F', 'seasonA-EXEL-2026-10-29-F', 'seasonA-GD-2026-10-30-F', 'seasonA-INTC-2026-10-29-F', 'seasonA-MSTR-2026-10-29-F', 'seasonA-PINS-2026-10-29-F', 'seasonA-RDDT-2026-10-29-F', 'seasonA-SBUX-2026-10-29-F']
- paper/long_ledger.json: open ['seasonA-ALNY-2026-10-29-L', 'seasonA-BDC-2026-10-29-L', 'seasonA-BHE-2026-10-28-L', 'seasonA-BOOT-2026-10-28-L', 'seasonA-CMG-2026-10-28-L', 'seasonA-COHU-2026-10-28-L', 'seasonA-CROX-2026-10-29-L', 'seasonA-ENTG-2026-10-29-L', 'seasonA-FTAI-2026-10-29-L', 'seasonA-FTNT-2026-10-28-L', 'seasonA-GEN-2026-10-28-L', 'seasonA-GOOG-2026-10-28-L', 'seasonA-HONA-2026-10-28-L', 'seasonA-HWM-2026-10-29-L', 'seasonA-IDCC-2026-10-29-L', 'seasonA-INCY-2026-10-29-L', 'seasonA-KLAC-2026-10-28-L', 'seasonA-LHX-2026-10-29-L', 'seasonA-MSFT-2026-10-28-L', 'seasonA-MUSA-2026-10-28-L', 'seasonA-NOW-2026-10-28-L', 'seasonA-OLED-2026-10-28-L', 'seasonA-QSR-2026-10-29-L', 'seasonA-QTWO-2026-10-28-L', 'seasonA-BBIO-2026-10-29-L', 'seasonA-AMZN-2026-10-29-L', 'seasonA-AXTI-2026-10-29-L', 'seasonA-COLM-2026-10-29-L', 'seasonA-DXCM-2026-10-29-L', 'seasonA-EXEL-2026-10-29-L', 'seasonA-GDDY-2026-10-29-L', 'seasonA-GD-2026-10-30-L', 'seasonA-INTC-2026-10-29-L', 'seasonA-MSTR-2026-10-29-L', 'seasonA-OSIS-2026-10-29-L', 'seasonA-PINS-2026-10-29-L', 'seasonA-RDDT-2026-10-29-L', 'seasonA-SPSC-2026-10-29-L', 'seasonA-SYK-2026-10-29-L']
- paper/options: AMZN: the account holds +16, the ledgers show +0 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: CMG: the account holds +0, the ledgers show +170 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: GOOG: the account holds +0, the ledgers show +19 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: INTC: the account holds +39, the ledgers show +0 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: MSFT: the account holds +0, the ledgers show +13 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: MSTR: the account holds +36, the ledgers show +0 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: NOW: the account holds +0, the ledgers show +22 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: QSR: the account holds +0, the ledgers show +78 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: RDDT: the account holds +19, the ledgers show +0 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: SNDK: the account holds +2, the ledgers show +0 - a ledger order on it is still live (the ledger lags the broker by one run)
- paper/options: ['seasonA-CMG-2026-10-28-sell', 'seasonA-GOOG-2026-10-28-sell', 'seasonA-MSFT-2026-10-28-sell', 'seasonA-NOW-2026-10-28-sell', 'seasonA-QSR-2026-10-29-sell', 'seasonA-AMZN-2026-10-29-buy', 'seasonA-INTC-2026-10-29-buy', 'seasonA-MSTR-2026-10-29-buy', 'seasonA-RDDT-2026-10-29-buy', 'seasonA-SNDK-2026-10-29-buy'] live in the ledger, no longer open at Alpaca (the next paper run records how they ended)
- paper/options: 131 position(s), 0 open order(s) - they match the ledgers
- paper/long: 79 position(s), 0 open order(s) - they match the ledgers
- Thu 29 Oct: 1 snapshot(s) - CIFR
- Fri 30 Oct: 19 snapshot(s) - AEHR, BETA, BMRN, BWXT, DOCN, DT, FN, ICHR, IPGP, JAZZ, LSCC, MTCH, ON, PAY, PLTR, SHOP, VRTX, VVX, YUMC
- Mon 02 Nov: 24 snapshot(s) - ALAB, AMD, ANET, DDOG, DUOL, FLYW, FRSH, HUT, NATL, NVTS, OUST, Q, RAL, RIOT, RPRX, SMCI, SWKS, TOST, UBER, VSH, W, XYZ, YOU, ZBH
- Tue 03 Nov: 45 snapshot(s) - ACIW, ACLS, ACMR, APPN, BROS, BSY, CAVA, CHYM, CORZ, CPAY, CRUS, CW, DASH, DAVE, DCO, EW, FICO, FIG, FOUR, FSLY, HUBS, KVYO, LOAR, MTSI, NTCT, ONC, OTEX, PAYC, PAYO, POWI, PTC, PTRN, QCOM, RELY, RVMD, SHAK, SITM, SNAP, STE, U, VECO, VERX, VIAV, VSEC, Z
- Wed 04 Nov: 34 snapshot(s) - AKAM, ALRM, ATEN, AVPT, AXON, BILL, CARG, CART, DBX, DIOD, FIGS, FIVN, FROG, GRND, HALO, IONQ, IREN, KRMN, LASR, LITE, LYFT, MRNA, NET, PCTY, PDFS, QNT, SARO, SOUN, TDC, TEAM, TXG, TXRH, UA, WULF
- seasonA: 66 name(s) still PENDING a confirmed date

