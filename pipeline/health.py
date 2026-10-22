"""Daily health check - code only, no AI, no rule. Writes ops/health/latest.md and ops/health/<date>.md (one per
day, overwritten by later runs that day) with one status: GREEN, AMBER (look at it) or RED (an event or a decision
is being lost, or is about to be). The workflow opens or comments on one "Health RED" GitHub issue on RED, and
closes it on GREEN.

    python pipeline/health.py [--write] [--commit]

Checks, each mechanical (reviewed by Opus 5.5, 2026-10-13, fixes applied):
  check.py           not exit 0 or last line not PASS                                             -> RED
  snapshot windows   a CONFIRMED event whose snapshot session ended (16:00 ET) with no gate.json in its own
                     folder (<T>_<calendar_date>) -> RED; a missed_window record within 24 h -> RED, older -> info
  stage 1            a PASS gate with no manifest.json after its entry open -> RED (T0, T1 and T2 are lost);
                     a gate of any other status with no manifest after its entry open -> AMBER
  T2 (D004 v4)       PASS event, no manifest_t2.json: past the deadline -> RED "T2 MISSING";
                     less than 14 h to the deadline -> RED "T2 AT RISK"          (deadline from the frozen rule)
  D013 shadows       T2R / T2O missing after the deadline, events entering after 2026-10-13 with a dossier -> AMBER
  Actions            failed / timed-out / startup-failure runs in the last 24 h; S2 window or T2 queue -> RED, else AMBER
  paper ledgers      a halt -> RED; alerts or errors on the last run -> AMBER
  paper exits        a filled position still open on its reaction session 15:15-15:55 ET -> RED (still savable);
                     still open after that -> AMBER (added after the DPZ incident)
  SH-M capture       no shadow/calendar/<today>.json after 12:00 ET on a session -> AMBER
  C1 capture         no shadow/c1/im/<P>.json for the latest session whose close has passed (D015) -> AMBER
  AI step refused    per step (logs/actions/ file suffix; logs/t2/ backend), the newest log within 5 days is a
                     refusal (actions: result.is_error; t2: error set and not a network exception) -> RED if the
                     refusals in a row began under 24 h ago, else AMBER (standing)
  dates stale        no date CONFIRMED or retired INELIGIBLE (a `rechecks` line) in 30 h while a PENDING name has a
                     calendar date within 7 days -> AMBER; RED if one is within 3 sessions
  runner not acting  14:40-15:56 ET on a full session, a window step running for the account: a ledger order still
                     open (not pending_cancel) 5 min past its cancel limit (a v3 close 2 min, any other 15) -> RED
                     with the run to cancel before dispatching paper-window-push.yml (read-only: it cancels nothing)
                     (the three added 2026-10-22, designed 2026-10-21 13:40 ET: STATE.md Log)
  paper window       a full session from 14:40 ET, per account (options, long): no afternoon window step of
                     paper-window-push.yml or paper-window.yml running now (once over: one that ran to 15:56) and no
                     frozen paper-options.yml / paper-long.yml run in the last 25 min -> RED while the window is open,
                     AMBER once over; only those frozen runs -> AMBER; a window step that started after 14:45 -> AMBER
                     (added 2026-10-15: on 10-14 every cron start of the window runner landed after the window, and
                     nothing alarmed)
  positions          each Alpaca paper account (read-only GETs) against its ledgers - options account:
                     options_ledger.json + ledger.json (paper.py's shares share the account); long account:
                     long_ledger.json. A position or open order the ledgers do not show as live, or a live ledger
                     position the account does not hold, seen again on a second look 2 minutes later -> RED. A mismatch
                     on a symbol with a live ledger order: information while that order is young (options 30 min,
                     shares 26 h), AMBER up to 24 h, then RED "LEDGER STALE". An unknown open order under 15 min old ->
                     information; an option still listed after its expiry day, or an unreadable account -> AMBER
                     (both added 2026-10-15; Sonnet review SHIP WITH FIXES, fixes applied; either check crashing -> AMBER)
Information: upcoming snapshots, PENDING date confirmations, open paper positions.

    python pipeline/health.py --shapes     # also print each account's open orders and positions (compact, read-only)
"""
import collections
import datetime
import glob
import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ET, ROOT, now_et  # noqa: E402
from sessions import close_time, is_session, shift  # noqa: E402

D = datetime.date.fromisoformat
REPO = os.environ.get("GITHUB_REPOSITORY", "jacobbuildmodel/earnings-experiment")
CRITICAL_WORKFLOWS = ("Earnings experiment - S2 window", "Earnings experiment - T2 queue (D004 v4)")
D013_START = datetime.date(2026, 10, 14)
AT_RISK = datetime.timedelta(hours=14)
LOOKBACK = datetime.timedelta(days=5)
D015_START = datetime.date(2026, 10, 14)
# paper window coverage: paper_window.py's afternoon window is 14:27-15:56 ET (paper-window*.yml)
WIN_START, WIN_CHECK, WIN_DEADLINE, WIN_END = (datetime.time(14, 27), datetime.time(14, 40), datetime.time(14, 45),
                                               datetime.time(15, 56))
WIN_SLACK = datetime.timedelta(minutes=3)        # a step that ended this close to 15:56 covered the window
FROZEN_GAP = datetime.timedelta(minutes=25)      # frozen 10-minute runs: one dropped fire tolerated, not two
WINDOW_STEPS = {"paper-window-push.yml": r"Afternoon window\b",             # the step that runs paper_window.py
                "paper-window.yml": r"Run the frozen paper code every \d+ minutes"}   # "3 minutes" before ec2bdee
