# D009 implementation v3 — addendum (2026-10-12 ET): the workflow that runs SH-RU

- **The registered `.github/workflows/runup.yml`** (hashed in `D009_implementation_v3.sha256`) failed its first
  CI run. Its season-list line `for s in seasonA seasonB; do [ -f ... ] && echo "$s"; done` exits 1 under
  `bash -e` because `universe/seasonB` does not exist yet. The `&&` list for seasonB is the last command of
  the loop.
- **Nothing ran.** No SH-RU event was graded, no price was fetched, and no outcome exists. The first X is
  about 2026-11-06.
- **The fix:**
  - `runup.yml` is left byte-identical as the registered record and is **disabled** in GitHub Actions
    (`gh workflow disable`).
  - `.github/workflows/runup-daily.yml`, hashed below, runs the same steps. It differs only in that shell line
    (`if [ -f ... ]; then echo "$s"; fi`), its name and its concurrency group.
  - `pipeline/shadow_runup.py`, the fixtures, the size gate and every pinned dependency are unchanged; their
    registered hashes still hold.
- This is an operational change to the scheduler, not to SH-RU's rules or code (§6).

`8d82fe75cac756d766fad7bc9c27a44b7f821fae1ed364f4301bf14ce4212f63  .github/workflows/runup-daily.yml`
