"""ops/hooks/context_guard.py: the fresh-chat rule's hook (calibration: ops/token_efficiency_2026-10.md)."""
import importlib.util
import json
import subprocess
import sys
import time as _time
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "ops" / "hooks" / "context_guard.py"
spec = importlib.util.spec_from_file_location("context_guard", HOOK)
cg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cg)

WED = lambda h, m: datetime(2026, 10, 21, h, m, tzinfo=cg.ET)  # a Wednesday
SAT = lambda h, m: datetime(2026, 10, 24, h, m, tzinfo=cg.ET)


def assistant(ctx, side=False, model="claude-opus-5-5", cr_share=0.9):
    cr = int(ctx * cr_share)
    return {"type": "assistant", "isSidechain": side,
            "message": {"model": model, "usage": {"input_tokens": 2, "cache_read_input_tokens": cr,
                                                  "cache_creation_input_tokens": ctx - cr - 2,
                                                  "output_tokens": 500}}}


def human(kind="human"):
    if kind == "human":
        return {"type": "user", "origin": {"kind": "human"}, "turnOrigin": "human",
                "message": {"role": "user", "content": "pre earnings model"}}
    return {"type": "user", "turnOrigin": "sdk", "message": {"role": "user", "content": "task from a session"}}


def transcript(tmp_path, recs, name="s.jsonl"):
    p = tmp_path / name
    p.write_text("".join(json.dumps(r) + "\n" for r in recs), encoding="utf-8")
    return p


def run(tmp_path, recs, event="UserPromptSubmit", now=None, **extra):
    p = transcript(tmp_path, recs)
    stdin = json.dumps({"session_id": "abc", "transcript_path": str(p), "hook_event_name": event, **extra})
    return cg.main(stdin, now=now or WED(10, 0), platform="win32", env={}, state_dir=str(tmp_path / "st"))


# --- reading the transcript -------------------------------------------------------------------

def test_latest_usage_is_the_last_main_chain_response(tmp_path):
    p = transcript(tmp_path, [human(), assistant(100_000), assistant(150_000),
                              assistant(900_000, side=True),                       # a subagent's call
                              assistant(0, model="<synthetic>", cr_share=0),       # an API error stub
                              {"type": "user", "message": {"content": [{"type": "tool_result"}]}}])
    assert cg.latest_usage(str(p))["ctx"] == 150_000


def test_latest_usage_reaches_past_a_huge_last_line(tmp_path):
    big = {"type": "user", "message": {"content": "x" * (3 * cg.TAIL_BYTES)}}
    p = transcript(tmp_path, [human(), assistant(320_000), big])
    assert cg.latest_usage(str(p))["ctx"] == 320_000


def test_latest_usage_none_when_no_response_yet(tmp_path):
    assert cg.latest_usage(str(transcript(tmp_path, [human()]))) is None


def test_side_session_is_detected_from_the_first_prompt(tmp_path):
    q = {"type": "queue-operation", "operation": "enqueue"}
    assert cg.started_by_session(str(transcript(tmp_path, [q, human("sdk"), assistant(1)], "a.jsonl")))
    assert not cg.started_by_session(str(transcript(tmp_path, [q, human(), assistant(1)], "b.jsonl")))


# --- thresholds and clock -----------------------------------------------------------------------

@pytest.mark.parametrize("ctx,level", [(120_000, None), (249_999, None), (250_000, "heads_up"),
                                       (299_999, "heads_up"), (300_000, "handoff"), (705_000, "handoff")])
def test_levels_outside_windows(ctx, level):
    assert cg.assess(ctx, WED(10, 0))[0] == level


def test_handoff_text_carries_the_rule():
    level, text, note = cg.assess(312_000, WED(10, 0))
    assert level == "handoff" and "312k" in text and "31%" in text and "300k" in text
    for must in ("STATE.md", "JOURNAL.md", "git push github HEAD:main", "git push local HEAD:main",
                 "start_session", "pre earnings model", "refuses every tool call"):
        assert must in text
    assert "312k" in note


