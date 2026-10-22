"""Token-efficiency study: when should a laptop chat hand off? (ops/token_efficiency_2026-10.md)

Reads this project's own Claude Code transcripts (never the DRIVE project's: rule 9) and
prints the numbers the hand-off threshold in ops/hooks/context_guard.py is calibrated on.
Re-run it after a month of chats:  python ops/token_study.py
"""
import glob
import json
import os
import re
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PROJECTS = Path.home() / ".claude" / "projects"
PREFIX = re.sub(r"[^A-Za-z0-9]", "-", str(REPO))      # Claude Code's folder name for this repo
# Opus 5.5 list-price weights, in base-input units (platform.claude.com pricing): what a
# cost-weighted plan limit would count. RAW counts every token alike, the worst case.
API = dict(inp=1, cr=0.05, cw1h=2.0, cw5m=1.25, out=5)
RAW = dict(inp=1, cr=1, cw1h=1, cw5m=1, out=1)


def cost(x, w):
    return sum(w[k] * x[k] for k in w)


def load(p):
    out = []
    for line in open(p, encoding="utf-8"):
        try:
            out.append(json.loads(line))
        except ValueError:
            pass
    return out


def calls(recs):
    """One row per API response of the main chain (a response spans several records)."""
    seen = {}
    for r in recs:
        m = r.get("message") or {}
        u = m.get("usage")
        if r.get("type") != "assistant" or r.get("isSidechain") or not u or m.get("model") == "<synthetic>":
            continue
        cc = u.get("cache_creation") or {}
        seen.setdefault(m.get("id") or r.get("uuid"), dict(
            t=r["timestamp"], inp=u.get("input_tokens") or 0, cr=u.get("cache_read_input_tokens") or 0,
            cw1h=cc.get("ephemeral_1h_input_tokens") or 0, cw5m=cc.get("ephemeral_5m_input_tokens") or 0,
            out=u.get("output_tokens") or 0, cw=u.get("cache_creation_input_tokens") or 0))
    rows = sorted(seen.values(), key=lambda x: x["t"])
    for x in rows:
        x["ctx"] = x["inp"] + x["cr"] + x["cw"]
    return rows


def is_human(r):
    if r.get("type") != "user" or r.get("isMeta") or r.get("isSidechain"):
        return False
    c = (r.get("message") or {}).get("content")
    return isinstance(c, str) or (isinstance(c, list) and not any(
        isinstance(b, dict) and b.get("type") == "tool_result" for b in c))


def first_edit_orientation(recs, rows):
    """(calls, context growth) from each human prompt to its first Edit/Write: new chat vs in-chat."""
    hum = [r["timestamp"] for r in recs if is_human(r)]
    edits = [r["timestamp"] for r in recs if r.get("type") == "assistant" and not r.get("isSidechain")
             and any(isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") in ("Edit", "Write")
                     for b in (r.get("message") or {}).get("content") or [])]
    new, inchat = [], []
    for i, h in enumerate(hum):
        nxt = hum[i + 1] if i + 1 < len(hum) else "9"
        e = [t for t in edits if h < t < nxt]
        s = [x for x in rows if h <= x["t"] < (e[0] if e else "")]
        if e and s:
            grow = s[-1]["ctx"] - (rows[0]["ctx"] if i == 0 else s[0]["ctx"])
            (new if i == 0 else inchat).append((len(s), grow))
    return new, inchat


# What a chat reads between a prompt and its first edit, by the tool call's target (first match wins).
SOURCES = (
    ("app and plan tools", r"^(mcp__ccd|ToolSearch)"),
    ("live status (gh, routines)", r"^RemoteTrigger|\bgh (run|workflow|api)\b"),
    ("subagent", r"^Agent\b"),
    ("STATE.md", r"STATE\.md(?!.*state_history)"),
    ("start-up (pull, check, clock)", r"git (pull|push|fetch)|python[^|;&]* check\.py|America/New_York|zoneinfo"),
    ("project docs (CHARTER, FRAMEWORK, JOURNAL, memory, health)",
     r"CHARTER|FRAMEWORK|JOURNAL|HYPOTHESES|RESEARCH_PLAN|/memory|CLAUDE\.md|health/latest"),
    ("code, registry, workflows", r"registry/|\.github/|pipeline/|analysis/|ops/|tests/|check\.py"),
    ("event and ledger data", r"events/|paper/|universe/|logs/|\.json"),
)


