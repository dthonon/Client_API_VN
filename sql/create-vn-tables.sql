-- Add columns based tables to Postgresql database, template for pyexpander3
-- Columns based tables are populated by triggers from JSON based tables
-- For each table, the following sequence is required
--  1) Create the table with the required columns
--  2) Add index and constraints as needed
--  3) If needed (geom colums), add trg_geom trigger for postgis geometry update
--  4) Create update function to extract from JSON and copy to columns:
--     a) DELETE row if JSON row is deleted
--     b) UPDATE/INSERT row if JSON row is updated:
--        i) UPDATE is row exists (change in JSON)
--        ii) INSERT if row does nopt exist, usually after table re-creation
--     c) INSERT row if JSON row is created
--     NOTICE: adding a new column must be done in 1), 4bi), 4bii) and 4c)!
--  5) Add trigger
--  6) Execute trigger by performing dummy update (site=site) on JSON table

-- Cleanup and create
DROP SCHEMA IF EXISTS $(evn_db_schema_vn) CASCADE ;
CREATE SCHEMA $(evn_db_schema_vn);

SET search_path TO $(evn_db_schema_vn),public;

-- Trigger function to add or update geometry
CREATE OR REPLACE FUNCTION update_geom_triggerfn()
RETURNS trigger AS \$body\$
    BEGIN
    NEW.geom := ST_SetSRID(ST_MakePoint(NEW.coord_x_l93, NEW.coord_y_l93), 2154);
    RETURN NEW;
    END;
\$body\$
LANGUAGE plpgsql;

-----------
-- Entities
-----------

--------
-- Forms
--------

--------------------
-- local_admin_units
--------------------

---------------
-- Observations
---------------
CREATE TABLE $(evn_db_schema_vn).observations (
    uuid                UUID DEFAULT uuid_generate_v4(),
    site                VARCHAR(50),
    id_sighting         INTEGER,
    pseudo_id_sighting  VARCHAR(200),
    id_universal        VARCHAR(200),
    id_species          INTEGER,
    french_name         VARCHAR(150),
    latin_name          VARCHAR(150),
    date                DATE,
    date_year           INTEGER, -- Missing time_start & time_stop
    timing              TIMESTAMP,
    id_place            INTEGER,
    place               VARCHAR(150),
    municipality        VARCHAR(150),
    county              VARCHAR(150),
    country             VARCHAR(100),
    insee               CHAR(5),
    coord_lat           FLOAT,
    coord_lon           FLOAT,
    coord_x_l93         INTEGER,
    coord_y_l93         INTEGER,
    precision           VARCHAR(100),
    atlas_grid_name     VARCHAR(50),
    estimation_code     VARCHAR(100),
    count               INTEGER,
    atlas_code          INTEGER,
    altitude            INTEGER,
    project_code        VARCHAR(50),
    hidden              VARCHAR(50),
    admin_hidden        VARCHAR(50),
    name                VARCHAR(100),
    anonymous           VARCHAR(50),
    entity              VARCHAR(50),
    details             VARCHAR(10000),
    comment             VARCHAR(10000),
    hidden_comment      VARCHAR(10000),
    mortality           VARCHAR(10000),
    death_cause2        VARCHAR(100),
    insert_date         TIMESTAMP,
    update_date         TIMESTAMP,
    PRIMARY KEY (id_sighting, site)
);
-- Add geometry column
\o /dev/null
SELECT AddGeometryColumn('observations', 'geom', 2154, 'POINT', 2);
\o

-- Indexes on $(evn_db_schema_vn).observations;
DROP INDEX IF EXISTS observations_idx_id_universal;
CREATE UNIQUE INDEX observations_idx_id_universal
    ON $(evn_db_schema_vn).observations USING btree
    (id_universal)
    TABLESPACE pg_default;

-- Add trigger for postgis geometry update
DROP TRIGGER IF EXISTS trg_geom ON $(evn_db_schema_vn).observations;
CREATE TRIGGER trg_geom BEFORE INSERT or UPDATE
    ON $(evn_db_schema_vn).observations FOR EACH ROW
    EXECUTE PROCEDURE update_geom_triggerfn();