def test_side_session_is_not_told_to_start_a_session():
    text = cg.assess(312_000, WED(10, 0), side=True)[1]
    assert "start_session" not in text and "started by another session" in text


BRIEF_FIELDS = ("TASK", "DONE", "DECIDED", "READ ONLY (path:lines)", "FACTS", "RULES THAT BITE", "NEXT STEP", "CLOCK")


@pytest.mark.parametrize("ctx,now,side", [(312_000, WED(10, 0), False), (312_000, WED(10, 0), True),
                                          (260_000, WED(10, 0), False), (210_000, WED(13, 30), False),
                                          (320_000, WED(15, 0), False)])
def test_every_hand_off_text_asks_for_the_lean_brief(ctx, now, side):
    text = cg.assess(ctx, now, side=side)[1]
    assert "CLAUDE.md's fresh-chat rule" in text and "NOW block" in text
    for field in BRIEF_FIELDS:
        assert field in text


def test_the_new_chat_is_told_to_start_lean():
    assert "`python ops/startup.py` and re-reads nothing else" in cg.assess(312_000, WED(10, 0))[1]


def test_claude_md_holds_the_template_the_hook_names():
    md = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    for field in ("TASK:", "DONE =", "DECIDED:", "READ ONLY:", "FACTS:", "RULES THAT BITE:", "NEXT STEP:", "CLOCK:"):
        assert field in md
    assert "python ops/startup.py" in md and "NOW block" in md


def test_lead_up_to_the_gates_lowers_the_bar():
    level, text, note = cg.assess(210_000, WED(13, 30))
    assert level == "pre_window" and "14:30" in text and "60 min" in text
    assert cg.assess(190_000, WED(13, 30))[0] is None
    assert cg.assess(210_000, SAT(13, 30))[0] is None        # no window at the weekend
    assert cg.assess(210_000, WED(12, 29))[0] is None        # lead-up starts 12:30


def test_lead_up_to_the_t2_window():
    level, text, _ = cg.assess(205_000, WED(6, 0))
    assert level == "pre_window" and "07:15" in text and "75 min" in text


def test_inside_the_t2_window_commits_are_the_work():
    level, text, note = cg.assess(320_000, WED(8, 0))
    assert level == "handoff" and "refuses nothing mid-window" in text and "commit what the deadline needs" in text
    assert "Do not hand off or commit" not in text and "09:15" in note
    assert not cg.must_hand_off(320_000, WED(8, 0))


def test_inside_the_gate_window_no_handoff_or_commit():
    level, text, note = cg.assess(320_000, WED(15, 0))
    assert level == "handoff" and "Do not hand off or commit mid-window" in text and "15:56" in note
    assert cg.assess(210_000, WED(15, 0))[0] is None         # under heads-up: silent mid-window
    assert cg.assess(320_000, WED(15, 56))[1].startswith("CONTEXT GUARD: HAND OFF NOW")


def test_handoff_in_lead_up_names_the_deadline():
    assert "before 14:30 ET" in cg.assess(330_000, WED(14, 0))[1]


def test_a_200k_window_scales_the_thresholds():
    assert cg.assess(150_000, WED(10, 0), window=200_000)[0] == "handoff"
    assert cg.assess(119_000, WED(10, 0), window=200_000)[0] is None


# --- the hook as Claude Code calls it -----------------------------------------------------------

