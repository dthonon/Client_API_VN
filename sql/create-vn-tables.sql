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
DROP SCHEMA IF EXISTS $(db_schema_vn) CASCADE ;
CREATE SCHEMA $(db_schema_vn);

SET search_path TO $(db_schema_vn),public;

-- Trigger function to add or update geometry
CREATE OR REPLACE FUNCTION update_geom_triggerfn()
RETURNS trigger AS \$body\$
    BEGIN
    NEW.geom := ST_SetSRID(ST_MakePoint(NEW.coord_x_local, NEW.coord_y_local), $(proj));
    RETURN NEW;
    END;
\$body\$
LANGUAGE plpgsql;

-----------
-- Entities
-----------
CREATE TABLE $(db_schema_vn).entities(
    uuid                UUID DEFAULT uuid_generate_v4(),
    site                VARCHAR(50),
    id                  INTEGER,
    short_name          VARCHAR(500),
    full_name_french    VARCHAR(500),
    description_french  VARCHAR(100000),
    url                 VARCHAR(1000),
    address             VARCHAR(1000),
    PRIMARY KEY (uuid)
);

DROP INDEX IF EXISTS entities_idx_site;
CREATE INDEX entities_idx_site
    ON $(db_schema_vn).entities USING btree(site);
DROP INDEX IF EXISTS entities_idx_id;
CREATE INDEX entities_idx_id
    ON $(db_schema_vn).entities USING btree(id);

CREATE OR REPLACE FUNCTION update_entities() RETURNS TRIGGER AS \$\$
    BEGIN
    IF (TG_OP = 'DELETE') THEN
        -- Deleting data when JSON data is deleted
        DELETE FROM $(db_schema_vn).entities
            WHERE id = OLD.id AND site = OLD.site;
        IF NOT FOUND THEN
            RETURN NULL;
        END IF;
        RETURN OLD;

    ELSIF (TG_OP = 'UPDATE') THEN
        -- Updating or inserting data when JSON data is updated
        UPDATE $(db_schema_vn).entities SET
            short_name         = CAST(NEW.item->>0 AS JSON)->>'short_name',
            full_name_french   = CAST(NEW.item->>0 AS JSON)->>'full_name_french',
            description_french = CAST(NEW.item->>0 AS JSON)->>'description_french',
            url                = CAST(NEW.item->>0 AS JSON)->>'url',
            address            = CAST(NEW.item->>0 AS JSON)->>'address'
        WHERE id = OLD.id AND site = OLD.site ;
        IF NOT FOUND THEN
            -- Inserting data in new row, usually after table re-creation
            INSERT INTO $(db_schema_vn).entities(site, id, short_name, full_name_french, description_french,
                                                     url, address)
            VALUES (
                NEW.site,
                NEW.id,
                CAST(NEW.item->>0 AS JSON)->>'short_name',
                CAST(NEW.item->>0 AS JSON)->>'full_name_french',
                CAST(NEW.item->>0 AS JSON)->>'description_french',
                CAST(NEW.item->>0 AS JSON)->>'url',
                CAST(NEW.item->>0 AS JSON)->>'address'
            );
            END IF;
        RETURN NEW;

    ELSIF (TG_OP = 'INSERT') THEN
        -- Inserting row when raw data is inserted
        INSERT INTO $(db_schema_vn).entities(site, id, short_name, full_name_french, description_french,
                                                 url, address)
        VALUES (
            NEW.site,
            NEW.id,
            CAST(NEW.item->>0 AS JSON)->>'short_name',
            CAST(NEW.item->>0 AS JSON)->>'full_name_french',
            CAST(NEW.item->>0 AS JSON)->>'description_french',
            CAST(NEW.item->>0 AS JSON)->>'url',
            CAST(NEW.item->>0 AS JSON)->>'address'
        );
        RETURN NEW;
    END IF;
END;
\$\$
LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS entities_trigger ON $(db_schema_import).entities_json;
CREATE TRIGGER entities_trigger
AFTER INSERT OR UPDATE OR DELETE ON $(db_schema_import).entities_json
    FOR EACH ROW EXECUTE FUNCTION $(db_schema_vn).update_entities();


---------
-- Fields
---------
CREATE TABLE $(db_schema_vn).fields(
    uuid                UUID DEFAULT uuid_generate_v4(),
    site                VARCHAR(50),
    id                  INTEGER,
    default_v           VARCHAR(500),
    empty_choice        VARCHAR(500),
    mandatory           VARCHAR(500),
    name                VARCHAR(1000),
    PRIMARY KEY (uuid)
);

DROP INDEX IF EXISTS fields_idx_site;
CREATE INDEX fields_idx_site
    ON $(db_schema_vn).fields USING btree(site);
DROP INDEX IF EXISTS fields_idx_id;
CREATE INDEX fields_idx_id
    ON $(db_schema_vn).fields USING btree(id);

CREATE OR REPLACE FUNCTION update_fields() RETURNS TRIGGER AS \$\$
    BEGIN
    IF (TG_OP = 'DELETE') THEN
        -- Deleting data when JSON data is deleted
        DELETE FROM $(db_schema_vn).fields
            WHERE id = OLD.id AND site = OLD.site;
        IF NOT FOUND THEN
            RETURN NULL;
        END IF;
        RETURN OLD;

    ELSIF (TG_OP = 'UPDATE') THEN
        -- Updating or inserting data when JSON data is updated
        UPDATE $(db_schema_vn).fields SET
            default_v    = CAST(NEW.item->>0 AS JSON)->>'default',
            empty_choice = CAST(NEW.item->>0 AS JSON)->>'empty_choice',
            mandatory    = CAST(NEW.item->>0 AS JSON)->>'mandatory',
            name         = CAST(NEW.item->>0 AS JSON)->>'name'
        WHERE id = OLD.id AND site = OLD.site ;
        IF NOT FOUND THEN
            -- Inserting data in new row, usually after table re-creation
            INSERT INTO $(db_schema_vn).fields(site, id, default_v, empty_choice, mandatory, name)
            VALUES (
                NEW.site,
                NEW.id,
                CAST(NEW.item->>0 AS JSON)->>'default',
                CAST(NEW.item->>0 AS JSON)->>'empty_choice',
                CAST(NEW.item->>0 AS JSON)->>'mandatory',
                CAST(NEW.item->>0 AS JSON)->>'name'
            );
            END IF;
        RETURN NEW;

    ELSIF (TG_OP = 'INSERT') THEN
        -- Inserting row when raw data is inserted
        INSERT INTO $(db_schema_vn).fields(site, id, default_v, empty_choice, mandatory, name)
        VALUES (
            NEW.site,
            NEW.id,
            CAST(NEW.item->>0 AS JSON)->>'default',
            CAST(NEW.item->>0 AS JSON)->>'empty_choice',
            CAST(NEW.item->>0 AS JSON)->>'mandatory',
            CAST(NEW.item->>0 AS JSON)->>'name'
        );
        RETURN NEW;
    END IF;
