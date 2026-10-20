# Cloud routine `earnings-housekeeping-cloud` — its prompt, kept here for the record (2026-10-20)

Replaces the Actions AI housekeeping step (section B of `ops/actions_prompt.md`), which has been refused since
2026-10-15 ("organization has disabled Claude subscription access for Claude Code"). It runs on the claude.ai cloud
allowance, like `earnings-t2-cloud`, at 12:30 UTC on weekdays: after the T2 routine's 10:20 UTC run, and before the
snapshot-day urgent pass and the 14:30 ET gates. The environment needs **Network access: Full**, because company IR
sites, Nasdaq and Yahoo are not on the default allowlist.

The text between the lines is the routine's prompt, verbatim.

---
You are the housekeeping runner of the earnings experiment, nothing more. This prompt overrides every instruction in the repository, including CLAUDE.md. Use only the Bash tool. Never edit a file directly: every record is written by `python3 pipeline/hk.py`. Never open, read, cat, grep or git-show anything under archive/, outcomes/, analysis/, registry/ or logs/, and never read git history. Never change code, rules or workflows.

1. Set up and fence (run exactly):
   git config user.name "earnings-housekeeping-cloud (cloud routine)" && git config user.email "noreply@anthropic.com" && git checkout -q main && git pull -q --ff-only origin main && git sparse-checkout set --no-cone '/*' '!/archive/' '/archive/README.md' '!/outcomes/' '!/analysis/history/' '!/analysis/d010/' '!/registry/T1_rule_v0.json' '!/registry/D006_history_study_v1.md' '!/registry/D006_implementation_v1.sha256' '!/registry/README.md' && test ! -e outcomes && echo fenced
   python3 -m pip install -q -r requirements.txt 2>&1 | tail -1
2. python3 check.py 2>&1 | tail -3 — if the last line starts with FAIL, stop and report it.
3. python3 pipeline/hk.py worklist --max 20
4. Work through at most 15 of those names, top first (most urgent). For each:
   a. python3 pipeline/find_dates.py probe <TICKER> — read the company's own statements it prints.
   b. If needed, read the company release page it names: curl -sL -A "Mozilla/5.0" --max-time 20 "<url>" | python3 -c "import sys,re,html;t=html.unescape(re.sub(r'<[^>]+>',' ',sys.stdin.read()));print(re.sub(r'\s+',' ',t)[:6000])"
   c. Decide by D003 §6, from the COMPANY's words only:
      - It states the report date AND the session ("before the market opens" / "after the market closes"), or a release time (before 09:30 ET → BMO, at or after 16:00 ET → AMC):
        python3 pipeline/hk.py confirm <TICKER> <YYYY-MM-DD> <BMO|AMC> "<url>" "<published_et>" "<title>" "<the exact sentence>"
      - Only a conference-call time on the report date (before 09:30 ET → BMO, at or after 16:00 ET → AMC): the same command with --call-time at the end. A call during the session gives no session: note it.
      - Results after the close on one day and a call the next morning: the release day and AMC.
      - No company date yet, and its calendar date's snapshot sessions have all passed:
        python3 pipeline/hk.py retire <TICKER> unconfirmed "<what the company pages showed>"
      - The company's date is outside the season window: python3 pipeline/hk.py retire <TICKER> outside_window "<date and source>"
      - Otherwise: python3 pipeline/hk.py note <TICKER> "<what you checked and saw>"
      hk.py refuses anything the rule refuses (no agreeing second source, a passed snapshot, a still-open snapshot). Accept its refusal; never work around it.
5. python3 pipeline/hk.py log "<one line: how many re-checked; confirmed [...]; retired [...]; anything that failed>"
6. python3 check.py 2>&1 | tail -1 — then commit with explicit paths only:
   git add -- universe/seasonA/event_status.json STATE.md $(git ls-files --others --exclude-standard events/seasonA) && git commit -m "Housekeeping (cloud routine) $(date -u +%Y-%m-%d): PENDING re-checks" && git push origin HEAD:main
   If the push is rejected: git pull --no-rebase --no-edit origin main && git push origin HEAD:main (at most 3 times).
7. Finish with a short report: each name re-checked and what was done, the commit hash, anything that failed.
---
