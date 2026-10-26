# Data and calculation contract

All race participants, performances, routes, dates and scores are **synthetic**. The fixture is a teaching dataset, not actual Tour de France results, official regulations or a forecast. Python seed: 5110. No personal data from the group report is copied into the analytical model.

## Source alignment and analytics extensions

The requirements PDF (pages 2–3) governs adjusted times, exits and Task 3. The group report, sections 2.2 and 2.5 and Appendix A, governs the relational keys and the chosen Best Team interpretation. `data/country.csv`, `team.csv`, `rider.csv`, `location.csv`, `stage.csv`, `result.csv` and `exit.csv` match their substantive entities and fields. No changes are made to the source Word document. Award/winner tables alone cannot support comparative standings; calculated rankings are used instead of fabricating stored award winners.

The source schema does not contain Points or Mountains scoring. `classification_score.csv` is an explicit extension at **one row per rider per completed stage**, joined to result on `(bib_no, stage_id)`. Demo rules:

* Flat-stage top ten: 50, 30, 20, 18, 16, 14, 12, 10, 8, 6 points.
* Other-stage top ten: 25, 20, 16, 12, 10, 8, 6, 4, 2, 1 points.
* Mountain-stage top six: 10, 8, 6, 4, 2, 1 mountain points. Other stages: zero.
* No intermediate sprint or summit events are simulated. These rules are not advertised as official 2026 rules.
* Young Rider eligibility: born on/after 2001-01-01, an explicit demo assumption.
* Bonuses: 10/6/4 seconds for the first three finishers except individual time trials. Selected fixture riders receive 30-second penalties.

## Grains and dimensions

| Table | Grain | Purpose |
|---|---|---|
| Result | Rider × completed stage | Finish, bonus, penalty, adjusted seconds, scores |
| Standing | Rider × as-of stage | Recomputed cumulative totals, eligibility and four ranks |
| Team Stage | Team × stage | Finisher count; fastest-three sum, blank when fewer than three |
| Team Standing | Team × as-of stage | Cumulative team score, scored-stage count and global rank |
| Rider | Bib | Name, nationality, team, team nationality, youth flag, exit metadata |
| Team | Team name | Team nationality for independent team analysis |
| Stage | Stage number | Route, date, type and kilometres |
| Country | ISO country code | Complete country list, including nonparticipating countries |
| As Of | Stage number | Disconnected historical standings selector |
| Classification | Classification name | Disconnected classification comparison axis |

Stage and Rider have one-to-many, single-direction relationships to Result and Standing. Stage and Team similarly filter Team Stage and Team Standing. Rider contains team labels intentionally for the rider-performance drill hierarchy; Team independently controls the Best Team page. There is no bidirectional relationship or ambiguous path between rider and team nationality. This is a small analytical star/constellation derived from the group's normalized design, not a replacement for its transactional schema.

## Measures and filters

Adjusted seconds = finish − bonus + penalty. Raw integer seconds are preserved. Hours divide seconds by 3,600. Duration text is `h:mm:ss` with unbounded hours, so a 90-hour ride does not wrap to 18 hours.

Standings snapshots are computed afresh from all results through stage S. A rider must have a result for every stage through S and no exit at/before S. Later exits do not erase historical eligibility. This deliberately extends the group's current-only `v_general_classification` to support historical analysis; final-stage eligibility agrees with the source view. Exited riders retain historical effort but have blank current ranks and eligible cumulative totals.

GC and Young Rider order adjusted cumulative seconds ascending. Points and Mountains order their own cumulative scores descending. Equal values share competition rank, with gaps (1, 1, 3). No official tie-break rules are claimed. Ranks are precomputed against the entire eligible race field; slicing a rider or team does not reset a rank. Blank ranks are not replaced by zero. Rank totals are suppressed outside a single rider/team.

Best Team sums the fastest three adjusted times **within each team on each stage**, then accumulates those stage scores. It is not the sum of the same three riders across the race. Fewer than three finishers yields a blank stage score. Following the group's SQL, rank by scored stages descending, then cumulative top-three seconds ascending. Incomplete coverage remains visibly labelled; Northstar Velo provides a deliberate fixture starting at stage 18.

The As Of selector uses the largest selected stage; clearing it selects the final stage by default. Snapshots are never summed across stages. Its scope is explicitly stated per page. Stage explorer slicers operate on completed results. Its cumulative effort chart includes every prior stage type, including historical effort from riders who subsequently exit. Team diagnostic charts show all stages while the standings table uses the As Of selector.

Classification rider-hours are summed eligible time for the classification's eligible population. General, Points and Mountains have the same eligible population, so these time totals legitimately match. Young Rider restricts to youth-eligible riders. **Hours do not determine Points or Mountains rank.** Their scores are displayed separately in the comparison table.

Country measures use `TREATAS` from the independent Country list into either Team nationality or Rider nationality. Registered riders include withdrawals. Countries with no riders/teams return zero. The roster's drill hierarchy follows rider nationality → team → rider; a team can appear under multiple rider nationalities. Team counts are not inferred from rider nationality. The “countries represented” KPI deliberately shows the whole race, as labelled.

## Replacing the dummy data

Retain the source CSV keys/column contract, replace the deterministic generator input with normalized query results, and recompute snapshot facts from those raw rows. For a production model, prefer Power Query or database views over committed embedded fixtures. Add checkpoint-level scoring if actual sprint/summit points are supplied, agree youth eligibility and tie-break rules, then repeat the automated and Desktop interaction tests. Do not merely replace snapshots without recalculating ranks, exits and eligibility. The present PBIP embeds all fixture data in M expressions to open without paths, credentials or database access; changing a CSV alone does not refresh that embedded data.

Format references: [Microsoft PBIR project documentation](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report) and the Microsoft schema URLs embedded in every report JSON file.
