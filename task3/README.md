# Tour de France analytics — BT5110 Task 3

Open **Tour de France.pbip** in Power BI Desktop. Keep the `.Report` and `.SemanticModel` directories beside it. If first-open visuals are empty, choose **Home → Refresh**; the embedded dummy data requires no credentials or external paths. Save after refresh to retain a local data cache. Use **File → Save As → Power BI (.pbix)** if a single packaged file is needed. The source-controlled deliverable is the editable PBIP/TMDL/PBIR project.

**All data is fictional.** This is a reproducible demonstration of Task 3, not real Tour de France results. The report has ten pages: Race overview, Stage explorer, Classifications, Team performance, Country participation, GC storyline, Terrain & consistency, Routes & stage focus, GC what-if, and Guide & definitions.

The PDF feedback refresh adds an Azure participation map, treemap, scatterplot, grouped columns, stacked bars and donut alongside the existing line charts and tables, under one shared palette. See [PDF feedback coverage and definitions](docs/pdf-feedback.md) for E1?E15 and the new controls.

## Demo

1. Overview: select the team bar chart, enable its down arrow and click a team. The chart drills to riders; the up arrow rolls back up.
2. Stage explorer: expand the matrix from stage type to stage, team and rider. Check finish − bonus + penalty against adjusted seconds. Slicers narrow the stage, rider or team.
3. Classifications: compare all four global ranks. Select stage 06 then 07 and rider Avery Laurent (bib 8): the exit removes current eligibility at stage 07.
4. Team performance: compare stages 17 and 18 for Northstar Velo. Fewer than three finishers creates an unscored stage; the team cannot win merely by accumulating less time.
5. Countries: inspect France's two teams; Singapore and Japan remain visible with zero participation. Expand the roster to see riders whose nationality differs from their team.

Slicers are local to a page. No As Of selection means the final stage; multiple selections use the latest stage. Use a slicer's eraser to clear it. Click a selected chart mark again to clear cross-filtering. Page 10 explains these controls and the demo scoring assumptions.

## Files

* `data/`: normalized raw CSV fixtures, scoring extension, derived snapshots, model input and DAX definitions.
* `tools/generate_data.py`: deterministic seed-5110 generator.
* `tools/build_model.mjs`: creates and refreshes a semantic model through Microsoft's Power BI Modeling MCP and exports TMDL.
* `tools/build_report.mjs`: creates ten pages in native, publicly documented PBIR format.
* `tests/test_data.py`: raw-data/SQLite tests and independently calculated expected DAX answers.
* `tools/test_dax.mjs`: executes those comparisons against the actual Desktop engine through MCP.
* `tools/test_visual_queries.mjs`: executes all 62 report visual field combinations at their deepest configured drill level; this validates queries, not visual rendering.
* `tools/validate_report.mjs`: validates project/report JSON against Microsoft's published schemas.
* `docs/`: calculation contract and requirement traceability.
* `review/`: test results, real Desktop screenshots/interaction notes and independent scored reviews.

## Reproduce

Requires Python 3.11+ (standard library only for generator/tests), Node 22+, Power BI Desktop and `npm ci` in `tools`. The lock file pins the MCP SDK and Microsoft Power BI Modeling MCP. Running the server uses its EULA acceptance flag; this is the installed Microsoft tool used for this local project.

From the repository root:

```powershell
python task3/tools/generate_data.py
python task3/tests/test_data.py
python task3/tools/run_checks.py
Push-Location task3/tools
npm ci
Pop-Location
node task3/tools/build_report.mjs
node task3/tools/validate_report.mjs
```

To rebuild the model, open a **new blank** Power BI Desktop file and obtain its port with MCP `connection_operations / ListLocalInstances`. Never point the model builder at a report containing work to keep; it creates tables and expects a blank model.

```powershell
node task3/tools/build_model.mjs 'Data Source=localhost:PORT'
# Open task3/Tour de France.pbip, refresh, discover its new port, then:
node task3/tools/test_dax.mjs 'Data Source=localhost:REPORT_PORT'
node task3/tools/test_visual_queries.mjs 'Data Source=localhost:REPORT_PORT'
```

The build-time CSVs are embedded into portable M tables. Editing CSVs alone does not alter the opened report. Rebuild the model and reopen the PBIP to apply replacement data. See `docs/semantics.md` for the migration contract and assumptions.

## Validation of the PDF feedback refresh

27 Python checks, 34 original live DAX comparisons, 173 additional independent analytics comparisons, and 62 visual queries pass. Report/project JSON passes Microsoft schema validation. Native Desktop inspection confirmed the new map and chart types render. The map requires an internet connection; zero-participation countries also remain in the adjacent bar chart.

`docs/pdf-feedback.md` maps every PDF suggestion to a page and documents the proxy calculations. Earlier scored reviews in `review/round-1.md` and `review/round-2.md` describe the previous six-page version, not this refresh.

Additional calculation checks:

```powershell
python task3/tests/analytics_expected.py
node task3/tools/test_dax.mjs 'Data Source=localhost:REPORT_PORT' analytics
```

`generate_data.py` also calls `extend_analytics.py`, which adds the route fields, race-start ages, scenario choices and analytical measures to the portable model. No external dataset credentials are needed.
