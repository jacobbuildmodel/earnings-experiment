"""Keep a durable record of what the AI step did, and flag any breach of its fences.

    python pipeline/runlog.py <claude-execution-output.json> <run-id>

GitHub deletes run artifacts after 90 days; the verdict is due in 2027. So every tool call the AI made
(name + input, truncated) is written to logs/actions/<UTC time>_<run-id>.json and committed. A call
that touches archive/, outcomes/ or the DRIVE folder is listed under `fence_breaches` - the evidence an
evaluator needs to check that T2 was blind (rules 9-10, D004 §3).
"""
import datetime
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
          (re.compile(r"\.\." + SEP + r"CLAUDE\b|\bDRIVE\b"), "DRIVE repo (rule 9)")]


def main(path, run_id):
    if not os.path.exists(path):
        print(f"no AI output at {path} - nothing to log")
        return
    msgs = json.load(open(path, encoding="utf-8"))
    calls, breaches, result = [], [], None
    for m in msgs:
        if m.get("type") == "assistant":
            for c in (m.get("message") or {}).get("content") or []:
                if c.get("type") == "tool_use":
                    inp = json.dumps(c.get("input"), ensure_ascii=False)
                    calls.append({"tool": c.get("name"), "input": inp[:600]})
                    for rx, what in FENCES:
                        if rx.search(inp):
                            breaches.append({"fence": what, "tool": c.get("name"), "input": inp[:600]})
        elif m.get("type") == "result":
            result = {k: m.get(k) for k in ("subtype", "is_error", "num_turns", "total_cost_usd")}
            result["text"] = (m.get("result") or "")[:4000]
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H%MZ")
    out = os.path.join(ROOT, "logs", "actions", f"{stamp}_{run_id}.json")
    write_json(out, {"run_id": run_id, "logged_utc": stamp, "tool_calls": len(calls),
                     "fence_breaches": breaches, "result": result, "calls": calls})
    print(f"{len(calls)} tool calls, {len(breaches)} fence breach(es) -> {os.path.relpath(out, ROOT)}")
    for b in breaches:
        print(f"FENCE BREACH: {b['fence']} via {b['tool']}: {b['input'][:200]}")
    commit([out], f"Log AI step of Actions run {run_id}: {len(calls)} tool calls, {len(breaches)} fence breach(es)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
