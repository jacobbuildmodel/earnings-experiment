"""D004 v4 stage 2: T2 decides from the frozen dossier with NO tools - a leak-probe call that sees nothing,
then ONE decision call that sees only the dossier - and the decision is frozen on its own (t2.json +
manifest_t2.json + RFC 3161 tokens), before its deadline (entry open - 15 min).

    python pipeline/t2_stage2.py run [--backend claude|gemini|all]            # the queue (workflow t2-queue.yml)
    python pipeline/t2_stage2.py list [--backend ...]                          # events waiting, in queue order
    python pipeline/t2_stage2.py dry <season> <TICKER> <date> --edir DIR [--backend ...] [--rule JSON]
                                                                               # decide a copy; nothing in the repo
    python pipeline/t2_stage2.py gemini-probe                                  # is the T2G model reachable?

Backends (D004 v4 §2, §4):
  claude - T2, the scored track. `claude -p` (Claude Code CLI) isolated: --safe-mode --strict-mcp-config
           --setting-sources "" --disable-slash-commands --tools "" --max-turns 1, a replaced system prompt,
           a scratch working directory. The CLI's init line must show no tools and no MCP servers, and the
           result one turn and no server tool use - else the call is rejected (review 2026-10-05, finding 2).
           Runs only on the Actions runner unless T2_ALLOW_LOCAL=1 (a laptop carries personal settings).
  gemini - T2G, a SHADOW (a second model): the Gemini API, same prompts, no tools, no grounding.
Queue order: (deadline, sha256("<season>|<TICKER>|<date>")) - earliest deadline first, random within a
deadline (D004 v3 change 3). At most MAX_ATTEMPTS failed attempts per event and backend, then it is left
MISSING. A usage-limit refusal stops that backend for this run; a later run retries while T2 is open.
"""
import datetime
import glob
import hashlib
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ET, REGISTRY, ROOT, now_et, rule_for, write_json, write_once  # noqa: E402
from freeze import decision_problems, git, push_all, timestamp  # noqa: E402

BACKENDS = {"claude": {"track": "T2", "file": "t2.json", "thesis": "t2_thesis.md", "manifest": "manifest_t2.json"},
            "gemini": {"track": "T2G", "file": "t2g.json", "thesis": "t2g_thesis.md", "manifest": "manifest_t2g.json"}}
MAX_ATTEMPTS = 3
CLI_TIMEOUT = 900

PROBE_SYSTEM = "Answer from memory only, in one or two sentences. If you do not know, say \"I don't know\"."

SYSTEM = """You are T2, the AI decision track of a pre-registered buy-side earnings experiment.
Task: estimate the probability that the stock's official OPEN on the exit session (the first open after the
earnings print) is ABOVE its official OPEN on the entry session. That is the only thing being scored.

Rules (registry D004 v4):
- You have NO tools and NO internet. Use only the DOSSIER below plus your general knowledge from training.
  Every dossier item was published before the snapshot time; nothing after it exists for you.
- Outside view first: start from the dossier's base_rates item (buy-everything hit rates overall, by cluster,
  by session) and state your prior p and which base rate you used. Then say what in the dossier moves you,
  and by how much.
- confidence = your honest probability of a rise, with two decimals. It is scored by a proper scoring rule:
  do not push it towards 0 or 1 to look decisive. The bar is the buy-everything hit rate (~54%), not 50%.
  Code sets the decision: BUY if and only if confidence > 0.50.
- Do not reason about this experiment's past outcomes; you have none.

Reply with ONE JSON object and nothing else, with exactly these keys:
{"prior": {"p": number, "from": str},
 "confidence": number (two decimals),
 "thesis": str (one sentence),
 "reasons": [2 to 5 short strings],
 "moved_from_prior": str (what moved you from the prior, and by how much),
 "deciding_variable": str (what will most likely decide the reaction),
 "theses": [3 objects {"expected": str, "mechanism": str, "wrong_if": str}],
 "key_observations": [strings: what to watch in the print],
 "items_used": [dossier item ids you relied on, e.g. "I4"]}"""

SYSTEM_SHA256 = hashlib.sha256((PROBE_SYSTEM + "\n---\n" + SYSTEM).encode()).hexdigest()


def load(p):
    return json.load(open(p, encoding="utf-8"))


