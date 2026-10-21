# Token efficiency: when a laptop chat should hand off (2026-10-21)

**Answer: hand off at 300k context tokens (30% of the 1M window).** A heads-up comes at 250k. The bar
drops to 200k in the two hours before a time-critical window (09:15 ET T2 deadline; 14:30–15:56 ET gates
and paper exits). This replaces "about 50%" (500k).

The hook `ops/hooks/context_guard.py` enforces it on every prompt and every tool call (wired in
`.claude/settings.json`; tests in `tests/test_context_guard.py`). Re-run the numbers with
`python ops/token_study.py`.

## Facts this rests on (checked 2026-10-21, not assumed)

| fact | value | source |
|---|---|---|
| context window, Opus 5.5 in Claude Code | **1M by default**, no `[1m]` suffix | code.claude.com/docs/en/model-config; platform context-windows page |
| auto-compact point (native-1M models) | about 967k tokens | model-config |
| Opus 5.5 list price per MTok | input $4 · 1-h cache write $8 (2×) · 5-min write $5 (1.25×) · **cache read $0.20 (0.05×)** · output $20 (5×) | platform.claude.com pricing |
| how cache reads count toward the 5-hour and weekly plan limits | **not documented** | support article 11145838; code.claude.com/docs/en/costs |
| prompt cache TTL on a subscription | 1 hour (all writes in these transcripts are 1-h) | settings schema `promptCacheTtl`; transcripts |
| context size of a call | input + cache_read + cache_creation of the latest response (the status line's formula) | code.claude.com/docs/en/statusline |
| hooks | UserPromptSubmit/PostToolUse get `transcript_path` and `session_id` on stdin, plus `agent_id` inside subagents; `hookSpecificOutput.additionalContext` reaches Claude; exit 0 never blocks; exit 2 blocks | code.claude.com/docs/en/hooks |

Plan weighting is unknown, so every result below is computed both ways: **price-weighted** (input-token
equivalents at list price, as a cost-weighted meter would count) and **raw** (every token counts the
same, the worst case).

## Data

There are 9 laptop chats in this project, Sep 21 to Oct 21, with 1,378 main-chain API calls. Each response
is counted once (one response spans several transcript records). Subagent calls are excluded. Scheduled
one-shot runs and the DRIVE project are excluded (rule 9).

| chat | calls | max context | cache-read | output |
|---|---|---|---|---|
| d5662dce (Sep 21) | 188 | 563k | 62.4M | 276k |
| d8da320b (Oct 9–14) | 335 | 649k | 100.9M | 511k |
| 02b934e0 (Oct 13–14) | 186 | 492k | 55.3M | 263k |
| 229fc019 (Oct 14–15) | 91 | 370k | 22.4M | 149k |
| 1ab48b7f (Oct 15) | 78 | 336k | 19.0M | 144k |
| fb52eec7 (Oct 17) | 122 | 488k | 39.9M | 214k |
| **8ce6bcd4 (Oct 15–21, the long chat)** | 301 | **705k** | **118.8M** | 335k |
| 712202ce (Oct 21) | 62 | 219k | 9.8M | 69k |

**Cache reads are 97.3% of all tokens.** Output is under 1%. Every call re-reads the whole context.

## What one more call costs

The fit over all 1,378 calls:

- **price-weighted: 10.3k + 0.085 × context** (0.05 for the cache read, plus cache misses and bigger writes in long chats);
- **raw: 1.6k + 1.0 × context.**

| context at the call | price-weighted cost | raw tokens |
|---|---|---|
| 100–150k | 21k | 127k |
| 200–300k | 33k | 249k |
| 400–500k | 39k | 452k |
| 600–800k | 86k | 645k |

So a call at 650k costs about 4× a call at 125k, by either measure. Context grows **2.7k per call** on
average (median 1.7k). Cache misses, where a call has to re-write the whole context, are rare: 1.6% of calls
come after a gap of more than 1 hour.

## What a hand-off costs

From a prompt to its first file edit:

- a **new chat** takes **22 calls and +110k** of context: start-up, then re-reading what the old chat already held;
- **a new task inside an old chat** takes **4 calls and +8k** (n = 44).

So a hand-off costs **about 18 extra calls**, and the fresh chat starts working at **about 182k**, not at
the 80k floor. The floor is the system prompt, the tool list and CLAUDE.md, about 80k before anything
is read. STATE.md alone is about 10k tokens.

## The threshold that minimises cost per unit of work

Model: a chat starts at C0, grows g per call, and costs a + b × context per call. Handing off at T adds
the start-up calls and about 8 wrap-up calls (STATE, JOURNAL, commit, start_session). The quantity minimised
is cost per work call. The table shows that cost relative to the best threshold, so 1.00 = the optimum.

| case | best | 200k | 250k | **300k** | 350k | 400k | 500k (old rule) | 700k (what happened) |
|---|---|---|---|---|---|---|---|---|
| price-weighted, measured hand-off | 377k | 2.68 | 1.23 | **1.05** | 1.00 | 1.00 | 1.05 | 1.20 |
| raw, measured hand-off | 327k | 2.29 | 1.12 | **1.01** | 1.00 | 1.04 | 1.14 | 1.39 |
| price-weighted, lean hand-off (6 calls, starts at 100k) | 230k | 1.01 | 1.00 | **1.03** | 1.08 | 1.13 | 1.25 | 1.50 |
| raw, lean hand-off | 185k | 1.00 | 1.07 | **1.16** | 1.26 | 1.37 | 1.59 | 2.06 |

**300k is the robust choice: it is never more than 16% worse than the best in any case.**

The old 500k rule is up to 59% worse. Running to 705k, as the Oct 15–21 chat did, is up to 2.06× worse.
The result holds for growth between 2.0k and 3.4k per call: the best threshold moves by ±25k, and 300k
stays within 7% in the measured cases.

In practice a hand-off lands a few calls after the threshold, about 300–320k. The 250k heads-up stops a
new phase from starting high.

## The session-limit days

This table is the local use (all Earnings Experiment chats and their subagents) inside each 5-hour window
that ended in "You've hit your session limit". Window start = the reset time minus 5 h.

| window | minutes before the hit | calls | mean context | price-weighted | raw |
|---|---|---|---|---|---|
| Oct 15 | 292 | 121 | 184k | 3.64M | 22.4M |
| Oct 19 (1st) | 271 | 114 | 366k | 3.72M | 41.9M |
| Oct 19 (2nd) | **69** | 62 | 448k | 2.83M | 27.8M |

- Price-weighted use is steadier across the windows than raw use (3.6–3.7M versus 22–42M). That is weak
  evidence that the meter is cost-weighted. It is not proof: DRIVE chats and the cloud routines draw on the
  same allowance and are not visible here.
- 🔴 **Uncomfortable finding.** If the meter is price-weighted, a 300k rule would not have saved Oct 19. The
  62 calls would have cost about the same, because today's hand-off is expensive (18 calls of re-reading).
  Under raw weighting they would have cost about 23% less. The volume of work drove that limit as much as
  the chat's length did.

## What follows

1. **Enforce a threshold at all.** This is the biggest win. The real chats ran to 490–705k because "about
   50%" was a feeling with no meter, and 700k costs 1.2–2.1× the optimum. The hook now does the measuring.
2. **Make the hand-off lean.** This is the next win, and bigger than the exact threshold. Cutting the
   re-orientation from 18 extra calls to about 2 would drop cost per call by about 29% (price-weighted,
   43k → 31k). It would also make about 230k optimal. Levers:
   - a hand-off brief that names files, lines and decisions, so the new chat does not re-read them;
   - a shorter STATE.md read at start-up.

   When hand-offs get lean, re-run `ops/token_study.py`: the threshold should then move down toward ~250k.
3. **Quality, not measured here.** Long contexts also lose detail (Jacob, 2026-10-20). That argues against
   moving the threshold up.

## Limits of this study

- 9 chats, one month, one model. The "unit of work" is an API call. If calls in a long chat get less done,
  the costs of length are understated.
- The hand-off overhead comes from 7 new chats, and some of their reading would have been needed anyway.
- Plan weighting is unknown (above). Cloud and DRIVE use is invisible.
- US holidays are not modelled: the hook warns on a holiday weekday as if it were a market day.