END;
\$\$
LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS fields_trigger ON $(db_schema_import).fields_json;
CREATE TRIGGER fields_trigger
AFTER INSERT OR UPDATE OR DELETE ON $(db_schema_import).fields_json
    FOR EACH ROW EXECUTE FUNCTION $(db_schema_vn).update_fields();


--------
-- Forms
--------
CREATE TABLE $(db_schema_vn).forms(
    uuid                UUID DEFAULT uuid_generate_v4(),
    site                VARCHAR(50),
    id                  INTEGER,
    id_form_universal   VARCHAR(500),
    time_start          VARCHAR(500),
    time_stop           VARCHAR(500),
    full_form           VARCHAR(500),
    version             VARCHAR(500),
    coord_lat           FLOAT,
    coord_lon           FLOAT,
    coord_x_local       FLOAT,
    coord_y_local       FLOAT,
    comments            VARCHAR(100000),
    protocol            VARCHAR(100000),
    geom                GEOMETRY(Point, $(proj)),
    PRIMARY KEY (uuid)
);


DROP INDEX IF EXISTS forms_idx_site;
CREATE INDEX forms_idx_site
    ON $(db_schema_vn).forms USING btree(site);
DROP INDEX IF EXISTS forms_idx_id;
CREATE INDEX forms_idx_id
    ON $(db_schema_vn).forms USING btree(id);
DROP INDEX IF EXISTS forms_gidx_geom;
CREATE INDEX forms_gidx_geom
    ON $(db_schema_vn).forms USING gist(geom);


-- Add trigger for postgis geometry update
DROP TRIGGER IF EXISTS trg_geom ON $(db_schema_vn).forms;
CREATE TRIGGER trg_geom BEFORE INSERT or UPDATE
    ON $(db_schema_vn).forms FOR EACH ROW
    EXECUTE PROCEDURE update_geom_triggerfn();

CREATE OR REPLACE FUNCTION update_forms() RETURNS TRIGGER AS \$\$
    BEGIN
    IF (TG_OP = 'DELETE') THEN
        -- Deleting data when JSON data is deleted
        DELETE FROM $(db_schema_vn).forms
            WHERE id = OLD.id AND site = OLD.site;
        IF NOT FOUND THEN
            RETURN NULL;
        END IF;
        RETURN OLD;

    ELSIF (TG_OP = 'UPDATE') THEN
        -- Updating or inserting data when JSON data is updated
        UPDATE $(db_schema_vn).forms SET
            id_form_universal = CAST(NEW.item->>0 AS JSON)->>'id_form_universal',
            time_start        = CAST(NEW.item->>0 AS JSON)->>'time_start',
            time_stop         = CAST(NEW.item->>0 AS JSON)->>'time_stop',
            full_form         = CAST(NEW.item->>0 AS JSON)->>'full_form',
            version           = CAST(NEW.item->>0 AS JSON)->>'version',
            coord_lat         = CAST(CAST(NEW.item->>0 AS JSON)->>'lat' AS FLOAT),
            coord_lon         = CAST(CAST(NEW.item->>0 AS JSON)->>'lon' AS FLOAT),
            coord_x_local     = CAST(CAST(NEW.item->>0 AS JSON)->>'coord_x_local' AS FLOAT),
            coord_y_local     = CAST(CAST(NEW.item->>0 AS JSON)->>'coord_y_local' AS FLOAT),
            comments          = CAST(NEW.item->>0 AS JSON)->>'comments',
            protocol          = CAST(NEW.item->>0 AS JSON)->>'protocol'
        WHERE id = OLD.id AND site = OLD.site ;
        IF NOT FOUND THEN
            -- Inserting data in new row, usually after table re-creation
            INSERT INTO $(db_schema_vn).forms(site, id, id_form_universal, time_start, time_stop,
                                              full_form, version, coord_lat, coord_lon,
                                              coord_x_local, coord_y_local, comments, protocol)
            VALUES (
                NEW.site,
                NEW.id,
                CAST(NEW.item->>0 AS JSON)->>'id_form_universal',
                CAST(NEW.item->>0 AS JSON)->>'time_start',
                CAST(NEW.item->>0 AS JSON)->>'time_stop',
                CAST(NEW.item->>0 AS JSON)->>'full_form',
                CAST(NEW.item->>0 AS JSON)->>'version',
                CAST(CAST(NEW.item->>0 AS JSON)->>'lat' AS FLOAT),
                CAST(CAST(NEW.item->>0 AS JSON)->>'lon' AS FLOAT),
                CAST(CAST(NEW.item->>0 AS JSON)->>'coord_x_local' AS FLOAT),
                CAST(CAST(NEW.item->>0 AS JSON)->>'coord_y_local' AS FLOAT),
                CAST(NEW.item->>0 AS JSON)->>'comments',
                CAST(NEW.item->>0 AS JSON)->>'protocol'
            );
            END IF;
        RETURN NEW;

    ELSIF (TG_OP = 'INSERT') THEN
        -- Inserting row when raw data is inserted
        INSERT INTO $(db_schema_vn).forms(site, id, id_form_universal, time_start, time_stop,
                                          full_form, version, coord_lat, coord_lon,
                                          coord_x_local, coord_y_local, comments, protocol)
        VALUES (
            NEW.site,
            NEW.id,
            CAST(NEW.item->>0 AS JSON)->>'id_form_universal',
            CAST(NEW.item->>0 AS JSON)->>'time_start',
            CAST(NEW.item->>0 AS JSON)->>'time_stop',
            CAST(NEW.item->>0 AS JSON)->>'full_form',
            CAST(NEW.item->>0 AS JSON)->>'version',
            CAST(CAST(NEW.item->>0 AS JSON)->>'lat' AS FLOAT),
            CAST(CAST(NEW.item->>0 AS JSON)->>'lon' AS FLOAT),
            CAST(CAST(NEW.item->>0 AS JSON)->>'coord_x_local' AS FLOAT),
            CAST(CAST(NEW.item->>0 AS JSON)->>'coord_y_local' AS FLOAT),
            CAST(NEW.item->>0 AS JSON)->>'comments',
            CAST(NEW.item->>0 AS JSON)->>'protocol'
        );
        RETURN NEW;
    END IF;
