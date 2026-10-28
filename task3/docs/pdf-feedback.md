# PDF feedback implementation

Source: `project+dashboard+suggested+functions (1).pdf`, E1–E15. The report now has ten pages and uses a shared teal, gold, violet, coral, blue and sage palette. It retains the fictional race and the original ranking rules while explicitly labelling the additional analytical proxies.

| PDF prompt | Where to explore |
|---|---|
| E1 — GC to daily turning points | 01 leaderboard → 06 GC storyline; choose the same rider, inspect daily rank changes and sort the evidence table. Page 06 starts with Alex Laurent. |
| E2 — Stage vignette and top-ten squads | 08 Routes & stage focus: route/date/type/start/finish/distance/winner, top-ten rider/team/nationality/time table, and team share donut. |
| E3 — Team time contribution | 01 whole-race adjusted-hours bars drill Team → Rider, including completed days before exit; 02 provides stage-level contributions. The fastest-three team classification remains on 04. |
| E4 — Parallel classifications | 03 retains all four original classifications and adds GC versus under-26-at-race-start rank versus mountain-only adjusted-time rank. |
| E5 — Mountain signals | 07 scatter: mountain podium frequency against mean adjusted-time gap to the stage winner; the adjacent matrix expands to individual stages. |
| E6 — Terrain speed | 07 grouped columns compare rider-distance / rider-finish-hours by terrain and team. Filter a rider for their profile. |
| E7 — Bonuses/penalties and counterfactuals | 09 selects official, no bonuses, no penalties, or neither; shows global rank changes and top-ten entry/exit labels, with cumulative adjustment bars. |
| E8 — National participation | 05 Azure bubble map, grouped participation columns (including zero countries), and Country → Team → Rider roster. |
| E9 — National outcomes | 05 best final GC rank, wins and podiums by rider nationality. Select a nation to reveal its roster; use its rider on 02/08 to inspect the underlying results. |
| E10 — Temporal GC | 06 cumulative adjusted hours by stage, daily places gained/lost, mountain-only trace and stage evidence, with rider/team slicers. |
| E11 — ITT catalogue | 08 clear Stage, then choose Individual Time-Trial; date, distance and winner appear in the catalogue. |
| E12 — Top-ten consistency | 07 top-ten bar hierarchy drills Team → Rider; evidence matrix expands Rider → Stage → Terrain. |
| E13 — Squad depth | 01 treemap drills Team → Rider using registered roster counts; rider nationality is available on 05. All six synthetic teams intentionally begin with eight riders. |
| E14 — Top-ten team intensity | 07 stacked bars split top-ten appearances by stage type; drill to contributing riders and inspect daily evidence. |
| E15 — Longest day | 08 opens on stage 15, Nimes–Valence (205 km). Clear Stage to restore the full catalogue, sorted by distance descending. |

## Interpretation

- Slicers remain local to each page. Cross-page narratives use the same rider selected on the destination page; there is no automatic cross-page drillthrough.
- The original Young Rider rule remains born on/after 2001-01-01. The additional race-start comparison uses age under 26 on the first stage date. These are explicitly separate rules; the current fictional birth dates produce the same qualifying set.
- Mountain GC is a time-only proxy, not KOM points. It returns blank before the first mountain stage and excludes riders no longer GC eligible at the selected stage.
- Speed uses raw finish time, so bonuses and penalties do not inflate physical speed. Team values divide total rider-distance by total rider-hours.
- Mountain gaps use the adjusted time of the rider with recorded position 1 as the benchmark, across the complete field. Adjustments can theoretically produce a negative gap.
- What-if scenarios hold eligibility fixed and recompute global competition ranks. Positive movement means places gained. Removing adjustments can change times without changing any ranks or top-ten membership.
- Country participation uses registration; national outcomes use rider nationality. Team nationality remains independent. Country best GC uses the final stage, while wins/podiums include completed results before a rider withdrew.
- The Azure map needs internet access and Azure Maps availability. The adjacent columns retain every country, including Singapore and Japan with zero counts.

## Validation

The source passes 27 Python data/report checks and Microsoft PBIR schema validation. The live Power BI engine passed the original 34 DAX comparisons and 173 additional independently calculated checks. All 62 visual field queries execute successfully. Native Desktop inspection verified the map, treemap, scatterplot, grouped and stacked bars, lines and donut rendering. See `review/analytics-tests.json` for the new calculation evidence.

Power BI authoring reference: [Microsoft Azure Map roles and layers](https://github.com/microsoft/skills-for-fabric/blob/main/skills/powerbi-report-cli/references/authoring/map.md).
