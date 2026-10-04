# Task 2: Relational Schema and Normalization

**BT5110 Group Project, Group 5: Tour de France Database**

This section converts the Task 1 ER diagram into a relational schema and normalizes it to BCNF. The full PostgreSQL DDL, including views and triggers, is in `task2_schema.sql` and was tested on PostgreSQL 18.

## 2.1 Assumptions and Agreed ER Interpretation

**Agreed design:** following the feedback, *"Exit and Result entity sets have no key. They could better be relationship sets,"* **Result and Exit are relationship sets between Rider and Stage**, represented by diamonds in the ER model. Their attributes describe a rider's participation in a stage or withdrawal from the race.

- **Result** (*completes*, M:N): a rider can complete multiple stages, and a stage can be completed by multiple riders. The relationship attributes are `finish_rank`, `finish_time`, `time_bonus` and `time_penalty`; `adjusted_time` is derived. Its relational mapping is `Result`, with primary key `(bib_no, stage_id)` drawn from the two participants (L3 Rule #3).
- **Exit** (*withdraws*, N:1 from Rider to Stage): a rider participates in at most one Exit relationship, while multiple riders can exit at the same stage. The relationship attribute is `exit_reason`. Its relational mapping is `Rider_Exit`, with primary key `bib_no`, because each rider exits at most once (L3 Rules #3 and #4).

**ER relationships and relational tables are different concepts.** Lecture 3 maps relationship sets to relations (tables) as well as mapping entity sets to relations. Thus `Result` and `Rider_Exit` remain in the Task 2 schema as relations that store relationships. Neither requires a new entity identifier such as `result_id` or `exit_id`.

**Assumptions.** The keys and FDs below depend on these:

- **A1.** The database holds one race edition, so `bib_no` and `team_name` are unique.
- **A2.** There is at most one stage per day, so `stage_date` is a key and defines stage order.
- **A3.** `finish_rank` is unique within a stage; it breaks ties in finish time.
- **A4.** Country names are unique.
- **A5.** Times are integer seconds, and a missing bonus or penalty is 0.
- **A6.** A stage may start and finish at the same location (circuit stages, time trials). The specification's phrase "to another location" is deliberately not enforced.

## 2.2 ER-to-Relational Mapping

The mapping follows [Lecture 3, *Entity-Relationship Model*](<Lectures/L3. Entity-Relationship Model.pdf>), pp. 23–29, which illustrates the translation rules using SQL `CREATE TABLE` statements with explicit key and integrity constraints.

| ER construct | Cardinality | Translation (L3 rule) |
|---|---|---|
| Country, Team, Rider, Location, Stage, Classification (6 entity sets) | — | One relation each (Rule #2) |
| *represents*, *consist of*, *based in*, *hosts*, *starts*, *ends* | (1,1) on the many side | `NOT NULL` FK in the many-side table (Rules #4 and #5) |
| Result relationship (*completes*) between Rider and Stage | M:N | Relation `result` stores the participant keys and result attributes; PK `(bib_no, stage_id)` (Rule #3) |
| Exit relationship (*withdraws*) between Rider and Stage | Rider (0,1); Stage (0,N) | Relation `rider_exit` stores the participant keys and `exit_reason`; PK `bib_no` (Rules #3 and #4) |
| *wins* (ternary) | Rider **or** Team | Split into `rider_award` and `team_award` (see 2.5) |
| `adjusted_time` | derived | Not stored; computed in a view (Rule #2) |

## 2.3 Relational Schema

We use **RelationName(attribute₁, attribute₂, …)**, with the primary-key attributes underlined, following [Lecture 2, *Relational Model*](<Lectures/L2. Relational Model.pdf>), pp. 8 and 20. All underlined attributes in one relation together form its primary key. **PK** = primary key; **AK** = alternate candidate key (implemented with `UNIQUE`); **FK** = foreign key. Below, `FK: attribute → Relation(key)` identifies the referenced relation and attribute; this is a reference mapping, not a functional dependency.

The tutorial sheets do not mandate one report layout. [Tutorial 1](Tutorials/BT5110_Tut1_Relational.pdf), Q1(c–f), asks for primary keys, foreign keys and constraints; [Tutorial 2](Tutorials/BT5110_Tut2_ER.pdf), Q2, asks for the relational schema, SQL DDL and integrity constraints. We list the keys and constraints beneath each relation; the data types and executable DDL are in [task2_schema.sql](task2_schema.sql). The abstract `R = {…}` and `Σ = {…}` notation in Tutorials 3 and 4 is used for attribute sets and functional dependencies in normalization exercises.

**Country**(<u>country_code</u>, country_name)

- **PK:** `country_code`. **AK:** `country_name`.
- **Constraints:** `country_code` matches `^[A-Z]{3}$`.

**Team**(<u>team_name</u>, country_code)

- **PK:** `team_name`.
- **FK:** `country_code → Country(country_code)`.
- **Constraints:** exactly one leader, hence at least one rider (T1).

**Rider**(<u>bib_no</u>, rider_name, dob, is_leader, team_name, country_code)

- **PK:** `bib_no`.
- **FK:** `team_name → Team(team_name)`; `country_code → Country(country_code)`.
- **Constraints:** `bib_no > 0`; `dob <= CURRENT_DATE`; `is_leader` defaults to `FALSE`; at most one leader per team (partial unique index).

**Location**(<u>location_name</u>, country_code)

- **PK:** `location_name`.
- **FK:** `country_code → Country(country_code)`.
- **Constraints:** must start or end at least one stage (T2).

**Stage**(<u>stage_id</u>, stage_date, start_location, end_location, distance_km, stage_type)

- **PK:** `stage_id`. **AK:** `stage_date`.
- **FK:** `start_location → Location(location_name)`; `end_location → Location(location_name)`.
- **Constraints:** `stage_id >= 0`; `distance_km > 0`; `stage_type` is `flat`, `hilly`, `mountain` or `individual time-trial`.

**Result**(<u>bib_no, stage_id</u>, finish_rank, finish_time, time_bonus, time_penalty)

- **ER origin:** the Result relationship between Rider and Stage. Each row records one rider completing one stage.
- **PK:** `(bib_no, stage_id)`. **AK:** `(stage_id, finish_rank)`.
- **FK:** `bib_no → Rider(bib_no)`; `stage_id → Stage(stage_id)`.
- **Constraints:** `finish_rank > 0`; `finish_time > 0`; `time_bonus >= 0` and `time_penalty >= 0`, both defaulting to `0`; `finish_time - time_bonus + time_penalty > 0`; no result on or after the exit stage (T3).

**Rider_Exit**(<u>bib_no</u>, stage_id, exit_reason)

- **ER origin:** the Exit relationship between Rider and Stage. A row exists only when a rider exits; it records the exit stage and reason.
- **PK:** `bib_no`.
- **FK:** `bib_no → Rider(bib_no)`; `stage_id → Stage(stage_id)`.
- **Constraints:** consistent with Result (T3).

**Classification**(<u>award_type</u>, is_team)

- **PK:** `award_type`.

**Rider_Award**(<u>award_type, bib_no</u>)

- **PK:** `(award_type, bib_no)`.
- **FK:** `award_type → Classification(award_type)`; `bib_no → Rider(bib_no)`.
- **Constraints:** the referenced classification must have `is_team = FALSE` (T4).

**Team_Award**(<u>award_type, team_name</u>)

- **PK:** `(award_type, team_name)`.
- **FK:** `award_type → Classification(award_type)`; `team_name → Team(team_name)`.
- **Constraints:** the referenced classification must have `is_team = TRUE` (T4).

All columns are `NOT NULL`. On foreign keys:

- **Deletes are restricted**, so race history cannot be lost.
- **Updates cascade** on names that can change, such as a team renamed after a sponsorship change.
- Two ER attributes are renamed. `rank` becomes `finish_rank`, because `RANK` is a reserved word in some DBMSs. `bonus` becomes `time_bonus`, to match the specification.

Some rules span several rows or tables, so they need **triggers**:

- **T1** (deferred to COMMIT): each team has exactly one leader. This also guarantees at least one rider.
- **T2** (deferred to COMMIT): a location is stored only if it is the start or finish of a stage.
- **T3**: no result exists on or after a rider's exit stage. It is checked from both tables and compares `stage_date`.
- **T4**: an award's winner type matches `is_team`. This is checked on the winner tables, and also when `is_team` is changed on `classification`.

One Task 1 constraint is **relaxed**: Classification (1,N) in *wins*, meaning every award has a winner. No winner exists until the final stage, so the schema does not enforce it. It is left as a check to run after the race.

**Views** compute the derived data:

- `result_adjusted`: adjusted time = finish − bonus + penalty.
- `gc_standings`: GC standings for riders who have not exited.
- `best_team_standings`: Best Team standings. Following the official race rule, this is the sum of each team's three fastest riders **on each stage**; the specification does not say whether to count per stage or overall.

## 2.4 Normalization

### Functional dependencies (from the business rules)

Following [Lecture 4, *Functional Dependencies*](<Lectures/L4. FD v2.pdf>), pp. 10–11 and 22, braces denote sets of attributes and `X → Y` means that X functionally determines Y. Let `Σ = {FD1, …, FD12}`. Dependencies with the same left-hand side are grouped below for readability; the minimal-cover step splits their right-hand sides into single attributes.

```
FD1   {country_code} → {country_name}
FD2   {country_name} → {country_code}
FD3   {team_name} → {team_country}
FD4   {bib_no} → {rider_name, dob, is_leader, team_name, rider_country}
FD5   {location_name} → {location_country}
FD6   {stage_id} → {stage_date, start_location, end_location, distance_km, stage_type}
FD7   {stage_date} → {stage_id}
FD8   {bib_no, stage_id} → {finish_rank, finish_time, time_bonus, time_penalty}
FD9   {stage_id, finish_rank} → {bib_no}
FD10  {finish_time, time_bonus, time_penalty} → {adjusted_time}
FD11  {bib_no} → {exit_stage, exit_reason}
FD12  {award_type} → {is_team}
```

FD8 describes the attributes of the Result relationship. FD11 describes the Exit relationship: the at-most-one-exit rule makes `bib_no` determine the exit stage and reason. Here `exit_stage` is the role-specific name for `Rider_Exit.stage_id`. These dependencies apply to the relations produced by the mapping, regardless of whether their ER origin is an entity or a relationship.

### Starting point: one flat "race sheet"

```
RaceSheet(bib_no, rider_name, dob, is_leader, team_name, team_country, rider_country, rider_country_name,
          stage_id, stage_date, start_location, end_location, distance_km, stage_type,
          finish_rank, finish_time, time_bonus, time_penalty, adjusted_time)
```

**Candidate keys.** {bib_no, stage_id}⁺ covers all attributes. Only FD9 determines `bib_no`, and only FD7 determines `stage_id`. So the candidate keys are {bib_no, stage_id}, {bib_no, stage_date}, {stage_id, finish_rank} and {stage_date, finish_rank}.

**Normal-form violations:**

- **2NF:** FD4 and FD6 are partial dependencies.
- **3NF:** FD1, FD2, FD3 and FD10 are transitive dependencies.
- **BCNF:** FD7 (`stage_date → stage_id`) and the `stage_id → stage_date` part of FD6 break BCNF only, because their right-hand sides are prime.

**Anomalies.** These make the flat table unusable:

- **Update:** a team's country is repeated on 8 riders × 21 stages = 168 rows.
- **Insertion:** a country with no riders, which the specification requires, cannot be stored. Nor can a stage before anyone has raced it.
- **Deletion:** removing a stage's results also removes its route and distance.

### Decomposition

**Minimal cover.** Following Lecture 4, pp. 43–44, first split every grouped right-hand side into singleton FDs. For example, FD8 becomes `{bib_no, stage_id} → {finish_rank}`, `{bib_no, stage_id} → {finish_time}`, `{bib_no, stage_id} → {time_bonus}` and `{bib_no, stage_id} → {time_penalty}`. Apply the same split to FD4, FD6 and FD11; the other FDs already have singleton right-hand sides. The resulting set is equivalent to Σ. Then check for redundant left-hand-side attributes and redundant FDs:

- No left-hand-side attribute is redundant. For example, {stage_id}⁺ and {bib_no}⁺ alone do not reach `finish_rank`.
- No FD is redundant. Removing any one FD makes its right-hand side unreachable from its left-hand side, as checked by attribute closure.

**3NF synthesis.** Create one relation per left-hand side:

- **Kept:** FD4 → **Rider**, FD3 → **Team**, FD1 → **Country**, FD6 → **Stage**, FD8 → **Result**.
- **Dropped as contained in another relation:** FD2 (in Country), FD7 (in Stage), FD9 (in Result).
- **Not stored:** FD10 would give a table that only records a subtraction, so `adjusted_time` is computed by a view instead.
- **Lossless:** Result contains the key {bib_no, stage_id}.

FD5, FD11 and FD12 give **Location**, **Rider_Exit** and **Classification**. **Apart from the two award tables, the FD analysis reproduces exactly the tables from the ER translation.** The award tables have no non-trivial FDs: they come from the M:N *wins* relationship.

### Final normal form

| Table | Determinants | Candidate keys | NF |
|---|---|---|---|
| Country | country_code, country_name | both | BCNF |
| Stage | stage_id, stage_date | both | BCNF |
| Result | {bib_no, stage_id}, {stage_id, finish_rank} | both | BCNF |
| Team, Rider, Location, Rider_Exit, Classification | the PK only | the PK | BCNF |
| Rider_Award, Team_Award | none (all-key) | all attributes | BCNF |

Every determinant is a candidate key, so all tables are in **BCNF**. The decomposition is also **dependency-preserving**. Every FD except FD10 lies within one table, so `PRIMARY KEY` and `UNIQUE` constraints enforce it. FD10 needs no enforcement, because `adjusted_time` is not stored.

**FDs rejected.** These do not hold:

- `start_location, end_location → distance_km`: the same endpoints can be joined by different routes, so distance stays in Stage.
- `finish_rank → time_bonus`: there is no fixed bonus scale, and time trials give no bonuses.
- `team_name → rider_country`: a rider's nationality can differ from the team's country.

## 2.5 Key Design Decisions

1. **Separate relations for the six entity sets.** Country, Team, Rider, Location, Stage and Classification each store their own entity facts. This removes the anomalies above and allows countries with no teams, and riders whose nationality differs from their team's. Result and Exit are mapped separately using the relationship rules.
2. **One-to-many relationships as foreign keys.** A `NOT NULL` FK on the many side enforces (1,1) participation directly. A separate table, such as `consist_of`, would let a rider exist without a team.
3. **Mapping the Result relationship.** Under L3 Rule #3, the M:N Result relationship becomes `Result(bib_no, stage_id, finish_rank, finish_time, time_bonus, time_penalty)`. Both participant keys are needed to identify a rider–stage completion, and the rank and times describe that completion. A single FK in Rider or Stage cannot represent all these completions.
4. **Mapping the optional Exit relationship.** Under L3 Rules #3 and #4, Exit becomes `Rider_Exit(bib_no, stage_id, exit_reason)`. The Rider (0,1) participation constraint allows `bib_no` alone to be the primary key; `stage_id` remains a foreign key and may occur for multiple riders. A rider who has not exited has no row in this relation. Storing a nullable exit-stage FK and reason in Rider is an alternative, but the separate relation keeps this optional relationship explicit and avoids those NULLs.
5. **Splitting the ternary *wins*.** A winner is a rider *or* a team, so a single `wins(award_type, team_name, bib_no)` table would need NULLs in its primary key. Two all-key tables avoid that, with T4 enforcing `is_team`.
6. **Derived data not stored.** Adjusted time, rider age and Young Rider eligibility, GC standings and Best Team standings are all computed at query time, so they cannot become inconsistent. Award winners are still stored, because Points and King of the Mountains cannot be derived from this schema. For GC and Best Team this is a controlled redundancy: winners are written once after the final stage and should be validated against the views.
7. **Team leader as a flag.** We kept `is_leader` from Task 1. A partial unique index allows at most one leader per team, and T1 requires at least one. A `team.leader_bib` FK was rejected because it creates a circular FK between Team and Rider.

## 2.6 Validation

`task2_schema.sql` was loaded on PostgreSQL 18 with sample data, including a stage that starts and finishes in Caen. Seventeen invalid operations were each rejected by the intended constraint:

- a team with no riders;
- a second leader in a team, and removing a team's only leader;
- an unused location, and deleting the only stage that uses a location;
- results on or after an exit, and an exit recorded before an existing result;
- duplicate ranks in a stage;
- awards given to the wrong kind of winner, and changing `is_team` on an award that already has winners;
- a bad stage type, two stages on the same date, and a bad country code;
- a bonus larger than the finish time;
- a second exit for the same rider.

Valid edge cases were accepted:

- a country with no riders;
- an exit after earlier results;
- swapping a team's leader within one transaction;
- renaming a team, which cascaded to its riders and awards.

The FD analysis in 2.4 was also checked by script. It recomputed the attribute closures, the four candidate keys of RaceSheet, the minimal-cover redundancy checks, BCNF for each table, and dependency preservation, and all match the text.
