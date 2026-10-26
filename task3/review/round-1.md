# Independent evaluation — round 1

**Score: 7.7/10. Not approved.** The initial dashboard covers all Task 3 subjects and has strong calculation documentation, but a visibly wrong country roster and material readability problems require revision. This review evaluates the initial Desktop screenshots and initial measures before the author's concurrent fixes, not the later revised report.

## Evidence examined

- Read the source requirements PDF and group DOCX earlier; checked traceability, semantics, README, data generator, DAX definitions and test code against them.
- Independently ran `python -m unittest discover -s task3/tests -p test_data.py -v`: **18/18 passed**. The SQL reference recomputes standings from raw results and score rows.
- Ran the generator twice in a temporary directory; all generated file SHA-256 values matched. The production data files were not modified by this check.
- Independently calculated fastest-trio diversity: 9–15 distinct trios per team across the race, proving the fixture exercises changing stage trios. Independently checked bib 1, stage 8: 17,028 − 6 + 0 = **17,022 seconds**.
- Inspected actual Desktop captures `01-overview-rolled-up.png`, `03-classifications.png`, `04-team-performance.png`, `05-country-initial-review.png`, and the interaction log. These demonstrate report loading and populated native visuals. Author-observed drill/roll-up, matrix expansion, cross-filter and historical selector interactions are recorded; I did not independently operate the Desktop during this round.
- Reviewed the reported live MCP DAX results and their executable comparison script. Those 19 tests are useful but omitted the country roster row context that exposes the defect below.

## Score breakdown

| Area | Score | Assessment |
|---|---:|---|
| Required analytical coverage | 1.9 / 2.0 | All four rankings, rider/team/classification times, stage detail and independent country participation are implemented. |
| Numerical/model correctness | 1.9 / 2.5 | Core standings, exits and top-three team calculations pass independent raw checks. Country roster is materially wrong; stage-order and ineligible-status assumptions need tightening. |
| OLAP interaction/drill | 1.5 / 2.0 | Real drill, roll-up, expansion and cross-filter evidence; global ranks retained. Country drill aggregation currently fails at its first level. |
| UI/UX/presentation | 0.7 / 1.5 | Coherent layout and explanations, but tiny table text, excessive unused table width, clipped/overflow text boxes, indistinguishable team series and blank ranks first hinder use. |
| Reproducibility/integration | 0.9 / 1.0 | Portable native PBIP, actual Desktop load, MCP model workflow, deterministic data and clear refresh instructions. |
| Verification/handover | 0.8 / 1.0 | Strong independent SQL reference and documented demo; tests missed a visible filter-context regression and several boundary cases. Final commit still pending. |
| **Total** | **7.7 / 10** | **Must exceed 8.0 after revision.** |

## Required fixes

1. **High — Country roster returns 48 for every nationality.** `Riders by Country` applies `TREATAS` to the same Rider Country column used by matrix rows, replacing that row's filter. France must show 5, Belgium 6, Australia/Colombia/Denmark 4, and remaining represented countries 5. Intersect filters with `KEEPFILTERS`; test country → team → rider and a selected Country slicer, not just the standalone Country dimension chart. Apply equivalent protection to related country measures where needed. Verify through live DAX and a new Desktop capture.
2. **Medium — Readability and overflow.** Increase table/matrix text to a usable size at the documented fit-to-page scale, use the available width for comparison columns, and remove header/footer scrollbars. Recheck all six pages after changing fonts because larger labels can introduce clipping.
3. **Medium — Indistinguishable team line series.** Use distinct colors, visible legend and a clear way to isolate a team. Similar performance traces will overlap even with different colors; retaining the team slicer and a readable tooltip/table is valuable.
4. **Medium — Classifications initially lead with blank ranks.** Sort eligible competitors ahead of exited riders while retaining the latter for eligibility analysis. Ensure all four classifications remain comparable and global rank is unchanged by rider filters.

## Further correctness hardening

- `len(rows) == stage_id`, the SQL reference's `COUNT(*) = stage_id`, and complete-team coverage based on `stage_id` assume stages start at 1 with no gaps. The group report expressly allows stage 0. Use the count of raced stages through the selected stage, or explicitly constrain this fixture and migration contract. Prefer an actual stage-0 regression test.
- `Exited Riders = Registered Riders − Eligible Riders` and snapshot `else 'Exited'` incorrectly describe a rider with a missing earlier result as withdrawn. This does not affect the present complete fixture but weakens reuse. Count explicit exits and distinguish incomplete results from exits; test a missing-stage case.
- Youth fixtures do not exercise the exact DOB threshold; add at/one-day-before boundary checks. Duration tests currently prove numeric time exceeds 24 hours, not that rendered strings avoid wrapping; include a live DAX expected formatted duration.
- Classification colors/jersey associations and friendlier measure column names would improve communication but are not correctness blockers.

The existing project is a substantial working Power BI implementation, not a mockup. Approval remains blocked by the country roster error until corrected and demonstrated. Repeat affected tests and review new screenshots in round 2.
