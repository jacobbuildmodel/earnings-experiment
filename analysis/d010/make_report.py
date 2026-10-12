import json
r = json.load(open('results.json'))
f = lambda v, p=2: 'n/a' if v is None else f'{100 * v:.{p}f}%'
g = lambda v: 'n/a' if v is None else f'{v:.2f}'
T = {t['id']: t for t in r['tests']}
L = []
L.append('# D010 v1 — the earnings straddle on history · RESULT\n')
L.append('> **EXPLORATION ONLY (rule 6).** Nothing here is confirmed. Confirmation is D009 H-X, live on Season A + B. '
         'Spec: `registry/D010_exploration_options_v1.md`, implemented unchanged. Raw data in `raw/`, code `run_d010.py` (deterministic: two runs gave byte-identical `results.json`).\n')
x1 = T['X1']; x2 = T['X2']
L.append('## Headline\n')
L.append(f"- **Selling the straddle at the bid and buying it back at the ask lost money.** X1 mean `short_exec` = **{f(x1['mean'])}** per $1 of spot "
         f"(t = {g(x1['t'])}, n = {x1['n']}, {x1['r_dates']} R dates). Hit rate {f(x1['hit_rate'],1)}, median {f(x1['median'])}.")
L.append(f"- **Buying it lost more.** X2 mean `long_exec` = **{f(x2['mean'])}** (t = {g(x2['t'])}). Both sides lose to spreads: the mid-price short return is only {f(x1['short_mid_mean'])}, "
         f"so the whole edge is smaller than the round-trip spread cost.")
L.append(f"- Implied move averaged {f(x1['implied_mean'],1)} of spot vs a realised {f(x1['realized_mean'],1)} (realised/implied = {g(x1['ratio_of_means'])} on means, {g(x1['ratio_mean'])} mean of ratios): "
         'the straddle was priced richer than the move on average, but not by enough to pay the spread.')
L.append(f"- **Tail:** worst 1% of short trades = {f(x1['worst_1pct'])}, CVaR 5% = {f(x1['cvar_5'])}, largest single loss = {f(x1['largest_loss'])} of spot. "
         f"Dropping the {x1['without_top1pct_abs']['n_dropped']} largest |returns| leaves mean {f(x1['without_top1pct_abs']['mean'])} (t = {g(x1['without_top1pct_abs']['t'])}).")
L.append(f"- **Findings meeting the rule (q < 0.10 AND |t| > 3 AND same sign in 2019–2022 and 2023–2026): {', '.join(r['findings']) if r['findings'] else 'NONE'}.** "
         'The one-sided tests are all in the "selling pays" direction (X2: "buying pays"), so a strongly negative t gives p ≈ 1.\n')
L.append('## ⚠ Data coverage — read this before trusting any number\n')
L.append(f"- DoltHub `earnings_calendar` has **no rows before 2020-01-22**, so 2019 has zero events (X6a untestable).")
L.append(f"- The DoltHub `option_chain` has **gaps: whole dates missing** (e.g. nothing at all on 2022-02-01) and thin pre-2025 coverage of our names. "
         f"Of {r['events_total']} events, only **{r['valid_events']}** had every quote needed. Valid by year: " + ', '.join(f'{y}: {n}' for y, n in sorted(r['valid_by_year'].items())) + '.')
L.append('- So the result is **dominated by 2025–2026 (' + str(r['valid_by_year'].get('2025', 0) + r['valid_by_year'].get('2026', 0)) + f" of {r['valid_events']} events)**; 2019–2023 has only {sum(v for y, v in r['valid_by_year'].items() if int(y) <= 2023)} valid events, so the "
         'two-halves test is nearly one-sided in sample. Missing quotes are not random (dates and names the source skipped), so the sample is a survivor of the data source on top of the disclosed universe survivorship.')
L.append('- Chain extraction kept rows with 0.25 ≤ |delta| ≤ 0.75 (spec §7 allowance); the traded contract\'s exact quotes on P and Q were pulled without a delta filter. Quotes are end-of-day as published.\n')
L.append('## Events and voids (every reason, by year)\n')
L.append(f"Calendar rows excluded: {r['excluded_calendar_rows']}. Events built: {r['events_total']} ({', '.join(f'{y}: {n}' for y, n in sorted(r['events_by_year'].items()))}).\n")
yrs = sorted(r['events_by_year'])
L.append('| void reason | total | ' + ' | '.join(yrs) + ' |'); L.append('|---|---|' + '---|' * len(yrs))
for k, v in r['voids'].items():
    L.append(f'| {k} | {v["total"]} | ' + ' | '.join(str(v['by_year'].get(y, 0)) for y in yrs) + ' |')