END;
\$\$
LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS forms_trigger ON $(db_schema_import).forms_json;
CREATE TRIGGER forms_trigger
AFTER INSERT OR UPDATE OR DELETE ON $(db_schema_import).forms_json
    FOR EACH ROW EXECUTE FUNCTION $(db_schema_vn).update_forms();

 
--------------------
-- local_admin_units
--------------------
CREATE TABLE $(db_schema_vn).local_admin_units(
    uuid                UUID DEFAULT uuid_generate_v4(),
    site                VARCHAR(50),
    id                  INTEGER,
    id_canton           INTEGER,
    name                VARCHAR(150),
    insee               VARCHAR(50),
    coord_lat           FLOAT,
    coord_lon           FLOAT,
    coord_x_local       FLOAT,
    coord_y_local       FLOAT,
    geom                GEOMETRY(Point, $(proj)),
    PRIMARY KEY (uuid)
);

DROP INDEX IF EXISTS local_admin_units_idx_site;
CREATE INDEX local_admin_units_idx_site
    ON $(db_schema_vn).local_admin_units USING btree(site);
DROP INDEX IF EXISTS local_admin_units_idx_id;
CREATE INDEX local_admin_units_idx_id
    ON $(db_schema_vn).local_admin_units USING btree(id);
DROP INDEX IF EXISTS local_admin_units_gidx_geom;
CREATE INDEX local_admin_units_gidx_geom
    ON $(db_schema_vn).local_admin_units USING gist(geom);

-- Add trigger for postgis geometry update
DROP TRIGGER IF EXISTS trg_geom ON $(db_schema_vn).local_admin_units;
CREATE TRIGGER trg_geom BEFORE INSERT or UPDATE
    ON $(db_schema_vn).local_admin_units FOR EACH ROW
    EXECUTE PROCEDURE update_geom_triggerfn();

CREATE OR REPLACE FUNCTION update_local_admin_units() RETURNS TRIGGER AS \$\$
    BEGIN
    IF (TG_OP = 'DELETE') THEN
        -- Deleting data when JSON data is deleted
        DELETE FROM $(db_schema_vn).local_admin_units
            WHERE id = OLD.id AND site = OLD.site;
        IF NOT FOUND THEN
            RETURN NULL;
        END IF;
        RETURN OLD;

    ELSIF (TG_OP = 'UPDATE') THEN
        -- Updating or inserting data when JSON data is updated
        UPDATE $(db_schema_vn).local_admin_units SET
            id_canton    = CAST(CAST(NEW.item->>0 AS JSON)->>'id_canton' AS INTEGER),
            name         = CAST(NEW.item->>0 AS JSON)->>'name',
            insee        = CAST(NEW.item->>0 AS JSON)->>'insee',
            coord_lat    = CAST(CAST(NEW.item->>0 AS JSON)->>'coord_lat' AS FLOAT),
            coord_lon    = CAST(CAST(NEW.item->>0 AS JSON)->>'coord_lon' AS FLOAT),
            coord_x_local  = CAST(CAST(NEW.item->>0 AS JSON)->>'coord_x_local' AS FLOAT),
            coord_y_local  = CAST(CAST(NEW.item->>0 AS JSON)->>'coord_y_local' AS FLOAT)
        WHERE id = OLD.id AND site = OLD.site ;
        IF NOT FOUND THEN
            -- Inserting data in new row, usually after table re-creation
            INSERT INTO $(db_schema_vn).local_admin_units(site, id, id_canton, name, insee,
                                                          coord_lat, coord_lon, coord_x_local, coord_y_local)
            VALUES (
                NEW.site,
                NEW.id,
                CAST(CAST(NEW.item->>0 AS JSON)->>'id_canton' AS INTEGER),
                CAST(NEW.item->>0 AS JSON)->>'name',
                CAST(NEW.item->>0 AS JSON)->>'insee',
                CAST(CAST(NEW.item->>0 AS JSON)->>'coord_lat' AS FLOAT),
                CAST(CAST(NEW.item->>0 AS JSON)->>'coord_lon' AS FLOAT),
                CAST(CAST(NEW.item->>0 AS JSON)->>'coord_x_local' AS FLOAT),
                CAST(CAST(NEW.item->>0 AS JSON)->>'coord_y_local' AS FLOAT)
            );
            END IF;
        RETURN NEW;

    ELSIF (TG_OP = 'INSERT') THEN
        -- Inserting row when raw data is inserted
        INSERT INTO $(db_schema_vn).local_admin_units(site, id, id_canton, name, insee,
                                                      coord_lat, coord_lon, coord_x_local, coord_y_local)
        VALUES (
            NEW.site,
            NEW.id,
            CAST(CAST(NEW.item->>0 AS JSON)->>'id_canton' AS INTEGER),
            CAST(NEW.item->>0 AS JSON)->>'name',
            CAST(NEW.item->>0 AS JSON)->>'insee',
            CAST(CAST(NEW.item->>0 AS JSON)->>'coord_lat' AS FLOAT),
            CAST(CAST(NEW.item->>0 AS JSON)->>'coord_lon' AS FLOAT),
            CAST(CAST(NEW.item->>0 AS JSON)->>'coord_x_local' AS FLOAT),
            CAST(CAST(NEW.item->>0 AS JSON)->>'coord_y_local' AS FLOAT)
        );
        RETURN NEW;
    END IF;
END;
\$\$
LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS local_admin_units_trigger ON $(db_schema_import).local_admin_units_json;
CREATE TRIGGER local_admin_units_trigger
AFTER INSERT OR UPDATE OR DELETE ON $(db_schema_import).local_admin_units_json
    FOR EACH ROW EXECUTE FUNCTION $(db_schema_vn).update_local_admin_units();


---------------
-- Observations
---------------
CREATE TABLE $(db_schema_vn).observations (
    uuid                UUID DEFAULT uuid_generate_v4(),
    site                VARCHAR(50),
    id_sighting         INTEGER,
    pseudo_id_sighting  VARCHAR(200),
    id_universal        VARCHAR(200),
    id_species          INTEGER,
    taxonomy            VARCHAR(150),
    date                DATE,
    date_year           INTEGER, -- Missing time_start & time_stop
    timing              TIMESTAMP,
    id_place            INTEGER,
    place               VARCHAR(150),
    coord_lat           FLOAT,
    coord_lon           FLOAT,
    coord_x_local       FLOAT,
    coord_y_local       FLOAT,
    precision           VARCHAR(100),
    estimation_code     VARCHAR(100),
    count               INTEGER,
    atlas_code          INTEGER,
    altitude            INTEGER,
    project_code        VARCHAR(50),
    hidden              BOOLEAN,
    admin_hidden        BOOLEAN,
    observer_uid        VARCHAR(100),
    details             VARCHAR(10000),
    behaviours          VARCHAR(10000),
    comment             VARCHAR(10000),
    hidden_comment      VARCHAR(10000),
    mortality           BOOLEAN,
    death_cause2        VARCHAR(100),
    insert_date         TIMESTAMP,
    update_date         TIMESTAMP,
    geom                GEOMETRY(Point, $(proj)),
    PRIMARY KEY (uuid)
);

