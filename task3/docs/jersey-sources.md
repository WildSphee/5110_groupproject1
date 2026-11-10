# Hardcoded Points and Mountains winners

Updated 10 November 2026 using Microsoft Power BI Modeling MCP.

Final 2025 Tour de France winners:
- **Points: Jonathan Milan — 372 points.** [Cyclingstage final points standings](https://www.cyclingstage.com/tour-de-france-2025-points/stage-21-green-jersey-tdf-2025/)
- **Mountains: Tadej Pogačar — 119 points.** [Cyclingstage final KOM standings](https://www.cyclingstage.com/tour-de-france-2025-stage-21/stage-21-polka-dot-tdf-2025/)

`data/jersey_leaders.json` is embedded as a Power Query `#table` in `Jersey Leaders.tmdl`; report refresh requires no internet connection. `Award leaders` and `Winning score` look up the selected checkpoint. There are 42 snapshots, so earlier stage selections remain accurate. Each snapshot records its source URL. Rank 1 is used, including published tie-break ordering; a substitute jersey wearer is not treated as the classification leader.

| Stage | Points leader | Score | Mountains leader | Score | Source |
|---|---|---:|---|---:|---|
| 1 | Jasper Philipsen | 63 | Benjamin Thomas | 2 | [Stage 1 classifications](https://fr.wikipedia.org/wiki/1re_%C3%A9tape_du_Tour_de_France_2025) |
| 2 | Jasper Philipsen | 71 | Tadej Pogačar | 3 | [Stage 2 classifications](https://fr.wikipedia.org/wiki/2e_%C3%A9tape_du_Tour_de_France_2025) |
| 3 | Jonathan Milan | 81 | Tim Wellens | 3 | [Stage 3 classifications](https://fr.wikipedia.org/wiki/3e_%C3%A9tape_du_Tour_de_France_2025) |
| 4 | Jonathan Milan | 92 | Tadej Pogačar | 5 | [Stage 4 classifications](https://fr.wikipedia.org/wiki/4e_%C3%A9tape_du_Tour_de_France_2025) |
| 5 | Tadej Pogačar | 97 | Tadej Pogačar | 5 | [Stage 5 classifications](https://fr.wikipedia.org/wiki/5e_%C3%A9tape_du_Tour_de_France_2025) |
| 6 | Jonathan Milan | 112 | Tim Wellens | 7 | [Stage 6 classifications](https://fr.wikipedia.org/wiki/6e_%C3%A9tape_du_Tour_de_France_2025) |
| 7 | Tadej Pogačar | 156 | Tim Wellens | 8 | [Stage 7 classifications](https://fr.wikipedia.org/wiki/7e_%C3%A9tape_du_Tour_de_France_2025) |
| 8 | Jonathan Milan | 182 | Tim Wellens | 8 | [Stage 8 classifications](https://fr.wikipedia.org/wiki/8e_%C3%A9tape_du_Tour_de_France_2025) |
| 9 | Jonathan Milan | 227 | Tim Wellens | 8 | [Stage 9 classifications](https://fr.wikipedia.org/wiki/9e_%C3%A9tape_du_Tour_de_France_2025) |
| 10 | Jonathan Milan | 227 | Lenny Martinez | 27 | [Stage 10 classifications](https://fr.wikipedia.org/wiki/10e_%C3%A9tape_du_Tour_de_France_2025) |
| 11 | Jonathan Milan | 231 | Lenny Martinez | 27 | [Stage 11 classifications](https://fr.wikipedia.org/wiki/11e_%C3%A9tape_du_Tour_de_France_2025) |
| 12 | Jonathan Milan | 231 | Tadej Pogačar | 27 | [Stage 12 classifications](https://fr.wikipedia.org/wiki/12e_%C3%A9tape_du_Tour_de_France_2025) |
| 13 | Jonathan Milan | 231 | Tadej Pogačar | 37 | [Stage 13 classifications](https://fr.wikipedia.org/wiki/13e_%C3%A9tape_du_Tour_de_France_2025) |
| 14 | Jonathan Milan | 251 | Lenny Martinez | 60 | [Stage 14 classifications](https://fr.wikipedia.org/wiki/14e_%C3%A9tape_du_Tour_de_France_2025) |
| 15 | Jonathan Milan | 251 | Lenny Martinez | 60 | [Stage 15 classifications](https://fr.wikipedia.org/wiki/15e_%C3%A9tape_du_Tour_de_France_2025) |
| 16 | Jonathan Milan | 251 | Tadej Pogačar | 60 | [Stage 16 classifications](https://fr.wikipedia.org/wiki/16e_%C3%A9tape_du_Tour_de_France_2025) |
| 17 | Jonathan Milan | 312 | Tadej Pogačar | 60 | [Stage 17 classifications](https://fr.wikipedia.org/wiki/17e_%C3%A9tape_du_Tour_de_France_2025) |
| 18 | Jonathan Milan | 332 | Tadej Pogačar | 105 | [Stage 18 classifications](https://fr.wikipedia.org/wiki/18e_%C3%A9tape_du_Tour_de_France_2025) |
| 19 | Jonathan Milan | 352 | Tadej Pogačar | 117 | [Stage 19 classifications](https://fr.wikipedia.org/wiki/19e_%C3%A9tape_du_Tour_de_France_2025) |
| 20 | Jonathan Milan | 352 | Tadej Pogačar | 117 | [Stage 20 classifications](https://fr.wikipedia.org/wiki/20e_%C3%A9tape_du_Tour_de_France_2025) |
| 21 | Jonathan Milan | 372 | Tadej Pogačar | 119 | [Stage 21 classifications](https://fr.wikipedia.org/wiki/21e_%C3%A9tape_du_Tour_de_France_2025) |

## Verification

Microsoft Power BI Modeling MCP updated the existing semantic model, exported the changed TMDL, and refreshed the embedded table in both open Desktop instances. Live DAX checks passed for all 42 jersey leader/score snapshots and all 42 unchanged General/Young Rider stage rows. Cleared, single-stage and multiple-stage selections also passed. Evidence: `review/jersey-live-tests.json` and `review/jersey-mcp-update.json`.

The existing portable suite passed 18 of 19 tests. Its unrelated `test_stage_selector_and_awards` failure expects the stage-page selector to default to `All`, whereas the user's current report uses stage 1. This task preserves that report setting.
