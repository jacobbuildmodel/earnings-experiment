# Pre-Earnings Model (PRE)

*An AI research system that tested whether positions taken before company earnings announcements can earn more
than simply buying every company that reports. July to November 2026. Closed on the evidence.*

**Purpose.** Earnings announcements are among the few scheduled moments when the market reprices a company. PRE
asked whether research done before an announcement could identify which positions would profit from it, and whether
that held up once it was measured honestly and traded at realistic cost.

**The journey.**

- **First model, July to September.** PRE began as a research analyst. It built a case on each company before its
  results and called the direction of the move, and every call was sealed before the announcement. The record showed
  no skill. More importantly, its rules had been adjusted during measurement, so the record could prove nothing
  either way. I closed it and kept the record exactly as it stood.
- **The experiment, September to November.** I rebuilt PRE as a controlled experiment. The benchmark became buying
  every eligible company, and a screening rule or an AI judge had to beat that benchmark to count. Every decision was
  frozen, timestamped and committed before the market opened, then graded by code after the result. Historical
  testing came first: no screening factor and no options strategy beat the benchmark after costs.
- **Independent review, November.** At the first formal checkpoint I commissioned an independent AI review. It ran
  separately from the model, could not see its reasoning, and had a mandate to recommend termination if the evidence
  warranted it. It rebuilt the results from raw data and found that the checkpoint report had left out the worst day
  in the sample. It also found that trading costs measured in paper trading were several times the study's
  assumption. PRE was narrowed to an automated monitor with exit criteria fixed in advance.
- **Close, 26 November 2026.** With the first full season graded, the live results sat below the historical
  evidence, and costs exceeded any plausible gain at a realistic position size. I closed the project and archived its
  record.

**How it worked.** Each part had a separate role. One step prepared each event, a decision step saw only what was
knowable before the open, code graded every outcome, and a health check halted the system when something broke.
Rules changed only through new versions with their own clock, never by editing a live rule. Any pattern found in
historical data stayed a candidate until it held on data it had not seen.

**Integrity.** The main risk in AI research is a system that agrees with itself and explains outcomes after the
fact. The countermeasures:
- every decision was sealed before the price that graded it existed;
- independent timestamps proved when each decision was made;
- the AI was barred from grading its own calls;
- the model was kept blind to my portfolio;
- an outside review held the authority to stop it.

**What it found.** Predicting earnings is not the same as profiting from them: the price reaction and the cost of
trading decide the result. Historical tests flattered the idea, because they drew on companies that are still large
today. A well-measured "no" is a result. It kept capital from following a belief that did not survive testing, and
it now shapes how my portfolio research treats earnings dates: as a risk to size for, not a reason to buy.

**My role.** Architect and final decision maker. I set the research questions, the rules, the evidence standard and
every funding decision, including the decision to close. Claude wrote and ran the code.

**Principle.** Measure before believing, and stop when the evidence says stop.
