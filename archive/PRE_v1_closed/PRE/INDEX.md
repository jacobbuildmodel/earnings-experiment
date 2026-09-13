# INDEX — PRE system master map
**The single file that tells any new session where everything lives and what is canonical.**
**Read this first.** Updated **2026-08-09** · engine **v1.5.6** · edge-score **v1.5.0** · 436 tests.
**`METHOD.md` is the AUDIT artifact (19k tokens) - read it to audit the method, never to run one; the runbook is `.claude/skills/pre/SKILL.md`.** The full auditable method — written for an external evaluator, and the best single
entry point if you want to know what this model actually does before touching anything.

PRE = **pre-earnings directional model.** Two layers with two different jobs:

| layer | question | may it abstain? | output |
|---|---|---|---|
| **FORECAST** (`pre_forecast`) | *what do I think will happen?* | **NEVER** | UP / DOWN + conviction |
| **TRADE** (`pre_edgescore`) | *should I put money on it?* | yes | BUY / SHORT / NO_TRADE |

Collapsing these into one output was the model's central design fault (HANDOFF §19). The
forecast layer is graded on **every** event; the trade layer protects capital and may decline.

> ⛔ **DO NOT TOUCH `../catalyst/` or `../meridian/`.** `../catalyst/` is the public GitHub
> mirror (project CATALYST, internal name PRE) — own `.git`, intentionally diverged,
> re-anonymised. **Never merge PRE/ into catalyst/.** `ledger.jsonl` is gitignored there and
> must never be published. catalyst/ is currently 6 versions behind and **unscrubbed** — its
> git history still contains real tickers. Needs owner approval before any push.

---

## 🎯 CANONICAL SOURCES OF TRUTH

| Question | File | Notes |
|---|---|---|
| **What did the model DECIDE, and how did it resolve?** | `ledger.jsonl` | Frozen pre-registrations (integrity-hashed, append-only) + beta-stripped outcomes. The capital record. |
| **What did the model PREDICT?** | `forecasts.jsonl` | Every name, every event, no abstentions. **Separate on purpose** — paper predictions must never contaminate the capital record. |
| **What is the model known to get WRONG?** | `errors.jsonl` | Error classes + independent confirmations. A wrong call now costs something. |
| **What do we know about THIS company?** | `dossiers/<T>.json` | Last 5 events per name, auto-purged. Read at T-1. |
| **Where did we leave off / what is live?** | `STATE.md`, then `HANDOFF.md` | Session state, directives, post-mortems. |
| **How is it justified / governed?** | `METHOD.md`, `PRE_UPGRADE_PLAN.md`, `docs/POSTMORTEM_SOP.md` | SOP is BINDING on every closed trade. |

**Anti-overfit prime directive:** freeze thresholds at small n; validate FORWARD. **Nothing is
validated.** Capital record **3/8**; forecast backtest **45.2% vs a 51.6% base rate** (§20).

---

## 📁 FOLDER MAP

```
PRE/
├── INDEX.md                this file
├── METHOD.md               *** THE FULL AUDITABLE METHOD — start here ***
├── STATE.md                where we left off
├── HANDOFF.md              history — §19 (forecast layer), §20 (contaminated backtest)
├── ledger.jsonl            THE CAPITAL RECORD (frozen pre-regs + outcomes)
├── forecasts.jsonl         THE PREDICTION RECORD (never abstains)
│
│  ENGINE / SCORING
├── pre_engine.py           v1.5.6  sealed core, all hard gates, C1-C13
├── pre_edgescore.py        v1.5.0  *** LIVE TRADE SCORER *** (§9.1/§9.2 shipped)
├── pre_forecast.py         v1.0.0  *** LIVE FORECAST LAYER — never abstains ***
├── pre_calcrisk.py         v1.3.0  payoff asymmetry — SHADOW ONLY, never decides
│
│  INPUT SOURCING  (all primary-source, all fail-closed)
├── pre_guidance.py         v1.0.0  GG construction + provenance contract + polarity
├── pre_edgar.py            v1.0.0  SEC EDGAR fetcher (8-K/6-K -> guidance prose)
├── pre_vel.py              v1.0.0  VEL from SEC XBRL RPO — FULLY AUTOMATED
├── pre_impliedmove.py      v1.0.0  implied move + provenance + fail-closed decontamination
├── pre_expectations.py     v1.0.0  expectations-bar DIAGNOSTIC (logged, never trades)
│
│  LEARNING  (new 2026-08-09 — the loop that makes a wrong call cost something)
├── pre_errors.py           v1.0.0  ERROR LEDGER: 3 INDEPENDENT confirmations, surprise gate
├── pre_dossier.py          v1.0.0  per-name memory, hard 5-event retention
│
│  RUNNING / SCORING
├── pre_batch.py            v1.0.0  *** THE BATCH RUNNER — use this, not a dated script ***
├── pre_ledger.py           v1.5.3  append-only I/O, market-model beta, kill switches
├── pre_postmortem.py               pulls realized OPEN gaps, writes outcomes
├── backtest_forecast.py            replays the forecast layer over the ledger (§20)
├── run_tests.py                    all 8 suites
│
├── tests/    pre(47) calcrisk(59) ledger(12) edge(67) guidance(76) vel(36) forecast(42)
│          batch(26) errors(49) dossier(22) = 436
├── docs/     POSTMORTEM_SOP.md (BINDING) · EDGE_SCORE_DESIGN.md · skew_overlay_design.md
├── dossiers/ per-name memory, last 5 events each, auto-purged
├── runs/     dated one-off drivers — IMMUTABLE HISTORY, never edit
└── archive/  pre-reorg manifest
```