L.append(f"\n`no_quote` breakdown (a data-coverage count, not an economic one): {r['no_quote_detail']}. "
         '`no_P_chain_rows` = no usable chain rows for that symbol on P; `Q_leg_missing` = contract not quoted on the reaction day; `spot_missing` = no yfinance close.\n')
L.append(f"Implied-straddle tercile cut points (full sample): {f(r['implied_tercile_cuts'][0])} and {f(r['implied_tercile_cuts'][1])} of spot.\n")
L.append('## All 22 tests (BH-FDR over all 22)\n')
L.append('| id | sample | n | R dates | mean | t | p | BH q | hit rate | median | worst 1% | CVaR 5% | largest loss | mean short_mid | mean ratio | mean w/o top 1% | halves (19-22 / 23-26) | finding |')
L.append('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
for t in r['tests']:
    h = t['half_means']
    hh = ' / '.join(f(v) for v in h)
    if t['id'] == 'X5':
        L.append(f"| X5 | top − bottom tercile (two-sided) | {t['n']} | {t['r_dates']} | {f(t['mean'])} | {g(t['t'])} | {t['p']:.3f} | {t['q_bh']:.3f} | – | – | – | – | – | – | – | – | {hh} | {'YES' if t['finding'] else 'no'} |")
        continue
    ins = ' (insufficient)' if t['insufficient'] else ''
    tr = t.get('without_top1pct_abs')
    L.append(f"| {t['id']} | {t['description'].split(',')[0]}{ins} | {t['n']} | {t['r_dates']} | {f(t['mean'])} | {g(t['t'])} | {t['p']:.3f} | {t['q_bh']:.3f} | "
             f"{f(t.get('hit_rate'),1)} | {f(t.get('median'))} | {f(t.get('worst_1pct'))} | {f(t.get('cvar_5'))} | {f(t.get('largest_loss'))} | {f(t.get('short_mid_mean'))} | {g(t.get('ratio_mean'))} | {f(tr['mean']) if tr else 'n/a'} | {hh} | {'YES' if t['finding'] else 'no'} |")
L.append('\nStatistic: X2 rows use `long_exec`; all others `short_exec`. Hit rate, median, worst 1%, CVaR 5% and largest loss are for the test\'s own statistic (for X2 that is `long_exec`). '
         'X5 detail: top tercile mean ' + f(T['X5']['top']['mean']) + ', bottom tercile mean ' + f(T['X5']['bottom']['mean']) + '.\n')
L.append('## Choices the spec left open (fixed before looking, stated here)\n')
for k, v in r['method_notes'].items():
    L.append(f'- **{k}**: {v}')
L.append('- CVaR 5% = mean of values at or below the 5th percentile; worst 1% = the 1st percentile; "without top 1%" drops ceil(1% × n) events with the largest absolute statistic.')
L.append('- Untestable cells (n = 0) are reported as missing, carry p = 1 in the BH count, and cannot be findings.\n')
L.append('## Margin note (spec §4)\n')
L.append('A short straddle needs margin of roughly 15–25% of spot. Returns per dollar of margin are about 4–6× the per-spot figures above — and so are the losses. '
         f"On X1 that would turn a {f(x1['mean'])} per-spot mean into roughly {f(x1['mean'] * 4)} to {f(x1['mean'] * 6)} on margin, with the 1%-worst tail at {f(x1['worst_1pct'] * 4,0)} to {f(x1['worst_1pct'] * 6,0)} of margin.\n")
L.append('## What it means\n')
L.append('On this (gappy, 2025-heavy) sample, **neither side of the end-of-day earnings straddle pays after real bid/ask costs**; the mid-price short edge is near zero. '
         'This does not support selling or buying the straddle as a strategy. It is exploration on a source with serious coverage gaps; the live D009 H-X test is the only place it can be confirmed.')
open('REPORT.md', 'w').write('\n'.join(L) + '\n')
