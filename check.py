"""Earnings Experiment - health check. The FIRST command of every session: PASS, or stop.

What must be true before any work builds on this repo:
  1. the core files exist
  2. this folder is its own git repo
  3. the archived PRE v1 record is exactly what was committed - no edits, additions or deletions
  4. no secret files are tracked
  5. uncommitted work is surfaced - a freeze is only provably blind once it is committed
  6. the US-Eastern clock reads, because every freeze is timed against it
  7. the toolchain the pipeline needs is importable
  8. every frozen registry file still matches the hash recorded when it was frozen
"""
import datetime
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

ROOT = os.path.dirname(os.path.abspath(__file__))
COLLECTION_OPENS = datetime.date(2026, 9, 21)
# archive/ is a CLOSED record: 99 tracked files as of commit ea772cf. This number must never change.
ARCHIVE_TRACKED = 99
REQUIRED = ["CLAUDE.md", "CHARTER.md", "STATE.md", "FRAMEWORK.md", "README.md", "archive/README.md",
            ".gitignore", ".gitattributes"]

fails, warns = [], []


def ok(msg):
    print(f"  [ok]   {msg}")


def warn(msg):
    warns.append(msg)
    print(f"  [warn] {msg}")


def bad(msg):
    fails.append(msg)
    print(f"  [FAIL] {msg}")


def git(*args):
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.returncode, r.stdout.strip()


print("=" * 72)
print("EARNINGS EXPERIMENT - health check")
print("=" * 72)

missing = [f for f in REQUIRED if not os.path.exists(os.path.join(ROOT, f))]
if missing:
    bad(f"core files missing: {missing}")
else:
    ok(f"all {len(REQUIRED)} core files present")

rc, top = git("rev-parse", "--show-toplevel")
if rc != 0:
    bad("not a git repository - without git a freeze has no timestamp, so no decision can be shown to be blind")
else:
    if os.path.normcase(os.path.abspath(top)) != os.path.normcase(ROOT):
        bad(f"the git repo root is {top}, not this folder")
    else:
        ok("this folder is its own git repo")

    _, listing = git("ls-files", "archive")
    n = len([x for x in listing.splitlines() if x.strip()])
    if n != ARCHIVE_TRACKED:
        bad(f"archive/ tracks {n} files, expected {ARCHIVE_TRACKED} - the closed record gained or lost files")
    else:
        ok(f"archive/ tracks {ARCHIVE_TRACKED} files")
    _, dirty = git("status", "--porcelain", "--", "archive")
    if dirty:
        bad("archive/ differs from its commit - the closed record must never change:")
        for line in dirty.splitlines()[:10]:
            print(f"           {line}")
    else:
        ok("archive/ matches its commit exactly")

    _, tracked = git("ls-files")
    secrets = [f for f in tracked.splitlines() if f.endswith(".env")]
    if secrets:
        bad(f"secret files are tracked: {secrets}")
    else:
        ok("no .env files tracked")

    _, status = git("status", "--porcelain")
    if status:
        lines = status.splitlines()
        warn(f"{len(lines)} uncommitted change(s) - commit before any freeze")
        for line in lines[:10]:
            print(f"           {line}")
    else:
        ok("working tree clean")
    _, head = git("log", "-1", "--format=%h %ad %s", "--date=short")
    print(f"           HEAD {head}")

# Frozen registry files must be byte-identical (line endings normalised) to the hash recorded when frozen.
import hashlib
frozen_list = os.path.join(ROOT, "registry", "FROZEN.sha256")
if not os.path.exists(frozen_list):
    bad("registry/FROZEN.sha256 is missing - frozen decisions cannot be proven unchanged")
else:
    changed, count = [], 0
    for line in open(frozen_list, encoding="utf-8"):
        if not line.strip():
            continue
        digest, name = line.split(maxsplit=1)
        name = name.strip().lstrip("*")
        path = os.path.join(ROOT, "registry", name)
        count += 1
        if not os.path.exists(path):
            # hidden on purpose by the AI step's sparse checkout (D004 v3 fence): tracked with the
            # skip-worktree flag "S", so its committed copy is checked instead of the disk
            import subprocess
            flag = subprocess.run(["git", "ls-files", "-t", "--", f"registry/{name}"], cwd=ROOT,
                                  capture_output=True, text=True).stdout.strip()
            if flag.startswith("S "):
                blob = subprocess.run(["git", "show", f"HEAD:registry/{name}"], cwd=ROOT, capture_output=True).stdout
                if hashlib.sha256(blob.replace(b"\r\n", b"\n")).hexdigest() != digest:
                    changed.append(f"{name} (fenced; committed copy differs)")
                continue
            changed.append(f"{name} (missing)")
            continue
        data = open(path, "rb").read().replace(b"\r\n", b"\n")
        if hashlib.sha256(data).hexdigest() != digest:
            changed.append(name)
    if changed:
        bad(f"frozen registry file(s) changed: {changed} - a change must be a NEW version, never an edit")
    else:
        ok(f"registry: {count} frozen file(s) match their hashes")