DROP INDEX IF EXISTS observations_idx_site;
CREATE INDEX observations_idx_site
    ON $(db_schema_vn).observations USING btree(site);
DROP INDEX IF EXISTS observations_idx_id_sighting;
CREATE INDEX observations_idx_id_sighting
    ON $(db_schema_vn).observations USING btree(id_sighting);
DROP INDEX IF EXISTS observations_idx_id_universal;
CREATE INDEX observations_idx_id_universal
    ON $(db_schema_vn).observations USING btree(id_universal);
DROP INDEX IF EXISTS observations_gidx_geom;
CREATE INDEX observations_gidx_geom
    ON $(db_schema_vn).observations USING gist(geom);

-- Add trigger for postgis geometry update
DROP TRIGGER IF EXISTS trg_geom ON $(db_schema_vn).observations;
CREATE TRIGGER trg_geom BEFORE INSERT or UPDATE
    ON $(db_schema_vn).observations FOR EACH ROW
    EXECUTE PROCEDURE update_geom_triggerfn();

CREATE OR REPLACE FUNCTION update_observations() RETURNS TRIGGER AS \$\$
    BEGIN
    IF (TG_OP = 'DELETE') THEN
        -- Deleting data on src_vn.observations when raw data is deleted
        DELETE FROM $(db_schema_vn).observations
            WHERE id_sighting = OLD.id AND site = OLD.site;
        IF NOT FOUND THEN
            RETURN NULL;
        END IF;
        RETURN OLD;

    ELSIF (TG_OP = 'UPDATE') THEN
        -- Updating data on src_vn.observations when raw data is updated
        UPDATE $(db_schema_vn).observations SET
            id_universal    = ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'id_universal',
            id_species      = CAST(CAST(NEW.item->>0 AS JSON) #>> '{species,@id}' AS INTEGER),
            taxonomy        = CAST(NEW.item->>0 AS JSON) #>> '{species,taxonomy}',
            "date"          = to_date(CAST(NEW.item->>0 AS JSON) #>> '{date,@ISO8601}', 'YYYY-MM-DD'),
            date_year       = CAST(extract(year from to_date(CAST(NEW.item->>0 AS JSON) #>> '{date,@ISO8601}', 'YYYY-MM-DD')) AS INTEGER),
            timing          = to_timestamp(CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) #>> '{timing,@timestamp}' AS DOUBLE PRECISION)),
            id_place        = CAST(CAST(NEW.item->>0 AS JSON) #>> '{place,@id}' AS INTEGER),
            place           = CAST(NEW.item->>0 AS JSON) #>> '{place,name}',
            coord_lat       = CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'coord_lat' AS FLOAT),
            coord_lon       = CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'coord_lon' AS FLOAT),
            coord_x_local   = CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'coord_x_local' AS FLOAT),
            coord_y_local   = CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'coord_y_local' AS FLOAT),
            precision       = ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'precision',
            estimation_code = ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'estimation_code',
            count           = CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'count' AS INTEGER),
            atlas_code      = CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'atlas_code' AS INTEGER),
            altitude        = CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'altitude' AS INTEGER),
            project_code    = ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'project_code',
            hidden          = CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'hidden' AS BOOLEAN),
            admin_hidden    = CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'admin_hidden' AS BOOLEAN),
            observer_uid    = ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> '@uid',
            details         = ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'details',
            behaviours      = ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'behaviours',
            comment         = ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'comment',
            hidden_comment  = ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'hidden_comment',
            mortality       = CAST(((((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) #>> '{extended_info,mortality}'::text []) is not null) as BOOLEAN),
            death_cause2    = ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) #>> '{extended_info, mortality, death_cause2}',
            insert_date     = to_timestamp(CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'insert_date' AS DOUBLE PRECISION)),
            update_date     = to_timestamp(CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) #>> '{update_date,@timestamp}' AS DOUBLE PRECISION))
        WHERE id_sighting = OLD.id AND site = OLD.site;

        IF NOT FOUND THEN
            -- Inserting data on src_vn.observations when raw data is inserted
            INSERT INTO $(db_schema_vn).observations (site, id_sighting, pseudo_id_sighting, id_universal, id_species, taxonomy,
                                             date, date_year, timing, id_place, place,
                                             coord_lat, coord_lon, coord_x_local, coord_y_local, precision, estimation_code,
                                             count, atlas_code, altitude, project_code, hidden, admin_hidden, observer_uid, details,
                                             behaviours, comment, hidden_comment, mortality, death_cause2, insert_date, update_date)
            VALUES (
                NEW.site,
                NEW.id,
                encode(hmac(NEW.id::text, '8Zz9C*%I*gY&eM*Ei', 'sha1'), 'hex'),
                ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'id_universal',
                CAST(CAST(NEW.item->>0 AS JSON) #>> '{species,@id}' AS INTEGER),
                CAST(NEW.item->>0 AS JSON) #>> '{species,taxonomy}',
                to_date(CAST(NEW.item->>0 AS JSON) #>> '{date,@ISO8601}', 'YYYY-MM-DD'),
                CAST(extract(year from to_date(CAST(NEW.item->>0 AS JSON) #>> '{date,@ISO8601}', 'YYYY-MM-DD')) AS INTEGER),
                -- Missing time_start & time_stop
                to_timestamp(CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) #>> '{timing,@timestamp}' AS DOUBLE PRECISION)),
                CAST(CAST(NEW.item->>0 AS JSON) #>> '{place,@id}' AS INTEGER),
                CAST(NEW.item->>0 AS JSON) #>> '{place,name}',
                CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'coord_lat' AS FLOAT),
                CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'coord_lon' AS FLOAT),
                CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'coord_x_local' AS FLOAT),
                CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'coord_y_local' AS FLOAT),
                ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'precision',
                ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'estimation_code',
                CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'count' AS INTEGER),
                CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'atlas_code' AS INTEGER),
                CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'altitude' AS INTEGER),
                ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'project_code',
                CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'hidden' AS BOOLEAN),
                CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'admin_hidden' AS BOOLEAN),
                ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> '@uid',
                ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'details',
                ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'behaviours',
                ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'comment',
                ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'hidden_comment',
                CAST(((((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) #>> '{extended_info,mortality}'::text []) is not null) as BOOLEAN),
                ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) #>> '{extended_info, mortality, death_cause2}',
                to_timestamp(CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'insert_date' AS DOUBLE PRECISION)),
                to_timestamp(CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) #>> '{update_date,@timestamp}' AS DOUBLE PRECISION)));
            END IF;
        RETURN NEW;

    ELSIF (TG_OP = 'INSERT') THEN
        -- Inserting data on src_vn.observations when raw data is inserted
        INSERT INTO $(db_schema_vn).observations (site, id_sighting, pseudo_id_sighting, id_universal, id_species, taxonomy,
                                         date, date_year, timing, id_place, place,
                                         coord_lat, coord_lon, coord_x_local, coord_y_local, precision, estimation_code,
                                         count, atlas_code, altitude, project_code, hidden, admin_hidden, observer_uid, details,
                                         behaviours, comment, hidden_comment, mortality, death_cause2, insert_date, update_date)
        VALUES (
            NEW.site,
            NEW.id,
            encode(hmac(NEW.id::text, '8Zz9C*%I*gY&eM*Ei', 'sha1'), 'hex'),
            ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'id_universal',
            CAST(CAST(NEW.item->>0 AS JSON) #>> '{species,@id}' AS INTEGER),
            CAST(NEW.item->>0 AS JSON) #>> '{species,taxonomy}',
            to_date(CAST(NEW.item->>0 AS JSON) #>> '{date,@ISO8601}', 'YYYY-MM-DD'),
            CAST(extract(year from to_date(CAST(NEW.item->>0 AS JSON) #>> '{date,@ISO8601}', 'YYYY-MM-DD')) AS INTEGER),
            -- Missing time_start & time_stop
            to_timestamp(CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) #>> '{timing,@timestamp}' AS DOUBLE PRECISION)),
            CAST(CAST(NEW.item->>0 AS JSON) #>> '{place,@id}' AS INTEGER),
            CAST(NEW.item->>0 AS JSON) #>> '{place,name}',
            CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'coord_lat' AS FLOAT),
            CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'coord_lon' AS FLOAT),
            CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'coord_x_local' AS FLOAT),
            CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'coord_y_local' AS FLOAT),
            ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'precision',
            ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'estimation_code',
            CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'count' AS INTEGER),
            CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'atlas_code' AS INTEGER),
            CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'altitude' AS INTEGER),
            ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'project_code',
            CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'hidden' AS BOOLEAN),
            CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'admin_hidden' AS BOOLEAN),
            ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> '@uid',
            ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'details',
            ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'behaviours',
            ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'comment',
            ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'hidden_comment',
            CAST(((((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) #>> '{extended_info,mortality}'::text []) is not null) as BOOLEAN),
            ((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) #>> '{extended_info, mortality, death_cause2}',
            to_timestamp(CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) ->> 'insert_date' AS DOUBLE PRECISION)),
            to_timestamp(CAST(((CAST(NEW.item->>0 AS JSON) -> 'observers') -> 0) #>> '{update_date,@timestamp}' AS DOUBLE PRECISION)));
        RETURN NEW;
    END IF;
END;
\$\$
LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS observations_trigger ON $(db_schema_import).observations_json;
CREATE TRIGGER observations_trigger
AFTER INSERT OR UPDATE OR DELETE ON $(db_schema_import).observations_json
    FOR EACH ROW EXECUTE FUNCTION update_observations();


------------
-- Observers
------------
CREATE TABLE $(db_schema_vn).observers(
    uuid                UUID DEFAULT uuid_generate_v4(),
    site                VARCHAR(50),
    id                  INTEGER,
    id_universal        INTEGER,
    id_entity           INTEGER,
    anonymous           BOOLEAN,
    collectif           BOOLEAN,
    default_hidden      BOOLEAN,
    name                VARCHAR(100),
    surname             VARCHAR(100),
    PRIMARY KEY (uuid)
);

DROP INDEX IF EXISTS observers_idx_site;
CREATE INDEX observers_idx_site
    ON $(db_schema_vn).observers USING btree(site);
DROP INDEX IF EXISTS observers_idx_id;
CREATE INDEX observers_idx_id
    ON $(db_schema_vn).observers USING btree(id);

CREATE OR REPLACE FUNCTION update_observers() RETURNS TRIGGER AS \$\$
    BEGIN
    IF (TG_OP = 'DELETE') THEN
        -- Deleting data when JSON data is deleted
        DELETE FROM $(db_schema_vn).observers
            WHERE id = OLD.id AND site = OLD.site;
        IF NOT FOUND THEN
            RETURN NULL;
        END IF;
        RETURN OLD;

    ELSIF (TG_OP = 'UPDATE') THEN
        -- Updating or inserting data when JSON data is updated
        UPDATE $(db_schema_vn).observers SET
            id_universal   = CAST(CAST(NEW.item->>0 AS JSON)->>'id_universal' AS INTEGER),
            id_entity      = CAST(CAST(NEW.item->>0 AS JSON)->>'id_entity' AS INTEGER),
            anonymous      = CAST(CAST(NEW.item->>0 AS JSON)->>'anonymous' AS BOOLEAN),
            collectif      = CAST(CAST(NEW.item->>0 AS JSON)->>'collectif' AS BOOLEAN),
            default_hidden = CAST(CAST(NEW.item->>0 AS JSON)->>'default_hidden' AS BOOLEAN),
            name           = CAST(NEW.item->>0 AS JSON)->>'name',
            surname        = CAST(NEW.item->>0 AS JSON)->>'surname'
        WHERE id = OLD.id AND site = OLD.site ;
        IF NOT FOUND THEN
            -- Inserting data in new row, usually after table re-creation
            INSERT INTO $(db_schema_vn).observers(site, id, id_universal, id_entity, anonymous,
                                                  collectif, default_hidden, name, surname)
            VALUES (
                NEW.site,
                NEW.id,
                CAST(CAST(NEW.item->>0 AS JSON)->>'id_universal' AS INTEGER),
                CAST(CAST(NEW.item->>0 AS JSON)->>'id_entity' AS INTEGER),
                CAST(CAST(NEW.item->>0 AS JSON)->>'anonymous' AS BOOLEAN),
                CAST(CAST(NEW.item->>0 AS JSON)->>'collectif' AS BOOLEAN),
                CAST(CAST(NEW.item->>0 AS JSON)->>'default_hidden' AS BOOLEAN),
                CAST(NEW.item->>0 AS JSON)->>'name',
                CAST(NEW.item->>0 AS JSON)->>'surname'
            );
            END IF;
        RETURN NEW;

    ELSIF (TG_OP = 'INSERT') THEN
        -- Inserting data on src_vn.observations when raw data is inserted
        INSERT INTO $(db_schema_vn).observers(site, id, id_universal, id_entity, anonymous,
                                              collectif, default_hidden, name, surname)
        VALUES (
            NEW.site,
            NEW.id,
            CAST(CAST(NEW.item->>0 AS JSON)->>'id_universal' AS INTEGER),
            CAST(CAST(NEW.item->>0 AS JSON)->>'id_entity' AS INTEGER),
            CAST(CAST(NEW.item->>0 AS JSON)->>'anonymous' AS BOOLEAN),
            CAST(CAST(NEW.item->>0 AS JSON)->>'collectif' AS BOOLEAN),
            CAST(CAST(NEW.item->>0 AS JSON)->>'default_hidden' AS BOOLEAN),
            CAST(NEW.item->>0 AS JSON)->>'name',
            CAST(NEW.item->>0 AS JSON)->>'surname'
        );
        RETURN NEW;
    END IF;
END;
\$\$
LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS observers_trigger ON $(db_schema_import).observers_json;
CREATE TRIGGER observers_trigger
AFTER INSERT OR UPDATE OR DELETE ON $(db_schema_import).observers_json
    FOR EACH ROW EXECUTE FUNCTION $(db_schema_vn).update_observers();


---------
-- Places
---------
CREATE TABLE $(db_schema_vn).places(
    uuid                UUID DEFAULT uuid_generate_v4(),
    site                VARCHAR(50),
    id                  INTEGER,
    id_commune          INTEGER,
    id_region           INTEGER,
    name                VARCHAR(150),
    is_private          BOOLEAN,
    loc_precision       INTEGER,
    altitude            INTEGER,
    place_type          VARCHAR(150),
    visible             BOOLEAN,
    coord_lat           FLOAT,
    coord_lon           FLOAT,
    coord_x_local       FLOAT,
    coord_y_local       FLOAT,
    geom                GEOMETRY(Point, $(proj)),
    PRIMARY KEY (uuid)
);


DROP INDEX IF EXISTS places_idx_site;
CREATE INDEX places_idx_site
    ON $(db_schema_vn).places USING btree(site);
DROP INDEX IF EXISTS places_idx_id;
CREATE INDEX places_idx_id
    ON $(db_schema_vn).places USING btree(id);
DROP INDEX IF EXISTS places_gidx_geom;
CREATE INDEX places_gidx_geom
    ON $(db_schema_vn).places USING gist(geom);

-- Add trigger for postgis geometry update
DROP TRIGGER IF EXISTS trg_geom ON $(db_schema_vn).places;
CREATE TRIGGER trg_geom BEFORE INSERT or UPDATE
    ON $(db_schema_vn).places FOR EACH ROW
    EXECUTE PROCEDURE update_geom_triggerfn();

CREATE OR REPLACE FUNCTION update_places() RETURNS TRIGGER AS \$\$
    BEGIN
    IF (TG_OP = 'DELETE') THEN
        -- Deleting data when JSON data is deleted
        DELETE FROM $(db_schema_vn).places
            WHERE id = OLD.id AND site = OLD.site;
        IF NOT FOUND THEN
            RETURN NULL;
        END IF;
        RETURN OLD;

    ELSIF (TG_OP = 'UPDATE') THEN
        -- Updating or inserting data when JSON data is updated
        UPDATE $(db_schema_vn).places SET
            id_commune    = CAST(CAST(NEW.item->>0 AS JSON)->>'id_commune' AS INTEGER),
            id_region     = CAST(CAST(NEW.item->>0 AS JSON)->>'id_region' AS INTEGER),
            name          = CAST(NEW.item->>0 AS JSON)->>'name',
            is_private    = CAST(CAST(NEW.item->>0 AS JSON)->>'is_private' AS BOOLEAN),
            loc_precision = CAST(CAST(NEW.item->>0 AS JSON)->>'loc_precision' AS INTEGER),
            altitude      = CAST(CAST(NEW.item->>0 AS JSON)->>'altitude' AS INTEGER),
            place_type    = CAST(NEW.item->>0 AS JSON)->>'place_type',
            visible       = CAST(CAST(NEW.item->>0 AS JSON)->>'visible' AS BOOLEAN),
            coord_lat     = CAST(CAST(NEW.item->>0 AS JSON)->>'coord_lat' AS FLOAT),
            coord_lon     = CAST(CAST(NEW.item->>0 AS JSON)->>'coord_lon' AS FLOAT),
            coord_x_local   = CAST(CAST(NEW.item->>0 AS JSON)->>'coord_x_local' AS FLOAT),
            coord_y_local   = CAST(CAST(NEW.item->>0 AS JSON)->>'coord_y_local' AS FLOAT)
        WHERE id = OLD.id AND site = OLD.site ;
        IF NOT FOUND THEN
            -- Inserting data in new row, usually after table re-creation
            INSERT INTO $(db_schema_vn).places(site, id, id_commune, id_region, name, is_private,
                                               loc_precision, altitude, place_type, visible,
                                               coord_lat, coord_lon, coord_x_local, coord_y_local)
            VALUES (
                NEW.site,
                NEW.id,
                CAST(CAST(NEW.item->>0 AS JSON)->>'id_commune' AS INTEGER),
                CAST(CAST(NEW.item->>0 AS JSON)->>'id_region' AS INTEGER),
                CAST(NEW.item->>0 AS JSON)->>'name',
                CAST(CAST(NEW.item->>0 AS JSON)->>'is_private' AS BOOLEAN),
                CAST(CAST(NEW.item->>0 AS JSON)->>'loc_precision' AS INTEGER),
                CAST(CAST(NEW.item->>0 AS JSON)->>'altitude' AS INTEGER),
                CAST(NEW.item->>0 AS JSON)->>'place_type',
                CAST(CAST(NEW.item->>0 AS JSON)->>'visible' AS BOOLEAN),
                CAST(CAST(NEW.item->>0 AS JSON)->>'coord_lat' AS FLOAT),
                CAST(CAST(NEW.item->>0 AS JSON)->>'coord_lon' AS FLOAT),
                CAST(CAST(NEW.item->>0 AS JSON)->>'coord_x_local' AS FLOAT),
                CAST(CAST(NEW.item->>0 AS JSON)->>'coord_y_local' AS FLOAT)
            );
            END IF;
        RETURN NEW;

    ELSIF (TG_OP = 'INSERT') THEN
        -- Inserting data on src_vn.observations when raw data is inserted
        INSERT INTO $(db_schema_vn).places(site, id, id_commune, id_region, name, is_private,
                                           loc_precision, altitude, place_type, visible,
                                           coord_lat, coord_lon, coord_x_local, coord_y_local)
        VALUES (
            NEW.site,
            NEW.id,
            CAST(CAST(NEW.item->>0 AS JSON)->>'id_commune' AS INTEGER),
            CAST(CAST(NEW.item->>0 AS JSON)->>'id_region' AS INTEGER),
            CAST(NEW.item->>0 AS JSON)->>'name',
            CAST(CAST(NEW.item->>0 AS JSON)->>'is_private' AS BOOLEAN),
            CAST(CAST(NEW.item->>0 AS JSON)->>'loc_precision' AS INTEGER),
            CAST(CAST(NEW.item->>0 AS JSON)->>'altitude' AS INTEGER),
            CAST(NEW.item->>0 AS JSON)->>'place_type',
            CAST(CAST(NEW.item->>0 AS JSON)->>'visible' AS BOOLEAN),
            CAST(CAST(NEW.item->>0 AS JSON)->>'coord_lat' AS FLOAT),
            CAST(CAST(NEW.item->>0 AS JSON)->>'coord_lon' AS FLOAT),
            CAST(CAST(NEW.item->>0 AS JSON)->>'coord_x_local' AS FLOAT),
            CAST(CAST(NEW.item->>0 AS JSON)->>'coord_y_local' AS FLOAT)
        );
        RETURN NEW;
    END IF;
END;
\$\$
LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS places_trigger ON $(db_schema_import).places_json;
CREATE TRIGGER places_trigger
AFTER INSERT OR UPDATE OR DELETE ON $(db_schema_import).places_json
    FOR EACH ROW EXECUTE FUNCTION $(db_schema_vn).update_places();


----------
-- Species
----------
CREATE TABLE $(db_schema_vn).species(
    uuid                UUID DEFAULT uuid_generate_v4(),
    site                VARCHAR(50),
    id                  INTEGER,
    id_taxo_group       INTEGER,
    is_used             BOOLEAN,
    french_name         VARCHAR(150),
    latin_name          VARCHAR(150),
    rarity              VARCHAR(50),
    category_1          VARCHAR(50),
    sys_order           INTEGER,
    atlas_start         INTEGER,
    atlas_end           INTEGER,
    PRIMARY KEY (uuid)
);

DROP INDEX IF EXISTS species_idx_site;
CREATE INDEX species_idx_site
    ON $(db_schema_vn).species USING btree(site);
DROP INDEX IF EXISTS species_idx_id;
CREATE INDEX species_idx_id
    ON $(db_schema_vn).species USING btree(id);

CREATE OR REPLACE FUNCTION update_species() RETURNS TRIGGER AS \$\$
    BEGIN
    IF (TG_OP = 'DELETE') THEN
        -- Deleting data when JSON data is deleted
        DELETE FROM $(db_schema_vn).species
            WHERE id = OLD.id AND site = OLD.site;
        IF NOT FOUND THEN
            RETURN NULL;
        END IF;
        RETURN OLD;

    ELSIF (TG_OP = 'UPDATE') THEN
        -- Updating or inserting data when JSON data is updated
        UPDATE $(db_schema_vn).species SET
            id_taxo_group = CAST(CAST(NEW.item->>0 AS JSON)->>'id_taxo_group' AS INTEGER),
            is_used       = CAST(CAST(NEW.item->>0 AS JSON)->>'is_used' AS BOOLEAN),
            french_name   = CAST(NEW.item->>0 AS JSON)->>'french_name',
            latin_name    = CAST(NEW.item->>0 AS JSON)->>'latin_name',
            rarity        = CAST(NEW.item->>0 AS JSON)->>'rarity',
            category_1    = CAST(NEW.item->>0 AS JSON)->>'category_1',
            sys_order     = CAST(CAST(NEW.item->>0 AS JSON)->>'sys_order' AS INTEGER),
            atlas_start   = CAST(CAST(NEW.item->>0 AS JSON)->>'atlas_start' AS INTEGER),
            atlas_end     = CAST(CAST(NEW.item->>0 AS JSON)->>'atlas_end' AS INTEGER)
        WHERE id = OLD.id AND site = OLD.site ;
        IF NOT FOUND THEN
            -- Inserting data in new row, usually after table re-creation
            INSERT INTO $(db_schema_vn).species(site, id, id_taxo_group, is_used, french_name, latin_name, rarity,
                                                         category_1, sys_order, atlas_start, atlas_end)
            VALUES (
                NEW.site,
                NEW.id,
                CAST(CAST(NEW.item->>0 AS JSON)->>'id_taxo_group' AS INTEGER),
                CAST(CAST(NEW.item->>0 AS JSON)->>'is_used' AS BOOLEAN),
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
        -- Inserting data on src_vn.observations when raw data is inserted
        INSERT INTO $(db_schema_vn).species(site, id, id_taxo_group, is_used, french_name, latin_name, rarity,
                                                category_1, sys_order, atlas_start, atlas_end)
        VALUES (
            NEW.site,
            NEW.id,
            CAST(CAST(NEW.item->>0 AS JSON)->>'id_taxo_group' AS INTEGER),
            CAST(CAST(NEW.item->>0 AS JSON)->>'is_used' AS BOOLEAN),
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

DROP TRIGGER IF EXISTS species_trigger ON $(db_schema_import).species_json;
CREATE TRIGGER species_trigger
AFTER INSERT OR UPDATE OR DELETE ON $(db_schema_import).species_json
    FOR EACH ROW EXECUTE FUNCTION $(db_schema_vn).update_species();


--------------
-- Taxo_groups
--------------
CREATE TABLE $(db_schema_vn).taxo_groups(
    uuid                UUID DEFAULT uuid_generate_v4(),
    site                VARCHAR(50),
    id                  INTEGER,
    name                VARCHAR(150),
    latin_name          VARCHAR(150),
    name_constant       VARCHAR(150),
    access_mode         VARCHAR(50),
    PRIMARY KEY (uuid)
);

DROP INDEX IF EXISTS taxo_groups_idx_site;
CREATE INDEX taxo_groups_idx_site
    ON $(db_schema_vn).taxo_groups USING btree(site);
DROP INDEX IF EXISTS taxo_groups_idx_id;
CREATE INDEX taxo_groups_idx_id
    ON $(db_schema_vn).taxo_groups USING btree(id);

CREATE OR REPLACE FUNCTION update_taxo_groups() RETURNS TRIGGER AS \$\$
    BEGIN
    IF (TG_OP = 'DELETE') THEN
        -- Deleting data when JSON data is deleted
        DELETE FROM $(db_schema_vn).taxo_groups
            WHERE id = OLD.id AND site = OLD.site;
        IF NOT FOUND THEN
            RETURN NULL;
        END IF;
        RETURN OLD;

    ELSIF (TG_OP = 'UPDATE') THEN
        -- Updating or inserting data when JSON data is updated
        UPDATE $(db_schema_vn).taxo_groups SET
            name          = CAST(NEW.item->>0 AS JSON)->>'name',
            latin_name    = CAST(NEW.item->>0 AS JSON)->>'latin_name',
            name_constant = CAST(NEW.item->>0 AS JSON)->>'name_constant',
            access_mode   = CAST(NEW.item->>0 AS JSON)->>'access_mode'
        WHERE id = OLD.id AND site = OLD.site ;
        IF NOT FOUND THEN
            -- Inserting data in new row, usually after table re-creation
            INSERT INTO $(db_schema_vn).taxo_groups(site, id, name, latin_name, name_constant,
                                                        access_mode)
            VALUES (
                NEW.site,
                NEW.id,
                CAST(NEW.item->>0 AS JSON)->>'name',
                CAST(NEW.item->>0 AS JSON)->>'latin_name',
                CAST(NEW.item->>0 AS JSON)->>'name_constant',
                CAST(NEW.item->>0 AS JSON)->>'access_mode'
            );
            END IF;
        RETURN NEW;

    ELSIF (TG_OP = 'INSERT') THEN
        -- Inserting data on src_vn.observations when raw data is inserted
        INSERT INTO $(db_schema_vn).taxo_groups(site, id, name, latin_name, name_constant,
                                                    access_mode)
        VALUES (
            NEW.site,
            NEW.id,
            CAST(NEW.item->>0 AS JSON)->>'name',
            CAST(NEW.item->>0 AS JSON)->>'latin_name',
            CAST(NEW.item->>0 AS JSON)->>'name_constant',
            CAST(NEW.item->>0 AS JSON)->>'access_mode'
        );
        RETURN NEW;
    END IF;
END;
\$\$
LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS taxo_groups_trigger ON $(db_schema_import).taxo_groups_json;
CREATE TRIGGER taxo_groups_trigger
AFTER INSERT OR UPDATE OR DELETE ON $(db_schema_import).taxo_groups_json
    FOR EACH ROW EXECUTE FUNCTION $(db_schema_vn).update_taxo_groups();

--------------------
-- Territorial_units
--------------------
CREATE TABLE $(db_schema_vn).territorial_units(
    uuid                UUID DEFAULT uuid_generate_v4(),
    site                VARCHAR(50),
    id                  INTEGER,
    id_country          INTEGER,
    name                VARCHAR(150),
    short_name          VARCHAR(150),
    PRIMARY KEY (uuid)
);

DROP INDEX IF EXISTS territorial_units_idx_site;
CREATE INDEX territorial_units_idx_site
    ON $(db_schema_vn).territorial_units USING btree(site);
DROP INDEX IF EXISTS territorial_units_idx_id;
CREATE INDEX territorial_units_idx_id
    ON $(db_schema_vn).territorial_units USING btree(id);

CREATE OR REPLACE FUNCTION update_territorial_units() RETURNS TRIGGER AS \$\$
    BEGIN
    IF (TG_OP = 'DELETE') THEN
        -- Deleting data when JSON data is deleted
        DELETE FROM $(db_schema_vn).territorial_units
            WHERE id = OLD.id AND site = OLD.site;
        IF NOT FOUND THEN
            RETURN NULL;
        END IF;
        RETURN OLD;

    ELSIF (TG_OP = 'UPDATE') THEN
        -- Updating or inserting data when JSON data is updated
        UPDATE $(db_schema_vn).territorial_units SET
            id_country   = CAST(CAST(NEW.item->>0 AS JSON)->>'id_country' AS INTEGER),
            name         = CAST(NEW.item->>0 AS JSON)->>'name',
            short_name   = CAST(NEW.item->>0 AS JSON)->>'short_name'
        WHERE id = OLD.id AND site = OLD.site ;
        IF NOT FOUND THEN
            -- Inserting data in new row, usually after table re-creation
            INSERT INTO $(db_schema_vn).territorial_units(site, id, id_country, name, short_name)
            VALUES (
                NEW.site,
                NEW.id,
                CAST(CAST(NEW.item->>0 AS JSON)->>'id_country' AS INTEGER),
                CAST(NEW.item->>0 AS JSON)->>'name',
                CAST(NEW.item->>0 AS JSON)->>'short_name'
            );
            END IF;
        RETURN NEW;

    ELSIF (TG_OP = 'INSERT') THEN
        -- Inserting data on src_vn.observations when raw data is inserted
        INSERT INTO $(db_schema_vn).territorial_units(site, id, id_country, name, short_name)
        VALUES (
            NEW.site,
            NEW.id,
            CAST(CAST(NEW.item->>0 AS JSON)->>'id_country' AS INTEGER),
            CAST(NEW.item->>0 AS JSON)->>'name',
            CAST(NEW.item->>0 AS JSON)->>'short_name'
        );
        RETURN NEW;
    END IF;
END;
\$\$
LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS territorial_units_trigger ON $(db_schema_import).territorial_units_json;
CREATE TRIGGER territorial_units_trigger
AFTER INSERT OR UPDATE OR DELETE ON $(db_schema_import).territorial_units_json
    FOR EACH ROW EXECUTE FUNCTION $(db_schema_vn).update_territorial_units();

-- Dummy update of all rows to trigger new FUNCTION
UPDATE $(db_schema_import).entities_json SET site=site;
UPDATE $(db_schema_import).fields_json SET site=site;
UPDATE $(db_schema_import).forms_json SET site=site;
UPDATE $(db_schema_import).territorial_units_json SET site=site;
UPDATE $(db_schema_import).local_admin_units_json SET site=site;
UPDATE $(db_schema_import).places_json SET site=site;
UPDATE $(db_schema_import).taxo_groups_json SET site=site;
UPDATE $(db_schema_import).species_json SET site=site;
UPDATE $(db_schema_import).observers_json SET site=site;
UPDATE $(db_schema_import).observations_json SET site=site;

-- Final cleanup
VACUUM FULL ANALYZE;
