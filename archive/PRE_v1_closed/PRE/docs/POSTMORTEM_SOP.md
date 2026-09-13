# POST-MORTEM SOP + FALSIFICATION PROTOCOL
**Status: BINDING.** Adopted 2026-07-29 from the independent adversarial review.
Applies to **every** closed trade — wins included. Run it before proposing any change.

> **Why this exists.** The model's builder also grades the model. Left unchecked that
> produces a predictable pathology: every loss gets explained, every explanation becomes a
> new gate, the gates accumulate, and the win-rate doesn't move. Between 2026-07-14 and
> 2026-07-28 exactly that happened — FUND-verified gate → guide-freshness gate → and the
> record went 1-for-5. This SOP exists to make patching *hard* and root-causing *easy*.

---

## PART 1 — THE POST-MORTEM (run per closed trade)

### Step 1 — State the outcome with no adjectives
No "unfortunately", no "despite", no "the model was right but". Numbers only.

> `AMKR BUY MEDIUM. Entry 2026-07-27 close $64.96 → exit 07-28 open. Raw gap −14.52%.
> Benchmark SMH −3.25%. Beta 1.344. Abnormal return −10.15%.`

Banned words in Step 1: *unlucky, unfortunately, despite, should have, obviously, just*.

### Step 2 — Name the deciding variable
What **actually** moved the stock — not what the model predicted would move it.

> `AMKR: Q2 beat (EPS 0.70 v 0.49). Q3 revenue guided ~4% below consensus with a
> high-single-digit communications decline. The GUIDE was the deciding variable.`

### Step 3 — Classify the failure type — **before proposing any fix**

| Type | Definition | Fixable? | Permitted response |
|---|---|---|---|
| **A — Observable miss** | The signal existed pre-print; the model ignored, mis-sourced, or mis-scored it | **Yes** | Fix the input or the scoring |
| **B — Unobservable** | The deciding variable did not exist in the pre-print observation space (forward guide, trial result, FDA action) | **No — information boundary** | **PATCHING IS FORBIDDEN.** Change the bet TYPE (magnitude/abstain) or accept the variance |
| **C — Right thesis, wrong expression** | The directional read was correct; the exit or instrument captured it wrong | **Yes** | Fix the expression/exit — **never** the signal |
| **D — Random** | No identifiable cause; move within the name's normal earnings distribution | **No** | Log it. **Any patch here is overfitting by definition** |

**Type B is the one that gets misclassified.** The temptation is to find *some* pre-print
proxy and gate on it. That is how the guide-freshness gate was born. If the deciding
variable was genuinely unobservable, say so and stop.

### Step 4 — Apply the response permitted by the type
- **A** → fix input/scoring. Usually plumbing, not logic.
- **B** → do **not** touch the inputs. Either switch the bet type for that name/sector, or
  accept it as the cost of playing. Record it as a boundary, not a bug.
- **C** → fix the exit/instrument only. The signal was right; leave it alone.
- **D** → log and move on. Write nothing.

### Step 5 — THE ABSTRACTION TEST (mandatory gate on every proposed fix)
A fix ships **only if it passes both limbs.**

> **Limb 1 — Would this fix have prevented the LAST failure of the same type?**
> If no → it is a symptom patch. **Do not ship.**
>
> **Limb 2 — Does this fix break any previously-WINNING trade?**
> If yes → it is overfitting to the latest loss. **Do not ship.**

**Worked example — the fix this SOP killed.** The guide-freshness gate (calc-risk v1.2.0):
- *Limb 1:* would it have prevented AMKR? **No** — the guide-down was Type B, unobservable.
- *Limb 2:* does it break a winner? **Yes** — it blocks AEHR (+35%), whose bookings were
  revealed *in* the print, so nothing fresh was declarable at T−1.
- **Failed both. Reverted in v1.3.0** — one day after shipping.

**Anti-gaming clause.** When a test forces the choice, you may **not** rescue a fix by
asserting a favourable input. (I did exactly this: I set `guidance_fresh=True` on AEHR to
keep the suite green, with a comment justifying it. That is fabricating evidence to protect
a patch.) If a fix only survives on an input you chose to make it survive, **it has failed.**

### Step 6 — Record
Every post-mortem writes: outcome (Step 1), deciding variable (Step 2), **type** (Step 3),
response, and Abstraction Test result. No type = no fix.

---

## PART 2 — THE FALSIFICATION PROTOCOL (run per trade, BEFORE entry)

### Pre-trade: write the falsifiable prediction
Not "BUY". Three lines:

> **Prediction:** what I expect and the mechanism.
> **Falsifier:** the observation that proves me wrong, stated in advance.
> **Null:** the boring explanation that would make this a non-trade.

Example:
> **Prediction:** CLS gaps up ≥3% — washed 38pts vs SMH while FY guidance was raised to $19B.
> **Falsifier:** it gaps < +1%, or down, *even on a beat* — meaning the raise was already priced.
> **Null:** the −38pt underperformance already reflects the good news; there is no gap left to capture.

**If you cannot state the falsifier, you do not have a thesis — you have a feeling. Do not trade.**

### Post-trade: attribute, don't just count P&L

| Question | If yes |
|---|---|
| Did it move for the reason I predicted? | Thesis **confirmed** — even if P&L was negative |
| Did it move for a **different** reason? | Thesis **wrong** — even if P&L was positive (you got lucky) |
| Was the move inside the normal distribution? | Type **D** — no evidence either way |

> **A winning trade can be a wrong thesis. A losing trade can be a right thesis.**
> P&L is not truth; attribution is. Grading on P&L alone is how a model defends bad calls
> ("right but unlucky") and banks bad reasoning ("wrong but paid").

### The inversion — the rule that breaks motivated defending
> **When a call is wrong, the FIRST hypothesis is "the model is wrong."
> You must DISPROVE that before you are allowed to conclude "unlucky."**

To discharge the burden you must positively demonstrate one of:
1. the deciding variable was genuinely unobservable pre-print (**Type B**), or
2. the signal was right and the expression/exit failed (**Type C**), or
3. the move was inside the name's normal distribution (**Type D**).

Absent one of those, the default conclusion is: **the model is wrong, and the root cause is
named.** The burden of proof sits on the model, not on the critic. This is the single most
important clause in this document, because it is the one that a self-grading builder will
otherwise quietly skip.

---

## PART 3 — QUARTERLY REVIEW

1. Re-run every post-mortem's **type** classification in aggregate. Count A/B/C/D.
2. **If Type B dominates** → the model is betting on an unobservable. That is not a tuning
   problem; it is a *bet-selection* problem. Escalate to a structural review.
3. **If Type C dominates** → the signal works and the expression doesn't. Fix exits/instruments.
4. **If Type A dominates** → sourcing discipline is the bottleneck. Fix the data layer.
5. **If Type D dominates** → there is no edge yet, only variance. **Do not tune.** Keep accruing.
6. Check every fix shipped that quarter still passes the Abstraction Test with the new data.
   A fix that has since broken a winner gets reverted.

---

## PART 4 — LEDGER FIELDS THIS SOP REQUIRES
- `failure_type` — A / B / C / D (mandatory on every scored outcome)
- `deciding_variable` — free text, Step 2
- `thesis_confirmed` — true / false / null, from the attribution table
- `falsifier` — recorded **pre-trade**, in the entry, not the outcome
- `abstraction_test` — on every shipped change: both limbs, pass/fail, and the winner checked