def text_of(c):
    if isinstance(c, str):
        return c
    return "".join(text_of(b.get("text") if b.get("type") == "text" else b.get("content"))
                   for b in c or [] if isinstance(b, dict))


def source(name, inp):
    s = f"{name} " + str(inp.get("file_path") or inp.get("command") or inp.get("pattern") or "").replace("\\", "/")
    return next((k for k, rx in SOURCES if re.search(rx, s)), "other")


def orientation_reads(recs, which):
    """{source: tokens} a prompt's context grew by before its first Edit/Write, or None.

    Each call's growth is the next call's context minus this one's; its own output (thinking,
    text, tool calls) is taken first, and the rest is split over its tool results by size."""
    hum = [r["timestamp"] for r in recs if is_human(r)]
    if which >= len(hum):
        return None
    h, nxt = hum[which], hum[which + 1] if which + 1 < len(hum) else "9"
    size = {b["tool_use_id"]: len(text_of(b.get("content"))) for r in recs
            if r.get("type") == "user" and not r.get("isSidechain")
            for b in (r.get("message") or {}).get("content") or [] if isinstance(b, dict) and b.get("type") == "tool_result"}
    msgs = {}
    for r in recs:
        m = r.get("message") or {}
        u = m.get("usage")
        if r.get("type") != "assistant" or r.get("isSidechain") or not u or m.get("model") == "<synthetic>" \
                or not h < r["timestamp"] < nxt:
            continue
        d = msgs.setdefault(m.get("id"), dict(t=r["timestamp"], out=0, uses=[], ctx=sum(
            u.get(k) or 0 for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))))
        d["out"] = max(d["out"], u.get("output_tokens") or 0)
        d["uses"] += [b for b in m.get("content") or [] if isinstance(b, dict) and b.get("type") == "tool_use"]
    L = sorted(msgs.values(), key=lambda d: d["t"])
    stop = next((i for i, d in enumerate(L) if any(b["name"] in ("Edit", "Write") for b in d["uses"])), 0)
    if stop < 1:
        return None
    got = {"own output (thinking, text, tool calls)": 0.0, "calls": stop}
    for a, b in zip(L[:stop], L[1:stop + 1]):
        grew = max(0, b["ctx"] - a["ctx"])
        own = min(a["out"], grew)
        got["own output (thinking, text, tool calls)"] += own
        sizes = [size.get(u["id"], 0) for u in a["uses"]]
        for u, n in zip(a["uses"], sizes):
            k = source(u["name"], u.get("input") or {})
            got[k] = got.get(k, 0) + (grew - own) * (n / sum(sizes) if sum(sizes) else 1 / len(sizes))
    return got


def per_call(T, S, C0, g, a, b, nh=8):
    """Cost per work call when a chat that starts at C0 and grows g per call hands off at T."""
    K = (T - C0) / g
    if K <= 1:
        return float("inf")
    return (S + K * a + b * (C0 * K + g * K * (K - 1) / 2) + nh * (a + b * T)) / K


def ols(xs, ys):
    mx, my = st.mean(xs), st.mean(ys)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    return my - b * mx, b


