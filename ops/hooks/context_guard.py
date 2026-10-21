"""Context guard: tells a laptop chat when to hand off to a fresh chat.

CLAUDE.md's fresh-chat rule, in code. Claude Code runs this on UserPromptSubmit and
PostToolUse (.claude/settings.json). It reads the latest main-chain `usage` in the
session transcript and takes context = input + cache-read + cache-creation tokens
(the status line's formula). Above the calibrated thresholds it injects an
instruction for Claude and a one-line notice for Jacob.

Calibration (ops/token_efficiency_2026-10.md): hand off at 300k context tokens,
heads-up at 250k, and 200k in the two hours before a time-critical window.

It never blocks: every path exits 0, and any error prints nothing. It is silent
off the Windows laptop, because the cloud routines and GitHub Actions clone this
repo too and must do only what their prompts say.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, time
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
WINDOW = 1_000_000       # Opus 5.5 runs with a 1M window by default (code.claude.com model-config)
HANDOFF = 300_000        # the calibrated hand-off point
HEADSUP = 250_000        # finish the current step; start no new phase here
PRE_WINDOW = 200_000     # "already long" before a time-critical window
REMIND_EVERY = 20        # PostToolUse repeats a standing hand-off notice every N tool calls
TAIL_BYTES = 256 * 1024  # first read from the transcript's end; doubled while nothing is found
MAX_TAIL = 32 * 1024 * 1024

# Time-critical windows, US Eastern, weekdays: (what, lead-up from, starts, ends).
WINDOWS = (
    ("the T2 deadline", time(7, 15), time(9, 15), time(9, 15)),
    ("the gates and paper exits", time(12, 30), time(14, 30), time(15, 56)),
)
RANK = {None: 0, "heads_up": 1, "pre_window": 2, "handoff": 3}


def latest_usage(path, tail=TAIL_BYTES):
    """Context tokens and model of the newest main-chain API response, or None."""
    size = os.path.getsize(path)
    while True:
        n = min(tail, size)
        with open(path, "rb") as f:
            f.seek(size - n)
            lines = f.read(n).split(b"\n")
        if n < size:
            lines = lines[1:]  # the first line is cut
        for raw in reversed(lines):
            if b'"usage"' not in raw:
                continue
            try:
                rec = json.loads(raw)
            except ValueError:
                continue
            msg = rec.get("message") or {}
            u = msg.get("usage")
            if (rec.get("type") != "assistant" or rec.get("isSidechain") or not u
                    or msg.get("model") == "<synthetic>" or rec.get("isApiErrorMessage")):
                continue
            ctx = sum(int(u.get(k) or 0) for k in
                      ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
            return {"ctx": ctx, "model": msg.get("model") or ""}
        if n >= size or tail >= MAX_TAIL:
            return None
        tail *= 2


def started_by_session(path):
    """True when the chat's first prompt came from another session, not from Jacob."""
    with open(path, "rb") as f:
        head = f.read(512 * 1024).split(b"\n")
    for raw in head:
        if b'"user"' not in raw:
            continue
        try:
            rec = json.loads(raw)
        except ValueError:
            continue
        if rec.get("type") != "user" or rec.get("isMeta") or rec.get("isSidechain"):
            continue
        if (rec.get("origin") or {}).get("kind") == "human":
            return False
        return rec.get("turnOrigin") not in (None, "human")
    return False


def window_phase(now):
    """('lead' | 'in' | None, what, starts, ends, minutes to start) for a weekday ET time."""
    if now.weekday() >= 5:
        return None, "", None, None, 0
    t = now.time()
    for what, lead, start, end in WINDOWS:
        if lead <= t < start:
            mins = (start.hour * 60 + start.minute) - (t.hour * 60 + t.minute)
            return "lead", what, start, end, mins
        if start <= t < end:
            return "in", what, start, end, 0
    return None, "", None, None, 0