def sha_file(p):
    return hashlib.sha256(open(p, "rb").read().replace(b"\r\n", b"\n")).hexdigest()


def v4(season):
    """The frozen D004 v4 rule if it governs the season. 'No version covers the season' (the pilot) is None;
    any other refusal - a hash mismatch above all - propagates, so a damaged rule fails loudly (finding 14)."""
    try:
        r = rule_for("D004_decision_protocol", season)
    except SystemExit as exc:
        if str(exc).startswith("no frozen"):
            return None
        raise
    return r if r.get("t2_mode") == "dossier_oneshot" else None


def entry_open(gate):
    d = datetime.date.fromisoformat(gate["timing"]["entry"]["session"])
    return datetime.datetime.combine(d, datetime.time(9, 30), ET)


def deadline(rule, gate):
    return entry_open(gate) - datetime.timedelta(minutes=int(rule.get("t2_deadline_minutes_before_entry_open", 15)))


def probe_question(gate):
    return f"What did {gate['ticker']}'s stock do after its earnings report of {gate['report_date']}?"


def prompt(dossier, gate):
    head = (f"EVENT: {gate['ticker']} reports {gate['report_date']} {gate['session']} "
            f"(BMO = before the open, AMC = after the close). Entry: the open of {gate['timing']['entry']['session']}; "
            f"exit: the open of {gate['timing']['exit_A']['session']}. Snapshot taken {gate['captured_et']}.\n\n")
    return head + "DOSSIER (JSON):\n" + json.dumps({"items": dossier["items"], "missing": dossier["missing"]}, ensure_ascii=False)


# ---------------------------------------------------------------- model calls

def call_claude(rule, sys_prompt, user):
    """One isolated call. The CLI's own init line and result are checked: no tools, no MCP, one turn, no
    server-side tool use. Anything else is rejected, never used."""
    if os.environ.get("GITHUB_ACTIONS") != "true" and os.environ.get("T2_ALLOW_LOCAL") != "1":
        return {"ok": False, "limited": False, "fatal": True,
                "error": "the claude backend runs only on the Actions runner (a laptop carries personal settings)"}
    model = rule["t2_model"]
    cmd = ["claude", "-p", "--model", model, "--output-format", "stream-json", "--verbose", "--safe-mode",
           "--strict-mcp-config", "--setting-sources", "", "--disable-slash-commands", "--tools", "",
           "--max-turns", "1", "--system-prompt", sys_prompt]
    try:
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run(cmd, input=user, capture_output=True, text=True, encoding="utf-8", cwd=tmp,
                               timeout=CLI_TIMEOUT)
    except subprocess.TimeoutExpired:
        return {"ok": False, "limited": False, "error": f"claude CLI timed out after {CLI_TIMEOUT}s"}
    except FileNotFoundError:
        return {"ok": False, "limited": False, "fatal": True, "error": "claude CLI not installed"}
    init, res = {}, {}
    for line in r.stdout.splitlines():
        try:
            x = json.loads(line)
        except ValueError:
            continue
        if x.get("type") == "system" and x.get("subtype") == "init":
            init = x
        elif x.get("type") == "result":
            res = x
    if not res:
        return {"ok": False, "limited": False, "error": f"no result from claude CLI (rc {r.returncode}): {(r.stderr or r.stdout)[-400:]}"}
    text = res.get("result") or ""
    limited = res.get("api_error_status") == 429 or (bool(res.get("is_error")) and "limit" in text.lower())
    if limited:
        return {"ok": False, "limited": True, "error": text}
    stu = (res.get("usage") or {}).get("server_tool_use") or {}
    isolation = {"tools": init.get("tools"), "mcp_servers": init.get("mcp_servers"), "num_turns": res.get("num_turns"),
                 "server_tool_use": stu, "model": init.get("model")}
    if init.get("tools") != [] or init.get("mcp_servers") != [] or res.get("num_turns") != 1 or any(stu.values()):
        return {"ok": False, "limited": False, "isolation": isolation,
                "error": f"isolation check failed: {isolation} - reply not used"}
    return {"ok": not res.get("is_error"), "limited": False, "text": text, "model": init.get("model") or model,
            "usage": res.get("usage"), "cost_usd_equiv": res.get("total_cost_usd"), "isolation": isolation,
            "error": text if res.get("is_error") else None}


