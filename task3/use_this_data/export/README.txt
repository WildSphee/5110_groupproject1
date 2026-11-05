BT5110 Group 5 - Tour de France database (offline copy)
Exported 2026-11-04 from PostgreSQL 18.6, database "tdf"

CONTENTS
  tdf_backup.sql   Full database: tables, data, triggers, views
  csv/             One CSV per table and per view (UTF-8, with header)
                   Tables: country, team, rider, location, stage, result, exit, award
                   Views:  v_result_adjusted, v_general_classification,
                           v_young_rider_classification, v_best_team

OPTION A - restore the full database (needs PostgreSQL installed)
  psql -U postgres -h localhost -c "CREATE DATABASE tdf ENCODING 'UTF8' TEMPLATE template0"
  psql -U postgres -h localhost -d tdf -f tdf_backup.sql
  Then connect Power BI / Tableau to localhost:5432, database tdf.

OPTION B - no PostgreSQL
  Load the files in csv/ directly into Power BI / Tableau / Excel.
  Join keys: rider.bib_no = result.bib_no, result.stage_id = stage.stage_id,
             rider.team_name = team.team_name, *.country_code = country.country_code

REBUILD FROM SCRATCH (from the raw CSVs in ../data)
  Run from the project folder:
  psql -U postgres -h localhost -d tdf -f sql/01_schema.sql
  psql -U postgres -h localhost -d tdf -f sql/02_load.sql

DATA NOTES
  - All CSV rows loaded; 02_load.sql aborts if any count or value differs.
  - stage_id = order of stage dates (1-21). Data is the 2025 race.
  - Team leader = rider whose bib ends in 1 (not in source data).
  - Rider 78 (Aleksandr Vlasov) has no country (NULL) in the source data.
  - Stage 13: bibs 23 and 197 share rank 108 (no rank 109).
  - Stages 1, 5, 11 start and finish at the same location.
  - Points / King of the Mountains cannot be computed: no sprint or climb points in the data.