# Nothing frozen may be removed, and the hash lists only ever grow (external review 2026-09-21: deleting
# an event folder, or editing a rule together with its hash line, would otherwise pass).
_, gone = git("log", "--diff-filter=D", "--name-only", "--format=", "--", "events", "universe", "registry", "shadow")
gone = sorted({g for g in gone.splitlines() if g.strip()})
if gone:
    bad(f"file(s) under events/, universe/, registry/ or shadow/ were deleted in history: {gone[:10]}")
else:
    ok("nothing under events/, universe/, registry/ or shadow/ has ever been deleted")
# D009 §3.2: a shadow calendar capture is write-once - the capture in force is the one first committed.
_, edited = git("log", "--diff-filter=M", "--name-only", "--format=", "--", "shadow/calendar")
_, dirty = git("diff", "HEAD", "--name-only", "--", "shadow/calendar")
edited = sorted({g for g in (edited + chr(10) + dirty).splitlines() if g.strip()})
if edited:
    bad(f"shadow calendar capture(s) changed after their first commit: {edited[:10]}")
APPEND_ONLY = ["registry/FROZEN.sha256", "registry/D005_implementation_v1.sha256",
               "registry/D004_implementation_v4.sha256"]
_, hist = git("log", "--format=", "-p", "--", *APPEND_ONLY)
_, work = git("diff", "HEAD", "--", *APPEND_ONLY)
removed = [ln for ln in (hist + "\n" + work).splitlines() if ln.startswith("-") and not ln.startswith("---")]
if removed:
    bad(f"an append-only hash list lost or changed a line: {removed[:5]}")
else:
    ok("hash lists are append-only (no line ever removed or changed)")

# D004 v4 (review 2026-10-05, finding 1): the T2 METHOD is frozen, not only its description. Every file in
# registry/D004_implementation_v4.sha256 must match its latest registered hash; a change is a new line
# with a date and reason (append-only), never a silent edit of the live T2.
_impl = os.path.join(ROOT, "registry", "D004_implementation_v4.sha256")
if os.path.exists(_impl):
    _want = {}
    for _ln in open(_impl, encoding="utf-8"):
        if _ln.strip() and not _ln.startswith("#"):
            _h, _n = _ln.split(maxsplit=1)
            _want[_n.strip()] = _h
    _drift = []
    for _n, _h in _want.items():
        _p = os.path.join(ROOT, _n)
        _d = hashlib.sha256(open(_p, "rb").read().replace(b"\r\n", b"\n")).hexdigest() if os.path.exists(_p) else "missing"
        if _d != _h:
            _drift.append(_n)
    if _drift:
        bad(f"D004 v4 implementation changed without a registered hash: {_drift} - append a dated line to "
            "registry/D004_implementation_v4.sha256 (rule 5: never a silent edit of the live T2)")
    else:
        ok(f"D004 v4 implementation: {len(_want)} file(s) match their registered hashes")

# Frozen events: every file listed in an event's manifest must still match its hash.
import json
import glob
# D004 v4: a stage-2 decision has its own manifest (manifest_t2.json, manifest_t2g.json), checked the same way
manifests = (glob.glob(os.path.join(ROOT, "events", "*", "*", "manifest.json"))
             + glob.glob(os.path.join(ROOT, "events", "*", "*", "manifest_t2*.json")))
changed, readable = [], []
for m in manifests:
    edir = os.path.dirname(m)
    try:
        man = json.load(open(m, encoding="utf-8"))
        listed, _ = man["sha256"], man["entry_open_et"]
    except (ValueError, KeyError) as exc:
        changed.append(f"{os.path.relpath(m, ROOT)} (unreadable: {type(exc).__name__})")
        continue
    readable.append(m)
    for name, digest in listed.items():
        path = os.path.join(edir, name)
        data = open(path, "rb").read().replace(b"\r\n", b"\n") if os.path.exists(path) else b""
        if hashlib.sha256(data).hexdigest() != digest:
            changed.append(os.path.relpath(path, ROOT))
    # No commit after the freeze may touch a frozen file - that is an edit, even if the manifest was
    # rewritten to match. (Commits BEFORE the freeze, e.g. the capture commit, are expected.)
    mrel = os.path.relpath(m, ROOT).replace(os.sep, "/")
    _, fz = git("log", "--diff-filter=A", "--format=%H", "--", mrel)
    if fz:
        for name in list(listed) + [os.path.basename(m)]:
            rel = os.path.relpath(os.path.join(edir, name), ROOT).replace(os.sep, "/")
            _, later = git("log", "--format=%h", f"{fz.split()[-1]}..HEAD", "--", rel)
            if later:
                changed.append(f"{rel} (changed after its freeze, in {later.split()})")
