# Task 3 traceability

Source: `BT5110 Project Tour de France 2026-1.pdf`, page 3, Task 3 (a–e), with page 4's invitation to go beyond the minimum. Group-report alignment is documented in `semantics.md`.

| Requirement | Report implementation | Verification |
|---|---|---|
| a. Drill-down by stage, rider, team | Overview Team → Rider bar; Stage Type → Stage → Team → Rider matrix; Team → Stage matrix; Country → Team → Rider roster | Independent 940-row result reconciliation at four hierarchy levels; Desktop drill/roll-up walkthrough |
| b. Compare General, Points, Mountains, Young Rider rankings | Page 03 side-by-side four ranks, cumulative duration, both score measures, eligibility status; historical As Of selector | SQL window-function reference vs DAX for every rider at six checkpoints; 21 snapshots validated from raw data |
| c. Cumulative race time by rider, team, classification | Overview rider-hours & rider duration; stage cumulative effort; team stage top-three cumulative hours; classification-eligible rider-hours | Raw time identity, duration >24h, team coverage and ranking, running-time context tests |
| d. Teams and riders per country | Separate team-country and rider-country bars/cards; zero-country support and drillable nationality roster | SQL counts vs all 12 Power BI country outputs, foreign-nationality fixture |
| e. Clear, intuitive, attractive layout and interaction | Six named pages, consistent typography/palette, prominent synthetic label, local slicers, in-page guidance, units and definitions | Microsoft JSON schema validation plus Desktop visual and interaction review; independent scored evaluation |
| Additional insight | Withdrawals, historical eligibility, team coverage shortfalls, cross-nationality participation, bonus/penalty audit | Exit boundary tests, stage 17/18 team coverage comparison, country filtering |

No claims are made that Task 4's normalized-vs-star SQL performance benchmark has been completed. This deliverable targets Task 3 and provides a documented analytical model that can support later work.
