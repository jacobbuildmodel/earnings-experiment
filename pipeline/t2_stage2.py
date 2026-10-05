"""D004 v4 stage 2: T2 decides from the frozen dossier in ONE model call with NO tools, then the decision
is frozen on its own (t2.json + manifest_t2.json + RFC 3161 tokens), before the entry open.

    python pipeline/t2_stage2.py run [--backend claude|gemini|all] [--commit]   # the queue (workflow t2-queue.yml)
    python pipeline/t2_stage2.py list                                             # events waiting, in hash order
    python pipeline/t2_stage2.py dry <season> <TICKER> <date> [--backend claude|gemini] [--edir DIR]
                                                                                  # decide a copy, write nothing in the repo

Backends (D004 v4 §2):
  claude  - T2, the scored track: `claude -p` (Claude Code CLI) with --tools "" and a replaced system prompt,
            authenticated by CLAUDE_CODE_OAUTH_TOKEN, or ANTHROPIC_API_KEY when that secret exists.
  gemini  - T2G, a SHADOW track (CHARTER I2, a second model): the Gemini API with GEMINI_API_KEY, no tools,
            no grounding. Runs only when the key exists.
A usage-limit refusal (HTTP 429) stops that backend for this run; a later run retries while T2 is open.
Order: sha256("<season>|<TICKER>|<date>") ascending (D004 v3 change 3), so whatever capacity misses is
missed at random.
"""
import datetime
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ET, REGISTRY, ROOT, now_et, rule_for, write_json, write_once  # noqa: E402
from freeze import decision_problems, git, push_all, timestamp  # noqa: E402

BACKENDS = {"claude": {"track": "T2", "file": "t2.json", "thesis": "t2_thesis.md", "manifest": "manifest_t2.json"},
            "gemini": {"track": "T2G", "file": "t2g.json", "thesis": "t2g_thesis.md", "manifest": "manifest_t2g.json"}}

SYSTEM = """You are T2, the AI decision track of a pre-registered buy-side earnings experiment.
Task: estimate the probability that the stock's official OPEN on the exit session (the first open after the
earnings print) is ABOVE its official OPEN on the entry session. That is the only thing being scored.

Rules (registry D004 v4):
- You have NO tools and NO internet. Use only the DOSSIER below plus your own general knowledge from training.
  Every dossier item was published before the snapshot time; nothing after it exists for you.
- FIRST, before reading the dossier, answer the leak probe from memory alone: "What did <TICKER>'s stock do
  after its earnings report of <DATE>?" The expected answer is "I don't know". Never guess a specific move.
- Outside view first: start from the dossier's base_rates item (buy-everything hit rates overall, by cluster,
  by session) and state your prior p and which base rate you used. Then say what in the dossier moves you,
  and by how much.
- confidence = your honest probability of a rise (0-1). It is scored by a proper scoring rule: do not push it
  towards 0 or 1 to look decisive. The bar is the buy-everything hit rate (~54%), not 50%.
- decision = "BUY" if and only if confidence > 0.5, else "NO_BUY".
- Do not reason about this experiment's past outcomes; you have none.

Reply with ONE JSON object and nothing else, with exactly these keys:
{"leak_probe": str,
 "prior": {"p": number, "from": str},
 "confidence": number,
 "decision": "BUY" | "NO_BUY",
 "thesis": str (one sentence),
 "reasons": [2 to 5 short strings],
 "moved_from_prior": str (what moved you from the prior, and by how much),
 "deciding_variable": str (what will most likely decide the reaction),
 "theses": [3 objects {"expected": str, "mechanism": str, "wrong_if": str}],
 "key_observations": [strings: what to watch in the print],
 "items_used": [dossier item ids you relied on, e.g. "I4"]}"""


def load(p):
    return json.load(open(p, encoding="utf-8"))


def sha_file(p):
    return hashlib.sha256(open(p, "rb").read().replace(b"\r\n", b"\n")).hexdigest()


def v4(season):
    try:
        r = rule_for("D004_decision_protocol", season)
    except SystemExit:
        return None
    return r if r.get("t2_mode") == "dossier_oneshot" else None


def entry_open(gate):
    d = datetime.date.fromisoformat(gate["timing"]["entry"]["session"])
    return datetime.datetime.combine(d, datetime.time(9, 30), ET)