CREATE OR REPLACE FUNCTION update_observations() RETURNS TRIGGER AS \$\$
    BEGIN
    IF (TG_OP = 'DELETE') THEN
        /* Deleting data on src_vn.observations when raw data is deleted */
        DELETE FROM $(evn_db_schema_vn).observations
            WHERE id_sighting = OLD.id_sighting AND site=OLD.site;
        IF NOT FOUND THEN
            RETURN NULL;
        END IF;
        RETURN OLD;

    ELSIF (TG_OP = 'UPDATE') THEN
        /* Updating data on src_vn.observations when raw data is updated */
        UPDATE $(evn_db_schema_vn).observations SET
            id_universal    = ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'id_universal',
            id_species      = CAST(CAST(NEW.item->>0 AS JSON) #>> '{species,@id}' AS INTEGER),
            french_name     = CAST(NEW.item->>0 AS JSON) #>> '{species,name}',
            latin_name      = CAST(NEW.item->>0 AS JSON) #>> '{species,latin_name}',
            "date"          = to_date(CAST(NEW.item->>0 AS JSON) #>> '{date,@ISO8601}', 'YYYY-MM-DD'),
            date_year       = CAST(extract(year from to_date(CAST(NEW.item->>0 AS JSON) #>> '{date,@ISO8601}', 'YYYY-MM-DD')) AS INTEGER),
            timing          = to_timestamp(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) #>> '{timing,@ISO8601}', 'YYYY-MM-DD"T"HH24:MI:SS'),
            id_place        = CAST(CAST(NEW.item->>0 AS JSON) #>> '{place,@id}' AS INTEGER),
            place           = CAST(NEW.item->>0 AS JSON) #>> '{place,name}',
            municipality    = CAST(NEW.item->>0 AS JSON) #>> '{place,municipality}',
            county          = CAST(NEW.item->>0 AS JSON) #>> '{place,county}',
            country         = CAST(NEW.item->>0 AS JSON) #>> '{place,country}',
            insee           = CAST(NEW.item->>0 AS JSON) #>> '{place,insee}',
            coord_lat       = CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'coord_lat' AS FLOAT),
            coord_lon       = CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'coord_lon' AS FLOAT),
            coord_x_l93     = CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'coord_x_l93' AS FLOAT),
            coord_y_l93     = CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'coord_y_l93' AS FLOAT),
            precision       = ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'precision',
            atlas_grid_name = ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'atlas_grid_name',
            estimation_code = ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'estimation_code',
            count           = CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'count' AS INTEGER),
            atlas_code      = CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) #>> '{atlas_code,#text}' AS INTEGER),
            altitude        = CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'altitude' AS INTEGER),
            project_code    = ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'project_code',
            hidden          = ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'hidden',
            admin_hidden    = ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'admin_hidden',
            name            = ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'name',
            anonymous       = ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'anonymous',
            entity          = ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'entity',
            details         = ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'details',
            comment         = ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'comment',
            hidden_comment  = ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'hidden_comment',
            mortality       = (((CAST(NEW.item->>0 AS JSON) -> 'observers'::text) -> 0) #>> '{extended_info,mortality}'::text []) is not null,
            death_cause2    = ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) #>> '{extended_info, mortality, death_cause2}',
            insert_date     = to_timestamp(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) #>> '{insert_date,@ISO8601}', 'YYYY-MM-DD"T"HH24:MI:SS'),
            update_date     = to_timestamp(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) #>> '{update_date,@ISO8601}', 'YYYY-MM-DD"T"HH24:MI:SS')
        WHERE id_sighting = OLD.id AND site = OLD.site ;

        IF NOT FOUND THEN
            /* Inserting data on src_vn.observations when raw data is inserted */
            INSERT INTO $(evn_db_schema_vn).observations (site, id_sighting, pseudo_id_sighting, id_universal, id_species, french_name, latin_name,
                                             date, date_year, timing, id_place, place, municipality, county, country, insee,
                                             coord_lat, coord_lon, coord_x_l93, coord_y_l93, precision, atlas_grid_name, estimation_code,
                                             count, atlas_code, altitude, project_code, hidden, admin_hidden, name, anonymous, entity, details,
                                             comment, hidden_comment, mortality, death_cause2, insert_date, update_date)
            VALUES (
                NEW.site,
                NEW.id,
                encode(hmac(NEW.id::text, '8Zz9C*%I*gY&eM*Ei', 'sha1'), 'hex'),
                ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'id_universal',
                CAST(CAST(NEW.item->>0 AS JSON) #>> '{species,@id}' AS INTEGER),
                CAST(NEW.item->>0 AS JSON) #>> '{species,name}',
                CAST(NEW.item->>0 AS JSON) #>> '{species,latin_name}',
                to_date(CAST(NEW.item->>0 AS JSON) #>> '{date,@ISO8601}', 'YYYY-MM-DD'),
                CAST(extract(year from to_date(CAST(NEW.item->>0 AS JSON) #>> '{date,@ISO8601}', 'YYYY-MM-DD')) AS INTEGER),
                -- Missing time_start & time_stop
                to_timestamp(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) #>> '{timing,@ISO8601}', 'YYYY-MM-DD"T"HH24:MI:SS'),
                CAST(CAST(NEW.item->>0 AS JSON) #>> '{place,@id}' AS INTEGER),
                CAST(NEW.item->>0 AS JSON) #>> '{place,name}',
                CAST(NEW.item->>0 AS JSON) #>> '{place,municipality}',
                CAST(NEW.item->>0 AS JSON) #>> '{place,county}',
                CAST(NEW.item->>0 AS JSON) #>> '{place,country}',
                CAST(NEW.item->>0 AS JSON) #>> '{place,insee}',
                CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'coord_lat' AS FLOAT),
                CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'coord_lon' AS FLOAT),
                CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'coord_x_l93' AS FLOAT),
                CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'coord_y_l93' AS FLOAT),
                ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'precision',
                ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'atlas_grid_name',
                ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'estimation_code',
                CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'count' AS INTEGER),
                CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) #>> '{atlas_code,#text}' AS INTEGER),
                CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'altitude' AS INTEGER),
                ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'project_code',
                ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'hidden',
                ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'admin_hidden',
                ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'name',
                ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'anonymous',
                ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'entity',
                ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'details',
                ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'comment',
                ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'hidden_comment',
                (((CAST(NEW.item->>0 AS JSON) -> 'observers' :: text) -> 0) #>> '{extended_info,mortality}' :: text []) is not null,
                ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) #>> '{extended_info, mortality, death_cause2}',
                to_timestamp(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) #>> '{insert_date,@ISO8601}', 'YYYY-MM-DD"T"HH24:MI:SS'),
                to_timestamp(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) #>> '{update_date,@ISO8601}', 'YYYY-MM-DD"T"HH24:MI:SS'));
            END IF;
        RETURN NEW;

    ELSIF (TG_OP = 'INSERT') THEN
        /* Inserting data on src_vn.observations when raw data is inserted */
        INSERT INTO $(evn_db_schema_vn).observations (site, id_sighting, pseudo_id_sighting, id_universal, id_species, french_name, latin_name,
                                         date, date_year, timing, id_place, place, municipality, county, country, insee,
                                         coord_lat, coord_lon, coord_x_l93, coord_y_l93, precision, atlas_grid_name, estimation_code,
                                         count, atlas_code, altitude, project_code, hidden, admin_hidden, name, anonymous, entity, details,
                                         comment, hidden_comment, mortality, death_cause2, insert_date, update_date)
        VALUES (
            NEW.site,
            NEW.id,
            encode(hmac(NEW.id::text, '8Zz9C*%I*gY&eM*Ei', 'sha1'), 'hex'),
            ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'id_universal',
            CAST(CAST(NEW.item->>0 AS JSON) #>> '{species,@id}' AS INTEGER),
            CAST(NEW.item->>0 AS JSON) #>> '{species,name}',
            CAST(NEW.item->>0 AS JSON) #>> '{species,latin_name}',
            to_date(CAST(NEW.item->>0 AS JSON) #>> '{date,@ISO8601}', 'YYYY-MM-DD'),
            CAST(extract(year from to_date(CAST(NEW.item->>0 AS JSON) #>> '{date,@ISO8601}', 'YYYY-MM-DD')) AS INTEGER),
            -- Missing time_start & time_stop
            to_timestamp(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) #>> '{timing,@ISO8601}', 'YYYY-MM-DD"T"HH24:MI:SS'),
            CAST(CAST(NEW.item->>0 AS JSON) #>> '{place,@id}' AS INTEGER),
            CAST(NEW.item->>0 AS JSON) #>> '{place,name}',
            CAST(NEW.item->>0 AS JSON) #>> '{place,municipality}',
            CAST(NEW.item->>0 AS JSON) #>> '{place,county}',
            CAST(NEW.item->>0 AS JSON) #>> '{place,country}',
            CAST(NEW.item->>0 AS JSON) #>> '{place,insee}',
            CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'coord_lat' AS FLOAT),
            CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'coord_lon' AS FLOAT),
            CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'coord_x_l93' AS FLOAT),
            CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'coord_y_l93' AS FLOAT),
            ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'precision',
            ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'atlas_grid_name',
            ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'estimation_code',
            CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'count' AS INTEGER),
            CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) #>> '{atlas_code,#text}' AS INTEGER),
            CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'altitude' AS INTEGER),
            ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'project_code',
            ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'hidden',
            ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'admin_hidden',
            ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'name',
            ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'anonymous',
            ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'entity',
            ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'details',
            ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'comment',
            ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'hidden_comment',
            (((CAST(NEW.item->>0 AS JSON) -> 'observers' :: text) -> 0) #>> '{extended_info,mortality}' :: text []) is not null,
            ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) #>> '{extended_info, mortality, death_cause2}',
            to_timestamp(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) #>> '{insert_date,@ISO8601}', 'YYYY-MM-DD"T"HH24:MI:SS'),
            to_timestamp(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) #>> '{update_date,@ISO8601}', 'YYYY-MM-DD"T"HH24:MI:SS'));
        RETURN NEW;
    END IF;
