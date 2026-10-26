# Tour de France analytics — BT5110 Task 3

Open **Tour de France.pbip** in Power BI Desktop. Keep the `.Report` and `.SemanticModel` directories beside it. If first-open visuals are empty, choose **Home → Refresh**; the embedded dummy data requires no credentials or external paths. Save after refresh to retain a local data cache. Use **File → Save As → Power BI (.pbix)** if a single packaged file is needed. The source-controlled deliverable is the editable PBIP/TMDL/PBIR project.

**All data is fictional.** This is a reproducible demonstration of Task 3, not real Tour de France results. The report has six pages: Race overview, Stage explorer, Classifications, Team performance, Country participation, Guide & definitions.

## Demo

1. Overview: select the team bar chart, enable its down arrow and click a team. The chart drills to riders; the up arrow rolls back up.
2. Stage explorer: expand the matrix from stage type to stage, team and rider. Check finish − bonus + penalty against adjusted seconds. Slicers narrow the stage, rider or team.
3. Classifications: compare all four global ranks. Select stage 06 then 07 and rider Avery Laurent (bib 8): the exit removes current eligibility at stage 07.
4. Team performance: compare stages 17 and 18 for Northstar Velo. Fewer than three finishers creates an unscored stage; the team cannot win merely by accumulating less time.
5. Countries: inspect France's two teams; Singapore and Japan remain visible with zero participation. Expand the roster to see riders whose nationality differs from their team.

Slicers are local to a page. No As Of selection means the final stage; multiple selections use the latest stage. Use a slicer's eraser to clear it. Click a selected chart mark again to clear cross-filtering. Page 06 explains these controls and the demo scoring assumptions.

## Files

* `data/`: normalized raw CSV fixtures, scoring extension, derived snapshots, model input and DAX definitions.
* `tools/generate_data.py`: deterministic seed-5110 generator.
* `tools/build_model.mjs`: creates and refreshes a semantic model through Microsoft's Power BI Modeling MCP and exports TMDL.
* `tools/build_report.mjs`: creates six pages in native, publicly documented PBIR format.
* `tests/test_data.py`: raw-data/SQLite tests and independently calculated expected DAX answers.
* `tools/test_dax.mjs`: executes those comparisons against the actual Desktop engine through MCP.
* `tools/test_visual_queries.mjs`: executes all 36 report visual field combinations at their deepest configured drill level; this validates queries, not visual rendering.
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

## Evaluation and validation

Independent review improved from **7.7/10 in round 1 to 8.6/10 in round 2**, exceeding the requested >8 target in two rounds. See `review/round-1.md` and `review/round-2.md` for the rubric, evidence and limitations.

Final checks: **27 Python tests, 34 live DAX comparisons, 36 visual queries and 86 schema-validated report/project files all pass**. The evaluator independently reran the Python and DAX tests. Real Desktop testing of the initial build verified team-to-rider drill, roll-up, four-level stage matrix expansion, row cross-filtering and historical slicers; screenshots and interaction notes are retained.

**Visual verification limitation:** desktop-control tools became unavailable after the first review. The corrected model was reopened and tested through MCP; typography, table labels, colours, sorting and layout changes were checked in definitions and schemas, but fresh screenshots of the final styling could not be captured. Existing screenshots show the initial build and must not be used as final-version screenshots. Perform a final visual pass at the presentation display scale before the demo. This limitation is included in the independent 8.6 score.
