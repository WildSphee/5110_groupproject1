# Task 2: Relational Schema and Normalization

**BT5110 Group Project, Group 5: Tour de France Database**

This section converts the Task 1 ER diagram into a relational schema and normalizes it to BCNF. The full PostgreSQL DDL, including views and triggers, is in `task2_schema.sql` and was tested on PostgreSQL 18.

## 2.1 Assumptions and Task 1 Feedback

**Feedback:** *"Exit and Result entity sets have no key. They could better be relationship sets."* We translate both as relationship sets, keyed by their participants (L3 Rule #3):

- **Result** (*completes*, M:N) has primary key `(bib_no, stage_id)`.
- **Rider_Exit** (*withdraws*, 1:N) has primary key `bib_no`, because a rider exits at most once.

The diagram will be redrawn to match in the final report.

**Assumptions.** The keys and FDs below depend on these:

- **A1.** The database holds one race edition, so `bib_no` and `team_name` are unique.
- **A2.** There is at most one stage per day, so `stage_date` is a key and defines stage order.
- **A3.** `finish_rank` is unique within a stage; it breaks ties in finish time.
- **A4.** Country names are unique.
- **A5.** Times are integer seconds, and a missing bonus or penalty is 0.
- **A6.** A stage may start and finish at the same location (circuit stages, time trials).

## 2.2 ER-to-Relational Mapping

| ER construct | Cardinality | Translation (L3 rule) |
|---|---|---|
| 6 entity sets | — | One table each (Rule #2) |
| *represents*, *consist of*, *based in*, *hosts*, *starts*, *ends* | (1,1) on the many side | `NOT NULL` FK in the many-side table (Rules #4 and #5) |
| *completes* (Result) | M:N | Table `result`, PK `(bib_no, stage_id)` (Rule #3) |
| *withdraws* (Exit) | Rider (0,1) | Table `rider_exit`, PK `bib_no` (Rules #3 and #4) |
| *wins* (ternary) | Rider **or** Team | Split into `rider_award` and `team_award` (see 2.5) |
| `adjusted_time` | derived | Not stored; computed in a view (Rule #2) |

## 2.3 Relational Schema

**PK** = primary key. **AK** = alternate key (`UNIQUE`). **FK** = foreign key.

| Table | Attributes | Keys | Other constraints |
|---|---|---|---|
| **Country** | country_code, country_name | PK country_code; AK country_name | `CHECK` code matches `^[A-Z]{3}$` |
| **Team** | team_name, country_code | PK team_name; FK country_code → Country | Exactly one leader, hence at least one rider (T1) |
| **Rider** | bib_no, rider_name, dob, is_leader, team_name, country_code | PK bib_no; FK team_name → Team; FK country_code → Country | `is_leader` defaults to FALSE; at most one leader per team (partial unique index) |
| **Location** | location_name, country_code | PK location_name; FK country_code → Country | Must start or end at least one stage (T2) |
| **Stage** | stage_id, stage_date, start_location, end_location, distance_km, stage_type | PK stage_id; AK stage_date; FK start_location, end_location → Location | `distance_km > 0`; `stage_type` is flat, hilly, mountain or individual time-trial |
| **Result** | bib_no, stage_id, finish_rank, finish_time, time_bonus, time_penalty | PK (bib_no, stage_id); AK (stage_id, finish_rank); FKs → Rider, Stage | Times ≥ 0; bonus and penalty default 0; finish − bonus + penalty > 0; none on or after the exit stage (T3) |
| **Rider_Exit** | bib_no, stage_id, exit_reason | PK bib_no; FKs → Rider, Stage | Consistent with Result (T3) |
| **Classification** | award_type, is_team | PK award_type | — |
| **Rider_Award** | award_type, bib_no | PK (award_type, bib_no); FKs → Classification, Rider | Only where `is_team = FALSE` (T4) |
| **Team_Award** | award_type, team_name | PK (award_type, team_name); FKs → Classification, Team | Only where `is_team = TRUE` (T4) |

All columns are `NOT NULL`. On foreign keys:

- **Deletes are restricted**, so race history cannot be lost.
- **Updates cascade** on names that can change, such as a team renamed after a sponsorship change.
- `rank` from the ER diagram is renamed `finish_rank`, because `RANK` is a reserved word in some DBMSs.

Some rules span several rows or tables, so they need **triggers**:

- **T1** (deferred to COMMIT): each team has exactly one leader. This also guarantees at least one rider.
- **T2** (deferred to COMMIT): a location is stored only if it is the start or finish of a stage.
- **T3**: no result exists on or after a rider's exit stage. It is checked from both tables and compares `stage_date`.
- **T4**: an award's winner type matches `is_team`.

**Views** compute the derived data:

- `result_adjusted`: adjusted time = finish − bonus + penalty.
- `gc_standings`: GC standings for riders who have not exited.
- `best_team_standings`: Best Team standings, from each team's three fastest riders per stage.

## 2.4 Normalization

### Functional dependencies (from the business rules)

```
FD1  country_code → country_name          FD2  country_name → country_code
FD3  team_name → team_country             FD4  bib_no → rider_name, dob, is_leader, team_name, rider_country
FD5  location_name → location_country     FD6  stage_id → stage_date, start_location, end_location, distance_km, stage_type
FD7  stage_date → stage_id                FD8  bib_no, stage_id → finish_rank, finish_time, time_bonus, time_penalty
FD9  stage_id, finish_rank → bib_no       FD10 finish_time, time_bonus, time_penalty → adjusted_time
FD11 bib_no → exit_stage, exit_reason     FD12 award_type → is_team
```

### Starting point: one flat "race sheet"

```
RaceSheet(bib_no, rider_name, dob, is_leader, team_name, team_country, rider_country, rider_country_name,
          stage_id, stage_date, start_location, end_location, distance_km, stage_type,
          finish_rank, finish_time, time_bonus, time_penalty, adjusted_time)
```

**Candidate keys.** {bib_no, stage_id}⁺ covers all attributes. Only FD9 determines `bib_no`, and only FD7 determines `stage_id`. So the candidate keys are {bib_no, stage_id}, {bib_no, stage_date}, {stage_id, finish_rank} and {stage_date, finish_rank}.

**Normal-form violations:**

- **2NF:** FD4 and FD6 are partial dependencies.
- **3NF:** FD1, FD3 and FD10 are transitive dependencies.
- **BCNF:** FD7 breaks BCNF only, because its right-hand side is prime.

**Anomalies.** These make the flat table unusable:

- **Update:** a team's country is repeated on 8 riders × 21 stages = 168 rows.
- **Insertion:** a country with no riders, which the specification requires, cannot be stored. Nor can a stage before anyone has raced it.
- **Deletion:** removing a stage's results also removes its route and distance.

### Decomposition

**Minimal cover.** Nothing can be removed:

- No left-hand-side attribute is redundant. For example, {stage_id}⁺ and {bib_no}⁺ alone do not reach `finish_rank`.
- No FD is redundant. Each right-hand-side attribute has exactly one derivation.

**3NF synthesis.** Create one relation per left-hand side:

- **Kept:** FD4 → **Rider**, FD3 → **Team**, FD1 → **Country**, FD6 → **Stage**, FD8 → **Result**.
- **Dropped as contained in another relation:** FD2 (in Country), FD7 (in Stage), FD9 (in Result).
- **Not stored:** FD10 would give a table that only records a subtraction, so `adjusted_time` is computed by a view instead.
- **Lossless:** Result contains the key {bib_no, stage_id}.

FD5, FD11 and FD12 give **Location**, **Rider_Exit** and **Classification**. **The FD analysis reproduces exactly the tables from the ER translation.**

### Final normal form

| Table | Determinants | Candidate keys | NF |
|---|---|---|---|
| Country | country_code, country_name | both | BCNF |
| Stage | stage_id, stage_date | both | BCNF |
| Result | {bib_no, stage_id}, {stage_id, finish_rank} | both | BCNF |
| Team, Rider, Location, Rider_Exit, Classification | the PK only | the PK | BCNF |
| Rider_Award, Team_Award | none (all-key) | all attributes | BCNF |

Every determinant is a candidate key, so all tables are in **BCNF**. The decomposition is also **dependency-preserving**: every FD lies within one table, so `PRIMARY KEY` and `UNIQUE` constraints enforce all of them.

**FDs rejected.** These do not hold:

- `start_location, end_location → distance_km`: the same endpoints can be joined by different routes, so distance stays in Stage.
- `finish_rank → time_bonus`: there is no fixed bonus scale, and time trials give no bonuses.
- `team_name → rider_country`: a rider's nationality can differ from the team's country.

## 2.5 Key Design Decisions

1. **Separate entity tables.** Each fact is stored once, which removes the anomalies above. It also allows countries with no teams, and riders whose nationality differs from their team's.
2. **One-to-many relationships as foreign keys.** A `NOT NULL` FK on the many side enforces (1,1) participation directly. A separate table, such as `consist_of`, would let a rider exist without a team.
3. **Many-to-many relationships as tables.** *completes* cannot be stored as an FK on either side without repeating groups. `result` keys it on both participants, and its attributes (rank, times) depend on that whole key.
4. **Exit in its own table, not columns in Rider.** Merging would still be BCNF, but most riders never exit, so the exit columns would be NULL on most rows. This follows the L3 passport example. Keying on `bib_no` alone also blocks a second exit for the same rider.
5. **Splitting the ternary *wins*.** A winner is a rider *or* a team, so a single `wins(award_type, team_name, bib_no)` table would need NULLs in its primary key. Two all-key tables avoid that, with T4 enforcing `is_team`.
6. **Derived data not stored.** Adjusted time, rider age and Young Rider eligibility, GC standings and Best Team standings are all computed at query time, so they cannot become inconsistent. Award winners are still stored, because Points and King of the Mountains cannot be derived from this schema. For GC and Best Team this is a controlled redundancy: winners are written once after the final stage and checked against the views.
7. **Team leader as a flag.** We kept `is_leader` from Task 1. A partial unique index allows at most one leader per team, and T1 requires at least one. A `team.leader_bib` FK was rejected because it creates a circular FK between Team and Rider.

## 2.6 Validation

`task2_schema.sql` was loaded on PostgreSQL 18 with sample data, including a stage that starts and finishes in Caen. Sixteen invalid operations were each rejected by the intended constraint:

- teams without a leader;
- unused locations;
- results on or after an exit;
- duplicate ranks;
- awards given to the wrong kind of winner;
- bad stage types, dates and country codes;
- a second exit for the same rider.

Valid edge cases were accepted:

- a country with no riders;
- swapping a team's leader within one transaction;
- renaming a team, which cascaded to its riders and awards.
