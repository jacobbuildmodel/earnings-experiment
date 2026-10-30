# D003 v5 · the choice of gate · v1 — FROZEN 2026-10-29 09:30 ET

> Jacob's decision, recorded **before the Stage 1 look** (D017 §5), so the Season B screen is not chosen by any
> Season A outcome (D005 v3).

- **Decision:** D003 v5 = **A4** (D016 §4): the better of the two strikes nearest spot (A1), together with the
  straddle spread `(spread call + spread put) / (mid call + mid put) ≤ 0.10` in place of the per-leg test (A3).
  Every other D003 v4 check is unchanged.
- **Who and when:** Jacob, in chat, Thu 2026-10-29 ~09:28 ET ("Yes, adopt A4").
- **On what:** the D016 counts only (5 → 7 PASS over the audit: RTX and TTMI added). The D016 §5 rule had already
  picked A4. No Season A outcome had been read in a chat before the choice.
- **Not yet the rule:** per D016 §5.4, D003 v5 is a new frozen file and its implementation. It is reviewed
  independently before its freeze and applies **from the Season B screen**. Season A keeps D003 v4 untouched
  (rule 5).
- **Owed before the Season B screen:** `registry/D003_universe_screen_v5.md` + `.json`, the gate code change
  under a new `D003_implementation_v5.sha256`, the independent review, and the note in pooled H-T2C that Seasons A
  and B ran under different gate versions.
