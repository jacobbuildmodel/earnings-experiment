# Health 2026-10-26 11:47 ET - **RED**

check.py: PASS - 1 warning(s)

## RED - events or decisions being lost, or about to be
- POSITION NOT IN LEDGER: paper/options DPZ: the account holds +100, the ledgers show +0
- LEDGER STALE: paper/options GLXY: the account holds +217, the ledgers show +0 - its ledger order (sent Fri 23 Oct 20:16 ET) still reads live: no paper run has refreshed the ledger

## AMBER - look at
- paper/options_ledger.json: alerts ['seasonA-DPZ-2026-10-13-F']

## Information
- paper/options_ledger.json: open ['seasonA-AGYS-2026-10-26-F', 'seasonA-CDNS-2026-10-26-F', 'seasonA-CLS-2026-10-26-F', 'seasonA-EEFT-2026-10-27-F', 'seasonA-GLXY-2026-10-27-F', 'seasonA-RMBS-2026-10-26-F']
- paper/long_ledger.json: open ['seasonA-AGYS-2026-10-26-L', 'seasonA-CDNS-2026-10-26-L', 'seasonA-EEFT-2026-10-27-L', 'seasonA-GLXY-2026-10-27-L', 'seasonA-RMBS-2026-10-26-L']
- paper/options: ['seasonA-GLXY-2026-10-27-buy'] live in the ledger, no longer open at Alpaca (the next paper run records how they ended)
- paper/long: 10 position(s), 0 open order(s) - they match the ledgers
- Mon 26 Oct: 20 snapshot(s) - BLKB, BSX, CAKE, EAT, ETSY, EXTR, FFIV, FLEX, GEHC, INTA, JMKE, LFUS, LOGI, MANH, NXPI, STX, TEL, TER, UCTT, VFC
- Tue 27 Oct: 33 snapshot(s) - ALNY, ARXS, BDC, BELFA, BHE, BOOT, CMG, COHU, CROX, ENTG, FORM, FTAI, FTNT, GEN, GOOG, HII, HONA, HWM, IDCC, INCY, KLAC, LHX, MSFT, MUSA, NOW, OLED, PI, PLXS, QSR, QTWO, TENB, TYL, WEX
- Wed 28 Oct: 20 snapshot(s) - AMZN, AXTI, BBIO, COLM, DXCM, EXEL, GD, GDDY, INTC, MPWR, MSTR, OSIS, PINS, RDDT, REGN, SBUX, SNDK, SPSC, SYK, TWLO
- Thu 29 Oct: 1 snapshot(s) - CIFR
- Fri 30 Oct: 18 snapshot(s) - AEHR, BETA, BWXT, DOCN, DT, FN, ICHR, IPGP, JAZZ, LSCC, MTCH, ON, PAY, PLTR, SHOP, VRTX, VVX, YUMC
- seasonA: 79 name(s) still PENDING a confirmed date

