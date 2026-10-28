"""Context guard: makes a laptop chat hand off to a fresh chat. Enforced since 2026-10-27.

CLAUDE.md's fresh-chat rule, in code (Jacob, 2026-10-27: "I want this to be enforced"). Claude Code
runs this on UserPromptSubmit, PreToolUse and PostToolUse (.claude/settings.json). It reads the
latest main-chain `usage` in the session transcript and takes context = input + cache-read +
cache-creation tokens (the status line's formula).

- Over the line, PreToolUse REFUSES every tool call except the hand-off steps: reading and editing
  STATE.md and JOURNAL.md, git add/commit/push, check.py, start_session and the app's turn tools.
- Inside a live window (T2 freezes 07:15-09:15 ET, gates and paper exits 14:30-15:56 ET) it never
  refuses. It says finish the window's work and hand off when the window closes.
- A turn that another session started cannot start a chat, so it is told to end its turn with the
  brief as its report.
- Jacob lifts the refusals for one turn by typing "override the guard".
- UserPromptSubmit and PostToolUse inject the instruction for Claude and a one-line notice for Jacob.

Calibration (ops/token_efficiency_2026-10.md): hand off at 300k context tokens, heads-up at 250k,
and 200k in the two hours before a time-critical window.

Any error allows the call and prints nothing. It is silent off the Windows laptop, because the
cloud routines and GitHub Actions clone this repo too (cloud sessions load project hooks) and must
do only what their prompts say.
"""
from __future__ import annotations

import json
import os
import re
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
OVERRIDE = "override the guard"  # Jacob's words, in his own prompt, lift the refusals for that turn

# Time-critical windows, US Eastern, weekdays: (what, lead-up from, starts, ends, commits allowed inside).
# The T2 window is the last two hours before the 09:15 ET deadline, when a missing T2 is rescued.
WINDOWS = (
    ("the T2 freezes before the 09:15 ET deadline", time(5, 15), time(7, 15), time(9, 15), True),
    ("the gates and paper exits", time(12, 30), time(14, 30), time(15, 56), False),
)
RANK = {None: 0, "heads_up": 1, "pre_window": 2, "handoff": 3}
# The hand-off brief (CLAUDE.md's fresh-chat rule). A brief-less fresh chat re-read ~100k before its first edit.
BRIEF = ("the brief template in CLAUDE.md's fresh-chat rule: `pre earnings model`, TASK, DONE, DECIDED, "
         "READ ONLY (path:lines), FACTS, RULES THAT BITE, NEXT STEP, CLOCK")

# What a chat over the line may still do: the hand-off steps and nothing else.
HANDOFF_FILES = {"state.md", "journal.md"}
NOTES_DIR = "/side-session-notes/"  # the app's shared notes folder, where a brief can be left
FILE_TOOLS = {"Read": "file_path", "Edit": "file_path", "MultiEdit": "file_path", "Write": "file_path",
              "Grep": "path"}
FREE_TOOLS = {"ToolSearch", "SendMessage", "AskUserQuestion", "ListAgents"}
FREE_PREFIXES = ("mcp__ccd_turn__", "mcp__ccd_session__", "mcp__ccd_session_mgmt__get_usage",
                 "mcp__ccd_session_mgmt__list_sessions")
GIT_STEPS = {"add", "commit", "push", "pull", "fetch", "rebase", "merge", "status", "diff", "log", "show",
             "rev-parse", "branch"}
SHELL_STEPS = {"cd", "date", "get-date", "head", "tail", "select-object", "out-string"}
ALLOWED = ("reading and editing STATE.md and JOURNAL.md (and the shared side-session notes), git status, diff, "
           "log, add, commit and push (fetch, pull, rebase or merge when a push is refused), `python check.py`, "
           "ToolSearch, start_session, SendMessage, AskUserQuestion and the app's plan and wrap-up tools")


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