FROZEN_PAPER = {"options": "paper-options.yml", "long": "paper-long.yml"}
# positions vs ledgers: account -> (key env vars, ledgers in paper/)
ACCOUNTS = {"options": (("APCA_API_KEY_ID", "APCA_API_SECRET_KEY"), ("options_ledger.json", "ledger.json")),
            "long": (("APCA_L_API_KEY_ID", "APCA_L_API_SECRET_KEY"), ("long_ledger.json",))}
SECOND_LOOK = 120                                # seconds; a RED mismatch must still be there on a second look
# a live ledger order excuses a mismatch on its symbols while it is this young (info), then AMBER, then RED: options
# ledgers are refreshed every 2 minutes in the windows; paper.py (shares) syncs only at 20:15 and 07:15 ET
LAG = {"options": (datetime.timedelta(minutes=30), datetime.timedelta(hours=24)),
       "shares": (datetime.timedelta(hours=26), datetime.timedelta(hours=26))}
NEW_ORDER = datetime.timedelta(minutes=15)       # an open order this young may not be committed to a ledger yet
OCC = re.compile(r"^[A-Z.]+(\d{2})(\d{2})(\d{2})[CP]\d{8}$")
TERMINAL = ("filled", "canceled", "expired", "rejected", "done_for_day", "replaced")   # paper_options.TERMINAL
# alarms (designed 2026-10-21 13:40 ET, STATE.md Log)
NETWORK = re.compile(r"^\w+(Error|Exception)\b")  # a t2 log error like this is the network, not a refusal
REFUSED_NEW = datetime.timedelta(hours=24)        # refusals in a row that began this recently are RED, older AMBER
STATUS_CHANGE = re.compile(r"CONFIRMED \d{4}-\d\d-\d\d|INELIGIBLE \w+")
DATES_QUIET = datetime.timedelta(hours=30)
CANCEL_AFTER = {"v3_close": 2, "other": 15}      # minutes: paper_options.V3_RETRY_AFTER_MIN / RETRY_AFTER_MIN
CANCEL_SLACK = datetime.timedelta(minutes=5)
WINDOW_LEDGER = {"options": "options_ledger.json", "long": "long_ledger.json"}   # the ledgers paper_window.py works


def load(p):
    return json.load(open(p, encoding="utf-8"))


def check_py():
    r = subprocess.run([sys.executable, os.path.join(ROOT, "check.py")], cwd=ROOT, capture_output=True, text=True)
    lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
    last = lines[-1] if lines else f"no output (rc {r.returncode}) {r.stderr[-200:]}"
    fails = [ln.strip() for ln in lines if ln.strip().startswith("[FAIL]")]
    return last, fails, r.returncode


def seasons():
    return [os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(ROOT, "universe", "*", "event_status.json"))
            if os.path.basename(os.path.dirname(p)) != "pilot"]


def v4_rule(season):
    """The frozen D004 v4 rule, None if no version covers the season. A damaged rule raises (-> RED)."""
    import t2_stage2
    return t2_stage2.v4(season)


def windows(now):
    red, info = [], []
    for s in seasons():
        st = load(os.path.join(ROOT, "universe", s, "event_status.json")).get("events", {})
        for t, ev in st.items():
            snap = ev.get("snapshot_session")
            if not snap:
                continue
            ended = datetime.datetime.combine(D(snap), datetime.time(16, 0), ET)
            if now < ended or now - ended > LOOKBACK:
                continue
            reason = ev.get("reason") or ev.get("gate_reason") or ""
            if "missed_window" in (reason, ev.get("status")):
                (red if now - ended < datetime.timedelta(hours=24) else info).append(
                    f"MISSED SNAPSHOT WINDOW (recorded): {s} {t} (snapshot {snap})")
                continue
            if ev.get("status") != "CONFIRMED":
                continue
            folder = os.path.join(ROOT, "events", s, f"{t}_{ev.get('calendar_date')}")
            if not os.path.exists(os.path.join(folder, "gate.json")):
                red.append(f"MISSED SNAPSHOT WINDOW: {s} {t} (report {ev.get('calendar_date')}, snapshot {snap}) - no gate.json")
    return red, info


def decisions(now):
    """Every gate of a live season with an entry open within LOOKBACK or still ahead."""
    import t2_stage2
    red, amber, info = [], [], []
    for g in glob.glob(os.path.join(ROOT, "events", "*", "*", "gate.json")):
        edir = os.path.dirname(g)
        season = os.path.basename(os.path.dirname(edir))
        if season == "pilot":
            continue
        gate = load(g)
        try:
            eo = datetime.datetime.combine(D(gate["timing"]["entry"]["session"]), datetime.time(9, 30), ET)
        except (KeyError, TypeError, ValueError):
            amber.append(f"{os.path.basename(edir)}: gate.json without an entry session")
            continue
        if now - eo > LOOKBACK:
            continue
        ev = os.path.basename(edir)
        mp = os.path.join(edir, "manifest.json")
        if not os.path.exists(mp):
            if now >= eo:
                (red if gate.get("status") == "PASS" else amber).append(
                    f"STAGE 1 NOT FROZEN before the entry open: {ev} (gate {gate.get('status')})")
            continue
        man = load(mp)
        if man.get("status") != "PASS":
            continue
        try:
            rule = v4_rule(season)
        except SystemExit as exc:
            red.append(f"D004 rule unreadable for {season}: {exc} - T2 cannot be checked")
            continue
        if not rule:
            continue
        dl = t2_stage2.deadline(rule, gate)
        have = {k: os.path.exists(os.path.join(edir, f)) for k, f in
                (("T2", "manifest_t2.json"), ("T2G", "manifest_t2g.json"), ("T2R", "manifest_t2r.json"),
                 ("T2O", "manifest_t2o.json"))}
        if not have["T2"]:
            if now >= dl:
                red.append(f"T2 MISSING: {ev} (deadline {dl:%a %d %b %H:%M} ET)")
            elif dl - now < AT_RISK:
                red.append(f"T2 AT RISK: {ev} - not frozen, deadline {dl:%a %d %b %H:%M} ET")
        if now >= dl and eo.date() >= D013_START and os.path.exists(os.path.join(edir, "dossier.json")):
            for k in ("T2R", "T2O"):
                if not have[k]:
                    amber.append(f"{k} missing: {ev} (D013 shadow; the budget may have skipped it)")
        if now < dl:
            info.append(f"{ev}: T2 deadline {dl:%a %d %b %H:%M} ET - frozen so far: "
                        + (", ".join(k for k, v in have.items() if v) or "none"))
    return red, amber, info


