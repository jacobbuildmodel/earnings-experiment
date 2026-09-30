"""Keep a durable record of what the AI step did, and flag any breach of its fences.

    python pipeline/runlog.py <claude-execution-output.json> <run-id>

GitHub deletes run artifacts after 90 days; the verdict is due in 2027. So every tool call the AI made
(name + input, truncated) is written to logs/actions/<UTC time>_<run-id>.json and committed. A call
that touches archive/, outcomes/ or the DRIVE folder is listed under `fence_breaches` - the evidence an
evaluator needs to check that T2 was blind (rules 9-10, D004 §3).
"""
import datetime
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, write_json  # noqa: E402
from due import commit  # noqa: E402

SEP = r"[/\x5c]"  # a forward or back slash
FENCES = [(re.compile(r"(^|[\s'\":/\x5c])archive" + SEP, re.I), "archive/ (rule 10)"),
          (re.compile(r"(^|[\s'\":/\x5c])outcomes" + SEP, re.I), "outcomes/ (D004: no graded outcomes)"),
          (re.compile(r"\.\." + SEP + r"CLAUDE\b|\bDRIVE\b"), "DRIVE repo (rule 9)"),
          (re.compile(r"T1_rule_v\d|analysis" + SEP + r"history", re.I), "T1 rule / history study (D004 v3: T2 may not see T1)")]

# git commands that can print file contents from history (external review 2026-09-21: `git log -p` or
# `git show <commit>` reads a graded outcome without naming outcomes/). Listed for review, not as breaches.
GIT_CONTENT = re.compile(r"\bgit\s+(show|cat-file|blame|grep|log\b[^|;&]*(\s-p\b|--patch|\s-S|\s-G)|diff\s+[^-\s]|"
                         r"checkout\s+\S+\s+--|restore\s+[^|;&]*--source)")

def main(path, run_id):
    if not os.path.exists(path):
        print(f"no AI output at {path} - nothing to log")
        return
    msgs = json.load(open(path, encoding="utf-8"))
    calls, breaches, review, result, by_id = [], [], [], None, {}
    for m in msgs:
        if m.get("type") == "assistant":
            for c in (m.get("message") or {}).get("content") or []:
                if c.get("type") == "tool_use":
                    inp = json.dumps(c.get("input"), ensure_ascii=False)
                    call = {"tool": c.get("name"), "input": inp[:600]}
                    calls.append(call)
                    by_id[c.get("id")] = call
                    # an Edit/Write is judged by the file it touches, not by the words it writes: a STATE.md
                    # note that MENTIONS analysis/history is not a read of it (false breach, 2026-09-29)
                    scope = inp
                    if c.get("name") in ("Edit", "Write", "NotebookEdit", "MultiEdit"):
                        scope = str((c.get("input") or {}).get("file_path", ""))
                    for rx, what in FENCES:
                        if rx.search(scope):
                            breaches.append({"fence": what, "tool": c.get("name"), "input": inp[:600]})
                    if c.get("name") == "Bash" and GIT_CONTENT.search(inp):
                        review.append({"flag": "git content read", "input": inp[:600]})
        elif m.get("type") == "user":
            # What a web fetch actually returned (external review 2026-09-21): the hash and opening of
            # the content, so a reviewer can check a claimed publish time against what T2 really saw.
            for c in (m.get("message") or {}).get("content") or []:
                if not isinstance(c, dict) or c.get("type") != "tool_result":
                    continue
                call = by_id.get(c.get("tool_use_id"))
                if not call or call["tool"] not in ("WebFetch", "WebSearch"):
                    continue
                body = c.get("content")
                if isinstance(body, list):
                    body = " ".join(x.get("text", "") for x in body if isinstance(x, dict))
                body = str(body or "")
                call["result_sha256"] = hashlib.sha256(body.encode("utf-8")).hexdigest()
                call["result_head"] = body[:500]
        elif m.get("type") == "result":
            result = {k: m.get(k) for k in ("subtype", "is_error", "num_turns", "total_cost_usd")}
            result["text"] = (m.get("result") or "")[:4000]
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H%MZ")
    out = os.path.join(ROOT, "logs", "actions", f"{stamp}_{run_id}.json")
    write_json(out, {"run_id": run_id, "logged_utc": stamp, "tool_calls": len(calls),
                     "fence_breaches": breaches, "review_flags": review, "result": result, "calls": calls})
    print(f"{len(calls)} tool calls, {len(breaches)} fence breach(es) -> {os.path.relpath(out, ROOT)}")
    for b in breaches:
        print(f"FENCE BREACH: {b['fence']} via {b['tool']}: {b['input'][:200]}")
    for r in review:
        print(f"::warning::review - {r['flag']}: {r['input'][:200]}")
    commit([out], f"Log AI step of Actions run {run_id}: {len(calls)} tool calls, {len(breaches)} fence breach(es)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