def _prompt(raw):
    """(came from Jacob, text) for a transcript line that is a prompt, else None."""
    try:
        rec = json.loads(raw)
    except ValueError:
        return None
    if rec.get("type") != "user" or rec.get("isMeta") or rec.get("isSidechain"):
        return None
    c = (rec.get("message") or {}).get("content")
    if isinstance(c, list):
        if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in c):
            return None
        c = " ".join(b.get("text") or "" for b in c if isinstance(b, dict))
    human = (rec.get("origin") or {}).get("kind") == "human" or rec.get("turnOrigin") in (None, "human")
    return human, c if isinstance(c, str) else ""


def started_by_session(path):
    """True when the chat's first prompt came from another session, not from Jacob."""
    with open(path, "rb") as f:
        head = f.read(512 * 1024).split(b"\n")
    for raw in head:
        if b'"user"' in raw and (p := _prompt(raw)):
            return not p[0]
    return False


def last_prompt(path):
    """(came from Jacob, text) of the turn now running, or (False, '') when none is found."""
    size = os.path.getsize(path)
    n = min(4 * TAIL_BYTES, size)
    with open(path, "rb") as f:
        f.seek(size - n)
        lines = f.read(n).split(b"\n")
    for raw in reversed(lines[1:] if n < size else lines):
        if b'"user"' in raw and (p := _prompt(raw)):
            return p
    return False, ""


def window_phase(now):
    """('lead' | 'in' | None, the window, minutes to its start) for a weekday ET time."""
    if now.weekday() >= 5:
        return None, None, 0
    t = now.time()
    for w in WINDOWS:
        _, lead, start, end, _ = w
        if lead <= t < start:
            return "lead", w, (start.hour * 60 + start.minute) - (t.hour * 60 + t.minute)
        if start <= t < end:
            return "in", w, 0
    return None, None, 0


