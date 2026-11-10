# Task 3 requirements and verification

The assignment specifies Task 3(a–e) on page 3. The team discussion calls for seven pages with terrain alongside routes and rider exits between GC progression and what-if.

| Requirement | Implementation | Check |
|---|---|---|
| a. Drill by stage, rider and team | Page 02 expands terrain → stage → team → rider. Page 01 drills team → rider, while 04 expands team scores by stage. | In Desktop, selected stage 15, expanded Muret–Carcassonne and Alpecin-Deceuninck to its riders. Live queries reconcile all 3,602 rider-stage results with the export. |
| b. Compare classifications | Page 03 shows General and Young Rider ranks plus all four classification leaders and rules. Published Points and Mountains leader snapshots supplement the export. | Final GC and Young tables reconcile to all 160 and 42 exported entries. MCP checks verify all 42 jersey snapshots and preserve General/Young Rider results. |
| c. Cumulative race times | Pages 01, 03, 04 and 05 show completed rider-hours, eligible classification hours, team top-three totals and rider progress. | Independent SQL checks on 21 snapshots and live checkpoint queries. |
| d. Riders and teams per country | Page 01 distinguishes the two nationality roles, with a map, country comparison and selectable roster. | All 30 country buckets reconcile. Selecting Belgium in Desktop filtered the roster to Belgian riders across teams. |
| e. Layout and interaction | Seven pages, local stage controls, cross-filtering and a single row of stage buttons. | Page/visual schema, layout, overlap and field binding checks, live Desktop interactions and independent scored review. |
| Meeting additions | Merged stages and terrain. Added DNS/withdrawal breakdown, prior rank, remaining field and an exit budget against the actual GC winner. | Tested exit type, terrain, field and budget for all 24 riders. |

See the [review](../review/export-validation.md) for the scoring breakdown and presentation limitations.
