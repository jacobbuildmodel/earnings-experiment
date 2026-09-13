@echo off
REM ============================================================
REM  PRE HEALTH CHECK - just double-click this file.
REM  Runs all 365 self-tests on the pre-earnings engine.
REM  You want to see "ALL SUITES PASSED" at the bottom.
REM ============================================================
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
echo.
echo   Checking the PRE pre-earnings engine (365 tests, 8 suites)...
echo   engine 47 + calc-risk 59 + ledger 12 + edge-score 67
echo   + guidance 76 + VEL 36 + forecast 42 + batch 26
echo.
python run_tests.py
echo.
echo ============================================================
echo   You want:  ALL SUITES PASSED
echo.
echo   If you saw errors, copy the window text and send it to
echo   Claude with the code to fix.
echo ============================================================
echo.
pause