def assess(ctx, now, window=WINDOW, side=False):
    """(level, text for Claude, notice for Jacob), or (None, '', '') when all is well."""
    hand, head, pre = min(HANDOFF, window * 3 // 4), min(HEADSUP, window * 3 // 5), min(PRE_WINDOW, window // 2)
    phase, w, mins = window_phase(now)
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
        step4 = ("(4) this turn was started by another session, so the app will not start a chat from here: "
                 f"end your turn with a report whose first line says HAND-OFF and that holds {BRIEF}, and says "
                 "a fresh chat should continue from it")
    else:
        step4 = (f"(4) start_session (context \"fresh\") with {BRIEF}, so the new chat runs "
                 "`python ops/startup.py` and re-reads nothing else; if the app refuses the start, propose it "
                 "(initiation \"own_initiative\"), and if that is refused too, end your turn with the brief as "
                 "your report")
    steps = ("(1) finish the current step and start no new one; (2) rewrite STATE.md's NOW block, and add the "
             "Log and JOURNAL.md entries; (3) commit explicit paths, then `git push github HEAD:main` and "
             f"`git push local HEAD:main`; {step4}; (5) stop working in this chat, and tell Jacob in one line that "
             "you are handing off and why.")
    enforced = ("The guard now refuses every tool call except the hand-off steps, and only Jacob can lift that. "
                "CLAUDE.md's fresh-chat rule: ")

    if phase == "in":
        what, _, start, end, commits = w
        e = end.strftime("%H:%M")
        if commits:
            inside = (f"Keep this chat to the window's work: freeze and commit what the deadline needs before {e} ET, "
                      f"then hand off right after {e} ET, when the guard starts refusing other work: ")
        else:
            inside = (f"Do not hand off or commit mid-window (CLAUDE.md: no commits {start:%H:%M}-{e} ET on a "
                      f"weekday). Keep this chat to the window's work, and hand off right after {e} ET, when the "
                      "guard starts refusing other work: ")
        text = (f"CONTEXT GUARD: this chat holds {size}, inside the {start:%H:%M}-{e} ET window ({what}). "
                f"The guard refuses nothing mid-window. {inside}{steps}")
        note = f"Context guard: {k}k tokens. Hand-off due after {e} ET, once the window closes."
        return level, text, note
    if level == "handoff":
        before = f" Do it before {w[2]:%H:%M} ET, when {w[0]} begin." if phase == "lead" else ""
        text = (f"CONTEXT GUARD: HAND OFF NOW. This chat holds {size}; the calibrated hand-off point is "
                f"{hk}k ({where}). Every further call re-reads the whole context. {enforced}{steps}{before}")
        note = (f"Context guard: {k}k tokens, past the {hk}k hand-off point. Claude must wrap up and move to a "
                f"fresh chat; to keep going here for one turn, type \"{OVERRIDE}\".")
        return level, text, note
    if level == "pre_window":
        what, start = w[0], w[2]
        text = (f"CONTEXT GUARD: {what} start at {start:%H:%M} ET, in {mins} min, and this chat is already long "
                f"({size}). CLAUDE.md: hand off before a time-critical window, so the window runs in a fresh "
                f"chat. Do it now and commit before {start:%H:%M} ET. {enforced}{steps}")
        note = (f"Context guard: {k}k tokens with {what} in {mins} min. Claude must hand off to a fresh chat "
                f"first; to keep going here for one turn, type \"{OVERRIDE}\".")
        return level, text, note
    text = (f"CONTEXT GUARD: heads-up. This chat holds {size}; the hand-off point is {hk}k ({where}), where the "
            "guard starts refusing every tool call except the hand-off steps. Finish the current step here, start "
            "no new phase in this chat, and plan the hand-off (STATE.md's NOW block, JOURNAL, commit and push, "
            f"then a fresh chat with {BRIEF}).")
    note = f"Context guard: {k}k tokens. Hand-off at {hk}k."
    return level, text, note


def must_hand_off(ctx, now, window=WINDOW, anytime=False):
    """True when the chat is past the line and no live window is open: only the hand-off steps may run."""
    return assess(ctx, now, window)[0] in ("handoff", "pre_window") and (anytime or window_phase(now)[0] != "in")


def drill_tokens(state_dir, now_ts):
    """Tokens a live drill adds, from <state dir>/drill.json until its `until` (epoch seconds), else 0.

    A drill can only make the guard stricter: it adds tokens and lifts the live-window exemption."""
    try:
        with open(os.path.join(state_dir, "drill.json"), encoding="utf-8") as f:
            d = json.load(f)
        return max(0, int(d.get("add") or 0)) if now_ts < float(d.get("until") or 0) else 0
    except (OSError, ValueError, TypeError, AttributeError):
        return 0


def handoff_command(cmd):
    """True when every command in a shell line is a hand-off step (git, check.py, the clock, cd, filters)."""
    # Quoted text becomes one placeholder word, so `git -C "C:\a b" merge` keeps -C's argument.
    s = re.sub(r"<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n.*?\n\s*\1[ \t]*(?=\r?\n|$)", " _ ", cmd, flags=re.S)  # heredocs
    s = re.sub(r"@(['\"])[ \t]*\r?\n.*?\r?\n\1@", " _ ", s, flags=re.S)                            # here-strings
    s = re.sub(r"'[^']*'|\"(?:[^\"\\`]|[\\`].)*\"", " _ ", s, flags=re.S)                           # quoted text
    s = re.sub(r"\d?>>?&?\d?", " ", s)                                                             # redirections
    s = re.sub(r"\bif\s*\(\s*\$\?\s*\)|[{}()$]", " ", s)                                           # if ($?) { }
    segments = [seg.split() for seg in re.split(r"&&|\|\||[;|\r\n]", s)]
    segments = [seg for seg in segments if seg]
    if not segments:
        return False
    for seg in segments:
        while seg and re.fullmatch(r"\w+=\S*", seg[0]):   # VAR=value prefixes
            seg = seg[1:]
        if not seg:
            continue
        exe = re.sub(r"\.exe$", "", seg[0].replace("\\", "/").rsplit("/", 1)[-1].lower())
        if exe == "git":
            rest, sub = seg[1:], None
            while rest:
                if rest[0] in ("-C", "-c"):
                    rest = rest[2:]
                elif rest[0].startswith("-"):
                    rest = rest[1:]
                else:
                    sub = rest[0]
                    break
            if sub not in GIT_STEPS:
                return False
        elif exe in ("python", "python3", "py"):
            if not any(a.replace("\\", "/").rsplit("/", 1)[-1] == "check.py" for a in seg[1:]):
                return False
        elif exe not in SHELL_STEPS:
            return False
    return True


def allowed(tool, inp):
    """True for a hand-off step: the only calls a chat past the line may make."""
    inp = inp if isinstance(inp, dict) else {}
    if tool in FREE_TOOLS or tool.startswith(FREE_PREFIXES):
        return True
    if tool in FILE_TOOLS:
        p = str(inp.get(FILE_TOOLS[tool]) or "").replace("\\", "/")
        return p.rsplit("/", 1)[-1].lower() in HANDOFF_FILES or NOTES_DIR in p.lower()
    if tool in ("Bash", "PowerShell"):
        return handoff_command(str(inp.get("command") or ""))
    return False


def refusal(tool, ctx, now, window, side):
    """The PreToolUse output that refuses a call."""
    text = assess(ctx, now, window, side)[1]
    reason = (f"CONTEXT GUARD refused {tool}: the fresh-chat rule is enforced and this chat is past the line. "
              f"It is {now:%a %Y-%m-%d %H:%M} ET. Allowed now: {ALLOWED}. {text}")
    return {"systemMessage": f"Context guard: refused {tool} at {round(ctx / 1000)}k tokens; Claude must hand off.",
            "hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                   "permissionDecisionReason": reason}}


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
    """The hook's whole output (a JSON string), or '' to stay silent (and, on PreToolUse, allow)."""
    env = os.environ if env is None else env
    if platform != "win32" and env.get("CONTEXT_GUARD_ANY_OS") != "1":
        return ""
    if env.get("GITHUB_ACTIONS") or env.get("CLAUDE_CODE_REMOTE", "").lower() in ("1", "true"):
        return ""
    data = json.loads((stdin_text or "{}").lstrip("﻿"))
    event = data.get("hook_event_name") or ""
    if event not in ("UserPromptSubmit", "PreToolUse", "PostToolUse") or data.get("agent_id"):
        return ""
    path = data.get("transcript_path") or ""
    if not path or not os.path.isfile(path):
        return ""
    u = latest_usage(path)
    if not u:
        return ""
    # Drills: the env knobs (tests) add tokens and set the clock (an ISO time, ET); drill.json (a live chat) adds
    # tokens for a few minutes. None is ever set in use.
    state_dir = state_dir or os.path.join(tempfile.gettempdir(), "claude-context-guard")
    live = drill_tokens(state_dir, (now or datetime.now(ET)).timestamp())
    ctx = u["ctx"] + int(env.get("CONTEXT_GUARD_DRILL_ADD") or 0) + live
    drill_at = env.get("CONTEXT_GUARD_DRILL_AT")
    window = 200_000 if env.get("CLAUDE_CODE_DISABLE_1M_CONTEXT") == "1" else WINDOW
    now = now or (datetime.fromisoformat(drill_at).replace(tzinfo=ET) if drill_at else datetime.now(ET))

    if event == "PreToolUse":
        tool = data.get("tool_name") or ""
        if not must_hand_off(ctx, now, window, anytime=bool(live)) or allowed(tool, data.get("tool_input")):
            return ""
        jacob, said = last_prompt(path)
        if jacob and OVERRIDE in said.lower():
            return ""
        side = started_by_session(path) and not jacob
        return json.dumps(refusal(tool, ctx, now, window, side))

    side = started_by_session(path) and not last_prompt(path)[0]
    level, text, note = assess(ctx, now, window, side=side)
    if not should_emit(state_dir, data.get("session_id") or "unknown", event, level):
        return ""
    return json.dumps({"systemMessage": note,
                       "hookSpecificOutput": {"hookEventName": event, "additionalContext": text}})


if __name__ == "__main__":
    try:
        out = main(sys.stdin.read())
        if out:
            sys.stdout.write(out)
    except BaseException:  # never block by accident, never complain
        pass
    sys.exit(0)
