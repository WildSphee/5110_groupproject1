# 2025 export validation and independent review

**Score: 8.9/10.** The independent reviewer inspected the raw CSVs, report definitions, populated Power BI Desktop overview and fresh live query results. The review led to clearer labels for the alternative age and mountain-time rankings and the mountain checkpoints on the cumulative GC chart.

| Rubric area | Score |
|---|---|
| Analytical coverage | 1.65 / 2 |
| Numerical correctness | 2.50 / 2.50 |
| Interaction and drill | 1.80 / 2 |
| Visual UX | 1.20 / 1.50 |
| Reproducibility | 0.95 / 1 |
| Verification | 0.80 / 1 |

## Checks performed on the 2025 model

- 19 offline data and report checks passed. The importer reconciled every row of all four supplied database views. Independent SQLite comparisons validated stage snapshots.
- All 66 project and report files passed schema validation. All 38 data-bound visual queries ran against the refreshed Desktop model, alongside 18 source/drill and 244 analytics comparisons through Microsoft's Power BI Modeling MCP. See the adjacent JSON results.
- In Desktop, selecting Belgium on the overview displayed 29 riders in the participation chart and filtered the roster to Belgian riders and their teams. The Azure map rendered locally. [Desktop overview](screenshots/2025-race-overview.jpg)
- On page 02, selecting stage 15 changed the winner to Tim Wellens on Muret–Carcassonne. The bottom terrain charts kept their race-wide comparisons. Expanding Hilly, the stage and Alpecin-Deceuninck exposed individual finish times. [Desktop capture](screenshots/2025-stage15-rider-drill.jpg)
- In the project opened directly from the checkout, selecting stage 14 mid-stage withdrawals returned three riders including Remco Evenepoel, third after stage 13. [Filtered exit table](screenshots/2025-stage14-withdrawals.jpg)
- Final reference results were Tadej Pogacar (277,349 s), Florian Lipowitz (278,009 s) and Team Visma (835,226 s). Of the 24 exits, 12 were DNS and 12 mid-stage withdrawals. Twelve occurred on mountain stages.

The export omits sprint and climb points. At small editor zoom, long team names and wide tables need scrolling. Azure Maps availability depends on the presentation environment, and the adjacent country chart provides the same participation comparison offline. UI actions were sampled; the full set of field combinations was checked in the engine.

Earlier round files, interaction logs, model-build logs and screenshots without the 2025 prefix document the historical synthetic release.

## Stage and rider selection update

Stages & terrain now opens on All. In Desktop, choosing 15 showed Tim Wellens first, one hilly route and three podium finishers. Choosing All restored the full field and the four terrain categories. GC progression opened with multiple riders in the daily table. Selecting Adam Yates narrowed the charts and table to his results, and clearing him restored the field.

The live regression suite now compares finish and podium counts under All and every individual stage, plus unfiltered cumulative hours at three GC checkpoints. The lower terrain charts now follow the stage button.