END;
\$\$
LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS observations_trigger ON $(evn_db_schema_import).observations_json;
CREATE TRIGGER observations_trigger
AFTER INSERT OR UPDATE OR DELETE ON $(evn_db_schema_import).observations_json
    FOR EACH ROW EXECUTE FUNCTION update_observations();

-- Dummy update of all rows to trigger new FUNCTION
UPDATE $(evn_db_schema_import).observations_json SET site=site;

---------
-- Places
---------

----------
-- Species
----------
CREATE TABLE $(evn_db_schema_vn).species (
    uuid                UUID DEFAULT uuid_generate_v4(),
    site                VARCHAR(50),
    id                  INTEGER,
    id_taxo_group       INTEGER,
    is_used             INTEGER,
    french_name         VARCHAR(150),
    latin_name          VARCHAR(150),
    rarity              VARCHAR(50),
    category_1          VARCHAR(50),
    sys_order           INTEGER,
    atlas_start         INTEGER,
    atlas_end           INTEGER,
    PRIMARY KEY (id, site)
);

CREATE OR REPLACE FUNCTION update_species() RETURNS TRIGGER AS \$\$
    BEGIN
    IF (TG_OP = 'DELETE') THEN
        /* Deleting data when JSON data is deleted */
        DELETE FROM $(evn_db_schema_vn).species
            WHERE id = OLD.id AND site = OLD.site;
        IF NOT FOUND THEN
            RETURN NULL;
        END IF;
        RETURN OLD;

    ELSIF (TG_OP = 'UPDATE') THEN
        /* Updating or inserting data when JSON data is updated */
        UPDATE $(evn_db_schema_vn).species SET
            id_taxo_group = CAST(CAST(NEW.item->>0 AS JSON)->>'id_taxo_group' AS INTEGER),
            is_used       = CAST(CAST(NEW.item->>0 AS JSON)->>'is_used' AS INTEGER),
            french_name   = CAST(NEW.item->>0 AS JSON)->>'french_name',
            latin_name    = CAST(NEW.item->>0 AS JSON)->>'latin_name',
            rarity        = CAST(NEW.item->>0 AS JSON)->>'rarity',
            category_1    = CAST(NEW.item->>0 AS JSON)->>'category_1',
            sys_order     = CAST(CAST(NEW.item->>0 AS JSON)->>'sys_order' AS INTEGER),
            atlas_start   = CAST(CAST(NEW.item->>0 AS JSON)->>'atlas_start' AS INTEGER),
            atlas_end     = CAST(CAST(NEW.item->>0 AS JSON)->>'atlas_end' AS INTEGER)
        WHERE id = OLD.id AND site = OLD.site ;
        IF NOT FOUND THEN
            /* Inserting data in new row, usually after table re-creation */
            INSERT INTO $(evn_db_schema_vn).species(site, id, id_taxo_group, is_used, french_name, latin_name, rarity,
                                                         category_1, sys_order, atlas_start, atlas_end)
            VALUES (
                NEW.site,
                NEW.id,
                CAST(CAST(NEW.item->>0 AS JSON)->>'id_taxo_group' AS INTEGER),
                CAST(CAST(NEW.item->>0 AS JSON)->>'is_used' AS INTEGER),
                CAST(NEW.item->>0 AS JSON)->>'french_name',
                CAST(NEW.item->>0 AS JSON)->>'latin_name',
                CAST(NEW.item->>0 AS JSON)->>'rarity',
                CAST(NEW.item->>0 AS JSON)->>'category_1',
                CAST(CAST(NEW.item->>0 AS JSON)->>'sys_order' AS INTEGER),
                CAST(CAST(NEW.item->>0 AS JSON)->>'atlas_start' AS INTEGER),
                CAST(CAST(NEW.item->>0 AS JSON)->>'atlas_end' AS INTEGER)
            );
            END IF;
        RETURN NEW;

    ELSIF (TG_OP = 'INSERT') THEN
        /* Inserting data on src_vn.observations when raw data is inserted */
        INSERT INTO $(evn_db_schema_vn).species(site, id, id_taxo_group, is_used, french_name, latin_name, rarity,
                                                category_1, sys_order, atlas_start, atlas_end)
        VALUES (
            NEW.site,
            NEW.id,
            CAST(CAST(NEW.item->>0 AS JSON)->>'id_taxo_group' AS INTEGER),
            CAST(CAST(NEW.item->>0 AS JSON)->>'is_used' AS INTEGER),
            CAST(NEW.item->>0 AS JSON)->>'french_name',
            CAST(NEW.item->>0 AS JSON)->>'latin_name',
            CAST(NEW.item->>0 AS JSON)->>'rarity',
            CAST(NEW.item->>0 AS JSON)->>'category_1',
            CAST(CAST(NEW.item->>0 AS JSON)->>'sys_order' AS INTEGER),
            CAST(CAST(NEW.item->>0 AS JSON)->>'atlas_start' AS INTEGER),
            CAST(CAST(NEW.item->>0 AS JSON)->>'atlas_end' AS INTEGER)
        );
        RETURN NEW;
    END IF;
END;
\$\$
LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS species_trigger ON $(evn_db_schema_import).species_json;
CREATE TRIGGER species_trigger
AFTER INSERT OR UPDATE OR DELETE ON $(evn_db_schema_import).species_json
    FOR EACH ROW EXECUTE FUNCTION $(evn_db_schema_vn).update_species();

-- Dummy update of all rows to trigger new FUNCTION
UPDATE $(evn_db_schema_import).species_json SET site=site;

--------------
-- Taxo_groups
--------------

--------------------
-- Territorial_units
--------------------