def test_prompt_output_shape(tmp_path):
    out = json.loads(run(tmp_path, [human(), assistant(330_000)]))
    assert out["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    assert "HAND OFF NOW" in out["hookSpecificOutput"]["additionalContext"]
    assert out["systemMessage"].startswith("Context guard: 330k")
    assert "decision" not in out and "continue" not in out     # never blocks


def test_quiet_when_small(tmp_path):
    assert run(tmp_path, [human(), assistant(150_000)]) == ""


def test_post_tool_use_speaks_on_a_new_level_then_every_n_calls(tmp_path):
    recs = [human(), assistant(310_000)]
    outs = [run(tmp_path, recs, event="PostToolUse") for _ in range(cg.REMIND_EVERY + 1)]
    assert outs[0] and not any(outs[1:cg.REMIND_EVERY]) and outs[cg.REMIND_EVERY]


def test_post_tool_use_escalates_from_heads_up(tmp_path):
    assert run(tmp_path, [human(), assistant(260_000)], event="PostToolUse")
    assert run(tmp_path, [human(), assistant(262_000)], event="PostToolUse") == ""
    assert "HAND OFF NOW" in run(tmp_path, [human(), assistant(301_000)], event="PostToolUse")


def test_silent_inside_a_subagent(tmp_path):
    assert run(tmp_path, [human(), assistant(400_000)], event="PostToolUse", agent_id="x1") == ""


def test_silent_off_the_laptop(tmp_path):
    p = transcript(tmp_path, [human(), assistant(400_000)])
    stdin = json.dumps({"session_id": "a", "transcript_path": str(p), "hook_event_name": "UserPromptSubmit"})
    assert cg.main(stdin, now=WED(10, 0), platform="linux", env={}, state_dir=str(tmp_path)) == ""
    for env in ({"GITHUB_ACTIONS": "true"}, {"CLAUDE_CODE_REMOTE": "true"}):
        assert cg.main(stdin, now=WED(10, 0), platform="win32", env=env, state_dir=str(tmp_path)) == ""


def test_other_events_and_missing_transcript_are_silent(tmp_path):
    assert run(tmp_path, [human(), assistant(400_000)], event="Stop") == ""
    stdin = json.dumps({"session_id": "a", "transcript_path": str(tmp_path / "nope.jsonl"),
                        "hook_event_name": "UserPromptSubmit"})
    assert cg.main(stdin, platform="win32", env={}, state_dir=str(tmp_path)) == ""


@pytest.mark.parametrize("stdin", ["", "not json", "[]", '{"transcript_path": 5}'])
def test_script_never_fails_and_never_blocks(stdin, tmp_path):
    r = subprocess.run([sys.executable, str(HOOK)], input=stdin, capture_output=True, text=True, timeout=30,
                       env={"CONTEXT_GUARD_ANY_OS": "1", "SYSTEMROOT": "C:\\Windows", "TEMP": str(tmp_path)})
    assert r.returncode == 0 and r.stdout == ""


def test_script_is_fast_on_a_large_transcript(tmp_path):
    filler = {"type": "user", "message": {"content": [{"type": "tool_result", "content": "y" * 2000}]}}
    recs = [human()] + [r for i in range(2500) for r in (assistant(100_000 + 100 * i), filler)]
    p = transcript(tmp_path, recs)
    assert p.stat().st_size > 5_000_000
    stdin = json.dumps({"session_id": "big", "transcript_path": str(p), "hook_event_name": "UserPromptSubmit"})
    t0 = _time.perf_counter()
    r = subprocess.run([sys.executable, str(HOOK)], input=stdin, capture_output=True, text=True, timeout=30,
                       env={"CONTEXT_GUARD_ANY_OS": "1", "SYSTEMROOT": "C:\\Windows", "TEMP": str(tmp_path)})
    # the wording depends on the real clock (mid-window or not); the level does not
    assert r.returncode == 0 and "CONTEXT GUARD" in r.stdout and "350k" in r.stdout
    assert _time.perf_counter() - t0 < 5


# --- enforcement: PreToolUse refuses all but the hand-off steps (Jacob, 2026-10-27) ----------------

def prompt(text, kind="human"):
    rec = human(kind)
    rec["message"] = {"role": "user", "content": text}
    return rec


def pre(tmp_path, recs, tool="Bash", tool_input=None, now=None, **extra):
    out = run(tmp_path, recs, event="PreToolUse", now=now, tool_name=tool,
              tool_input={"command": "python -m pytest"} if tool_input is None else tool_input, **extra)
    return json.loads(out) if out else None


def test_past_the_line_new_work_is_refused(tmp_path):
    out = pre(tmp_path, [human(), assistant(312_000)])
    h = out["hookSpecificOutput"]
    assert h["hookEventName"] == "PreToolUse" and h["permissionDecision"] == "deny"
    reason = h["permissionDecisionReason"]
    for must in ("refused Bash", "Wed 2026-10-21 10:00 ET", "STATE.md", "git push github HEAD:main",
                 "start_session", "READ ONLY (path:lines)"):
        assert must in reason
    assert out["systemMessage"].startswith("Context guard: refused Bash at 312k")


@pytest.mark.parametrize("tool,tool_input", [
    ("Read", {"file_path": r"C:\Users\jacob\x\Earnings Experiment\STATE.md"}),
    ("Edit", {"file_path": "/c/x/JOURNAL.md"}),
    ("Write", {"file_path": r"C:\Users\jacob\AppData\Local\Claude-Data\c\side-session-notes\local_1\handoff.md"}),
    ("Grep", {"pattern": "## Log", "path": "STATE.md"}),
    ("Bash", {"command": "git add STATE.md JOURNAL.md && git commit -m 'x' && git push github HEAD:main"}),
    ("PowerShell", {"command": "python ops/check.py"}),
    ("ToolSearch", {"query": "select:mcp__ccd_session__start_session"}),
    ("mcp__ccd_session__start_session", {}),
    ("mcp__ccd_turn__wrap_up", {}),
    ("mcp__ccd_session_mgmt__get_usage", {}),
    ("SendMessage", {}),
])
def test_past_the_line_the_hand_off_steps_run(tmp_path, tool, tool_input):
    assert pre(tmp_path, [human(), assistant(400_000)], tool, tool_input) is None


@pytest.mark.parametrize("tool,tool_input", [
    ("Read", {"file_path": "FRAMEWORK.md"}), ("Read", {"file_path": "ops/state_history/STATE_2026.md"}),
    ("Edit", {"file_path": "pipeline/due.py"}), ("Grep", {"pattern": "x"}), ("Glob", {"pattern": "*"}),
    ("Agent", {"prompt": "x"}), ("WebSearch", {"query": "x"}), ("Bash", {"command": "gh run view 1 --log"}),
    ("mcp__ccd_session_mgmt__list_events", {}), ("Read", "not a dict"),
])
def test_past_the_line_everything_else_is_refused(tmp_path, tool, tool_input):
    assert pre(tmp_path, [human(), assistant(400_000)], tool, tool_input)["hookSpecificOutput"][
        "permissionDecision"] == "deny"


def test_under_the_line_nothing_is_refused(tmp_path):
    assert pre(tmp_path, [human(), assistant(299_000)]) is None
    assert pre(tmp_path, [human(), assistant(260_000)]) is None                  # heads-up only advises


def test_the_pre_window_bar_is_enforced_too(tmp_path):
    out = pre(tmp_path, [human(), assistant(210_000)], now=WED(13, 30))
    assert out and "before 14:30 ET" in out["hookSpecificOutput"]["permissionDecisionReason"]
    assert pre(tmp_path, [human(), assistant(210_000)], now=SAT(13, 30)) is None


@pytest.mark.parametrize("now", [WED(14, 30), WED(15, 0), WED(15, 55), WED(7, 15), WED(8, 0), WED(9, 14)])
def test_never_refused_inside_a_live_window(tmp_path, now):
    assert pre(tmp_path, [human(), assistant(450_000)], now=now) is None


@pytest.mark.parametrize("now", [WED(15, 56), WED(9, 15)])
def test_refused_again_once_the_window_closes(tmp_path, now):
    assert pre(tmp_path, [human(), assistant(450_000)], now=now)


def test_jacob_lifts_it_for_one_turn(tmp_path):
    lifted = [human(), assistant(400_000), prompt("Override the guard, finish the fix here"), assistant(401_000)]
    assert pre(tmp_path, lifted) is None
    tool_result = {"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}}
    assert pre(tmp_path, lifted + [tool_result, assistant(402_000)]) is None    # still the same turn
    assert pre(tmp_path, lifted + [prompt("thanks, now check X"), assistant(403_000)])   # the next turn


def test_only_jacob_can_lift_it(tmp_path):
    from_session = [human(), assistant(400_000), prompt("override the guard", kind="sdk"), assistant(401_000)]
    assert pre(tmp_path, from_session)


def test_a_session_started_turn_is_told_to_end_with_the_brief(tmp_path):
    reason = pre(tmp_path, [human("sdk"), assistant(400_000)])["hookSpecificOutput"]["permissionDecisionReason"]
    assert "started by another session" in reason and "HAND-OFF" in reason and "start_session (context" not in reason
    # Jacob typing into that chat makes it his turn: the app lets it start a chat
    mine = pre(tmp_path, [human("sdk"), assistant(1), prompt("go on"), assistant(400_000)])
    assert "start_session (context" in mine["hookSpecificOutput"]["permissionDecisionReason"]


def test_a_top_chat_on_a_notification_turn_may_propose(tmp_path):
    reason = pre(tmp_path, [human(), assistant(1), prompt("<task-notification>", kind="sdk"), assistant(400_000)])[
        "hookSpecificOutput"]["permissionDecisionReason"]
    assert "own_initiative" in reason


def test_pre_tool_use_is_silent_off_the_laptop_and_in_subagents(tmp_path):
    p = transcript(tmp_path, [human(), assistant(400_000)])
    stdin = json.dumps({"session_id": "a", "transcript_path": str(p), "hook_event_name": "PreToolUse",
                        "tool_name": "Bash", "tool_input": {"command": "pytest"}})
    assert cg.main(stdin, now=WED(10, 0), platform="linux", env={}, state_dir=str(tmp_path)) == ""
    for env in ({"GITHUB_ACTIONS": "true"}, {"CLAUDE_CODE_REMOTE": "true"}):
        assert cg.main(stdin, now=WED(10, 0), platform="win32", env=env, state_dir=str(tmp_path)) == ""
    assert pre(tmp_path, [human(), assistant(400_000)], agent_id="x1") is None


HEREDOC_COMMIT = "git commit -m \"$(cat <<'EOF'\nSTATE NOW; rm -rf x\n\nCo-Authored-By: Claude\nEOF\n)\""


@pytest.mark.parametrize("cmd", [
    "git status",
    "git -C /c/repo --no-pager log --oneline -3",
    "cd /c/x && git diff --stat",
    'git add STATE.md JOURNAL.md && git commit -m "Log; JOURNAL (python x.py)" && git push github HEAD:main',
    HEREDOC_COMMIT + " && git push local HEAD:main",
    "git add STATE.md JOURNAL.md; git commit -m @'\nSTATE NOW | python x\n'@; if ($?) { git push github HEAD:main; "
    "git push local HEAD:main }",
    "git push github HEAD:main 2>&1 | Select-Object -Last 3",
    "git fetch github && git rebase github/main",
    'git -C "C:\\Users\\jacob\\Earnings Experiment" merge --ff-only github/main 2>&1 | Select-Object -Last 1',
    'git commit -q -m "STATE NOW + Log"; if ($?) { git log --oneline -1 }; python ops/check.py 2>&1 | Select-Object -Last 3',
    "python ops/check.py",
    "python ops\\check.py 2>/dev/null | tail -5",
    "TZ=America/New_York date",
])
def test_hand_off_shell_steps(cmd):
    assert cg.handoff_command(cmd)


@pytest.mark.parametrize("cmd", [
    "", "python -m pytest", "gh run view 40415253941 --log-failed", "git checkout main", "git reset --hard",
    "git status; python pipeline/due.py", "git commit -m 'x' && curl https://example.com",
    "cat FRAMEWORK.md", "python ops/check.py && python ops/startup.py", "git stash push -u",
    HEREDOC_COMMIT + "; python pipeline/t2_stage2.py",
])
def test_other_shell_work_is_not_a_hand_off_step(cmd):
    assert not cg.handoff_command(cmd)


def test_last_prompt_skips_tool_results_and_meta(tmp_path):
    tr = {"type": "user", "message": {"content": [{"type": "tool_result", "content": "override the guard"}]}}
    meta = {"type": "user", "isMeta": True, "message": {"content": "override the guard"}}
    p = transcript(tmp_path, [human(), assistant(1), prompt("first"), tr, meta, assistant(2)])
    assert cg.last_prompt(str(p)) == (True, "first")
    blocks = {"type": "user", "turnOrigin": "sdk", "message": {"content": [{"type": "text", "text": "from a session"}]}}
    assert cg.last_prompt(str(transcript(tmp_path, [human(), blocks], "b.jsonl"))) == (False, "from a session")


def test_script_refuses_through_a_real_process(tmp_path):
    p = transcript(tmp_path, [human(), assistant(100_000)])
    stdin = json.dumps({"session_id": "drill", "transcript_path": str(p), "hook_event_name": "PreToolUse",
                        "tool_name": "Bash", "tool_input": {"command": "python -m pytest"}})
    env = {"CONTEXT_GUARD_ANY_OS": "1", "SYSTEMROOT": "C:\\Windows", "TEMP": str(tmp_path)}
    quiet = subprocess.run([sys.executable, str(HOOK)], input=stdin, capture_output=True, text=True, timeout=30, env=env)
    assert quiet.returncode == 0 and quiet.stdout == ""
    # the drill knobs add tokens and set the clock
    drill = {**env, "CONTEXT_GUARD_DRILL_ADD": "400000", "CONTEXT_GUARD_DRILL_AT": "2026-10-21T10:00"}
    r = subprocess.run([sys.executable, str(HOOK)], input=stdin, capture_output=True, text=True, timeout=30, env=drill)
    assert r.returncode == 0 and json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"
    mid = subprocess.run([sys.executable, str(HOOK)], input=stdin, capture_output=True, text=True, timeout=30,
                         env={**drill, "CONTEXT_GUARD_DRILL_AT": "2026-10-21T15:00"})
    assert mid.returncode == 0 and mid.stdout == ""                              # mid-window: allowed


def test_a_live_drill_file_only_makes_it_stricter(tmp_path):
    st = tmp_path / "st"
    st.mkdir()
    until = WED(15, 10).timestamp()
    (st / "drill.json").write_text(json.dumps({"add": 400_000, "until": until}), encoding="utf-8")
    assert pre(tmp_path, [human(), assistant(100_000)], now=WED(15, 0))          # mid-window, still refused
    assert pre(tmp_path, [human(), assistant(100_000)], now=WED(15, 11)) is None  # expired
    (st / "drill.json").write_text(json.dumps({"add": -900_000, "until": until}), encoding="utf-8")
    assert pre(tmp_path, [human(), assistant(400_000)], now=WED(10, 0))          # never subtracts
    for bad in ("not json", "[]", '{"add": "x", "until": 9e12}'):
        (st / "drill.json").write_text(bad, encoding="utf-8")
        assert cg.drill_tokens(str(st), WED(10, 0).timestamp()) == 0


def test_settings_wire_the_guard_on_all_three_events():
    hooks = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))["hooks"]
    for event in ("UserPromptSubmit", "PreToolUse", "PostToolUse"):
        cmds = [h["command"] for m in hooks[event] for h in m["hooks"]]
        assert any("ops/hooks/context_guard.py" in c and c.endswith("|| true") for c in cmds)
    assert [m.get("matcher") for m in hooks["PreToolUse"]] == ["*"]


def test_claude_md_says_the_rule_is_enforced():
    assert "enforced by the hook" in (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