---

## ⚙️ HOW TO RUN A BATCH  (this is the only supported path)

```bash
# 0. what do we already know? (NEW — this is the compounding step)
python pre_dossier.py brief AAPL          # the name's last 5 events
python pre_errors.py board                # what the model is known to get wrong

# 1. fetch guidance excerpts, then READ them and write gg_<date>.json
python pre_batch.py --tickers AAPL,AMZN --event-date 2026-07-30 --session amc --gg-fetch

# 2. dry run — VEL is automatic; forecasts print for EVERY name
python pre_batch.py --tickers AAPL,AMZN --event-date 2026-07-30 --session amc

# 3. freeze to the ledger. REFUSED automatically after the cutoff.
python pre_batch.py --tickers AAPL,AMZN --event-date 2026-07-30 --session amc --register

# 4. next day
python pre_postmortem.py            # capital record: realized OPEN gaps
python -c "from pre_forecast import score; print(score())"   # prediction record, by regime
python pre_errors.py board          # what moved, what is now RIPE, the surprise rate
```

**THE CLOCK GUARD IS NOT ADVISORY.** `--register` is refused once the session cutoff
(16:00 ET AMC / 09:30 ET BMO) has passed. Cutoffs resolve in exchange time via `zoneinfo`, so
DST is handled. A batch scored after its own print is a counterfactual, not a record — that is
what voided the 2026-07-29 batch (HANDOFF §14).

---

## 🔎 LOOKING SOMETHING UP

```bash
python pre_ledger.py show 10        # last 10 frozen entries
python pre_ledger.py outcomes       # entries still awaiting an outcome
python pre_ledger.py stats          # kill-switch dashboard
python backtest_forecast.py         # forecast accuracy by regime / conviction / basis
python pre_errors.py show <class>   # every observation in one error class, wins included
python pre_dossier.py brief TICKER  # what we know about the company
python pre_vel.py TICKER            # forward-book velocity, with its audit trail
python pre_edgar.py TICKER          # the guidance documents themselves
```
Entry IDs are `TICKER:event_date:hash`. The ledger row **is** the record — there are no
per-name cards.

---

## ✅ INTEGRITY BACKTEST

```bash
python -m py_compile pre_*.py run_tests.py backtest_forecast.py
python run_tests.py                 # 358 assertions across 8 suites
python -c "import json;print(len([l for l in open('ledger.jsonl',encoding='utf-8') if l.strip()]))"
```
As of 2026-08-09: **436/436 pass**; ledger **115 rows**; forecasts **28 rows** (14 + 14 outcomes).

---

## 🚩 WHAT A NEW SESSION MUST NOT DO
- Do **not** register an entry after its own event (`--register` blocks it; do not work around it).
- Do **not** report NO_TRADE as a final answer to Jacob — the forecast layer always has a call.
- Do **not** tune weights or thresholds on small samples. The ±15 washout bar, `CONF_FLOOR
  0.55` and `EDGE_MIN 0.08` are all **un-audited**, and the ±15 bar is the prime suspect
  (it silenced LRCX and ARM before +19.3% and +8.2% moves).
- Do **not** score on the close. The exit is the first OPEN after the print.
- Do **not** quote a CLUSTERED error count as a sample. Three same-sector names on one night is
  **n=1**; `pre_errors.py` counts distinct `(sector, event_date)` keys for exactly this reason.
- Do **not** patch a Type B or Type D miss at any confirmation count. They escalate to a
  bet-selection or distribution QUESTION, never to a parameter change.
- Do **not** quote the forecast backtest (§20) as evidence — the layer post-dates its outcomes.