def call_gemini(rule, sys_prompt, user, json_mode=True):
    import requests
    key = os.environ.get("GEMINI_API_KEY")
    model = rule["t2g"]["model"]
    if not key:
        return {"ok": False, "limited": False, "skip": True, "error": "no GEMINI_API_KEY"}
    body = {"system_instruction": {"parts": [{"text": sys_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"temperature": 1.0, **({"responseMimeType": "application/json"} if json_mode else {})}}
    try:
        r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                          params={"key": key}, json=body, timeout=600)
        if r.status_code in (429, 503):  # quota, or the free tier's "high demand" (seen 2026-10-05): retry next run
            return {"ok": False, "limited": True, "error": f"HTTP {r.status_code}: {r.text[:200]}"}
        if r.status_code != 200:
            return {"ok": False, "limited": False, "error": f"HTTP {r.status_code}: {r.text[:300]}"}
        d = r.json()
        text = "".join(p.get("text", "") for p in d["candidates"][0]["content"]["parts"])
    except Exception as exc:  # network, JSON, or no candidate
        return {"ok": False, "limited": False, "error": f"{type(exc).__name__}: {str(exc)[:200]}"}
    return {"ok": True, "limited": False, "text": text, "model": model, "usage": d.get("usageMetadata"),
            "isolation": {"tools": "none sent", "grounding": "none sent"}}


def call(backend, rule, sys_prompt, user, json_mode=True):
    if backend == "claude":
        return call_claude(rule, sys_prompt, user)
    return call_gemini(rule, sys_prompt, user, json_mode)


# ---------------------------------------------------------------- reply -> t2 record

def parse_reply(text):
    s = text.strip()
    i, j = s.find("{"), s.rfind("}")
    return json.loads(s[i:j + 1])


def shape_problems(reply):
    p = []
    pr = reply.get("prior")
    if not isinstance(pr, dict) or not isinstance(pr.get("p"), (int, float)) or not pr.get("from"):
        p.append("prior must be {p: number, from: text}")
    c = reply.get("confidence")
    if not isinstance(c, (int, float)) or not 0 <= c <= 1:
        p.append("confidence must be a number in [0, 1]")
    th = reply.get("theses")
    if not isinstance(th, list) or len(th) != 3 or not all(isinstance(x, dict) for x in th):
        p.append("theses must be 3 objects")
    for k in ("reasons", "key_observations"):
        if not isinstance(reply.get(k), list) or not all(isinstance(x, str) for x in reply[k]):
            p.append(f"{k} must be a list of strings")
    for k in ("thesis", "deciding_variable", "moved_from_prior"):
        if not isinstance(reply.get(k), str) or not reply[k].strip():
            p.append(f"{k} must be text")
    return p


def to_t2(reply, probe, dossier, res, decided):
    ids = {it["id"]: it for it in dossier["items"]}
    used = [ids[i] for i in reply.get("items_used") or [] if isinstance(i, str) and i in ids] or dossier["items"]
    conf = round(float(reply["confidence"]), 2)
    return {"decision": "BUY" if conf > 0.5 else "NO_BUY",  # code applies D004's rule; the model only estimates
            "confidence": conf, "thesis": reply["thesis"], "reasons": reply["reasons"],
            "deciding_variable": reply["deciding_variable"], "prior": reply["prior"],
            "leak_probe": probe, "moved_from_prior": reply["moved_from_prior"], "theses": reply["theses"],
            "key_observations": reply["key_observations"],
            "inputs_read": [{"what": f"{it['kind']}{(' ' + it['form']) if it.get('form') else ''}", "url_or_file": it["source"],
                             "published": it["published"], "dossier_item": it["id"]} for it in used],
            "decided_et": decided.isoformat(timespec="seconds"), "model": res.get("model"),
            "method": "D004 v4: leak-probe call without the dossier, then one decision call on the frozen dossier; no tools",
            "system_sha256": SYSTEM_SHA256, "isolation": res.get("isolation"), "usage": res.get("usage"),
            "cost_usd_equiv": res.get("cost_usd_equiv")}


def thesis_md(gate, t2, track):
    th = "\n".join(f"{k + 1}. **Expected:** {x.get('expected')} · **Mechanism:** {x.get('mechanism')} · "
                   f"**Wrong if:** {x.get('wrong_if')}" for k, x in enumerate(t2["theses"]) if isinstance(x, dict))
    pr = t2["prior"] if isinstance(t2["prior"], dict) else {}
    return (f"# {gate['ticker']} {gate['report_date']} {gate['session']} — {track} ({t2.get('model')})\n\n"
            f"**{t2['decision']}, confidence {t2['confidence']:.2f}.** {t2['thesis']}\n\n"
            f"- Prior: {pr.get('p')} — {pr.get('from')}\n- Moved from the prior: {t2['moved_from_prior']}\n"
            f"- Deciding variable: {t2['deciding_variable']}\n- Leak probe (asked before the dossier): {t2['leak_probe']}\n\n"
            "## Reasons\n" + "\n".join(f"- {r}" for r in t2["reasons"]) + f"\n\n## Three theses\n{th}\n\n## Watch in the print\n"
            + "\n".join(f"- {r}" for r in t2["key_observations"])
            + f"\n\nInputs: the frozen dossier ({len(t2['inputs_read'])} items used).\n")


# ---------------------------------------------------------------- one event

def attempts(edir, backend):
    return len([p for p in glob.glob(os.path.join(ROOT, "logs", "t2", f"{os.path.basename(edir)}_{backend}_*.json"))
                if load(p).get("outcome") not in ("limited", "skip")])


def log_call(edir, backend, entry):
    p = os.path.join(ROOT, "logs", "t2", f"{os.path.basename(edir)}_{backend}_{now_et():%Y%m%dT%H%M%S}.json")
    write_json(p, entry)
    return p


def decide(season, edir, backend, rule, write=True):
    """Returns 'limited', 'skip', 'fatal: ...', 'done: ...' or an error string. Never raises."""
    try:
        return _decide(season, edir, backend, rule, write)
    except Exception as exc:  # one event must never stop the queue (review finding 3)
        if write:
            log_call(edir, backend, {"event": os.path.basename(edir), "backend": backend, "outcome": "exception",
                                     "error": f"{type(exc).__name__}: {exc}"})
        return f"exception: {type(exc).__name__}: {exc}"


def _decide(season, edir, backend, rule, write):
    b = BACKENDS[backend]
    gate = load(os.path.join(edir, "gate.json"))
    dpath = os.path.join(edir, "dossier.json")
    if write:
        man = load(os.path.join(edir, "manifest.json"))
        if man["sha256"].get("dossier.json") != sha_file(dpath):
            return "the dossier is not the one frozen in manifest.json - refusing"
        if attempts(edir, backend) >= MAX_ATTEMPTS:
            return "skip"
    dossier = load(dpath)
    dl = deadline(rule, gate)
    if write and now_et() >= dl:
        return "skip"
    base = {"event": os.path.basename(edir), "backend": backend, "system_sha256": SYSTEM_SHA256,
            "dossier_sha256": sha_file(dpath)}
    # 1. the leak probe, with nothing in context (D004 v3 change 5: before any file about the event)
    pr = call(backend, rule, PROBE_SYSTEM, probe_question(gate), json_mode=False)
    if pr.get("skip"):
        return "skip"
    if pr.get("limited"):
        return "limited"
    if pr.get("fatal"):
        return f"fatal: {pr['error']}"
    if not pr.get("ok"):
        if write:
            log_call(edir, backend, {**base, "outcome": "probe_failed", "error": pr.get("error"), "isolation": pr.get("isolation")})
        return f"leak probe failed: {pr.get('error')}"
    # 2. the decision, from the frozen dossier
    user = prompt(dossier, gate)
    res = call(backend, rule, SYSTEM, user)
    decided = now_et()
    if res.get("limited"):
        return "limited"
    if res.get("fatal"):
        return f"fatal: {res['error']}"
    entry = {**base, "called_et": decided.isoformat(timespec="seconds"), "prompt_sha256": hashlib.sha256(user.encode()).hexdigest(),
             "probe_reply": pr.get("text"), "reply": res.get("text"), "error": res.get("error"), "usage": res.get("usage"),
             "model": res.get("model"), "isolation": res.get("isolation")}
    if not res.get("ok"):
        if write:
            log_call(edir, backend, {**entry, "outcome": "call_failed"})
        return f"call failed: {res.get('error')}"
    try:
        reply = parse_reply(res["text"])
    except (ValueError, TypeError) as exc:
        if write:
            log_call(edir, backend, {**entry, "outcome": "unparseable"})
        return f"unparseable reply: {exc}"
    sp = shape_problems(reply)
    if sp:
        if write:
            log_call(edir, backend, {**entry, "outcome": "bad_shape", "problems": sp})
        return f"invalid reply: {sp}"
    t2 = to_t2(reply, pr["text"].strip(), dossier, res, decided)
    stage1 = load(os.path.join(edir, "decision.json")) if os.path.exists(os.path.join(edir, "decision.json")) else \
        {"t0": {"decision": "BUY"}, "t1": {"decision": None, "note": "dry run"}}
    probs = decision_problems({"t0": stage1["t0"], "t1": stage1["t1"], "t2": t2}, {**gate, "season": season}, dl)
    out = {"track": b["track"], "event": os.path.basename(edir), "season": season, "rule": rule["id"], "t2": t2}
    if not write:
        return {**out, "problems": probs}
    if probs:
        log_call(edir, backend, {**entry, "outcome": "invalid", "problems": probs})
        return f"invalid decision: {probs}"
    log_call(edir, backend, {**entry, "outcome": "decided"})
    write_json(os.path.join(edir, b["file"]), out)
    open(os.path.join(edir, b["thesis"]), "w", encoding="utf-8", newline="\n").write(thesis_md(gate, t2, b["track"]))
    return freeze_stage2(season, edir, backend, gate, dl, t2)


def freeze_stage2(season, edir, backend, gate, dl, t2):
    b = BACKENDS[backend]
    rel = os.path.relpath(edir, ROOT).replace(os.sep, "/")
    eo = entry_open(gate)
    if now_et() >= dl:  # the freeze itself must land before the deadline, not only the decision (finding 9)
        for f in (b["file"], b["thesis"]):
            os.replace(os.path.join(edir, f), os.path.join(edir, f.replace(".", "_late.", 1)))
        return "decided, but the freeze would land after the deadline - not frozen (kept as *_late)"
    files = [b["file"], b["thesis"]]
    man = {"event": os.path.basename(edir), "season": season, "track": b["track"], "frozen_et": now_et().isoformat(),
           "entry_open_et": eo.isoformat(), "t2_deadline_et": dl.isoformat(), "system_sha256": SYSTEM_SHA256,
           "dossier_sha256": load(os.path.join(edir, "manifest.json"))["sha256"]["dossier.json"],
           "sha256": {f: sha_file(os.path.join(edir, f)) for f in files}}
    mname = b["manifest"]
    write_once(os.path.join(edir, mname), man)
    digest = sha_file(os.path.join(edir, mname))
    # own token names: the stage-1 manifest.tsr_* files are never touched (rehearsal 2026-10-05)
    tokens, errs = timestamp(digest, edir, stem=mname.replace(".json", ""))
    logs = [os.path.relpath(p, ROOT).replace(os.sep, "/")
            for p in glob.glob(os.path.join(ROOT, "logs", "t2", f"{os.path.basename(edir)}_{backend}_*.json"))]
    git("add", *[f"{rel}/{f}" for f in files + [mname] + tokens], *logs)
    git("commit", "-q", "-m", f"{b['track']} stage 2: {gate['ticker']} {gate['report_date']} {t2['decision']} "
        f"{t2['confidence']:.2f} before entry open {gate['timing']['entry']['session']}\n\n"
        f"manifest sha256 {digest}\nDecided-by: {t2.get('model')} (D004 v4, pipeline/t2_stage2.py)")
    when = datetime.datetime.fromisoformat(git("log", "-1", "--format=%cI"))
    pushes = push_all()
    if not any(pushes.values()):
        return f"error: committed but NOT pushed ({pushes}) - the decision exists only on this runner"
    return (f"done: {t2['decision']} {t2['confidence']:.2f}, committed {when.astimezone(ET):%H:%M:%S} ET "
            f"({'BLIND' if when < eo else 'VOID'}), tokens {tokens or 'NONE'}" + (f", tsa errors {errs}" if errs else ""))


# ---------------------------------------------------------------- the queue

def waiting(backend):
    out = []
    for m in glob.glob(os.path.join(ROOT, "events", "*", "*", "manifest.json")):
        edir = os.path.dirname(m)
        season = os.path.basename(os.path.dirname(edir))
        rule = v4(season)
        if not rule:
            continue
        man = load(m)
        if man["status"] != "PASS" or "dossier.json" not in man["sha256"]:
            continue
        if os.path.exists(os.path.join(edir, BACKENDS[backend]["manifest"])) or attempts(edir, backend) >= MAX_ATTEMPTS:
            continue
        gate = load(os.path.join(edir, "gate.json"))
        dl = deadline(rule, gate)
        if now_et() >= dl:
            continue
        h = hashlib.sha256(f"{season}|{gate['ticker']}|{gate['report_date']}".encode()).hexdigest()
        out.append((dl.isoformat(), h, season, edir, rule))
    return [x[2:] for x in sorted(out)]


def commit_logs():
    """Failed, rejected and refused attempts are on the record too (finding 9)."""
    new = git("status", "--porcelain", "--untracked-files=all", "--", "logs/t2", check=False)
    paths = [ln[3:].strip().strip('"') for ln in new.splitlines() if ln.strip()]
    if not paths:
        return
    git("add", *paths)
    git("commit", "-q", "-m", f"T2 queue: {len(paths)} attempt log(s) {now_et():%Y-%m-%d %H:%M} ET (code, D004 v4)")
    push_all()


def run(backends):
    failed = False
    for backend in backends:
        todo = waiting(backend)
        print(f"{backend}: {len(todo)} event(s) waiting")
        for season, edir, rule in todo:
            r = decide(season, edir, backend, rule)
            print(f"  {backend} {os.path.basename(edir)}: {r}", flush=True)
            if r == "limited":
                print(f"  {backend}: usage limit reached - stopping this backend; a later run retries")
                break
            if r.startswith("fatal") or (r == "skip" and backend == "gemini" and not os.environ.get("GEMINI_API_KEY")):
                failed = failed or r.startswith("fatal")
                break
            if r.startswith("error"):
                failed = True
    commit_logs()
    if failed:
        raise SystemExit(1)


def gemini_probe():
    import requests
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit("no GEMINI_API_KEY")
    rule = v4("seasonA") or load(os.path.join(ROOT, "reviews", "proposals", "D004_v4_DRAFT.json"))
    r = requests.get("https://generativelanguage.googleapis.com/v1beta/models", params={"key": key, "pageSize": 200}, timeout=60)
    names = [m["name"].split("/")[-1] for m in r.json().get("models", [])] if r.status_code == 200 else []
    print(f"models endpoint HTTP {r.status_code}; {len(names)} models; flash/pro: {[n for n in names if 'flash' in n or 'pro' in n][:40]}")
    for model in [rule["t2g"]["model"]] + [m for m in os.environ.get("T2G_PROBE_ALSO", "").split() if m]:
        for attempt in range(3):
            res = call_gemini({**rule, "t2g": {**rule["t2g"], "model": model}}, PROBE_SYSTEM, "Reply with the single word OK.", json_mode=False)
            print(f"{model} try {attempt + 1}: ok={res.get('ok')} limited={res.get('limited')} error={str(res.get('error'))[:160]} text={str(res.get('text'))[:20]!r}")
            if res.get("ok"):
                break


if __name__ == "__main__":
    a = sys.argv[1:]
    bk = a[a.index("--backend") + 1] if "--backend" in a else "all"
    chosen = list(BACKENDS) if bk == "all" else [bk]
    if a[:1] == ["run"]:
        run(chosen)
    elif a[:1] == ["list"]:
        for b in chosen:
            for season, edir, _ in waiting(b):
                print(b, season, os.path.basename(edir))
    elif a[:1] == ["gemini-probe"]:
        gemini_probe()
    elif a[:1] == ["dry"]:
        season, t, d = a[1], a[2].upper(), a[3]
        edir = a[a.index("--edir") + 1]
        rule = json.loads(a[a.index("--rule") + 1]) if "--rule" in a else load(os.path.join(REGISTRY, "D004_decision_protocol_v4.json"))
        out = decide(season, edir, chosen[0], rule, write=False)
        print(json.dumps(out, indent=1, ensure_ascii=False, default=str) if isinstance(out, dict) else out)
    else:
        raise SystemExit(__doc__)