def main():
    files = [p for d in glob.glob(str(PROJECTS / (PREFIX + "*"))) for p in glob.glob(os.path.join(d, "*.jsonl"))]
    allrows, grow, new, inchat, reads = [], [], [], [], {"new chat": [], "in an old chat": []}
    print(f"{'chat':8} {'calls':>5} {'max ctx':>8} {'cache-read':>10} {'output':>7}")
    for p in sorted(files, key=os.path.getmtime):
        recs = load(p)
        rows = calls(recs)
        if len(rows) < 20:
            continue
        print(f"{Path(p).stem[:8]} {len(rows):5d} {max(x['ctx'] for x in rows) / 1e3:7.0f}k "
              f"{sum(x['cr'] for x in rows) / 1e6:9.1f}M {sum(x['out'] for x in rows) / 1e3:6.0f}k")
        grow += [b["ctx"] - a["ctx"] for a, b in zip(rows, rows[1:]) if b["ctx"] - a["ctx"] > -20000]
        n, i = first_edit_orientation(recs, rows)
        new += n
        inchat += i
        allrows += rows[1:]
        for w in range(sum(1 for r in recs if is_human(r))):
            got = orientation_reads(recs, w)
            if got and got["calls"] >= (3 if w == 0 else 1):
                reads["new chat" if w == 0 else "in an old chat"].append(got)
    g = st.mean(grow)
    a_api, b_api = ols([x["ctx"] for x in allrows], [cost(x, API) for x in allrows])
    a_raw, b_raw = ols([x["ctx"] for x in allrows], [cost(x, RAW) for x in allrows])
    tot = sum(cost(x, RAW) for x in allrows)
    print(f"\ncalls {len(allrows)}; cache reads are {sum(x['cr'] for x in allrows) / tot:.1%} of all tokens")
    print(f"context growth per call: mean {g:.0f}, median {st.median(grow):.0f}")
    print(f"cost per call (price-weighted) = {a_api:.0f} + {b_api:.4f} x context;  raw = {a_raw:.0f} + {b_raw:.4f} x context")
    nc, ng = st.median([c for c, _ in new]), st.median([d for _, d in new])
    ic, ig = st.median([c for c, _ in inchat]), st.median([d for _, d in inchat])
    print(f"prompt -> first edit: new chat {nc:.0f} calls / +{ng / 1e3:.0f}k (n={len(new)}); "
          f"in an old chat {ic:.0f} calls / +{ig / 1e3:.0f}k (n={len(inchat)})")
    extra, c0 = nc - ic, 80e3 + ng - ig
    print(f"hand-off overhead: {extra:.0f} extra calls, a fresh chat starts working at ~{c0 / 1e3:.0f}k\n")
    Ts = [200e3, 250e3, 300e3, 350e3, 400e3, 500e3, 700e3]
    print("cost per unit of work vs the best threshold (1.00 = optimum)")
    for name, a, b in (("price-weighted", a_api, b_api), ("raw tokens", a_raw, b_raw)):
        for label, calls_, start in (("measured hand-off", extra, c0), ("lean hand-off", 6, 100e3)):
            c = dict(S=calls_ * (a + b * (start + 80e3) / 2), C0=start, g=g, a=a, b=b)
            best = min((per_call(T, **c), T) for T in range(int(start) + 5000, 1_000_001, 5000))
            row = "  ".join(f"{T / 1e3:.0f}k {per_call(T, **c) / best[0]:.2f}" for T in Ts)
            print(f"  {name:14} {label:17} best {best[1] / 1e3:.0f}k | {row}")
    print("\nwhat a prompt reads before its first edit, tokens of context growth per prompt (mean)")
    keys = sorted({k for g_ in reads.values() for x in g_ for k in x if k != "calls"},
                  key=lambda k: -sum(x.get(k, 0) for x in reads["new chat"]))
    print(f"  {'':58} " + "  ".join(f"{w} (n={len(g_)}, median {st.median([x['calls'] for x in g_] or [0]):.0f} calls)"
                                    for w, g_ in reads.items()))
    for k in keys + ["total"]:
        cells = []
        for g_ in reads.values():
            v = st.mean([sum(x[j] for j in x if j != "calls") if k == "total" else x.get(k, 0) for x in g_] or [0])
            cells.append(f"{v / 1e3:8.1f}k")
        print(f"  {k:58} " + "  ".join(f"{c:>30}" for c in cells))


if __name__ == "__main__":
    main()
