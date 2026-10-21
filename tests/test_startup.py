"""ops/startup.py: a new chat's start-up in one call, reading only STATE.md's start-up sections."""
import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("startup", ROOT / "ops" / "startup.py")
su = importlib.util.module_from_spec(spec)
spec.loader.exec_module(su)

STATE = """# STATE — test

**Season A live** · header line

## NOW — rewritten at every hand-off
- next action: the gate audit

## PLAN — Mon 2026-10-19
plan body line 1
plan body line 2

## Standing rules for every session
- no commits 14:30-15:56 ET

## Waiting on Jacob
1. DPZ shares

## Where things are
| what | where |

## Log — newest first
**2026-10-21 (Wed) 09:36 ET — newest entry** (side session).
- body of the newest
**2026-10-20 (Tue) 20:40 ET — second entry.**
- body
**2026-10-20 (Tue) 07:40 ET — third entry.**
**2026-10-19 (Mon) 12:00 ET — fourth entry.**
- old body

## Cloud run log
Intro line.
- **2026-10-20 (Tue):** older
- **2026-10-21 (Wed):** newest run line
"""


def test_keeps_the_start_up_sections_in_full():
    r = su.startup_read(STATE)
    for must in ("**Season A live** · header line", "- next action: the gate audit", "- no commits 14:30-15:56 ET",
                 "1. DPZ shares", "| what | where |"):
        assert must in r


def test_points_at_the_plan_and_log_without_their_bodies():
    r = su.startup_read(STATE)
    assert "## PLAN — Mon 2026-10-19  [4 lines not shown]" in r and "plan body" not in r
    assert "- 2026-10-21 (Wed) 09:36 ET — newest entry" in r and "- 2026-10-20 (Tue) 07:40 ET — third entry." in r
    assert "fourth entry" not in r and "body of the newest" not in r
    assert "newest run line" in r and "older" not in r


def test_real_state_has_a_now_block_and_fits_the_budget():
    text = (ROOT / "STATE.md").read_text(encoding="utf-8")
    r = su.startup_read(text)
    assert "\n## NOW" in text and "## NOW" in r and "## Standing rules" in r and "## Waiting on Jacob" in r
    assert len(r) <= su.BUDGET, f"start-up read is {len(r)} characters: trim STATE.md's NOW block"
    assert len(r) < 0.4 * len(text)


def test_script_runs_without_git():
    out = subprocess.run([sys.executable, str(ROOT / "ops" / "startup.py"), "--no-git"], capture_output=True,
                         cwd=ROOT, timeout=60)
    assert out.returncode == 0
    text = out.stdout.decode("utf-8")
    assert "US Eastern now:" in text and "## NOW" in text and "$ git" not in text