def deadline(rule, gate):
    return entry_open(gate) - datetime.timedelta(minutes=int(rule.get("t2_deadline_minutes_before_entry_open", 15)))


def prompt(dossier, gate):
    head = (f"EVENT: {gate['ticker']} reports {gate['report_date']} {gate['session']} "
            f"(BMO = before the open, AMC = after the close). Entry: the open of {gate['timing']['entry']['session']}; "
            f"exit: the open of {gate['timing']['exit_A']['session']}. Snapshot taken {gate['captured_et']}.\n"
            f"Leak probe question: \"What did {gate['ticker']}'s stock do after its earnings report of {gate['report_date']}?\"\n\n")
    body = "DOSSIER (JSON):\n" + json.dumps({"items": dossier["items"], "missing": dossier["missing"]}, ensure_ascii=False)
    return head + body


def call_claude(rule, sys_prompt, user):
    """One call, no tools, from a scratch directory (so no project CLAUDE.md is loaded)."""
    model = rule["t2_model"]
    env = dict(os.environ)
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run(["claude", "-p", "--model", model, "--output-format", "json", "--tools", "",
                            "--max-turns", "1", "--system-prompt", sys_prompt],
                           input=user, capture_output=True, text=True, encoding="utf-8", cwd=tmp, env=env, timeout=900)
    try:
        res = json.loads(r.stdout)
    except ValueError:
        return {"ok": False, "limited": False, "error": f"no JSON from claude CLI (rc {r.returncode}): {r.stderr[-500:] or r.stdout[-500:]}"}
    if isinstance(res, list):
        res = next((x for x in res if isinstance(x, dict) and x.get("type") == "result"), {})
    text = res.get("result") or ""
    limited = res.get("api_error_status") == 429 or ("limit" in text.lower() and bool(res.get("is_error")))
    return {"ok": not res.get("is_error"), "limited": limited, "text": text, "model": model,
            "usage": res.get("usage"), "cost_usd_equiv": res.get("total_cost_usd"),
            "error": text if res.get("is_error") else None}


