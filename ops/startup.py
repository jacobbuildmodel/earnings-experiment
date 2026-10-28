"""Start-up for a new laptop chat: CLAUDE.md's hand-off steps 0-2 in one call.

    python ops/startup.py            # pull, back up, check.py, then STATE.md's start-up read
    python ops/startup.py --no-git   # the STATE.md part only

A full STATE.md read cost a fresh chat ~20k tokens, and the PLAN and the Log are most of it
(ops/token_efficiency_2026-10.md, "What a fresh chat reads"). This prints the header, the NOW
block, the standing rules, Waiting on Jacob and Where things are in full, and one line for
every other section, so the chat knows what exists and reads a Log entry only when its brief
or its task names it.
"""
from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
KEEP = ("NOW", "Standing rules", "Waiting on Jacob", "Where things are")
BUDGET = 12_000  # characters of STATE.md printed, ~5k tokens; over it, trim the NOW block


def sections(text):
    """[(heading, body)] split at '## ' headings; the part before the first one has heading ''."""
    return [(p.splitlines()[0] if p.startswith("## ") else "", p) for p in re.split(r"(?m)^(?=## )", text) if p]


def startup_read(text):
    """The parts of STATE.md every chat needs, and a pointer line for the rest."""
    out = []
    for head, body in sections(text):
        name, n = head[3:], len(body.splitlines())
        if not head or name.startswith(KEEP):
            out.append(body.rstrip())
        elif name.startswith("Log"):
            titles = re.findall(r"(?m)^\*\*(\d{4}-\d\d-\d\d[^*]*)\*\*", body)[:3]
            out.append(f"{head}  [{n} lines not shown; newest entries:]\n" + "\n".join(f"- {t}" for t in titles))
        elif name.startswith("Cloud run log"):
            last = [ln for ln in body.splitlines() if ln.startswith("- ")][-1:]
            out.append(f"{head}  [{n} lines not shown; newest line:]\n" + "".join(ln[:300] for ln in last))
        else:
            out.append(f"{head}  [{n} lines not shown]")
    return "\n\n".join(out) + "\n"


def run(cmd):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout + r.stderr).strip()


def main_folder():
    """The main project folder when this chat runs in one of the app's worktrees, else None."""
    rc, common = run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"])
    rc2, own = run(["git", "rev-parse", "--path-format=absolute", "--git-dir"])
    if rc or rc2 or Path(common).resolve() == Path(own).resolve():
        return None
    return Path(common).resolve().parent


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # STATE.md has emoji; the console may be cp1252
    print("US Eastern now:", datetime.now(ZoneInfo("America/New_York")).strftime("%a %Y-%m-%d %H:%M"))
    code = 0
    if "--no-git" not in argv:
        cmds = [["git", "pull", "--ff-only", "github", "main"]]
        # A worktree chat's hooks run the main folder's copy (${CLAUDE_PROJECT_DIR}): fast-forward its main, so
        # the context guard there is the current one. It sat 286 commits behind on 2026-10-27.
        top = main_folder()
        if top and run(["git", "-C", str(top), "symbolic-ref", "--short", "HEAD"])[1] == "main":
            cmds.append(["git", "-C", str(top), "merge", "--ff-only", "github/main"])
        for cmd in cmds + [["git", "push", "local", "github/main:main"]]:
            rc, out = run(cmd)
            print(f"$ {' '.join(cmd)}  (exit {rc}) " + " | ".join(out.splitlines()[-2:]))
        code, out = run([sys.executable, "check.py"])
        print(out)
    read = startup_read((ROOT / "STATE.md").read_text(encoding="utf-8"))
    print("=" * 72 + "\nSTATE.md, start-up read (the rest only when a brief or the task names it)\n" + "=" * 72)
    print(read)
    if len(read) > BUDGET:
        print(f"[warn] this read is {len(read):,} characters, over the {BUDGET:,} budget: trim STATE.md's NOW block")
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
