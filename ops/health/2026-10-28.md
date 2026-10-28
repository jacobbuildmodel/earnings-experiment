# Health 2026-10-28 13:14 ET - **GREEN** (2 known)

check.py: PASS - 1 warning(s)

## RED - events or decisions being lost, or about to be
- none

## AMBER - look at
- none

## KNOWN - acknowledged in ops/health_known.json, reads exactly as acknowledged; not in the status
- 9 paper-options run(s) in 24 h failed only on the acknowledged alert(s) ['seasonA-DPZ-2026-10-13-F'], each read from its job log; newest 2026-10-28T02:17:04Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/40620011970 (ops/incidents/2026-10-13_DPZ_exit.md)
- paper/options_ledger.json: alerts ['seasonA-DPZ-2026-10-13-F'] - the DPZ trade's flag held_past_expiry is set once and never cleared (pipeline/paper_options.py, hash-locked); no other alert is on the ledger (ops/incidents/2026-10-13_DPZ_exit.md; acknowledged 2026-10-28, laptop chat (the new-RED marker owed in STATE.md NOW, 2026-10-27), until 2026-11-06)

## Information
- paper/options_ledger.json: open ['seasonA-BSX-2026-10-28-F', 'seasonA-CAKE-2026-10-27-F', 'seasonA-EAT-2026-10-28-F', 'seasonA-ETSY-2026-10-28-F', 'seasonA-EXTR-2026-10-28-F', 'seasonA-FFIV-2026-10-27-F', 'seasonA-FLEX-2026-10-28-F', 'seasonA-GEHC-2026-10-28-F', 'seasonA-JMKE-2026-10-28-F', 'seasonA-LFUS-2026-10-28-F', 'seasonA-LOGI-2026-10-27-F', 'seasonA-MANH-2026-10-27-F', 'seasonA-NXPI-2026-10-27-F', 'seasonA-STX-2026-10-27-F', 'seasonA-TEL-2026-10-28-F', 'seasonA-VFC-2026-10-28-F', 'seasonA-ALNY-2026-10-29-F', 'seasonA-ARXS-2026-10-28-F', 'seasonA-BDC-2026-10-29-F', 'seasonA-BHE-2026-10-28-F', 'seasonA-BOOT-2026-10-28-F', 'seasonA-CMG-2026-10-28-F', 'seasonA-COHU-2026-10-28-F', 'seasonA-CROX-2026-10-29-F', 'seasonA-ENTG-2026-10-29-F', 'seasonA-FTAI-2026-10-29-F', 'seasonA-GEN-2026-10-28-F']
- paper/long_ledger.json: open ['seasonA-BSX-2026-10-28-L', 'seasonA-CAKE-2026-10-27-L', 'seasonA-EAT-2026-10-28-L', 'seasonA-ETSY-2026-10-28-L', 'seasonA-EXTR-2026-10-28-L', 'seasonA-FFIV-2026-10-27-L', 'seasonA-FLEX-2026-10-28-L', 'seasonA-GEHC-2026-10-28-L', 'seasonA-JMKE-2026-10-28-L', 'seasonA-LFUS-2026-10-28-L', 'seasonA-LOGI-2026-10-27-L', 'seasonA-MANH-2026-10-27-L', 'seasonA-NXPI-2026-10-27-L', 'seasonA-STX-2026-10-27-L', 'seasonA-TEL-2026-10-28-L', 'seasonA-TER-2026-10-27-L', 'seasonA-ALNY-2026-10-29-L', 'seasonA-BDC-2026-10-29-L', 'seasonA-BHE-2026-10-28-L', 'seasonA-BOOT-2026-10-28-L', 'seasonA-CMG-2026-10-28-L', 'seasonA-COHU-2026-10-28-L', 'seasonA-CROX-2026-10-29-L', 'seasonA-ENTG-2026-10-29-L', 'seasonA-FTAI-2026-10-29-L', 'seasonA-FTNT-2026-10-28-L', 'seasonA-GEN-2026-10-28-L', 'seasonA-GOOG-2026-10-28-L', 'seasonA-HONA-2026-10-28-L', 'seasonA-HWM-2026-10-29-L', 'seasonA-IDCC-2026-10-29-L', 'seasonA-INCY-2026-10-29-L', 'seasonA-KLAC-2026-10-28-L', 'seasonA-LHX-2026-10-29-L', 'seasonA-MSFT-2026-10-28-L', 'seasonA-MUSA-2026-10-28-L', 'seasonA-NOW-2026-10-28-L', 'seasonA-OLED-2026-10-28-L', 'seasonA-QSR-2026-10-29-L', 'seasonA-QTWO-2026-10-28-L']
- paper/options: 129 position(s), 0 open order(s) - they match the ledgers
- paper/long: 80 position(s), 0 open order(s) - they match the ledgers
- Wed 28 Oct: 20 snapshot(s) - AMZN, AXTI, BBIO, COLM, DXCM, EXEL, GD, GDDY, INTC, MPWR, MSTR, OSIS, PINS, RDDT, REGN, SBUX, SNDK, SPSC, SYK, TWLO
- Thu 29 Oct: 1 snapshot(s) - CIFR
- Fri 30 Oct: 19 snapshot(s) - AEHR, BETA, BMRN, BWXT, DOCN, DT, FN, ICHR, IPGP, JAZZ, LSCC, MTCH, ON, PAY, PLTR, SHOP, VRTX, VVX, YUMC
- Mon 02 Nov: 24 snapshot(s) - ALAB, AMD, ANET, DDOG, DUOL, FLYW, FRSH, HUT, NATL, NVTS, OUST, Q, RAL, RIOT, RPRX, SMCI, SWKS, TOST, UBER, VSH, W, XYZ, YOU, ZBH
- Tue 03 Nov: 45 snapshot(s) - ACIW, ACLS, ACMR, APPN, BROS, BSY, CAVA, CHYM, CORZ, CPAY, CRUS, CW, DASH, DAVE, DCO, EW, FICO, FIG, FOUR, FSLY, HUBS, KVYO, LOAR, MTSI, NTCT, ONC, OTEX, PAYC, PAYO, POWI, PTC, PTRN, QCOM, RELY, RVMD, SHAK, SITM, SNAP, STE, U, VECO, VERX, VIAV, VSEC, Z
- seasonA: 70 name(s) still PENDING a confirmed date

