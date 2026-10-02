-- BT5110 Group 5 - Task 2: Tour de France relational schema (PostgreSQL 18)

-- ============ 1. Tables ============

CREATE TABLE country (
    country_code  CHAR(3)       PRIMARY KEY
                                CHECK (country_code ~ '^[A-Z]{3}$'),
    country_name  VARCHAR(100)  NOT NULL UNIQUE
);

CREATE TABLE team (
    team_name     VARCHAR(100)  PRIMARY KEY,
    country_code  CHAR(3)       NOT NULL
                                REFERENCES country (country_code)
                                ON UPDATE CASCADE
);

CREATE TABLE rider (
    bib_no        SMALLINT      PRIMARY KEY CHECK (bib_no > 0),
    rider_name    VARCHAR(100)  NOT NULL,
    dob           DATE          NOT NULL CHECK (dob <= CURRENT_DATE),
    is_leader     BOOLEAN       NOT NULL DEFAULT FALSE,
    team_name     VARCHAR(100)  NOT NULL
                                REFERENCES team (team_name)
                                ON UPDATE CASCADE,
    country_code  CHAR(3)       NOT NULL
                                REFERENCES country (country_code)
                                ON UPDATE CASCADE
);

-- At most one leader per team (partial unique index)
CREATE UNIQUE INDEX rider_one_leader_per_team
    ON rider (team_name) WHERE is_leader;

CREATE TABLE location (
    location_name VARCHAR(100)  PRIMARY KEY,
    country_code  CHAR(3)       NOT NULL
                                REFERENCES country (country_code)
                                ON UPDATE CASCADE
);

CREATE TABLE stage (
    stage_id       SMALLINT      PRIMARY KEY CHECK (stage_id >= 0),
    stage_date     DATE          NOT NULL UNIQUE,
    start_location VARCHAR(100)  NOT NULL
                                 REFERENCES location (location_name)
                                 ON UPDATE CASCADE,
    end_location   VARCHAR(100)  NOT NULL
                                 REFERENCES location (location_name)
                                 ON UPDATE CASCADE,
    distance_km    NUMERIC(5,1)  NOT NULL CHECK (distance_km > 0),
    stage_type     VARCHAR(25)   NOT NULL
                                 CHECK (stage_type IN ('flat', 'hilly', 'mountain',
                                                       'individual time-trial'))
);

CREATE TABLE result (
    bib_no        SMALLINT  REFERENCES rider (bib_no),
    stage_id      SMALLINT  REFERENCES stage (stage_id),
    finish_rank   SMALLINT  NOT NULL CHECK (finish_rank > 0),
    finish_time   INTEGER   NOT NULL CHECK (finish_time > 0),       -- seconds
    time_bonus    INTEGER   NOT NULL DEFAULT 0 CHECK (time_bonus >= 0),
    time_penalty  INTEGER   NOT NULL DEFAULT 0 CHECK (time_penalty >= 0),
    PRIMARY KEY (bib_no, stage_id),
    UNIQUE (stage_id, finish_rank),
    CHECK (finish_time - time_bonus + time_penalty > 0)
);

CREATE TABLE rider_exit (
    bib_no       SMALLINT      PRIMARY KEY REFERENCES rider (bib_no),
    stage_id     SMALLINT      NOT NULL REFERENCES stage (stage_id),
    exit_reason  VARCHAR(200)  NOT NULL
);

CREATE TABLE classification (
    award_type  VARCHAR(40)  PRIMARY KEY,
    is_team     BOOLEAN      NOT NULL
);

CREATE TABLE rider_award (
    award_type  VARCHAR(40)  REFERENCES classification (award_type)
                             ON UPDATE CASCADE,
    bib_no      SMALLINT     REFERENCES rider (bib_no),
    PRIMARY KEY (award_type, bib_no)
);

CREATE TABLE team_award (
    award_type  VARCHAR(40)   REFERENCES classification (award_type)
                              ON UPDATE CASCADE,
    team_name   VARCHAR(100)  REFERENCES team (team_name)
                              ON UPDATE CASCADE,
    PRIMARY KEY (award_type, team_name)
);

-- ============ 2. Derived data (views, never stored) ============

CREATE VIEW result_adjusted AS
SELECT r.*,
       r.finish_time - r.time_bonus + r.time_penalty AS adjusted_time
FROM result r;

CREATE VIEW gc_standings AS
SELECT ra.bib_no,
       SUM(ra.adjusted_time)                            AS total_time,
       RANK() OVER (ORDER BY SUM(ra.adjusted_time))     AS gc_position