def actions_failures(now):
    """Runs in the last 24 h that failed, timed out or failed to start. None if the API cannot be read."""
    import requests
    since = (now - datetime.timedelta(hours=24)).astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    h = {"Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        h["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    out = []
    try:
        for page in range(1, 11):
            r = requests.get(f"https://api.github.com/repos/{REPO}/actions/runs",
                             params={"created": f">={since}", "per_page": 100, "page": page}, headers=h, timeout=30)
            if r.status_code != 200:
                return None
            runs = r.json().get("workflow_runs", [])
            out += [(x["name"], x["created_at"], x["html_url"], x.get("conclusion")) for x in runs
                    if x.get("conclusion") in ("failure", "timed_out", "startup_failure")]
            if len(runs) < 100:
                break
    except Exception:
        return None
    return out


def exits(name, led, now):
    """D011 exits (added 2026-10-14 after the DPZ incident). A filled position still open on its reaction session
    between 15:15 and 15:55 ET is RED, while it can still be saved. One still open later is AMBER: the primary exit
    is already lost, and the frozen code keeps retrying until expiry."""
    red, amber = [], []
    today = now.date().isoformat()
    for k, t in led.get("trades", {}).items():
        if "result" in t or t.get("skipped") or t.get("close_sim") or not t.get("reaction_session"):
            continue
        o = (t.get("orders") or {}).get("open", [])
        c = (t.get("orders") or {}).get("close", [])
        o_f = sum(r.get("filled_qty") or 0 for r in o)        # a refused attempt has filled_qty 0
        c_f = sum(r.get("filled_qty") or 0 for r in c)
        if not o_f or c_f >= o_f:
            continue
        tries = f"{len(c)} close order(s) sent, {c_f:g} of {o_f:g} closed"
        same_day = t["reaction_session"] == today
        # the last send: 15:55 ET; a D011 v3 trade on its expiry date: 15:10 ET (Alpaca's 15:15 cut-off)
        last = datetime.time(15, 10) if t.get("exec") == "v3" and t.get("expiry") == today else datetime.time(15, 55)
        if same_day and datetime.time(15, 15) <= now.time() < last:
            red.append(f"EXIT NOT FILLED: paper/{name} {k} - {tries}; the last send is {last:%H:%M} ET "
                       "(the ledger can lag the broker by one run)")
        elif t["reaction_session"] < today or (same_day and now.time() >= last):
            amber.append(f"EXIT MISSED: paper/{name} {k} still open after its reaction session "
                         f"{t['reaction_session']} - {tries}; expiry {t.get('expiry')}")
    return red, amber


def ledgers(now):
    red, amber, info = [], [], []
    for name in ("options_ledger.json", "long_ledger.json"):
        p = os.path.join(ROOT, "paper", name)
        if not os.path.exists(p):
            continue
        led = load(p)
        r, a = exits(name, led, now)
        red, amber = red + r, amber + a
        if led.get("halt"):
            red.append(f"paper/{name}: HALT - {led['halt'].get('why')}")
        if led.get("alerts"):
            amber.append(f"paper/{name}: alerts {led['alerts']}")
        if led.get("errors_last_run"):
            amber.append(f"paper/{name}: errors on its last run {led['errors_last_run']}")
        open_ = [k for k, t in led.get("trades", {}).items() if (t.get("orders") or {}).get("open") and "result" not in t
                 and not t.get("skipped") and not t.get("open_failed")]
        if open_:
            info.append(f"paper/{name}: open {open_}")
    return red, amber, info


def capture_check(now):
    d = now.date()
    if not is_session(d) or now.time() < datetime.time(12, 0):
        return None
    return None if os.path.exists(os.path.join(ROOT, "shadow", "calendar", f"{d.isoformat()}.json")) else \
        f"no SH-M calendar capture for {d} yet"


def c1_capture_check(now):
    """D015 §3: the C1 implied-move capture of the latest session whose close has passed. A missing one means that
    session's SH-M events can never be C1. Silent until D015 is registered."""
    if not os.path.exists(os.path.join(ROOT, "registry", "D015_implementation_v1.sha256")):
        return None
    d = now.date()
    p = d if is_session(d) and now >= datetime.datetime.combine(d, close_time(d), ET) else shift(d, -1)
    if p < D015_START:
        return None
    return None if os.path.exists(os.path.join(ROOT, "shadow", "c1", "im", f"{p.isoformat()}.json")) else         f"no C1 implied-move capture for {p} (D015): that session's events can never be C1"


# ---------------------------------------------------------------- alarms: AI step refused, dates stale
def ai_logs():
    """[(step, when ET, refused, text)] from logs/actions/ (the Actions AI step; the step is the file-name suffix,
    stamped UTC) and logs/t2/ (one per T2 call; the step is the backend, stamped ET)."""
    out = []
    for p in glob.glob(os.path.join(ROOT, "logs", "actions", "*.json")):
        m = re.fullmatch(r"(\d{4}-\d\d-\d\dT\d{4}Z)_\d+(?:_(.+))?\.json", os.path.basename(p))
        if not m:
            continue
        when = datetime.datetime.strptime(m[1], "%Y-%m-%dT%H%MZ").replace(tzinfo=datetime.timezone.utc).astimezone(ET)
        try:
            res = load(p).get("result") or {}
        except (OSError, ValueError, AttributeError):
            continue
        out.append((f"Actions AI step ({m[2] or 'main'})", when, res.get("is_error") is True, res.get("text")))
    for p in glob.glob(os.path.join(ROOT, "logs", "t2", "*.json")):
        m = re.fullmatch(r".+?_\d{4}-\d\d-\d\d_(.+)_(\d{8}T\d{6})\.json", os.path.basename(p))
        if not m:
            continue
        try:
            d = load(p)
        except (OSError, ValueError):
            continue
        when = ts(d.get("called_et")) or datetime.datetime.strptime(m[2], "%Y%m%dT%H%M%S").replace(tzinfo=ET)
        err = d.get("error")
        out.append((f"T2 backend {m[1]}", when, bool(err) and not NETWORK.match(str(err)), err))
    return out


def ai_refusals(now, logs=None):
    """Alarm 1: the newest log of a step (within LOOKBACK) is a refusal. RED while the refusals in a row began under
    24 h ago, AMBER after that (a standing refusal is on STATE.md's Waiting on Jacob)."""
    red, amber = [], []
    by_step = collections.defaultdict(list)
    for step, when, refused, text in (ai_logs() if logs is None else logs):
        by_step[step].append((when, refused, text))
    for step, xs in sorted(by_step.items()):
        xs.sort(key=lambda x: x[0])
        if not xs[-1][1] or now - xs[-1][0] > LOOKBACK:
            continue
        n = 0
        while n < len(xs) and xs[-1 - n][1]:
            n += 1
        began = xs[-n][0]
        text = re.sub(r"\s+", " ", str(xs[-1][2]))[:200]       # not inside the f-string: Python 3.11 refuses "\"
        msg = (f"AI STEP REFUSED: {step} - {n} refusal(s) in a row since {began:%a %d %b %H:%M} ET, newest "
               f"{xs[-1][0]:%a %d %b %H:%M} ET: {text}")
        if now - began < REFUSED_NEW:
            red.append(msg)
        else:
            amber.append(msg + " (standing: STATE.md, Waiting on Jacob)")
    return red, amber


def stamp(line):
    """The time a `rechecks` line was written: the text before its first ": "."""
    return ts(line.split(": ", 1)[0])


def dates_stale(now):
    """Alarm 2: no PENDING date confirmed or retired in 30 h while a PENDING name has a calendar date within 7 days.
    The newest re-check of those names tells "the re-checks run but confirm nothing" from "they are not running"."""
    red, amber = [], []
    today = now.date()
    soon_end = shift(today, 3)
    for s in seasons():
        st = load(os.path.join(ROOT, "universe", s, "event_status.json")).get("events", {})
        changes = [t for ev in st.values() for ln in ev.get("rechecks") or [] if STATUS_CHANGE.search(ln)
                   for t in [stamp(ln)] if t]
        last = max(changes, default=None)
        if last and now - last <= DATES_QUIET:
            continue
        near, soon = [], []
        for t, ev in st.items():
            if ev.get("status") != "PENDING":
                continue
            ds = [D(x) for x in ev.get("calendar_dates") or [] if re.fullmatch(r"\d{4}-\d\d-\d\d", str(x))]
            if any(today <= x <= today + datetime.timedelta(days=7) for x in ds):
                near.append(t)
                if any(today <= x <= soon_end for x in ds):
                    soon.append(t)
        if not near:
            continue
        seen = max((x for t in near for x in map(stamp, st[t].get("rechecks") or []) if x), default=None)
        how = ("never re-checked" if seen is None else f"newest re-check {seen:%a %d %b %H:%M} ET - "
               + ("the re-checks run but confirm nothing" if now - seen <= DATES_QUIET else "the re-checks are not running"))
        since = f"{last:%a %d %b %H:%M} ET" if last else "the season began"
        within = f", {len(soon)} within 3 sessions {sorted(soon)}" if soon else ""
        msg = (f"DATES STALE ({s}): no date confirmed or retired since {since} (over 30 h), while {len(near)} "
               f"PENDING name(s) have a calendar date within 7 days{within}; {how}")
        (red if soon else amber).append(msg)
    return red, amber


# ---------------------------------------------------------------- paper window coverage
def ts(s):
    """An API timestamp (Z or offset) as an aware ET datetime; None if absent or unreadable."""
    try:
        return datetime.datetime.fromisoformat(str(s).replace("Z", "+00:00")).astimezone(ET) if s else None
    except ValueError:
        return None


def gh_get(path, params=None):
    import requests
    h = {"Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        h["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    for attempt in (1, 2):                     # one retry: a single 502 must not blind the 14:45 run
        try:
            r = requests.get(f"https://api.github.com/repos/{REPO}/{path}", params=params, headers=h, timeout=30)
            if r.status_code == 200:
                return r.json()
            err = f"HTTP {r.status_code}"
        except requests.RequestException as e:
            err = type(e).__name__
        if attempt == 1:
            time.sleep(2)
    raise OSError(f"GitHub API {path}: {err}")


def window_jobs(now):
    """Today's paper window steps and frozen paper runs, from the Actions API (actions: read). None if unreadable.
    steps:  [{account, workflow, url, job_status, status, started, completed}] - the afternoon step of every
            window job ("window (options)" / "window (long)"); a job still waiting for its group has no step yet
    frozen: [(account, when)] - frozen paper-options.yml / paper-long.yml runs that ran: when = completion time
            (updated_at; they take 20-35 s), or now while one runs. Pending runs that a window job's group
            cancelled never ran and are left out."""
    day0 = datetime.datetime.combine(now.date(), datetime.time(0), ET).astimezone(datetime.timezone.utc)
    q = {"created": f">={day0:%Y-%m-%dT%H:%M:%SZ}", "per_page": 100}
    steps, frozen = [], []
    try:
        for wf, step_name in WINDOW_STEPS.items():
            for run in gh_get(f"actions/workflows/{wf}/runs", q).get("workflow_runs", []):
                for j in gh_get(f"actions/runs/{run['id']}/jobs", {"per_page": 100}).get("jobs", []):
                    m = re.fullmatch(r"window \((\w+)\)", j.get("name") or "")
                    if not m or m[1] not in ACCOUNTS:
                        continue
                    st = next((s for s in j.get("steps") or [] if re.match(step_name, s.get("name") or "")), {})
                    steps.append({"account": m[1], "workflow": wf, "url": run.get("html_url"),
                                  "job_status": j.get("status"), "status": st.get("status"),
                                  "started": ts(st.get("started_at")), "completed": ts(st.get("completed_at"))})
        for acct, wf in FROZEN_PAPER.items():
            for run in gh_get(f"actions/workflows/{wf}/runs", q).get("workflow_runs", []):
                if run.get("status") == "in_progress":
                    frozen.append((acct, now))
                elif run.get("conclusion") in ("success", "failure"):
                    frozen.append((acct, ts(run.get("updated_at"))))
    except Exception:
        return None
    return steps, frozen


def full_session_afternoon(now):
    d = now.date()
    return is_session(d) and close_time(d) == datetime.time(16, 0) and now.time() >= WIN_CHECK


def window_coverage(now, steps, frozen):
    """Is each paper account's afternoon window (14:27-15:56 ET) worked by a window job? Silent before 14:40 ET and
    on days that are not full sessions (paper_window.py's window is fixed; an early close ends trading at 13:00)."""
    red, amber, info = [], [], []
    if not full_session_afternoon(now):
        return red, amber, info
    d = now.date()
    at = lambda t: datetime.datetime.combine(d, t, ET)  # noqa: E731
    upto = min(now, at(WIN_END))
    over = now >= at(WIN_END)
    for acct in ACCOUNTS:
        # a step covers the window if it started today and is running now; once the window is over, if it started by
        # 15:56 and ran to within 3 minutes of it. A step that already ended inside the window (a crash, a cancel, a
        # late morning-mode start that exits at once) does not. (A completion after `now` only happens when a recorded
        # day is replayed, as the tests do: it reads as running at `now`.)
        mine = sorted((s for s in steps if s["account"] == acct and s["started"] and s["started"].date() == d
                       and s["started"] <= now), key=lambda s: s["started"])
        running = lambda s: (s["completed"] is None and s["status"] == "in_progress") or             (s["completed"] is not None and s["completed"] > now)  # noqa: E731
        live = [s for s in mine if s["started"] <= upto and (
            (running(s) or (s["completed"] is not None and s["completed"] >= at(WIN_END) - WIN_SLACK))
            if over else running(s))]
        if live and live[0]["started"] <= at(WIN_DEADLINE):
            info.append(f"paper window ({acct}): {live[0]['workflow']} afternoon step since "
                        f"{live[0]['started']:%H:%M} ET{' (done)' if over else ''}")
            continue
        if live:
            amber.append(f"PAPER WINDOW LATE ({acct}): the window job's afternoon step started "
                         f"{live[0]['started']:%H:%M} ET, after 14:45 - before that only the frozen 10-minute runs "
                         f"could work the exit and gate window {live[0]['url']}")
            continue
        ran = [f"{s['started']:%H:%M}-{s['completed']:%H:%M}" if s["completed"] and s["completed"] <= now
               else f"{s['started']:%H:%M}-" for s in mine]
        waiting = sum(1 for s in steps if s["account"] == acct and s["job_status"] != "completed"
                      and s["status"] != "in_progress")
        facts = "; ".join(filter(None, [
            f"window steps today ran {', '.join(ran)} ET" if ran else "no window step ran today",
            f"{waiting} window job(s) not yet in their afternoon step" if waiting else ""]))
        todo = "the window is over" if over else \
            "dispatch paper-window-push.yml now (first cancel any paper run holding the group)"
        recent = [t for a, t in frozen if a == acct and t and at(WIN_START) <= t <= min(now, upto + WIN_SLACK)
                  and t >= upto - FROZEN_GAP]
        if recent:
            amber.append(f"PAPER WINDOW NOT RUNNING ({acct}): {facts}; only the frozen {FROZEN_PAPER[acct]} runs "
                         f"work the window (last {max(recent):%H:%M} ET) - {todo}")
        else:                                  # RED while it can still be saved, AMBER once over (as exits() does)
            (amber if over else red).append(
                f"PAPER WINDOW NOT COVERED ({acct}): {facts}; no frozen {FROZEN_PAPER[acct]} run either in the 25 "
                f"minutes to {upto:%H:%M} ET - exits and gates {'were' if over else 'are'} not being worked - {todo}")
    return red, amber, info


def runner_idle(now, steps, state=None, read=None):
    """Alarm 3: a window step runs for the account, yet a ledger order is still open 5 min past its cancel limit, so
    the runner is not acting (10-21: a stuck step). From 14:40 ET, not 14:27: a morning order the runner has not yet
    reached is not a fault. Read-only: it names the run to cancel and cancels or dispatches nothing."""
    red = []
    d = now.date()
    if not full_session_afternoon(now) or now >= datetime.datetime.combine(d, WIN_END, ET):
        return red
    state, read = state or alpaca_state, read or read_ledgers
    for acct, name in WINDOW_LEDGER.items():
        live = [s for s in steps if s["account"] == acct and s["started"] and s["started"].date() == d
                and s["started"] <= now and s["completed"] is None and s["status"] == "in_progress"]
        st = state(acct) if live else None
        if not isinstance(st, tuple):                # no step running, or the account unreadable (positions_check)
            continue
        led = read([name]).get(name)
        trades = led.get("trades") or {} if isinstance(led, dict) else {}
        for o in st[1]:
            m = re.fullmatch(r"(.+)-(open|close)(?:-r\d+)?", str(o.get("client_order_id")))
            made = ts(o.get("submitted_at") or o.get("created_at"))
            if o.get("status") == "pending_cancel" or not m or m[1] not in trades or not made:
                continue
            limit = CANCEL_AFTER["v3_close" if m[2] == "close" and trades[m[1]].get("exec") == "v3" else "other"]
            age = now - made
            if age > datetime.timedelta(minutes=limit) + CANCEL_SLACK:
                run_id = str(live[0]["url"]).rstrip("/").rsplit("/", 1)[-1]
                red.append(f"RUNNER NOT ACTING (paper/{acct}): order {m[0]} ({o.get('status')}) live "
                           f"{age.total_seconds() / 60:.0f} min, past its {limit}-min cancel limit + 5, while the window "
                           f"step runs ({live[0]['url']}) - cancel that run FIRST (gh run cancel {run_id}), then dispatch "
                           "paper-window-push.yml (GitHub keeps one waiting run per group)")
    return red


def paper_window(now):
    if not full_session_afternoon(now):
        return [], [], []
    got = window_jobs(now)
    if got is None:
        return [], ["paper window coverage unreadable (GitHub Actions API)"], []
    red, amber, info = window_coverage(now, *got)
    return red + runner_idle(now, got[0]), amber, info


# ---------------------------------------------------------------- Alpaca positions vs the paper ledgers
def alpaca_state(acct):
    """(positions, open orders) of one Alpaca paper account: read-only GETs. "unconfigured" without its keys,
    None if unreadable. The keys are never printed or stored."""
    import requests
    from paper import BASE
    k, s = (os.environ.get(x) for x in ACCOUNTS[acct][0])
    if not k or not s:
        return "unconfigured"
    h = {"APCA-API-KEY-ID": k, "APCA-API-SECRET-KEY": s}
    try:
        p = requests.get(f"{BASE}/positions", headers=h, timeout=30)
        o = requests.get(f"{BASE}/orders", params={"status": "open", "limit": 500, "nested": "true"}, headers=h,
                         timeout=30)
        if p.status_code != 200 or o.status_code != 200:
            return None
        pos, orders = p.json(), o.json()
    except Exception:
        return None
    return (pos, orders) if isinstance(pos, list) and isinstance(orders, list) else None


def read_ledgers(names):
    """The ledgers as committed on GitHub NOW (git fetch), so a paper run that committed after this checkout is
    seen; the working copy where git cannot say. {name: ledger; None if absent; "unreadable" if not JSON}."""
    fetched = subprocess.run(["git", "fetch", "-q", "origin", "main"], cwd=ROOT, capture_output=True).returncode == 0
    out = {}
    for n in names:
        txt = None
        if fetched:
            r = subprocess.run(["git", "show", f"origin/main:paper/{n}"], cwd=ROOT, capture_output=True)
            txt = r.stdout.decode("utf-8") if r.returncode == 0 else None
        if txt is None and os.path.exists(os.path.join(ROOT, "paper", n)):
            txt = open(os.path.join(ROOT, "paper", n), encoding="utf-8").read()
        try:
            out[n] = json.loads(txt) if txt else None
        except ValueError:
            out[n] = "unreadable"
    return out


def norm(symbol):
    return (symbol or "").upper().replace("-", ".")


def option_expiry(symbol):
    m = OCC.match(symbol)
    return datetime.date(2000 + int(m[1]), int(m[2]), int(m[3])) if m else None


def ledger_book(ledgers):
    """What the ledgers say one account holds and has working. Returns (held {symbol: signed qty}, orders [(ids,
    status, symbols)], busy {symbol: (newest live ledger order's send time, ledger kind)}, unsure {symbols whose fill
    cannot be read}, notes).
    Options ledgers (paper_options.py): every filled order's legs_filled, buy +, sell -; a v3 close that dropped a
    long leg leaves that leg held, as the account does. Shares (paper.py, ledger.json): buy - sell filled_qty."""
    held, orders, busy, unsure, notes = collections.defaultdict(float), [], {}, set(), []

    def order(rec, symbols, kind="options"):
        ids = tuple(x for x in (rec.get("client_order_id"), rec.get("id")) if x)
        if ids:
            orders.append((ids, rec.get("status"), symbols))
        if rec.get("status") and rec["status"] not in TERMINAL:
            sent = ts(rec.get("sent_et") or rec.get("submitted_et"))     # None (an orphan): treated as old
            for x in symbols:
                old = busy.get(x)
                if old is None or (sent and (old[0] is None or sent > old[0])):
                    busy[x] = (sent, kind)

    for name, led in ledgers.items():
        if led == "unreadable":
            notes.append(f"paper/{name} is not readable JSON")
            continue
        for key, t in (led or {}).get("trades", {}).items():
            if name == "ledger.json":
                s = norm(t.get("ticker"))
                for side, sign in (("buy", 1), ("sell", -1)):
                    if t.get(side):
                        held[s] += sign * float(t[side].get("filled_qty") or 0)
                        order(t[side], {s}, "shares")
                continue
            legs = {lg.get("symbol") for lg in t.get("legs") or []}
            for r in (t.get("orders") or {}).get("open", []) + (t.get("orders") or {}).get("close", []):
                lf, q = r.get("legs_filled") or [], float(r.get("filled_qty") or 0)
                syms = (set(r.get("all_sides") or r.get("sides") or {}) | {lg.get("symbol") for lg in lf}) or legs
                order(r, syms)
                if not q:
                    continue
                # paper_options.fill_net's rule: every leg's quantity equals its order's filled quantity
                if not lf or any(lg.get("side") not in ("buy", "sell") or not lg.get("symbol")
                                 or abs(float(lg.get("qty") or 0) - q) > 1e-9 for lg in lf):
                    unsure.update(syms)
                    notes.append(f"{key} {r.get('client_order_id')}: filled, but its legs cannot be read")
                    continue
                for lg in lf:
                    held[lg["symbol"]] += q if lg["side"] == "buy" else -q
            if t.get("orphan_order"):
                order(dict(t["orphan_order"], client_order_id=f"{key}-open"), legs)
    return dict(held), orders, busy, unsure, notes


def reconcile(acct, state, ledgers, now):
    """One look at one account at `now`. Returns (red {stable key: message}, amber, info)."""
    positions, open_orders = state
    held, orders, busy, unsure, notes = ledger_book(ledgers)
    red, amber, info = {}, [f"paper/{acct}: {n}" for n in notes], []
    today = now.date()
    closed = is_session(today) and now.time() >= close_time(today)
    have = collections.defaultdict(float)
    for p in positions:
        q = abs(float(p.get("qty") or 0))
        have[norm(p.get("symbol"))] += -q if p.get("side") == "short" else q
    for s in sorted(set(have) | set(held)):
        a, e = have.get(s, 0.0), held.get(s, 0.0)
        exp = option_expiry(s)
        # an option past its expiry close is no longer expected: Alpaca removes it, or exercises / assigns it into
        # shares (which then show as shares no ledger holds); the ledger settles it at intrinsic
        if exp and exp < today:
            if a:
                amber.append(f"paper/{acct}: {s} {a:+g} still listed after its expiry {exp} "
                             "(awaiting Alpaca's expiry processing)")
            continue
        if exp == today and closed:
            continue
        if abs(a - e) < 1e-9:
            continue
        what = f"{s}: the account holds {a:+g}, the ledgers show {e:+g}"
        if s in unsure:
            amber.append(f"paper/{acct}: {what} - a fill in the ledger cannot be read")
        elif s in busy and (busy[s][0] is not None and now - busy[s][0] < LAG[busy[s][1]][0]):
            info.append(f"paper/{acct}: {what} - a ledger order on it is still live (the ledger lags the broker "
                        "by one run)")
        elif s in busy and (busy[s][0] is None or now - busy[s][0] < LAG[busy[s][1]][1]):
            sent = f"sent {busy[s][0]:%a %H:%M} ET" if busy[s][0] else "no send time"
            amber.append(f"paper/{acct}: {what} - its ledger order ({sent}) still reads live: the paper runs have "
                         "not refreshed the ledger since")
        elif s in busy:
            red[(acct, "position", s)] = (f"LEDGER STALE: paper/{acct} {what} - its ledger order (sent "
                                          f"{busy[s][0]:%a %d %b %H:%M} ET) still reads live: no paper run has "
                                          "refreshed the ledger")
        else:
            kind = "POSITION NOT IN LEDGER" if not e else "LEDGER POSITION NOT IN ACCOUNT" if not a else \
                "POSITION MISMATCH"
            red[(acct, "position", s)] = f"{kind}: paper/{acct} {what}"
    index = {i: n for n, (ids, _, _) in enumerate(orders) for i in ids}
    seen = set()
    children = {x.get("id") for o in open_orders for x in o.get("legs") or [] if x.get("id")}
    for o in open_orders:
        if o.get("id") in children:                # a multi-leg order's leg listed on its own: the parent counts
            continue
        n = next((index[x] for x in (o.get("client_order_id"), o.get("id")) if x in index), None)
        syms = sorted({norm(x.get("symbol")) for x in o.get("legs") or []}
                      | ({norm(o["symbol"])} if o.get("symbol") else set()))
        desc = f"{o.get('client_order_id') or o.get('id')} ({', '.join(syms)}; {o.get('status')})"
        if n is None:
            made = ts(o.get("submitted_at") or o.get("created_at"))
            if made and now - made < NEW_ORDER:    # sent moments ago; the sending run commits its ledger next
                info.append(f"paper/{acct}: open order {desc} sent {made:%H:%M} ET, not in a committed ledger yet")
            else:
                red[(acct, "order", o.get("id"))] = f"OPEN ORDER NOT IN LEDGER: paper/{acct} {desc}"
            continue
        seen.add(n)
        if not orders[n][1] or orders[n][1] in TERMINAL:
            red[(acct, "order", o.get("id"))] = (f"OPEN ORDER THE LEDGER SHOWS AS ENDED: paper/{acct} {desc}; "
                                                 f"ledger status {orders[n][1]}")
    lag = [ids[0] for n, (ids, st, _) in enumerate(orders) if st and st not in TERMINAL and n not in seen]
    if lag:
        info.append(f"paper/{acct}: {lag} live in the ledger, no longer open at Alpaca (the next paper run records "
                    "how they ended)")
    if not red:
        info.append(f"paper/{acct}: {sum(1 for v in have.values() if v)} position(s), {len(open_orders)} open "
                    "order(s) - they match the ledgers")
    return red, amber, info


def positions_check(now, state=None, read=None, sleep=time.sleep, wait=SECOND_LOOK):
    """Every account reconciled. A RED needs the same mismatch on a second look `wait` seconds later, with the
    account and the committed ledgers read again: a paper run may have sent an order and not yet pushed."""
    state, read = state or alpaca_state, read or read_ledgers

    def look():
        out, amber, info, seen = {}, [], [], set()
        for acct, (_, names) in ACCOUNTS.items():
            st = state(acct)                      # the account first, then the ledgers: never older than it
            if st == "unconfigured":
                (amber if os.environ.get("GITHUB_ACTIONS") == "true" else info).append(
                    f"paper/{acct}: no Alpaca keys here - positions not reconciled")
                continue
            if st is None:
                amber.append(f"paper/{acct}: Alpaca positions / orders unreadable - not reconciled")
                continue
            seen.add(acct)
            r, a, i = reconcile(acct, st, read(names), now)
            out.update(r)
            amber += a
            info += i
        return out, amber, info, seen

    first, amber, info, _ = look()
    if not first:
        return [], amber, info
    sleep(wait)
    second, amber, info, seen = look()
    red = [m for k, m in second.items() if k in first]
    amber += [f"seen once, the account was unreadable on the second look: {m}" for k, m in first.items()
              if k[0] not in seen]
    info += [f"cleared on a second look {wait} s later: {m}" for k, m in first.items()
             if k[0] in seen and k not in second]
    info += [f"seen once, checked again next run: {m}" for k, m in second.items() if k not in first]
    return red, amber, info


def upcoming(now, n=5):
    out = []
    d = now.date()
    days = [d if is_session(d) else shift(d, 1)]
    for _ in range(n - 1):
        days.append(shift(days[-1], 1))
    for s in seasons():
        st = load(os.path.join(ROOT, "universe", s, "event_status.json")).get("events", {})
        for day in days:
            names = sorted(t for t, ev in st.items() if ev.get("snapshot_session") == day.isoformat())
            if names:
                out.append(f"{day:%a %d %b}: {len(names)} snapshot(s) - {', '.join(names)}")
        out.append(f"{s}: {sum(1 for ev in st.values() if ev.get('status') == 'PENDING')} name(s) still PENDING a confirmed date")
    return out


def run(write=False, commit=False, now=None):
    now = now or now_et()
    red, amber, info = [], [], []
    last, fails, rc = check_py()
    if rc != 0 or not last.startswith("PASS"):
        red.append(f"check.py: {last} {fails}")
    r, i = windows(now)
    red, info = red + r, info + i
    r, a, i = decisions(now)
    red, amber, info = red + r, amber + a, info + i
    fl = actions_failures(now)
    if fl is None:
        amber.append("GitHub Actions status unreadable (API)")
    else:
        for name, when, url, st in fl:
            (red if name in CRITICAL_WORKFLOWS else amber).append(f"Actions {st}: {name} at {when} {url}")
    r, a, i = ledgers(now)
    red, amber, info = red + r, amber + a, info + i
    for check in (ai_refusals, dates_stale):
        try:
            r, a = check(now)
        except Exception as e:
            r, a = [], [f"{check.__name__} crashed: {type(e).__name__}: {str(e)[:200]}"]
        red, amber = red + r, amber + a
    for check in (paper_window, positions_check):     # they parse outside JSON: a surprise is AMBER, not a crash
        try:
            r, a, i = check(now)
        except Exception as e:
            r, a, i = [], [f"{check.__name__} crashed: {type(e).__name__}: {str(e)[:200]}"], []
        red, amber, info = red + r, amber + a, info + i
    for c in (capture_check(now), c1_capture_check(now)):
        if c:
            amber.append(c)
    info += upcoming(now)
    status = "RED" if red else "AMBER" if amber else "GREEN"
    md = [f"# Health {now:%Y-%m-%d %H:%M} ET - **{status}**", "", f"check.py: {last}", ""]
    for title, xs in (("RED - events or decisions being lost, or about to be", red), ("AMBER - look at", amber),
                      ("Information", info)):
        md.append(f"## {title}")
        md += [f"- {x}" for x in xs] or ["- none"]
        md.append("")
    text = "\n".join(md)
    print(text)
    if write:
        d = os.path.join(ROOT, "ops", "health")
        os.makedirs(d, exist_ok=True)
        for f in ("latest.md", f"{now:%Y-%m-%d}.md"):
            open(os.path.join(d, f), "w", encoding="utf-8", newline="\n").write(text + "\n")
        open(os.path.join(d, "status.txt"), "w", encoding="utf-8", newline="\n").write(status + "\n")
    if commit:
        from freeze import git, push_all
        git("add", "ops/health")
        if git("diff", "--cached", "--name-only"):
            git("commit", "-q", "-m", f"Health {now:%Y-%m-%d %H:%M} ET: {status} (code)\n\n"
                "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
            print(f"pushed: {push_all()}")
    return status, red, amber, info


def shapes():
    """Each configured account's open orders and positions, compact (the fields reconcile() reads)."""
    for acct in ACCOUNTS:
        st = alpaca_state(acct)
        if not isinstance(st, tuple):
            print(f"{acct}: {st}")
            continue
        for p in st[0]:
            print(f"{acct} position: {p.get('symbol')} qty {p.get('qty')} side {p.get('side')} {p.get('asset_class')}")
        for o in st[1]:
            legs = [(x.get('id', '')[:8], x.get('symbol'), x.get('status')) for x in o.get('legs') or []]
            print(f"{acct} open order: {str(o.get('id'))[:8]} {o.get('client_order_id')} class {o.get('order_class')!r} "
                  f"{o.get('status')} symbol {o.get('symbol')!r} submitted {o.get('submitted_at')} legs {legs}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--shapes" in a:
        shapes()
    run("--write" in a, "--commit" in a)