def assess(ctx, now, window=WINDOW, side=False):
    """(level, text for Claude, notice for Jacob), or (None, '', '') when all is well."""
    hand, head, pre = min(HANDOFF, window * 3 // 4), min(HEADSUP, window * 3 // 5), min(PRE_WINDOW, window // 2)
    phase, what, start, end, mins = window_phase(now)
    if ctx >= hand:
        level = "handoff"
    elif phase == "lead" and ctx >= pre:
        level = "pre_window"
    elif ctx >= head:
        level = "heads_up"
    else:
        return None, "", ""
    k, pct, hk = round(ctx / 1000), round(100 * ctx / window), hand // 1000
    wk = f"{window // 1_000_000}M" if window % 1_000_000 == 0 else f"{window // 1000}k"
    size = f"{k}k context tokens ({pct}% of the {wk} window)"
    where = "ops/token_efficiency_2026-10.md"
    if side:
        step4 = ("(4) this chat was started by another session, so the app will not start one from here: "
                 "end your turn with a report saying a fresh chat should continue, with `pre earnings model`, "
                 "the next task, the files involved and what done looks like")
    else:
        step4 = ("(4) start_session (context \"fresh\") with a prompt that begins `pre earnings model` and names "
                 "the next task, the files involved and what done looks like, so the new chat re-reads little")
    steps = ("(1) finish the current step and start no new one; (2) update STATE.md and JOURNAL.md; "
             "(3) commit explicit paths, then `git push github main` and `git push local main`; "
             f"{step4}; (5) stop working in this chat, and tell Jacob in one line that you are handing off and why.")

    if phase == "in":
        e = end.strftime("%H:%M")
        text = (f"CONTEXT GUARD: this chat holds {size}, inside the {start:%H:%M}-{e} ET window "
                f"({what}). Do not hand off or commit mid-window (CLAUDE.md: no commits 14:30-15:50 ET on a "
                f"snapshot day). Keep this chat to the window's work, and hand off right after {e} ET: {steps}")
        note = f"Context guard: {k}k tokens. Hand-off due after {e} ET, once the window closes."
        return level, text, note
    if level == "handoff":
        before = f" Do it before {start:%H:%M} ET, when {what} begin." if phase == "lead" else ""
        text = (f"CONTEXT GUARD: HAND OFF NOW. This chat holds {size}; the calibrated hand-off point is "
                f"{hk}k ({where}). Every further call re-reads the whole context. CLAUDE.md's fresh-chat "
                f"rule: {steps}{before}")
        note = f"Context guard: {k}k tokens, past the {hk}k hand-off point. Claude will wrap up and move to a fresh chat."
        return level, text, note
    if level == "pre_window":
        text = (f"CONTEXT GUARD: {what} start at {start:%H:%M} ET, in {mins} min, and this chat is already long "
                f"({size}). CLAUDE.md: hand off before a time-critical window, so the window runs in a fresh "
                f"chat. Do it now and commit before {start:%H:%M} ET: {steps}")
        note = f"Context guard: {k}k tokens with {what} in {mins} min. Claude will hand off to a fresh chat first."
        return level, text, note
    text = (f"CONTEXT GUARD: heads-up. This chat holds {size}; the hand-off point is {hk}k ({where}). "
            "Finish the current step here, start no new phase in this chat, and plan the hand-off "
            "(STATE, JOURNAL, commit and push, then a fresh chat with `pre earnings model`).")
    note = f"Context guard: {k}k tokens. Hand-off at {hk}k."
    return level, text, note


def should_emit(state_dir, session_id, event, level):
    """UserPromptSubmit always speaks. PostToolUse speaks on a new level, then every REMIND_EVERY calls."""
    path = os.path.join(state_dir, "".join(c for c in session_id if c.isalnum() or c in "-_") + ".json")
    try:
        with open(path, encoding="utf-8") as f:
            st = json.load(f)
    except (OSError, ValueError):
        st = {"level": None, "n": 0}
    emit = False
    if event == "UserPromptSubmit" or RANK.get(level, 0) > RANK.get(st.get("level"), 0):
        emit, n = level is not None, 0
    else:
        n = int(st.get("n") or 0) + 1
        if level == "handoff" and n >= REMIND_EVERY:
            emit, n = True, 0
    os.makedirs(state_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"level": level, "n": n}, f)
    return emit


def main(stdin_text, now=None, platform=sys.platform, env=None, state_dir=None):
    """The hook's whole output (a JSON string), or '' to stay silent."""
    env = os.environ if env is None else env
    if platform != "win32" and env.get("CONTEXT_GUARD_ANY_OS") != "1":
        return ""
    if env.get("GITHUB_ACTIONS") or env.get("CLAUDE_CODE_REMOTE", "").lower() in ("1", "true"):
        return ""
    data = json.loads(stdin_text or "{}")
    event = data.get("hook_event_name") or ""
    if event not in ("UserPromptSubmit", "PostToolUse") or data.get("agent_id"):
        return ""
    path = data.get("transcript_path") or ""
    if not path or not os.path.isfile(path):
        return ""
    u = latest_usage(path)
    if not u:
        return ""
    window = 200_000 if env.get("CLAUDE_CODE_DISABLE_1M_CONTEXT") == "1" else WINDOW
    level, text, note = assess(u["ctx"], now or datetime.now(ET), window, side=started_by_session(path))
    state_dir = state_dir or os.path.join(tempfile.gettempdir(), "claude-context-guard")
    if not should_emit(state_dir, data.get("session_id") or "unknown", event, level):
        return ""
    return json.dumps({"systemMessage": note,
                       "hookSpecificOutput": {"hookEventName": event, "additionalContext": text}})


if __name__ == "__main__":
    try:
        out = main(sys.stdin.read())
        if out:
            sys.stdout.write(out)
    except BaseException:  # never block, never complain
        pass
    sys.exit(0)