def call_gemini(rule, sys_prompt, user):
    import requests
    key = os.environ.get("GEMINI_API_KEY")
    model = rule["t2g"]["model"]
    if not key:
        return {"ok": False, "limited": False, "error": "no GEMINI_API_KEY", "skip": True}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {"system_instruction": {"parts": [{"text": sys_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 1.0}}
    try:
        r = requests.post(url, params={"key": key}, json=body, timeout=600)
    except requests.RequestException as exc:
        return {"ok": False, "limited": False, "error": f"{type(exc).__name__}"}
    if r.status_code == 429:
        return {"ok": False, "limited": True, "error": "HTTP 429 (free-tier quota)"}
    if r.status_code != 200:
        return {"ok": False, "limited": False, "error": f"HTTP {r.status_code}: {r.text[:300]}"}
    d = r.json()
    try:
        text = "".join(p.get("text", "") for p in d["candidates"][0]["content"]["parts"])
    except (KeyError, IndexError):
        return {"ok": False, "limited": False, "error": f"no candidate: {json.dumps(d)[:300]}"}
    return {"ok": True, "limited": False, "text": text, "model": model, "usage": d.get("usageMetadata")}


CALL = {"claude": call_claude, "gemini": call_gemini}


def parse_reply(text):
    s = text.strip()
    if s.startswith("```"):
        s = s.strip("`")
        s = s[s.find("{"):]
    i, j = s.find("{"), s.rfind("}")
    return json.loads(s[i:j + 1])


def to_t2(reply, dossier, call, decided, rule):
    ids = {it["id"]: it for it in dossier["items"]}
    used = [ids[i] for i in reply.get("items_used") or [] if i in ids] or dossier["items"]
    conf = float(reply["confidence"])
    return {"decision": reply.get("decision"), "confidence": conf, "thesis": reply.get("thesis"),
            "reasons": reply.get("reasons"), "deciding_variable": reply.get("deciding_variable"),
            "prior": reply.get("prior"), "leak_probe": reply.get("leak_probe"),
            "moved_from_prior": reply.get("moved_from_prior"), "theses": reply.get("theses"),
            "key_observations": reply.get("key_observations"),
            "inputs_read": [{"what": f"{it['kind']}{(' ' + it['form']) if it.get('form') else ''}", "url_or_file": it["source"],
                             "published": it["published"], "dossier_item": it["id"]} for it in used],
            "decided_et": decided.isoformat(timespec="seconds"), "model": call.get("model"),
            "method": "D004 v4: one call, no tools, frozen dossier", "usage": call.get("usage"),
            "cost_usd_equiv": call.get("cost_usd_equiv")}


def thesis_md(gate, t2, track):
    th = "\n".join(f"{k + 1}. **Expected:** {x.get('expected')} · **Mechanism:** {x.get('mechanism')} · "
                   f"**Wrong if:** {x.get('wrong_if')}" for k, x in enumerate(t2.get("theses") or []))
    return (f"# {gate['ticker']} {gate['report_date']} {gate['session']} — {track} ({t2.get('model')})\n\n"
            f"**{t2['decision']}, confidence {t2['confidence']:.2f}.** {t2.get('thesis')}\n\n"
            f"- Prior: {(t2.get('prior') or {}).get('p')} — {(t2.get('prior') or {}).get('from')}\n"
            f"- Moved from the prior: {t2.get('moved_from_prior')}\n"
            f"- Deciding variable: {t2.get('deciding_variable')}\n"
            f"- Leak probe: {t2.get('leak_probe')}\n\n## Reasons\n" + "\n".join(f"- {r}" for r in t2.get("reasons") or [])
            + f"\n\n## Three theses\n{th}\n\n## Watch in the print\n" + "\n".join(f"- {r}" for r in t2.get("key_observations") or [])
            + f"\n\nInputs: the frozen dossier ({len(t2['inputs_read'])} items used).\n")


def decide(season, edir, backend, rule, write=True):
    """Decide one event with one backend. Returns 'limited', 'done', 'skip' or an error string."""
    b = BACKENDS[backend]
    gate = load(os.path.join(edir, "gate.json"))
    dpath = os.path.join(edir, "dossier.json")
    man = load(os.path.join(edir, "manifest.json")) if os.path.exists(os.path.join(edir, "manifest.json")) else None
    if write and (not man or man["sha256"].get("dossier.json") != sha_file(dpath)):
        return "the dossier is not the one frozen in manifest.json - refusing"
    dossier = load(dpath)
    sys_prompt, user = SYSTEM, prompt(dossier, gate)
    dl = deadline(rule, gate)
    if write and now_et() >= dl:
        return "skip"
    call = CALL[backend](rule, sys_prompt, user)
    decided = now_et()
    if call.get("skip"):
        return "skip"
    if call.get("limited"):
        return "limited"
    log = {"event": os.path.basename(edir), "backend": backend, "called_et": decided.isoformat(timespec="seconds"),
           "system_sha256": hashlib.sha256(sys_prompt.encode()).hexdigest(),
           "prompt_sha256": hashlib.sha256(user.encode()).hexdigest(), "dossier_sha256": sha_file(dpath),
           "reply": call.get("text"), "error": call.get("error"), "usage": call.get("usage"), "model": call.get("model")}
    if write:
        write_json(os.path.join(ROOT, "logs", "t2", f"{os.path.basename(edir)}_{backend}_{decided:%Y%m%dT%H%M%S}.json"), log)
    if not call.get("ok"):
        return f"call failed: {call.get('error')}"
    try:
        reply = parse_reply(call["text"])
        t2 = to_t2(reply, dossier, call, decided, rule)
    except (ValueError, KeyError, TypeError) as exc:
        return f"unparseable reply: {type(exc).__name__}: {exc}"
    stage1 = load(os.path.join(edir, "decision.json")) if os.path.exists(os.path.join(edir, "decision.json")) else \
        {"t0": {"decision": "BUY"}, "t1": {"decision": None, "note": "dry run"}}
    probs = decision_problems({"t0": stage1["t0"], "t1": stage1["t1"], "t2": t2}, {**gate, "season": season}, dl)
    out = {"track": b["track"], "event": os.path.basename(edir), "season": season, "rule": rule["id"], "t2": t2,
           "problems": probs}
    if not write:
        return out
    if probs:
        write_json(os.path.join(edir, b["file"].replace(".json", "_rejected.json")), out)
        return f"invalid decision: {probs}"
    write_json(os.path.join(edir, b["file"]), out)
    open(os.path.join(edir, b["thesis"]), "w", encoding="utf-8", newline="\n").write(thesis_md(gate, t2, b["track"]))
    return freeze_stage2(season, edir, backend, gate, dl)


def freeze_stage2(season, edir, backend, gate, dl):
    b = BACKENDS[backend]
    rel = os.path.relpath(edir, ROOT).replace(os.sep, "/")
    eo = entry_open(gate)
    if now_et() >= eo:
        return "after the entry open - not frozen (VOID, not late)"
    files = [b["file"], b["thesis"]]
    man = {"event": os.path.basename(edir), "season": season, "track": b["track"], "frozen_et": now_et().isoformat(),
           "entry_open_et": eo.isoformat(), "t2_deadline_et": dl.isoformat(),
           "dossier_sha256": load(os.path.join(edir, "manifest.json"))["sha256"]["dossier.json"],
           "sha256": {f: sha_file(os.path.join(edir, f)) for f in files}}
    mpath = os.path.join(edir, b["manifest"])
    write_once(mpath, man)
    digest = sha_file(mpath)
    # own token names: the stage-1 manifest.tsr_* files are never touched (rehearsal 2026-10-05 caught
    # an earlier version overwriting them)
    renamed, errs = timestamp(digest, edir, stem=b["manifest"].replace(".json", ""))
    logs = glob.glob(os.path.join(ROOT, "logs", "t2", f"{os.path.basename(edir)}_{backend}_*.json"))
    git("add", *[f"{rel}/{f}" for f in files + [b["manifest"]] + renamed],
        *[os.path.relpath(p, ROOT).replace(os.sep, "/") for p in logs])
    t2 = load(os.path.join(edir, b["file"]))["t2"]
    git("commit", "-q", "-m", f"{b['track']} stage 2: {gate['ticker']} {gate['report_date']} {t2['decision']} "
        f"{t2['confidence']:.2f} before entry open {gate['timing']['entry']['session']}\n\n"
        f"manifest sha256 {digest}\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
    when = datetime.datetime.fromisoformat(git("log", "-1", "--format=%cI"))
    pushes = push_all()
    return f"done: {t2['decision']} {t2['confidence']:.2f}, committed {when.astimezone(ET):%H:%M:%S} ET " \
           f"({'BLIND' if when < eo else 'VOID'}), tokens {renamed or 'NONE'}, push {pushes}" + (f", tsa errors {errs}" if errs else "")


def waiting(backend):
    """Frozen PASS events of a v4 season whose stage-2 file for this backend is missing and still open."""
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
        if os.path.exists(os.path.join(edir, BACKENDS[backend]["manifest"])):
            continue
        gate = load(os.path.join(edir, "gate.json"))
        if now_et() >= deadline(rule, gate):
            continue
        out.append((hashlib.sha256(f"{season}|{gate['ticker']}|{gate['report_date']}".encode()).hexdigest(), season, edir, rule))
    return [x[1:] for x in sorted(out)]


def run(backends):
    for backend in backends:
        todo = waiting(backend)
        print(f"{backend}: {len(todo)} event(s) waiting")
        for season, edir, rule in todo:
            r = decide(season, edir, backend, rule)
            print(f"  {backend} {os.path.basename(edir)}: {r}", flush=True)
            if r == "limited":
                print(f"  {backend}: usage limit reached - stopping this backend; a later run retries")
                break
            if r == "skip" and backend == "gemini":
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
    elif a[:1] == ["dry"]:
        season, t, d = a[1], a[2].upper(), a[3]
        edir = a[a.index("--edir") + 1] if "--edir" in a else os.path.join(ROOT, "events", season, f"{t}_{d}")
        rule = load(os.path.join(REGISTRY, "D004_decision_protocol_v4.json")) if os.path.exists(
            os.path.join(REGISTRY, "D004_decision_protocol_v4.json")) else json.loads(a[a.index("--rule") + 1])
        out = decide(season, edir, chosen[0], rule, write=False)
        print(json.dumps(out, indent=1, ensure_ascii=False, default=str) if isinstance(out, dict) else out)
    else:
        raise SystemExit(__doc__)
