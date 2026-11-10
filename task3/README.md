# Tour de France 2025 · Task 3

Open **Tour de France.pbip** in Power BI Desktop. On a fresh clone, choose **Home → Refresh**, then save. The model contains the supplied 2025 database export in portable Power Query tables. Keep the Report and SemanticModel folders beside the project file.

| Page | What to look for |
|---|---|
| 01 Race & participation | Select a nationality or team to see its riders, bibs and teams in the roster. The country columns also work offline. |
| 02 Stages & terrain | Opens on All. Pick one stage or click All to restore the full race. Stage 15 shows Tim Wellens first on Muret–Carcassonne. Expand its results from terrain to route, team and rider. The terrain charts follow the stage selection. |
| 03 Classifications | Compare all four classification leaders, scores and winning criteria at each checkpoint. Points and Mountains use embedded published leader snapshots. |
| 04 Team performance | Compare cumulative team ranks, then expand a team to see its stage scores and finisher counts. Team Visma won across 21 scored stages. |
| 05 GC progression | Opens with the full field. Select a rider to follow their daily rank and gap, or clear the selection for the field again. Remco Evenepoel was third after stage 13. |
| 06 Rider exits | Select a stage or terrain to see which riders left, how the exit was recorded and their last GC positions. Remco withdrew on stage 14. |
| 07 GC what-if | Compare four bonus and penalty rules. The separate exit table gives the adjusted time each rider had left to tie the actual final GC winner. |

The source includes 184 registered riders, 23 teams, 21 stages and 3,602 completed rider-stage results. The final General and Young Rider tables have 160 and 42 finishers respectively. [Calculation definitions](docs/semantics.md) · [Requirements coverage](docs/requirements-matrix.md) · [Independent review and testing](review/export-validation.md)

## Rebuild from the supplied export

From the repository root, use Python 3.11+ and Node.js 22+. The CSV input is under `task3/use_this_data/export/csv`. Refresh in Desktop reads the embedded tables. After changing a CSV, regenerate the project, reopen it and refresh.

```powershell
npm ci --prefix task3/tools
python task3/tools/import_export.py
node task3/tools/build_report.mjs
python task3/tests/test_data.py
python task3/tests/analytics_expected.py
python task3/tools/run_checks.py
node task3/tools/validate_report.mjs
```

To check the running model, open and refresh this PBIP in Desktop. Discover its local Analysis Services port and replace PORT with that value. The test scripts use Microsoft's Power BI Modeling MCP.

```powershell
node task3/tools/discover.mjs
node task3/tools/test_dax.mjs 'Data Source=localhost:PORT'
node task3/tools/test_dax.mjs 'Data Source=localhost:PORT' analytics
node task3/tools/test_visual_queries.mjs 'Data Source=localhost:PORT'
```

Points and Mountains leaders are hardcoded for all 21 stages, including final winners Jonathan Milan (372 points) and Tadej Pogačar (119 mountain points). See [sources and verification](docs/jersey-sources.md).