FROM result_adjusted ra
WHERE NOT EXISTS (SELECT 1 FROM rider_exit e WHERE e.bib_no = ra.bib_no)
GROUP BY ra.bib_no;

CREATE VIEW best_team_standings AS
WITH per_stage AS (
    SELECT rd.team_name, ra.stage_id, ra.adjusted_time,
           ROW_NUMBER() OVER (PARTITION BY rd.team_name, ra.stage_id
                              ORDER BY ra.adjusted_time)  AS pos_in_team
    FROM result_adjusted ra
    JOIN rider rd ON rd.bib_no = ra.bib_no
)
SELECT team_name,
       SUM(adjusted_time)                               AS team_time,
       RANK() OVER (ORDER BY SUM(adjusted_time))        AS team_position
FROM per_stage
WHERE pos_in_team <= 3
GROUP BY team_name;

-- ============ 3. Constraints that need triggers ============

-- (T1) Every team has exactly one leader (=> at least one rider). Checked at COMMIT.
CREATE FUNCTION check_team_leader() RETURNS trigger AS $$
DECLARE
    t VARCHAR(100);
BEGIN
    IF TG_TABLE_NAME = 'team' THEN t := NEW.team_name; ELSE t := OLD.team_name; END IF;
    IF EXISTS (SELECT 1 FROM team WHERE team_name = t)
       AND (SELECT COUNT(*) FROM rider WHERE team_name = t AND is_leader) <> 1 THEN
        RAISE EXCEPTION 'Team % must have at least one rider and exactly one leader', t;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE CONSTRAINT TRIGGER team_has_leader
    AFTER INSERT OR UPDATE ON team
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION check_team_leader();

CREATE CONSTRAINT TRIGGER rider_leaves_team
    AFTER UPDATE OR DELETE ON rider
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION check_team_leader();

-- (T2) A location is stored only if it starts or ends at least one stage. Checked at COMMIT.
CREATE FUNCTION check_location_used() RETURNS trigger AS $$
DECLARE
    locs VARCHAR(100)[];
    loc  VARCHAR(100);
BEGIN
    IF TG_TABLE_NAME = 'location' THEN
        locs := ARRAY[NEW.location_name];
    ELSE
        locs := ARRAY[OLD.start_location, OLD.end_location];
    END IF;
    FOREACH loc IN ARRAY locs
    LOOP
        IF EXISTS (SELECT 1 FROM location WHERE location_name = loc)
           AND NOT EXISTS (SELECT 1 FROM stage
                           WHERE start_location = loc OR end_location = loc) THEN
            RAISE EXCEPTION 'Location % is not the start or finish of any stage', loc;
        END IF;
    END LOOP;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE CONSTRAINT TRIGGER location_is_used
    AFTER INSERT OR UPDATE ON location
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION check_location_used();

CREATE CONSTRAINT TRIGGER stage_releases_location
    AFTER UPDATE OR DELETE ON stage
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION check_location_used();

-- (T3) No result for a rider on or after the stage at which the rider exited.
CREATE FUNCTION check_exit_vs_result() RETURNS trigger AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM result r
        JOIN rider_exit e ON e.bib_no = r.bib_no
        JOIN stage sr ON sr.stage_id = r.stage_id
        JOIN stage se ON se.stage_id = e.stage_id
        WHERE r.bib_no = NEW.bib_no
          AND sr.stage_date >= se.stage_date
    ) THEN
        RAISE EXCEPTION 'Rider % has a result on/after their exit stage', NEW.bib_no;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER result_before_exit
    AFTER INSERT OR UPDATE ON result
    FOR EACH ROW EXECUTE FUNCTION check_exit_vs_result();

CREATE TRIGGER exit_after_results
    AFTER INSERT OR UPDATE ON rider_exit
    FOR EACH ROW EXECUTE FUNCTION check_exit_vs_result();

-- (T4) Rider awards only for rider classifications; team awards only for team classifications.
CREATE FUNCTION check_award_kind() RETURNS trigger AS $$
BEGIN
    IF (SELECT is_team FROM classification WHERE award_type = NEW.award_type)
       <> (TG_TABLE_NAME = 'team_award') THEN
        RAISE EXCEPTION 'Award % cannot be won by a %', NEW.award_type,
            CASE WHEN TG_TABLE_NAME = 'team_award' THEN 'team' ELSE 'rider' END;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER rider_award_kind
    BEFORE INSERT OR UPDATE ON rider_award
    FOR EACH ROW EXECUTE FUNCTION check_award_kind();

CREATE TRIGGER team_award_kind
    BEFORE INSERT OR UPDATE ON team_award
    FOR EACH ROW EXECUTE FUNCTION check_award_kind();
