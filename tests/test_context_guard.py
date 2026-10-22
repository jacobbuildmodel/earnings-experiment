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
    for must in ("STATE.md", "JOURNAL.md", "git push github main", "git push local main",
                 "start_session", "pre earnings model"):
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


def test_lead_up_to_the_t2_deadline():
    level, text, _ = cg.assess(205_000, WED(8, 0))
    assert level == "pre_window" and "09:15" in text and "75 min" in text


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
