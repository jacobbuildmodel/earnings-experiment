"""The paper window runner. Infrastructure only: it changes no rule.

Inside ONE GitHub job it runs the FROZEN paper code every STEP minutes through a window. GitHub's "*/10" cron
drops fires: on 2026-10-13 the DPZ close was sent at 14:46 ET, the next runs came at 15:46 and after 16:00, and a
cancelled close was never resent (ops/incidents/2026-10-13_DPZ_exit.md).
- `pipeline/paper_options.py` and `pipeline/paper_long.py` run exactly as their own workflows run them: `sync
  --commit`, with `--exits-only` when check.py fails.
- Only the cadence becomes reliable. The frozen code's own rules decide everything else: the 15-minute cancel,
  the resend on a later run, the windows and the cut-offs.

    python pipeline/paper_window.py options|long [--start HH:MM] [--end HH:MM] [--step MIN] [--only-if-active]

--only-if-active  exit at once unless the ledger has a filled position not yet closed, or a live order.
                  Morning windows use it; the afternoon window always runs, because a gate may appear at any time.
"""
import datetime
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ET, ROOT, now_et  # noqa: E402
from sessions import is_session  # noqa: E402

SCRIPTS = {"options": ("pipeline/paper_options.py", "paper/options_ledger.json"),
           "long": ("pipeline/paper_long.py", "paper/long_ledger.json")}
MAX_WAIT = datetime.timedelta(hours=4)


def hm(s):
    h, m = map(int, s.split(":"))
    return datetime.time(h, m)


def active(ledger_path):
    """A filled position not yet settled, or an order with no final status."""
    p = os.path.join(ROOT, ledger_path)
    if not os.path.exists(p):
        return False
    led = json.load(open(p, encoding="utf-8"))
    for t in led.get("trades", {}).values():
        if "result" in t or t.get("skipped"):
            continue
        recs = (t.get("orders") or {}).get("open", []) + (t.get("orders") or {}).get("close", [])
        if any(r.get("filled_qty") for r in (t.get("orders") or {}).get("open", [])):
            return True
        if any(r.get("id") and r.get("status") not in ("filled", "canceled", "expired", "rejected") for r in recs):
            return True
    return False


def run(cmd):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    tail = (r.stdout + r.stderr).strip().splitlines()[-6:]
    print(f"[{now_et():%H:%M:%S}] {' '.join(cmd[1:])} -> rc {r.returncode}", *tail, sep="\n  ", flush=True)
    return r.returncode


def main(which, start="14:27", end="15:56", step=3, only_if_active=False, sleep=time.sleep, clock=now_et):
    script, ledger = SCRIPTS[which]
    now = clock()
    if not is_session(now.date()):
        print("not a session - nothing to do")
        return 0
    t0 = datetime.datetime.combine(now.date(), hm(start), ET)
    t1 = datetime.datetime.combine(now.date(), hm(end), ET)
    if now >= t1:
        print(f"window {start}-{end} ET already over")
        return 0
    if t0 - now > MAX_WAIT:
        print(f"window {start} ET is more than {MAX_WAIT} away - exiting")
        return 0
    if now < t0:
        print(f"waiting until {start} ET", flush=True)
        sleep((t0 - now).total_seconds())
    runs = 0
    while clock() < t1:
        subprocess.run(["git", "pull", "-q", "--no-rebase", "--no-edit", "origin", "main"], cwd=ROOT)
        if only_if_active and not active(ledger):
            print("nothing active in the ledger - done")
            break
        ok = run([sys.executable, "check.py"]) == 0
        run([sys.executable, script, "sync", "--commit"] + ([] if ok else ["--exits-only"]))
        runs += 1
        left = (t1 - clock()).total_seconds()
        if left <= 0:
            break
        sleep(min(step * 60, left))
    print(f"window done: {runs} run(s)")
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    sys.exit(main(a[0], opt("--start", "14:27"), opt("--end", "15:56"), int(opt("--step", "3")),
                  "--only-if-active" in a))
