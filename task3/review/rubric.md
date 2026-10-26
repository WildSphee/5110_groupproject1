# Task 3 independent evaluation rubric

Primary authority: `BT5110 Project Tour de France 2026-1.pdf`, pp. 1–4, especially Task 3 on p. 3. Implementation context: `BT5110_Group Project.docx`, §§2.2–2.5 and Appendix A. This rubric evaluates Task 3; it does not require completing Task 4's database performance comparison.

The user requires an independent score **strictly greater than 8/10**, with up to three evaluation/revision rounds. Each round must report observable evidence, unresolved defects and limitations. Generated artifacts, static validation, independent calculation, semantic-model execution and observed desktop interactions are distinct evidence classes. Passing one must not be represented as passing another.

## Weighted scoring (10 points)

| Area | Weight | Full-credit evidence |
|---|---:|---|
| Required analytical coverage | 2.0 | Explicit stage/rider/team detail; comparison of GC, Points, KOM and Young Rider ranks; cumulative adjusted times by rider, team and classification; distinct team-country and rider-country participation counts, including zero-participation countries. |
| Numerical and model correctness | 2.5 | Correct grain and keys, safe relationships/filter direction, finish − bonus + penalty, complete-stage GC eligibility, exit-aware historical snapshots, documented youth eligibility, points/KOM descending rank versus time ascending rank, ties handled consistently, correct per-stage top-three team aggregation and completeness ordering. Independent expected values match data and executable calculations. |
| OLAP interaction and drill behavior | 2.0 | Actual drill hierarchy or drillthrough beyond slicers alone; detail reconciles to parent totals; return/reset navigation; consistent stage/team/rider filtering; full-field ranks retain meaningful global scope; history and selected-stage context are unambiguous; meaningful empty selections. Desktop interaction evidence earns stronger credit than static definitions alone. |
| UI, UX and presentation quality | 1.5 | Clear overview-to-detail journey, readable hierarchy/labels, well-spaced unclipped visuals, coherent jersey colors with non-color labels, meaningful units and duration formatting beyond 24 hours, restrained precision, explicit synthetic-data status and analytical caveats. Review rendered screenshots where available. |
| Data, reproducibility and integration | 1.0 | Deterministic synthetic fixture with meaningful edge cases; source-aligned schema plus documented extensions; repeatable build/refresh steps; usable Power BI artifact; all source/code objects in project; Power BI MCP use or transparently documented tool availability and fallback; source files and user changes preserved. |
| Verification and handover | 1.0 | Repeatable automated checks plus a concrete drill test script; logged results and provenance; independent evaluation with actionable findings; requirements traceability and demo guidance; final commit includes intended files only. |

## Evidence rules and release blockers

- A missing required classification, wholly absent country analysis, or nonfunctional report artifact blocks approval regardless of aesthetic quality.
- Material wrong rankings, exit behavior or Best Team totals block approval until corrected.
- A screenshot is evidence of appearance, not proof that filters and calculations are correct. A generated schema is evidence of configuration, not proof that Power BI opened it successfully.
- Without a successful Power BI load and observed interactions, explicitly state the remaining integration and UI verification gap. Do not call the dashboard fully tested. Evaluation may score delivered source quality separately, but must not hide the gap behind a passing overall score.
- Tests derived solely from the same generator/calculation implementation do not independently establish numerical correctness. Recompute selected expected values with a separate implementation or hand-check fixtures.
- No external production publication or push is needed. The user requested a local commit.

## Source-derived correctness criteria

1. Country is ISO alpha-3; a country may have no riders and no teams. Team country and rider nationality may differ and must not accidentally share one ambiguous relationship/filter.
2. A rider belongs to one team and one nationality. Team must have riders; DOCX adds exactly one leader. A rider-stage result has unique `(bib_no, stage_id)` and unique finishing position per stage. Equal finish times are legitimate and do not imply equal position.
3. Stage order follows stage ID, including possible stage 0/prologue. All four stage types must be representable. Start/end locations differ under the DOCX constraints.
4. Adjusted seconds = finish seconds − bonus seconds + penalty seconds, always positive. Rank on numeric seconds, not formatted strings. Format long durations without wrapping after 24 hours.
5. No result exists at or after a rider's exit stage. GC at a snapshot requires every raced stage through that snapshot. A short incomplete result history must not win GC due to a smaller total. Preserve legitimate pre-exit historical standing when offering historical analysis; explain that Appendix A's current GC view excludes all recorded exits.
6. DOCX Best Team: on each stage select the three fastest adjusted rider times within each team, sum those three, then sum stage scores. Fewer than three finishers means the stage does not score. Rank first by stages scored descending, then total top-three time ascending, or clearly mark incomplete teams ineligible using a documented deliberate change. Do not select the same three riders across the full race, or sum all riders.
7. The supplied normalized schema does not contain points/KOM observations or a youth rule. Add an explicitly synthetic, documented analytics extension. Do not describe simulated scoring or fabricated 2026 results as actual Tour de France data or official rules. GC/Young Rider rank low adjusted time first; Points/KOM rank high points first. Cumulative time is still a time metric even when grouped by a points classification.
8. Do not average or sum classification rank as a performance total. Rank comparisons are ordinal and need clear population/snapshot context. Selection should not quietly turn every selected rider into rank 1.

## Minimum test cases

| ID | Check | Expected result |
|---|---|---|
| T01 | Regenerate fixture twice | Identical data and deterministic counts/hash. |
| T02 | Keys, foreign keys, domain constraints | No duplicate results/positions, orphan records, negative adjusted times, impossible exits or leader violations. |
| T03 | Bonus + penalty known row | Independently calculated adjusted seconds equals exported/model value. |
| T04 | Same finish time, different positions | Distinct stage finishing positions retained; classification tie rule documented. |
| T05 | Rider exits at stage S | Results stop before S; eligible historical standing before S; no GC placement at/after S. |
| T06 | Missing earlier stage | Rider is not GC eligible even if later result exists and cumulative total is low. |
| T07 | Team rotating fastest trio | Sum of per-stage top-three equals independent computation and differs from full-race fixed-trio shortcut in at least one fixture. |
| T08 | Team with fewer than 3 finishers | Stage is not scored; short total does not unfairly outrank complete teams. |
| T09 | Youth eligibility boundary | DOB threshold and race reference date produce documented exact boundary behavior. |
| T10 | Points/KOM and time ranks | Descending points and ascending seconds, tie behavior and exclusions independently checked. |
| T11 | Country participation | Distinct teams and riders counted on correct nationalities; zero-participation country visible. |
| T12 | Team → rider → stage drill | Child details remain in selected team; result/time counts reconcile; drill-up/back restores context. |
| T13 | Classification/snapshot selection | Selected classification/snapshot values change together; no cross-multiplication or stale rank. |
| T14 | Selected rider/team filter | Context is readable and full-field ranks remain consistent where advertised. |
| T15 | Empty, single, multiple selection | Clear blank/no-data handling; no misleading zero rank, division errors or non-additive totals. |
| T16 | Reopen and refresh Power BI artifact | Report loads with no schema/data/visual errors; paths resolve from documented setup. |
| T17 | UI at normal display size | Titles, labels and tooltips are readable; no overlap/truncation; duration units and dummy-data label clear. |

## Round report format

Record round number; exact artifact/revision reviewed; commands executed and results; UI/runtime evidence inspected; score by six weighted areas; defects with severity and reproducible steps; total score; pass/fail against `> 8/10`; and explicit residual limitations. After revisions, rerun affected checks and material integration checks, up to three rounds in total.