for m in readable:
    b = os.path.basename(m)
    if not b.startswith("manifest_t2"):
        continue
    edir = os.path.dirname(m)
    s2 = json.load(open(m, encoding="utf-8"))
    s1p = os.path.join(edir, "manifest.json")
    s1 = json.load(open(s1p, encoding="utf-8")) if os.path.exists(s1p) else {}
    if s1.get("sha256", {}).get("dossier.json") != s2.get("dossier_sha256"):
        changed.append(f"{os.path.relpath(m, ROOT)} (decided on a dossier that is not the stage-1 frozen one)")
    _, when = git("log", "--diff-filter=A", "--format=%cI", "--", os.path.relpath(m, ROOT).replace(os.sep, "/"))
    if when and datetime.datetime.fromisoformat(when.split()[-1]) >= datetime.datetime.fromisoformat(s2["entry_open_et"]):
        changed.append(f"{os.path.relpath(m, ROOT)} (committed at/after the entry open)")
for f in glob.glob(os.path.join(ROOT, "events", "*", "*", "t2*.json")):
    stem = os.path.basename(f)
    if stem in ("t2.json", "t2g.json") and not os.path.exists(os.path.join(os.path.dirname(f), "manifest_" + stem)):
        warn(f"{os.path.relpath(f, ROOT)} has no stage-2 manifest - not a frozen decision")
manifests = readable
# D013 shadows (T2O, T2R): their integrity problems WARN, labelled, and never FAIL the check - a FAIL would stop
# T2's own queue (t2-queue.yml gates on check.py). The D013 grader excludes any shadow not frozen in time.
D013_STEMS = ("t2o.json", "t2o_thesis", "manifest_t2o", "t2r.json", "t2r_thesis", "manifest_t2r")
d013 = [x for x in changed if any(s_ in x for s_ in D013_STEMS)]
changed = [x for x in changed if x not in d013]
if d013:
    warn(f"D013 SHADOW file problem(s), T2 unaffected: {d013}")
if changed:
    bad(f"frozen event file(s) changed: {changed} - a frozen decision can never be edited")
else:
    ok(f"events: {len(manifests)} frozen manifest(s) match their hashes")

# RFC 3161 timestamp tokens (freeze.py): each must cover the manifest's hash and pre-date the entry open.
# This reads the token's imprint and time; it does not walk the authority's certificate chain.
import re
tok_bad, tok_ok, untimed = [], 0, []
for m in manifests:
    edir = os.path.dirname(m)
    digest = hashlib.sha256(open(m, "rb").read().replace(b"\r\n", b"\n")).hexdigest()
    entry_open = datetime.datetime.fromisoformat(json.load(open(m, encoding="utf-8"))["entry_open_et"])
    tokens = glob.glob(os.path.join(edir, os.path.basename(m).replace(".json", "") + ".tsr_*"))
    if not tokens:
        untimed.append(os.path.basename(edir))
    for t in tokens:
        r = subprocess.run(["openssl", "ts", "-reply", "-in", t, "-text"], capture_output=True, text=True)
        imprint = "".join(re.findall(r"^\s*[0-9a-f]{4} - ([0-9a-f -]+?)\s{2,}", r.stdout, re.M)).replace(" ", "").replace("-", "")
        when = re.search(r"Time stamp: (.+?) GMT", r.stdout)
        if r.returncode or not when:
            tok_bad.append(f"{os.path.relpath(t, ROOT)} (unreadable)")
            continue
        ts = datetime.datetime.strptime(" ".join(when.group(1).split()).split(".")[0], "%b %d %H:%M:%S %Y")
        ts = ts.replace(tzinfo=datetime.timezone.utc)
        if imprint != digest:
            tok_bad.append(f"{os.path.relpath(t, ROOT)} (does not cover the manifest)")
        elif ts >= entry_open:
            tok_bad.append(f"{os.path.relpath(t, ROOT)} (timestamped at/after the entry open)")
        else:
            tok_ok += 1
d013_tok = [x for x in tok_bad if any(s_ in x for s_ in D013_STEMS)]
tok_bad = [x for x in tok_bad if x not in d013_tok]
if d013_tok:
    warn(f"D013 SHADOW timestamp token problem(s), T2 unaffected: {d013_tok}")
if tok_bad:
    bad(f"timestamp token(s) fail: {tok_bad}")
elif manifests:
    ok(f"timestamps: {tok_ok} token(s) cover their manifests and pre-date entry")
if untimed:
    warn(f"{len(untimed)} frozen event(s) have no timestamp token - their proof of time is the git commit alone: {untimed}")

try:
    from zoneinfo import ZoneInfo
    now = datetime.datetime.now(ZoneInfo("America/New_York"))
    days = (COLLECTION_OPENS - now.date()).days
    when = (f"collection opens in {days} day(s)" if days > 0 else
            "collection opens TODAY" if days == 0 else f"collection opened {-days} day(s) ago")
    ok(f"US Eastern {now:%Y-%m-%d %a %H:%M} - {when}")
except Exception as exc:
    warn(f"cannot read the US-Eastern clock ({type(exc).__name__}) - every freeze is timed against it; install tzdata")

try:
    import yfinance  # noqa: F401
    ok("yfinance importable")
except Exception as exc:
    warn(f"yfinance not importable ({type(exc).__name__}) - the pipeline needs it")

print("-" * 72)
if fails:
    print(f"FAIL - {len(fails)} problem(s), {len(warns)} warning(s). Stop: nothing built on this repo counts until it is fixed.")
    sys.exit(1)
print(f"PASS - {len(warns)} warning(s)")
