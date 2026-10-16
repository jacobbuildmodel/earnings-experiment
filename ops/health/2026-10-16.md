# Health 2026-10-16 18:07 ET - **AMBER**

check.py: PASS - 1 warning(s)

## RED - events or decisions being lost, or about to be
- none

## AMBER - look at
- Actions failure: Earnings experiment - paper window runner (routine push) at 2026-10-16T14:46:38Z https://github.com/jacobbuildmodel/earnings-experiment/actions/runs/38918509966
- EXIT MISSED: paper/options_ledger.json seasonA-DPZ-2026-10-13-F still open after its reaction session 2026-10-13 - 28 close order(s) sent, 0 of 1 closed; expiry 2026-10-16

## Information
- paper/options_ledger.json: open ['seasonA-DPZ-2026-10-13-F', 'seasonA-NOC-2026-10-20-F', 'seasonA-RTX-2026-10-20-F', 'seasonA-VICR-2026-10-20-F']
- paper/long_ledger.json: open ['seasonA-RTX-2026-10-20-L', 'seasonA-VICR-2026-10-20-L']
- paper window (options): paper-window-push.yml afternoon step since 12:00 ET (done)
- paper window (long): paper-window-push.yml afternoon step since 10:49 ET (done)
- paper/options: 15 position(s), 0 open order(s) - they match the ledgers
- paper/long: 4 position(s), 0 open order(s) - they match the ledgers
- Fri 16 Oct: 3 snapshot(s) - NOC, RTX, VICR
- Mon 19 Oct: 2 snapshot(s) - ABT, PEGA
- Tue 20 Oct: 6 snapshot(s) - HXL, LMT, LRCX, ROP, TSCO, TXN
- Wed 21 Oct: 8 snapshot(s) - APPF, DECK, KN, MXL, RNG, SSNC, VRSN, WDC
- seasonA: 238 name(s) still PENDING a confirmed date

