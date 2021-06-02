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
DROP SCHEMA IF EXISTS {{ cfg.db_schema_vn }} CASCADE;
CREATE SCHEMA {{ cfg.db_schema_vn }} AUTHORIZATION {{ cfg.db_group }};

SET search_path TO {{ cfg.db_schema_vn }},public;

-- Trigger function to add or update geometry
CREATE OR REPLACE FUNCTION update_geom_triggerfn()
RETURNS trigger AS $body$
    BEGIN
    NEW.geom := ST_SetSRID(ST_MakePoint(NEW.coord_x_local, NEW.coord_y_local), {{ cfg.proj }});
    RETURN NEW;
    END;
$body$
LANGUAGE plpgsql;

-----------
-- Entities
-----------
CREATE TABLE {{ cfg.db_schema_vn }}.entities(
    site                TEXT,
    id                  INTEGER,
    short_name          TEXT,
    full_name_french    TEXT,
    description_french  TEXT,
    url                 TEXT,
    address             TEXT,
    PRIMARY KEY (site, id)
);

DROP INDEX IF EXISTS entities_idx_site;
CREATE INDEX entities_idx_site
    ON {{ cfg.db_schema_vn }}.entities USING btree(site);
DROP INDEX IF EXISTS entities_idx_id;
CREATE INDEX entities_idx_id
    ON {{ cfg.db_schema_vn }}.entities USING btree(id);

CREATE OR REPLACE FUNCTION update_entities() RETURNS TRIGGER AS $$
    BEGIN
    IF (TG_OP = 'DELETE') THEN
        -- Deleting data when JSON data is deleted
        DELETE FROM {{ cfg.db_schema_vn }}.entities
            WHERE id = OLD.id AND site = OLD.site;
        IF NOT FOUND THEN
            RETURN NULL;
        END IF;
        RETURN OLD;

    ELSIF (TG_OP = 'UPDATE') THEN
        -- Updating or inserting data when JSON data is updated
        UPDATE {{ cfg.db_schema_vn }}.entities SET
            short_name         = NEW.item->>'short_name',
            full_name_french   = NEW.item->>'full_name_french',
            description_french = NEW.item->>'description_french',
            url                = NEW.item->>'url',
            address            = NEW.item->>'address'
        WHERE id = OLD.id AND site = OLD.site ;
        IF NOT FOUND THEN
            -- Inserting data in new row, usually after table re-creation
            INSERT INTO {{ cfg.db_schema_vn }}.entities(site, id, short_name, full_name_french, description_french,
                                                     url, address)
            VALUES (
                NEW.site,
                NEW.id,
                NEW.item->>'short_name',
                NEW.item->>'full_name_french',
                NEW.item->>'description_french',
                NEW.item->>'url',
                NEW.item->>'address'
            );
            END IF;
        RETURN NEW;

    ELSIF (TG_OP = 'INSERT') THEN
        -- Inserting row when raw data is inserted
        INSERT INTO {{ cfg.db_schema_vn }}.entities(site, id, short_name, full_name_french, description_french,
                                                 url, address)
        VALUES (
            NEW.site,
            NEW.id,
            NEW.item->>'short_name',
            NEW.item->>'full_name_french',
            NEW.item->>'description_french',
            NEW.item->>'url',
            NEW.item->>'address'
        );
        RETURN NEW;
    END IF;
END;
$$
LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS entities_trigger ON {{ cfg.db_schema_import }}.entities_json;
CREATE TRIGGER entities_trigger
AFTER INSERT OR UPDATE OR DELETE ON {{ cfg.db_schema_import }}.entities_json
    FOR EACH ROW EXECUTE PROCEDURE {{ cfg.db_schema_vn }}.update_entities();

-----------
-- Families
-----------
CREATE TABLE {{ cfg.db_schema_vn }}.families(
    site                TEXT,
    id                  INTEGER,
    id_taxo_group       INTEGER,
    latin_name          TEXT,
    name                TEXT,
    generic             TEXT,
    PRIMARY KEY (site, id)
);

DROP INDEX IF EXISTS families_idx_site;
CREATE INDEX families_idx_site
    ON {{ cfg.db_schema_vn }}.families USING btree(site);
DROP INDEX IF EXISTS families_idx_id;
CREATE INDEX families_idx_id
    ON {{ cfg.db_schema_vn }}.families USING btree(id);

CREATE OR REPLACE FUNCTION update_families() RETURNS TRIGGER AS $$
    BEGIN
    IF (TG_OP = 'DELETE') THEN
        -- Deleting data when JSON data is deleted
        DELETE FROM {{ cfg.db_schema_vn }}.families
            WHERE id = OLD.id AND site = OLD.site;
        IF NOT FOUND THEN
            RETURN NULL;
        END IF;
        RETURN OLD;

    ELSIF (TG_OP = 'UPDATE') THEN
        -- Updating or inserting data when JSON data is updated
        UPDATE {{ cfg.db_schema_vn }}.families SET
            id_taxo_group = CAST(NEW.item->>'id_taxo_group' AS INTEGER),
            latin_name    = NEW.item->>'latin_name',
            name          = NEW.item->>'name',
            generic       = NEW.item->>'generic'
        WHERE id = OLD.id AND site = OLD.site ;
        IF NOT FOUND THEN
            -- Inserting data in new row, usually after table re-creation
            INSERT INTO {{ cfg.db_schema_vn }}.families(site, id, id_taxo_group, latin_name, name,
                                                        generic)
            VALUES (
                NEW.site,
                NEW.id,
                CAST(NEW.item->>'id_taxo_group' AS INTEGER),
                NEW.item->>'latin_name',
                NEW.item->>'name',
                NEW.item->>'generic'
            );
            END IF;
        RETURN NEW;

    ELSIF (TG_OP = 'INSERT') THEN
        -- Inserting row when raw data is inserted
        INSERT INTO {{ cfg.db_schema_vn }}.families(site, id, id_taxo_group, latin_name, name,
                                                    generic)
        VALUES (
            NEW.site,
            NEW.id,
            CAST(NEW.item->>'id_taxo_group' AS INTEGER),
            NEW.item->>'latin_name',
            NEW.item->>'name',
            NEW.item->>'generic'
        );
        RETURN NEW;
    END IF;
END;
$$
LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS families_trigger ON {{ cfg.db_schema_import }}.families_json;
CREATE TRIGGER families_trigger
AFTER INSERT OR UPDATE OR DELETE ON {{ cfg.db_schema_import }}.families_json
    FOR EACH ROW EXECUTE PROCEDURE {{ cfg.db_schema_vn }}.update_families();


----------------
-- Field_details
----------------
CREATE TABLE {{ cfg.db_schema_vn }}.field_details(
    id                  TEXT,
    group_id            INTEGER,
    value_id            INTEGER,
    order_id            INTEGER,
    name                TEXT,
    text_v              TEXT,
    PRIMARY KEY (id)
);

DROP INDEX IF EXISTS field_details_idx_group_id;
CREATE INDEX field_details_idx_group_id
    ON {{ cfg.db_schema_vn }}.field_details USING btree(group_id);

CREATE OR REPLACE FUNCTION update_field_details() RETURNS TRIGGER AS $$
    BEGIN
    IF (TG_OP = 'DELETE') THEN
        -- Deleting data when JSON data is deleted
        DELETE FROM {{ cfg.db_schema_vn }}.field_details
            WHERE id = OLD.id;
        IF NOT FOUND THEN
            RETURN NULL;
        END IF;
        RETURN OLD;

    ELSIF (TG_OP = 'UPDATE') THEN
        -- Updating or inserting data when JSON data is updated
        UPDATE {{ cfg.db_schema_vn }}.field_details SET
            group_id = CAST(NEW.item->>'group' AS INTEGER),
            value_id = CAST(NEW.item->>'value' AS INTEGER),
            order_id = CAST(NEW.item->>'order_id' AS INTEGER),
            name     = NEW.item->>'name',
            text_v   = NEW.item->>'text'
        WHERE id = OLD.id;
        IF NOT FOUND THEN
            -- Inserting data in new row, usually after table re-creation
            INSERT INTO {{ cfg.db_schema_vn }}.field_details(id, group_id, value_id, order_id, name, text_v)
            VALUES (
                NEW.id,
                CAST(NEW.item->>'group' AS INTEGER),
                CAST(NEW.item->>'value' AS INTEGER),
                CAST(NEW.item->>'order_id' AS INTEGER),
                NEW.item->>'name',
                NEW.item->>'text'
            );
            END IF;
        RETURN NEW;

    ELSIF (TG_OP = 'INSERT') THEN
        -- Inserting row when raw data is inserted
        INSERT INTO {{ cfg.db_schema_vn }}.field_details(id, group_id, value_id, order_id, name, text_v)
        VALUES (
            NEW.id,
            CAST(NEW.item->>'group' AS INTEGER),
            CAST(NEW.item->>'value' AS INTEGER),
            CAST(NEW.item->>'order_id' AS INTEGER),
            NEW.item->>'name',
            NEW.item->>'text'
        );
        RETURN NEW;
    END IF;
END;
$$
LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS field_details_trigger ON {{ cfg.db_schema_import }}.field_details_json;
CREATE TRIGGER field_details_trigger
AFTER INSERT OR UPDATE OR DELETE ON {{ cfg.db_schema_import }}.field_details_json
    FOR EACH ROW EXECUTE PROCEDURE {{ cfg.db_schema_vn }}.update_field_details();


---------------
-- Field_groups
---------------
CREATE TABLE {{ cfg.db_schema_vn }}.field_groups(
    id                  INTEGER,
    default_v           TEXT,
    empty_choice        TEXT,
    mandatory           TEXT,
    name                TEXT,
    text_v              TEXT,
    group_v             TEXT,
    PRIMARY KEY (id)
);

CREATE OR REPLACE FUNCTION update_field_groups() RETURNS TRIGGER AS $$
    BEGIN
    IF (TG_OP = 'DELETE') THEN
        -- Deleting data when JSON data is deleted
        DELETE FROM {{ cfg.db_schema_vn }}.field_groups
            WHERE id = OLD.id;
        IF NOT FOUND THEN
            RETURN NULL;
        END IF;
        RETURN OLD;

    ELSIF (TG_OP = 'UPDATE') THEN
        -- Updating or inserting data when JSON data is updated
        UPDATE {{ cfg.db_schema_vn }}.field_groups SET
            default_v    = NEW.item->>'default',
            empty_choice = NEW.item->>'empty_choice',
            mandatory    = NEW.item->>'mandatory',
            name         = NEW.item->>'name',
            text_v       = NEW.item->>'text',
            group_v      = NEW.item->>'group'
        WHERE id = OLD.id;
        IF NOT FOUND THEN
            -- Inserting data in new row, usually after table re-creation
            INSERT INTO {{ cfg.db_schema_vn }}.field_groups(id, default_v, empty_choice, mandatory, name, text_v, group_v)
            VALUES (
                NEW.id,
                NEW.item->>'default',
                NEW.item->>'empty_choice',
                NEW.item->>'mandatory',
                NEW.item->>'name',
                NEW.item->>'text',
                NEW.item->>'group'
            );
            END IF;
        RETURN NEW;

    ELSIF (TG_OP = 'INSERT') THEN
        -- Inserting row when raw data is inserted
        INSERT INTO {{ cfg.db_schema_vn }}.field_groups(id, default_v, empty_choice, mandatory, name, text_v, group_v)
        VALUES (
            NEW.id,
            NEW.item->>'default',
            NEW.item->>'empty_choice',
            NEW.item->>'mandatory',
            NEW.item->>'name',
            NEW.item->>'text',
            NEW.item->>'group'
        );
        RETURN NEW;
    END IF;
END;
$$
LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS field_groups_trigger ON {{ cfg.db_schema_import }}.field_groups_json;
CREATE TRIGGER field_groups_trigger
AFTER INSERT OR UPDATE OR DELETE ON {{ cfg.db_schema_import }}.field_groups_json
    FOR EACH ROW EXECUTE PROCEDURE {{ cfg.db_schema_vn }}.update_field_groups();


--------
-- Forms
--------
CREATE TABLE {{ cfg.db_schema_vn }}.forms(
    site                TEXT,
    id                  INTEGER,
    id_form_universal   TEXT,
    observer_uid        INT,
    date_start          DATE,
    date_stop           DATE,
    time_start          TEXT,
    time_stop           TEXT,
    full_form           TEXT,
    version             TEXT,
    coord_lat           FLOAT,
    coord_lon           FLOAT,
    coord_x_local       FLOAT,
    coord_y_local       FLOAT,
    comments            TEXT,
    protocol_name       TEXT,
    protocol            JSONB,
    geom                GEOMETRY(Point, {{ cfg.proj }}),
    PRIMARY KEY (site, id)
);


DROP INDEX IF EXISTS forms_idx_site;
CREATE INDEX forms_idx_site
    ON {{ cfg.db_schema_vn }}.forms USING btree(site);
DROP INDEX IF EXISTS forms_idx_id;
CREATE INDEX forms_idx_id
    ON {{ cfg.db_schema_vn }}.forms USING btree(id);
DROP INDEX IF EXISTS forms_idx_id_form_universal;
CREATE INDEX forms_idx_id_form_universal
    ON {{ cfg.db_schema_vn }}.forms USING btree(id_form_universal);
DROP INDEX IF EXISTS forms_gidx_protocol_name;
CREATE INDEX forms_gidx_protocol_name
    ON {{ cfg.db_schema_vn }}.forms USING btree(protocol_name);
DROP INDEX IF EXISTS forms_gidx_protocol;
CREATE INDEX forms_gidx_protocol
    ON {{ cfg.db_schema_vn }}.forms USING GIN(protocol);
DROP INDEX IF EXISTS forms_gidx_geom;
CREATE INDEX forms_gidx_geom
    ON {{ cfg.db_schema_vn }}.forms USING gist(geom);

-- Add trigger for postgis geometry update
DROP TRIGGER IF EXISTS trg_geom ON {{ cfg.db_schema_vn }}.forms;
CREATE TRIGGER trg_geom BEFORE INSERT or UPDATE
    ON {{ cfg.db_schema_vn }}.forms FOR EACH ROW
    EXECUTE PROCEDURE update_geom_triggerfn();

CREATE OR REPLACE FUNCTION update_forms() RETURNS TRIGGER AS $$
    BEGIN
    IF (TG_OP = 'DELETE') THEN
        -- Deleting data when JSON data is deleted
        DELETE FROM {{ cfg.db_schema_vn }}.forms
            WHERE id = OLD.id AND site = OLD.site;
        IF NOT FOUND THEN
            RETURN NULL;
        END IF;
        RETURN OLD;

    ELSIF (TG_OP = 'UPDATE') THEN
        -- Updating or inserting data when JSON data is updated
        UPDATE {{ cfg.db_schema_vn }}.forms SET
            id_form_universal = NEW.item->>'id_form_universal',
            observer_uid      = CAST(NEW.item->>'@uid' as INT),
            date_start        = CAST(NEW.item->>'date_start' AS DATE),
            date_stop         = CAST(NEW.item->>'date_stop' AS DATE),
            time_start        = NEW.item->>'time_start',
            time_stop         = NEW.item->>'time_stop',
            full_form         = NEW.item->>'full_form',
            version           = NEW.item->>'version',
            coord_lat         = CAST(NEW.item->>'lat' AS FLOAT),
            coord_lon         = CAST(NEW.item->>'lon' AS FLOAT),
            coord_x_local     = CAST(NEW.item->>'coord_x_local' AS FLOAT),
            coord_y_local     = CAST(NEW.item->>'coord_y_local' AS FLOAT),
            comments          = NEW.item->>'comment',
            protocol_name     = NEW.item #>>'{protocol,protocol_name}',
            protocol          = CAST(NEW.item->>'protocol' AS JSONB)
        WHERE id = OLD.id AND site = OLD.site ;
        IF NOT FOUND THEN
            -- Inserting data in new row, usually after table re-creation
            INSERT INTO {{ cfg.db_schema_vn }}.forms(site, id, id_form_universal, observer_uid, date_start, 
                                              date_stop, time_start, time_stop, full_form, version, 
                                              coord_lat, coord_lon, coord_x_local, coord_y_local, 
                                              comments, protocol_name, protocol)
            VALUES (
                NEW.site,
                NEW.id,
                NEW.item->>'id_form_universal',
                CAST(NEW.item->>'@uid' as INT),
                CAST(NEW.item->>'date_start' AS DATE),
                CAST(NEW.item->>'date_stop' AS DATE),
                NEW.item->>'time_start',
                NEW.item->>'time_stop',
                NEW.item->>'full_form',
                NEW.item->>'version',
                CAST(NEW.item->>'lat' AS FLOAT),
                CAST(NEW.item->>'lon' AS FLOAT),
                CAST(NEW.item->>'coord_x_local' AS FLOAT),
                CAST(NEW.item->>'coord_y_local' AS FLOAT),
                NEW.item->>'comment',
                NEW.item #>>'{protocol,protocol_name}',
                CAST(NEW.item->>'protocol' AS JSONB)
            );
            END IF;
        RETURN NEW;

    ELSIF (TG_OP = 'INSERT') THEN
        -- Inserting row when raw data is inserted
        INSERT INTO {{ cfg.db_schema_vn }}.forms(site, id, id_form_universal, observer_uid, date_start, 
                                          date_stop, time_start, time_stop, full_form, version, 
                                          coord_lat, coord_lon, coord_x_local, coord_y_local, 
                                          comments, protocol_name, protocol)
        VALUES (
            NEW.site,
            NEW.id,
            NEW.item->>'id_form_universal',
            CAST(NEW.item->>'@uid' as INT),
            CAST(NEW.item->>'date_start' AS DATE),
            CAST(NEW.item->>'date_stop' AS DATE),
            NEW.item->>'time_start',
            NEW.item->>'time_stop',
            NEW.item->>'full_form',
            NEW.item->>'version',
            CAST(NEW.item->>'lat' AS FLOAT),
            CAST(NEW.item->>'lon' AS FLOAT),
            CAST(NEW.item->>'coord_x_local' AS FLOAT),
            CAST(NEW.item->>'coord_y_local' AS FLOAT),
            NEW.item->>'comment',
            NEW.item #>>'{protocol,protocol_name}',
            CAST(NEW.item->>'protocol' AS JSONB)
        );
        RETURN NEW;
    END IF;
END;
$$
LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS forms_trigger ON {{ cfg.db_schema_import }}.forms_json;
CREATE TRIGGER forms_trigger
AFTER INSERT OR UPDATE OR DELETE ON {{ cfg.db_schema_import }}.forms_json
    FOR EACH ROW EXECUTE PROCEDURE {{ cfg.db_schema_vn }}.update_forms();


--------------------
-- local_admin_units
--------------------
CREATE TABLE {{ cfg.db_schema_vn }}.local_admin_units(
    site                TEXT,
    id                  INTEGER,
    id_canton           INTEGER,
    name                TEXT,
    insee               TEXT,
    coord_lat           FLOAT,
    coord_lon           FLOAT,
    coord_x_local       FLOAT,
    coord_y_local       FLOAT,
    geom                GEOMETRY(Point, {{ cfg.proj }}),
    PRIMARY KEY (site, id)
);

DROP INDEX IF EXISTS local_admin_units_idx_site;
CREATE INDEX local_admin_units_idx_site
    ON {{ cfg.db_schema_vn }}.local_admin_units USING btree(site);
DROP INDEX IF EXISTS local_admin_units_idx_id;
CREATE INDEX local_admin_units_idx_id
    ON {{ cfg.db_schema_vn }}.local_admin_units USING btree(id);
DROP INDEX IF EXISTS local_admin_units_idx_id_canton;
CREATE INDEX local_admin_units_idx_id_canton
    ON {{ cfg.db_schema_vn }}.local_admin_units USING btree(id_canton);
DROP INDEX IF EXISTS local_admin_units_gidx_geom;
CREATE INDEX local_admin_units_gidx_geom
    ON {{ cfg.db_schema_vn }}.local_admin_units USING gist(geom);

-- Add trigger for postgis geometry update
DROP TRIGGER IF EXISTS trg_geom ON {{ cfg.db_schema_vn }}.local_admin_units;
CREATE TRIGGER trg_geom BEFORE INSERT or UPDATE
    ON {{ cfg.db_schema_vn }}.local_admin_units FOR EACH ROW
    EXECUTE PROCEDURE update_geom_triggerfn();

CREATE OR REPLACE FUNCTION update_local_admin_units() RETURNS TRIGGER AS $$
    BEGIN
    IF (TG_OP = 'DELETE') THEN
        -- Deleting data when JSON data is deleted
        DELETE FROM {{ cfg.db_schema_vn }}.local_admin_units
            WHERE id = OLD.id AND site = OLD.site;
        IF NOT FOUND THEN
            RETURN NULL;
        END IF;
        RETURN OLD;

    ELSIF (TG_OP = 'UPDATE') THEN
        -- Updating or inserting data when JSON data is updated
        UPDATE {{ cfg.db_schema_vn }}.local_admin_units SET
            id_canton     = CAST(NEW.item->>'id_canton' AS INTEGER),
            name          = NEW.item->>'name',
            insee         = NEW.item->>'insee',
            coord_lat     = CAST(NEW.item->>'coord_lat' AS FLOAT),
            coord_lon     = CAST(NEW.item->>'coord_lon' AS FLOAT),
            coord_x_local = CAST(NEW.item->>'coord_x_local' AS FLOAT),
            coord_y_local = CAST(NEW.item->>'coord_y_local' AS FLOAT)
        WHERE id = OLD.id AND site = OLD.site ;
        IF NOT FOUND THEN
            -- Inserting data in new row, usually after table re-creation
            INSERT INTO {{ cfg.db_schema_vn }}.local_admin_units(site, id, id_canton, name, insee,
                                                          coord_lat, coord_lon, coord_x_local, coord_y_local)
            VALUES (
                NEW.site,
                NEW.id,
                CAST(NEW.item->>'id_canton' AS INTEGER),
                NEW.item->>'name',
                NEW.item->>'insee',
                CAST(NEW.item->>'coord_lat' AS FLOAT),
                CAST(NEW.item->>'coord_lon' AS FLOAT),
                CAST(NEW.item->>'coord_x_local' AS FLOAT),
                CAST(NEW.item->>'coord_y_local' AS FLOAT)
            );
            END IF;
        RETURN NEW;

    ELSIF (TG_OP = 'INSERT') THEN
        -- Inserting row when raw data is inserted
        INSERT INTO {{ cfg.db_schema_vn }}.local_admin_units(site, id, id_canton, name, insee,
                                                      coord_lat, coord_lon, coord_x_local, coord_y_local)
        VALUES (
            NEW.site,
            NEW.id,
            CAST(NEW.item->>'id_canton' AS INTEGER),
            NEW.item->>'name',
            NEW.item->>'insee',
            CAST(NEW.item->>'coord_lat' AS FLOAT),
            CAST(NEW.item->>'coord_lon' AS FLOAT),
            CAST(NEW.item->>'coord_x_local' AS FLOAT),
            CAST(NEW.item->>'coord_y_local' AS FLOAT)
        );
        RETURN NEW;
    END IF;
END;
$$
LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS local_admin_units_trigger ON {{ cfg.db_schema_import }}.local_admin_units_json;
CREATE TRIGGER local_admin_units_trigger
AFTER INSERT OR UPDATE OR DELETE ON {{ cfg.db_schema_import }}.local_admin_units_json
    FOR EACH ROW EXECUTE PROCEDURE {{ cfg.db_schema_vn }}.update_local_admin_units();


---------------
-- Observations
---------------
CREATE TABLE {{ cfg.db_schema_vn }}.observations (
    site                TEXT,
    id_sighting         INTEGER,
    pseudo_id_sighting  TEXT,
    id_universal        TEXT,
    uuid                TEXT,
    id_form_universal   TEXT,
    id_species          INTEGER,
    taxonomy            INTEGER,
    date                TIMESTAMP,
    date_year           INTEGER, -- Missing time_start & time_stop
    timing              TIMESTAMP,
    id_place            INTEGER,
    place               TEXT,
    coord_lat           FLOAT,
    coord_lon           FLOAT,
    coord_x_local       FLOAT,
    coord_y_local       FLOAT,
    precision           TEXT,
    estimation_code     TEXT,
    count               INTEGER,
    atlas_code          INTEGER,
    altitude            INTEGER,
    project_code        TEXT,
    hidden              BOOLEAN,
    admin_hidden        BOOLEAN,
    observer_uid        INTEGER,
    details             TEXT,
    behaviours          TEXT[],
    comment             TEXT,
    hidden_comment      TEXT,
    confirmed_by        TEXT,
    mortality           BOOLEAN,
    death_cause2        TEXT,
    insert_date         TIMESTAMP,
    update_date         TIMESTAMP,
    geom                GEOMETRY(Point, {{ cfg.proj }}),
    PRIMARY KEY (site, id_sighting)
);

DROP INDEX IF EXISTS observations_idx_site;
CREATE INDEX observations_idx_site
    ON {{ cfg.db_schema_vn }}.observations USING btree(site);
DROP INDEX IF EXISTS observations_idx_id_sighting;
CREATE INDEX observations_idx_id_sighting
    ON {{ cfg.db_schema_vn }}.observations USING btree(id_sighting);
DROP INDEX IF EXISTS observations_idx_id_species;
CREATE INDEX observations_idx_id_species
    ON {{ cfg.db_schema_vn }}.observations USING btree(id_species);
DROP INDEX IF EXISTS observations_idx_taxonomy;
CREATE INDEX observations_idx_taxonomy
    ON {{ cfg.db_schema_vn }}.observations USING btree(taxonomy);
DROP INDEX IF EXISTS observations_idx_id_universal;
CREATE INDEX observations_idx_id_universal
    ON {{ cfg.db_schema_vn }}.observations USING btree(id_universal);
DROP INDEX IF EXISTS observations_idx_id_form_universal;
CREATE INDEX observations_idx_id_form_universal
    ON {{ cfg.db_schema_vn }}.observations USING btree(id_form_universal);
DROP INDEX IF EXISTS observations_idx_observer_uid;
CREATE INDEX observations_idx_observer_uid
    ON {{ cfg.db_schema_vn }}.observations USING btree(observer_uid);
DROP INDEX IF EXISTS observations_idx_project_code;
CREATE INDEX observations_idx_project_code
    ON {{ cfg.db_schema_vn }}.observations USING btree(project_code);
DROP INDEX IF EXISTS observations_gidx_geom;
CREATE INDEX observations_gidx_geom
    ON {{ cfg.db_schema_vn }}.observations USING gist(geom);

-- Add trigger for postgis geometry update
DROP TRIGGER IF EXISTS trg_geom ON {{ cfg.db_schema_vn }}.observations;
CREATE TRIGGER trg_geom BEFORE INSERT or UPDATE
    ON {{ cfg.db_schema_vn }}.observations FOR EACH ROW
    EXECUTE PROCEDURE update_geom_triggerfn();

-- Transform behaviours JSON array in PG ARRAY
CREATE OR REPLACE FUNCTION behaviour_array(
    p_input JSONB
    ) RETURNS TEXT[] AS $v_output$

DECLARE v_output TEXT[];

BEGIN
    SELECT array_agg(u.x)::TEXT[]
    INTO v_output
    FROM (SELECT t.value->>'@id' AS x
        FROM jsonb_array_elements(p_input) AS t)  AS u;

    RETURN v_output;
END;
$v_output$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION update_observations() RETURNS TRIGGER AS $$
    BEGIN
    IF (TG_OP = 'DELETE') THEN
        -- Deleting data on src_vn.observations when raw data is deleted
        DELETE FROM {{ cfg.db_schema_vn }}.observations
            WHERE id_sighting = OLD.id AND site = OLD.site;
        IF NOT FOUND THEN
            RETURN NULL;
        END IF;
        RETURN OLD;

    ELSIF (TG_OP = 'UPDATE') THEN
        -- Updating data on src_vn.observations when raw data is updated
        UPDATE {{ cfg.db_schema_vn }}.observations SET
            id_universal      = ((NEW.item -> 'observers') -> 0) ->> 'id_universal',
            uuid              = ((NEW.item -> 'observers') -> 0) ->> 'uuid',
            id_form_universal = NEW.id_form_universal,
            id_species        = CAST(NEW.item #>> '{species,@id}' AS INTEGER),
            taxonomy          = CAST(NEW.item #>> '{species,taxonomy}' AS INTEGER),
            "date"            = to_timestamp(CAST(NEW.item #>> '{date,@timestamp}' AS DOUBLE PRECISION)),
            date_year         = CAST(extract(year from to_timestamp(CAST(NEW.item #>> '{date,@timestamp}' AS DOUBLE PRECISION))) AS INTEGER),
            timing            = to_timestamp(CAST(((NEW.item -> 'observers') -> 0) #>> '{timing,@timestamp}' AS DOUBLE PRECISION)),
            id_place          = CAST(NEW.item #>> '{place,@id}' AS INTEGER),
            place             = NEW.item #>> '{place,name}',
            coord_lat         = CAST(((NEW.item -> 'observers') -> 0) ->> 'coord_lat' AS FLOAT),
            coord_lon         = CAST(((NEW.item -> 'observers') -> 0) ->> 'coord_lon' AS FLOAT),
            coord_x_local     = CAST(((NEW.item -> 'observers') -> 0) ->> 'coord_x_local' AS FLOAT),
            coord_y_local     = CAST(((NEW.item -> 'observers') -> 0) ->> 'coord_y_local' AS FLOAT),
            precision         = ((NEW.item -> 'observers') -> 0) ->> 'precision',
            estimation_code   = ((NEW.item -> 'observers') -> 0) ->> 'estimation_code',
            count             = CAST(((NEW.item -> 'observers') -> 0) ->> 'count' AS INTEGER),
            atlas_code        = CAST(((NEW.item -> 'observers') -> 0) ->> 'atlas_code' AS INTEGER),
            altitude          = CAST(((NEW.item -> 'observers') -> 0) ->> 'altitude' AS INTEGER),
            project_code      = ((NEW.item -> 'observers') -> 0) ->> 'project_code',
            hidden            = CAST(((NEW.item -> 'observers') -> 0) ->> 'hidden' AS BOOLEAN),
            admin_hidden      = CAST(((NEW.item -> 'observers') -> 0) ->> 'admin_hidden' AS BOOLEAN),
            observer_uid      = CAST(((NEW.item -> 'observers') -> 0) ->> '@uid' AS INTEGER),
            details           = ((NEW.item -> 'observers') -> 0) ->> 'details',
            behaviours        = {{ cfg.db_schema_vn }}.behaviour_array(((NEW.item -> 'observers') -> 0) -> 'behaviours'),
            comment           = ((NEW.item -> 'observers') -> 0) ->> 'comment',
            hidden_comment    = ((NEW.item -> 'observers') -> 0) ->> 'hidden_comment',
            confirmed_by      = ((NEW.item -> 'observers') -> 0) ->> 'confirmed_by',
            mortality         = CAST(((((NEW.item -> 'observers') -> 0) #>> '{extended_info,mortality}'::text []) is not null) as BOOLEAN),
            death_cause2      = ((NEW.item -> 'observers') -> 0) #>> '{extended_info, mortality, death_cause2}',
            insert_date       = to_timestamp(CAST(((NEW.item -> 'observers') -> 0) ->> 'insert_date' AS DOUBLE PRECISION)),
            update_date       = to_timestamp(NEW.update_ts)
        WHERE id_sighting = OLD.id AND site = OLD.site;

        IF NOT FOUND THEN
            -- Inserting data on src_vn.observations when raw data is inserted
            INSERT INTO {{ cfg.db_schema_vn }}.observations (site, id_sighting, pseudo_id_sighting, id_universal, uuid, id_form_universal,
                                             id_species, taxonomy, date, date_year, timing, id_place, place,
                                             coord_lat, coord_lon, coord_x_local, coord_y_local, precision, estimation_code,
                                             count, atlas_code, altitude, project_code, hidden, admin_hidden, observer_uid, details,
                                             behaviours, comment, hidden_comment, confirmed_by, mortality, death_cause2, insert_date, update_date)
            VALUES (
                NEW.site,
                NEW.id,
                encode(hmac(NEW.id::text, '{{ cfg.db_secret_key }}', 'sha1'), 'hex'),
                ((NEW.item -> 'observers') -> 0) ->> 'id_universal',
                ((NEW.item -> 'observers') -> 0) ->> 'uuid',
                NEW.id_form_universal,
                CAST(NEW.item #>> '{species,@id}' AS INTEGER),
                CAST(NEW.item #>> '{species,taxonomy}' AS INTEGER),
                to_timestamp(CAST(NEW.item #>> '{date,@timestamp}' AS DOUBLE PRECISION)),
                CAST(extract(year from to_timestamp(CAST(NEW.item #>> '{date,@timestamp}' AS DOUBLE PRECISION))) AS INTEGER),
                -- Missing time_start & time_stop
                to_timestamp(CAST(((NEW.item -> 'observers') -> 0) #>> '{timing,@timestamp}' AS DOUBLE PRECISION)),
                CAST(NEW.item #>> '{place,@id}' AS INTEGER),
                NEW.item #>> '{place,name}',
                CAST(((NEW.item -> 'observers') -> 0) ->> 'coord_lat' AS FLOAT),
                CAST(((NEW.item -> 'observers') -> 0) ->> 'coord_lon' AS FLOAT),
                CAST(((NEW.item -> 'observers') -> 0) ->> 'coord_x_local' AS FLOAT),
                CAST(((NEW.item -> 'observers') -> 0) ->> 'coord_y_local' AS FLOAT),
                ((NEW.item -> 'observers') -> 0) ->> 'precision',
                ((NEW.item -> 'observers') -> 0) ->> 'estimation_code',
                CAST(((NEW.item -> 'observers') -> 0) ->> 'count' AS INTEGER),
                CAST(((NEW.item -> 'observers') -> 0) ->> 'atlas_code' AS INTEGER),
                CAST(((NEW.item -> 'observers') -> 0) ->> 'altitude' AS INTEGER),
                ((NEW.item -> 'observers') -> 0) ->> 'project_code',
                CAST(((NEW.item -> 'observers') -> 0) ->> 'hidden' AS BOOLEAN),
                CAST(((NEW.item -> 'observers') -> 0) ->> 'admin_hidden' AS BOOLEAN),
                CAST(((NEW.item -> 'observers') -> 0) ->> '@uid' AS INTEGER),
                ((NEW.item -> 'observers') -> 0) ->> 'details',
                {{ cfg.db_schema_vn }}.behaviour_array(((NEW.item -> 'observers') -> 0) -> 'behaviours'),
                ((NEW.item -> 'observers') -> 0) ->> 'comment',
                ((NEW.item -> 'observers') -> 0) ->> 'hidden_comment',
                ((NEW.item -> 'observers') -> 0) ->> 'confirmed_by',
                CAST(((((NEW.item -> 'observers') -> 0) #>> '{extended_info,mortality}'::text []) is not null) as BOOLEAN),
                ((NEW.item -> 'observers') -> 0) #>> '{extended_info, mortality, death_cause2}',
                to_timestamp(CAST(((NEW.item -> 'observers') -> 0) ->> 'insert_date' AS DOUBLE PRECISION)),
                to_timestamp(NEW.update_ts));
            END IF;
        RETURN NEW;

    ELSIF (TG_OP = 'INSERT') THEN
        -- Inserting data on src_vn.observations when raw data is inserted
        INSERT INTO {{ cfg.db_schema_vn }}.observations (site, id_sighting, pseudo_id_sighting, id_universal, uuid, id_form_universal,
                                         id_species, taxonomy, date, date_year, timing, id_place, place,
                                         coord_lat, coord_lon, coord_x_local, coord_y_local, precision, estimation_code,
                                         count, atlas_code, altitude, project_code, hidden, admin_hidden, observer_uid, details,
                                         behaviours, comment, hidden_comment, confirmed_by, mortality, death_cause2, insert_date, update_date)
        VALUES (
            NEW.site,
            NEW.id,
            encode(hmac(NEW.id::text, '{{ cfg.db_secret_key }}', 'sha1'), 'hex'),
            ((NEW.item -> 'observers') -> 0) ->> 'id_universal',
            ((NEW.item -> 'observers') -> 0) ->> 'uuid',
            NEW.id_form_universal,
            CAST(NEW.item #>> '{species,@id}' AS INTEGER),
            CAST(NEW.item #>> '{species,taxonomy}' AS INTEGER),
            to_timestamp(CAST(NEW.item #>> '{date,@timestamp}' AS DOUBLE PRECISION)),
            CAST(extract(year from to_timestamp(CAST(NEW.item #>> '{date,@timestamp}' AS DOUBLE PRECISION))) AS INTEGER),
            -- Missing time_start & time_stop
            to_timestamp(CAST(((NEW.item -> 'observers') -> 0) #>> '{timing,@timestamp}' AS DOUBLE PRECISION)),
            CAST(NEW.item #>> '{place,@id}' AS INTEGER),
            NEW.item #>> '{place,name}',
            CAST(((NEW.item -> 'observers') -> 0) ->> 'coord_lat' AS FLOAT),
            CAST(((NEW.item -> 'observers') -> 0) ->> 'coord_lon' AS FLOAT),
            CAST(((NEW.item -> 'observers') -> 0) ->> 'coord_x_local' AS FLOAT),
            CAST(((NEW.item -> 'observers') -> 0) ->> 'coord_y_local' AS FLOAT),
            ((NEW.item -> 'observers') -> 0) ->> 'precision',
            ((NEW.item -> 'observers') -> 0) ->> 'estimation_code',
            CAST(((NEW.item -> 'observers') -> 0) ->> 'count' AS INTEGER),
            CAST(((NEW.item -> 'observers') -> 0) ->> 'atlas_code' AS INTEGER),
            CAST(((NEW.item -> 'observers') -> 0) ->> 'altitude' AS INTEGER),
            ((NEW.item -> 'observers') -> 0) ->> 'project_code',
            CAST(((NEW.item -> 'observers') -> 0) ->> 'hidden' AS BOOLEAN),
            CAST(((NEW.item -> 'observers') -> 0) ->> 'admin_hidden' AS BOOLEAN),
            CAST(((NEW.item -> 'observers') -> 0) ->> '@uid' AS INTEGER),
            ((NEW.item -> 'observers') -> 0) ->> 'details',
            {{ cfg.db_schema_vn }}.behaviour_array(((NEW.item -> 'observers') -> 0) -> 'behaviours'),
            ((NEW.item -> 'observers') -> 0) ->> 'comment',
            ((NEW.item -> 'observers') -> 0) ->> 'hidden_comment',
            ((NEW.item -> 'observers') -> 0) ->> 'confirmed_by',
            CAST(((((NEW.item -> 'observers') -> 0) #>> '{extended_info,mortality}'::text []) is not null) as BOOLEAN),
            ((NEW.item -> 'observers') -> 0) #>> '{extended_info, mortality, death_cause2}',
            to_timestamp(CAST(((NEW.item -> 'observers') -> 0) ->> 'insert_date' AS DOUBLE PRECISION)),
            to_timestamp(NEW.update_ts));
        RETURN NEW;
    END IF;
END;
$$
LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS observations_trigger ON {{ cfg.db_schema_import }}.observations_json;
CREATE TRIGGER observations_trigger
AFTER INSERT OR UPDATE OR DELETE ON {{ cfg.db_schema_import }}.observations_json
    FOR EACH ROW EXECUTE PROCEDURE update_observations();


------------
-- Observers
------------
CREATE TABLE {{ cfg.db_schema_vn }}.observers(
    site                TEXT,
    id                  INTEGER,
    id_universal        INTEGER,
    pseudo_observer_uid TEXT,
    id_entity           INTEGER,
    anonymous           BOOLEAN,
    collectif           BOOLEAN,
    default_hidden      BOOLEAN,
    name                TEXT,
    surname             TEXT,
    PRIMARY KEY (site, id)
);

DROP INDEX IF EXISTS observers_idx_site;
CREATE INDEX observers_idx_site
    ON {{ cfg.db_schema_vn }}.observers USING btree(site);
DROP INDEX IF EXISTS observers_idx_id;
CREATE INDEX observers_idx_id
    ON {{ cfg.db_schema_vn }}.observers USING btree(id);
DROP INDEX IF EXISTS observers_idx_id_universal;
CREATE INDEX observers_idx_id_universal
    ON {{ cfg.db_schema_vn }}.observers USING btree(id_universal);

CREATE OR REPLACE FUNCTION update_observers() RETURNS TRIGGER AS $$
    BEGIN
    IF (TG_OP = 'DELETE') THEN
        -- Deleting data when JSON data is deleted
        DELETE FROM {{ cfg.db_schema_vn }}.observers
            WHERE id = OLD.id AND site = OLD.site;
        IF NOT FOUND THEN
            RETURN NULL;
        END IF;
        RETURN OLD;

    ELSIF (TG_OP = 'UPDATE') THEN
        -- Updating or inserting data when JSON data is updated
        UPDATE {{ cfg.db_schema_vn }}.observers SET
            id_universal   = NEW.id_universal,
            id_entity      = CAST(NEW.item->>'id_entity' AS INTEGER),
            anonymous      = CAST(NEW.item->>'anonymous' AS BOOLEAN),
            collectif      = CAST(NEW.item->>'collectif' AS BOOLEAN),
            default_hidden = CAST(NEW.item->>'default_hidden' AS BOOLEAN),
            name           = NEW.item->>'name',
            surname        = NEW.item->>'surname'
        WHERE id = OLD.id AND site = OLD.site ;
        IF NOT FOUND THEN
            -- Inserting data in new row, usually after table re-creation
            INSERT INTO {{ cfg.db_schema_vn }}.observers(site, id, id_universal, pseudo_observer_uid, id_entity, anonymous,
                                                  collectif, default_hidden, name, surname)
            VALUES (
                NEW.site,
                NEW.id,
                NEW.id_universal,
                encode(hmac(CAST(NEW.id_universal AS TEXT), '{{ cfg.db_secret_key }}', 'sha1'), 'hex'),
                CAST(NEW.item->>'id_entity' AS INTEGER),
                CAST(NEW.item->>'anonymous' AS BOOLEAN),
                CAST(NEW.item->>'collectif' AS BOOLEAN),
                CAST(NEW.item->>'default_hidden' AS BOOLEAN),
                NEW.item->>'name',
                NEW.item->>'surname'
            );
            END IF;
        RETURN NEW;

    ELSIF (TG_OP = 'INSERT') THEN
        -- Inserting data on src_vn.observations when raw data is inserted
        INSERT INTO {{ cfg.db_schema_vn }}.observers(site, id, id_universal, pseudo_observer_uid, id_entity, anonymous,
                                              collectif, default_hidden, name, surname)
        VALUES (
            NEW.site,
            NEW.id,
            NEW.id_universal,
            encode(hmac(CAST(NEW.id_universal AS TEXT), '{{ cfg.db_secret_key }}', 'sha1'), 'hex'),
            CAST(NEW.item->>'id_entity' AS INTEGER),
            CAST(NEW.item->>'anonymous' AS BOOLEAN),
            CAST(NEW.item->>'collectif' AS BOOLEAN),
            CAST(NEW.item->>'default_hidden' AS BOOLEAN),
            NEW.item->>'name',
            NEW.item->>'surname'
        );
        RETURN NEW;
    END IF;
END;
$$
LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS observers_trigger ON {{ cfg.db_schema_import }}.observers_json;
CREATE TRIGGER observers_trigger
AFTER INSERT OR UPDATE OR DELETE ON {{ cfg.db_schema_import }}.observers_json
    FOR EACH ROW EXECUTE PROCEDURE {{ cfg.db_schema_vn }}.update_observers();


---------
-- Places
---------
CREATE TABLE {{ cfg.db_schema_vn }}.places(
    site                TEXT,
    id                  INTEGER,
    id_commune          INTEGER,
    id_region           INTEGER,
    name                TEXT,
    is_private          BOOLEAN,
    loc_precision       INTEGER,
    altitude            INTEGER,
    place_type          TEXT,
    visible             BOOLEAN,
    coord_lat           FLOAT,
    coord_lon           FLOAT,
    coord_x_local       FLOAT,
    coord_y_local       FLOAT,
    geom                GEOMETRY(Point, {{ cfg.proj }}),
    PRIMARY KEY (site, id)
);


DROP INDEX IF EXISTS places_idx_site;
CREATE INDEX places_idx_site
    ON {{ cfg.db_schema_vn }}.places USING btree(site);
DROP INDEX IF EXISTS places_idx_id;
CREATE INDEX places_idx_id
    ON {{ cfg.db_schema_vn }}.places USING btree(id);
DROP INDEX IF EXISTS places_idx_id_commune;
CREATE INDEX places_idx_id_commune
    ON {{ cfg.db_schema_vn }}.places USING btree(id_commune);
DROP INDEX IF EXISTS places_gidx_geom;
CREATE INDEX places_gidx_geom
    ON {{ cfg.db_schema_vn }}.places USING gist(geom);

-- Add trigger for postgis geometry update
DROP TRIGGER IF EXISTS trg_geom ON {{ cfg.db_schema_vn }}.places;
CREATE TRIGGER trg_geom BEFORE INSERT or UPDATE
    ON {{ cfg.db_schema_vn }}.places FOR EACH ROW
    EXECUTE PROCEDURE update_geom_triggerfn();

CREATE OR REPLACE FUNCTION update_places() RETURNS TRIGGER AS $$
    BEGIN
    IF (TG_OP = 'DELETE') THEN
        -- Deleting data when JSON data is deleted
        DELETE FROM {{ cfg.db_schema_vn }}.places
            WHERE id = OLD.id AND site = OLD.site;
        IF NOT FOUND THEN
            RETURN NULL;
        END IF;
        RETURN OLD;

    ELSIF (TG_OP = 'UPDATE') THEN
        -- Updating or inserting data when JSON data is updated
        UPDATE {{ cfg.db_schema_vn }}.places SET
            id_commune    = CAST(NEW.item->>'id_commune' AS INTEGER),
            id_region     = CAST(NEW.item->>'id_region' AS INTEGER),
            name          = NEW.item->>'name',
            is_private    = CAST(NEW.item->>'is_private' AS BOOLEAN),
            loc_precision = CAST(NEW.item->>'loc_precision' AS INTEGER),
            altitude      = CAST(NEW.item->>'altitude' AS INTEGER),
            place_type    = NEW.item->>'place_type',
            visible       = CAST(NEW.item->>'visible' AS BOOLEAN),
            coord_lat     = CAST(NEW.item->>'coord_lat' AS FLOAT),
            coord_lon     = CAST(NEW.item->>'coord_lon' AS FLOAT),
            coord_x_local = CAST(NEW.item->>'coord_x_local' AS FLOAT),
            coord_y_local = CAST(NEW.item->>'coord_y_local' AS FLOAT)
        WHERE id = OLD.id AND site = OLD.site ;
        IF NOT FOUND THEN
            -- Inserting data in new row, usually after table re-creation
            INSERT INTO {{ cfg.db_schema_vn }}.places(site, id, id_commune, id_region, name, is_private,
                                               loc_precision, altitude, place_type, visible,
                                               coord_lat, coord_lon, coord_x_local, coord_y_local)
            VALUES (
                NEW.site,
                NEW.id,
                CAST(NEW.item->>'id_commune' AS INTEGER),
                CAST(NEW.item->>'id_region' AS INTEGER),
                NEW.item->>'name',
                CAST(NEW.item->>'is_private' AS BOOLEAN),
                CAST(NEW.item->>'loc_precision' AS INTEGER),
                CAST(NEW.item->>'altitude' AS INTEGER),
                NEW.item->>'place_type',
                CAST(NEW.item->>'visible' AS BOOLEAN),
                CAST(NEW.item->>'coord_lat' AS FLOAT),
                CAST(NEW.item->>'coord_lon' AS FLOAT),
                CAST(NEW.item->>'coord_x_local' AS FLOAT),
                CAST(NEW.item->>'coord_y_local' AS FLOAT)
            );
            END IF;
        RETURN NEW;

    ELSIF (TG_OP = 'INSERT') THEN
        -- Inserting data on src_vn.observations when raw data is inserted
        INSERT INTO {{ cfg.db_schema_vn }}.places(site, id, id_commune, id_region, name, is_private,
                                           loc_precision, altitude, place_type, visible,
                                           coord_lat, coord_lon, coord_x_local, coord_y_local)
        VALUES (
            NEW.site,
            NEW.id,
            CAST(NEW.item->>'id_commune' AS INTEGER),
            CAST(NEW.item->>'id_region' AS INTEGER),
            NEW.item->>'name',
            CAST(NEW.item->>'is_private' AS BOOLEAN),
            CAST(NEW.item->>'loc_precision' AS INTEGER),
            CAST(NEW.item->>'altitude' AS INTEGER),
            NEW.item->>'place_type',
            CAST(NEW.item->>'visible' AS BOOLEAN),
            CAST(NEW.item->>'coord_lat' AS FLOAT),
            CAST(NEW.item->>'coord_lon' AS FLOAT),
            CAST(NEW.item->>'coord_x_local' AS FLOAT),
            CAST(NEW.item->>'coord_y_local' AS FLOAT)
        );
        RETURN NEW;
    END IF;
END;
$$
LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS places_trigger ON {{ cfg.db_schema_import }}.places_json;
CREATE TRIGGER places_trigger
AFTER INSERT OR UPDATE OR DELETE ON {{ cfg.db_schema_import }}.places_json
    FOR EACH ROW EXECUTE PROCEDURE {{ cfg.db_schema_vn }}.update_places();


----------
-- Species
----------
CREATE TABLE {{ cfg.db_schema_vn }}.species(
    site                TEXT,
    id                  INTEGER,
    id_taxo_group       INTEGER,
    is_used             BOOLEAN,
    french_name         TEXT,
    latin_name          TEXT,
    rarity              TEXT,
    category_1          TEXT,
    sys_order           INTEGER,
    atlas_start         INTEGER,
    atlas_end           INTEGER,
    PRIMARY KEY (site, id)
);

DROP INDEX IF EXISTS species_idx_site;
CREATE INDEX species_idx_site
    ON {{ cfg.db_schema_vn }}.species USING btree(site);
DROP INDEX IF EXISTS species_idx_id;
CREATE INDEX species_idx_id
    ON {{ cfg.db_schema_vn }}.species USING btree(id);
DROP INDEX IF EXISTS species_idx_id_taxo_group;
CREATE INDEX species_idx_id_taxo_group
    ON {{ cfg.db_schema_vn }}.species USING btree(id_taxo_group);

CREATE OR REPLACE FUNCTION update_species() RETURNS TRIGGER AS $$
    BEGIN
    IF (TG_OP = 'DELETE') THEN
        -- Deleting data when JSON data is deleted
        DELETE FROM {{ cfg.db_schema_vn }}.species
            WHERE id = OLD.id AND site = OLD.site;
        IF NOT FOUND THEN
            RETURN NULL;
        END IF;
        RETURN OLD;

    ELSIF (TG_OP = 'UPDATE') THEN
        -- Updating or inserting data when JSON data is updated
        UPDATE {{ cfg.db_schema_vn }}.species SET
            id_taxo_group = CAST(NEW.item->>'id_taxo_group' AS INTEGER),
            is_used       = CAST(NEW.item->>'is_used' AS BOOLEAN),
            french_name   = NEW.item->>'french_name',
            latin_name    = NEW.item->>'latin_name',
            rarity        = NEW.item->>'rarity',
            category_1    = NEW.item->>'category_1',
            sys_order     = CAST(NEW.item->>'sys_order' AS INTEGER),
            atlas_start   = CAST(NEW.item->>'atlas_start' AS INTEGER),
            atlas_end     = CAST(NEW.item->>'atlas_end' AS INTEGER)
        WHERE id = OLD.id AND site = OLD.site ;
        IF NOT FOUND THEN
            -- Inserting data in new row, usually after table re-creation
            INSERT INTO {{ cfg.db_schema_vn }}.species(site, id, id_taxo_group, is_used, french_name, latin_name, rarity,
                                                         category_1, sys_order, atlas_start, atlas_end)
            VALUES (
                NEW.site,
                NEW.id,
                CAST(NEW.item->>'id_taxo_group' AS INTEGER),
                CAST(NEW.item->>'is_used' AS BOOLEAN),
                NEW.item->>'french_name',
                NEW.item->>'latin_name',
                NEW.item->>'rarity',
                NEW.item->>'category_1',
                CAST(NEW.item->>'sys_order' AS INTEGER),
                CAST(NEW.item->>'atlas_start' AS INTEGER),
                CAST(NEW.item->>'atlas_end' AS INTEGER)
            );
            END IF;
        RETURN NEW;

    ELSIF (TG_OP = 'INSERT') THEN
        -- Inserting data on src_vn.observations when raw data is inserted
        INSERT INTO {{ cfg.db_schema_vn }}.species(site, id, id_taxo_group, is_used, french_name, latin_name, rarity,
                                                category_1, sys_order, atlas_start, atlas_end)
        VALUES (
            NEW.site,
            NEW.id,
            CAST(NEW.item->>'id_taxo_group' AS INTEGER),
            CAST(NEW.item->>'is_used' AS BOOLEAN),
            NEW.item->>'french_name',
            NEW.item->>'latin_name',
            NEW.item->>'rarity',
            NEW.item->>'category_1',
            CAST(NEW.item->>'sys_order' AS INTEGER),
            CAST(NEW.item->>'atlas_start' AS INTEGER),
            CAST(NEW.item->>'atlas_end' AS INTEGER)
        );
        RETURN NEW;
    END IF;
END;
$$
LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS species_trigger ON {{ cfg.db_schema_import }}.species_json;
CREATE TRIGGER species_trigger
AFTER INSERT OR UPDATE OR DELETE ON {{ cfg.db_schema_import }}.species_json
    FOR EACH ROW EXECUTE PROCEDURE {{ cfg.db_schema_vn }}.update_species();


--------------
-- Taxo_groups
--------------
CREATE TABLE {{ cfg.db_schema_vn }}.taxo_groups(
    site                TEXT,
    id                  INTEGER,
    name                TEXT,
    latin_name          TEXT,
    name_constant       TEXT,
    access_mode         TEXT,
    PRIMARY KEY (site, id)
);

DROP INDEX IF EXISTS taxo_groups_idx_site;
CREATE INDEX taxo_groups_idx_site
    ON {{ cfg.db_schema_vn }}.taxo_groups USING btree(site);
DROP INDEX IF EXISTS taxo_groups_idx_id;
CREATE INDEX taxo_groups_idx_id
    ON {{ cfg.db_schema_vn }}.taxo_groups USING btree(id);

CREATE OR REPLACE FUNCTION update_taxo_groups() RETURNS TRIGGER AS $$
    BEGIN
    IF (TG_OP = 'DELETE') THEN
        -- Deleting data when JSON data is deleted
        DELETE FROM {{ cfg.db_schema_vn }}.taxo_groups
            WHERE id = OLD.id AND site = OLD.site;
        IF NOT FOUND THEN
            RETURN NULL;
        END IF;
        RETURN OLD;

    ELSIF (TG_OP = 'UPDATE') THEN
        -- Updating or inserting data when JSON data is updated
        UPDATE {{ cfg.db_schema_vn }}.taxo_groups SET
            name          = NEW.item->>'name',
            latin_name    = NEW.item->>'latin_name',
            name_constant = NEW.item->>'name_constant',
            access_mode   = NEW.item->>'access_mode'
        WHERE id = OLD.id AND site = OLD.site ;
        IF NOT FOUND THEN
            -- Inserting data in new row, usually after table re-creation
            INSERT INTO {{ cfg.db_schema_vn }}.taxo_groups(site, id, name, latin_name, name_constant,
                                                    access_mode)
            VALUES (
                NEW.site,
                NEW.id,
                NEW.item->>'name',
                NEW.item->>'latin_name',
                NEW.item->>'name_constant',
                NEW.item->>'access_mode'
            );
            END IF;
        RETURN NEW;

    ELSIF (TG_OP = 'INSERT') THEN
        -- Inserting data on src_vn.observations when raw data is inserted
        INSERT INTO {{ cfg.db_schema_vn }}.taxo_groups(site, id, name, latin_name, name_constant,
                                                access_mode)
        VALUES (
            NEW.site,
            NEW.id,
            NEW.item->>'name',
            NEW.item->>'latin_name',
            NEW.item->>'name_constant',
            NEW.item->>'access_mode'
        );
        RETURN NEW;
    END IF;
END;
$$
LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS taxo_groups_trigger ON {{ cfg.db_schema_import }}.taxo_groups_json;
CREATE TRIGGER taxo_groups_trigger
AFTER INSERT OR UPDATE OR DELETE ON {{ cfg.db_schema_import }}.taxo_groups_json
    FOR EACH ROW EXECUTE PROCEDURE {{ cfg.db_schema_vn }}.update_taxo_groups();

--------------------
-- Territorial_units
--------------------
CREATE TABLE {{ cfg.db_schema_vn }}.territorial_units(
    site                TEXT,
    id                  INTEGER,
    id_country          INTEGER,
    name                TEXT,
    short_name          TEXT,
    PRIMARY KEY (site, id)
);

DROP INDEX IF EXISTS territorial_units_idx_site;
CREATE INDEX territorial_units_idx_site
    ON {{ cfg.db_schema_vn }}.territorial_units USING btree(site);
DROP INDEX IF EXISTS territorial_units_idx_id;
CREATE INDEX territorial_units_idx_id
    ON {{ cfg.db_schema_vn }}.territorial_units USING btree(id);

CREATE OR REPLACE FUNCTION update_territorial_units() RETURNS TRIGGER AS $$
    BEGIN
    IF (TG_OP = 'DELETE') THEN
        -- Deleting data when JSON data is deleted
        DELETE FROM {{ cfg.db_schema_vn }}.territorial_units
            WHERE id = OLD.id AND site = OLD.site;
        IF NOT FOUND THEN
            RETURN NULL;
        END IF;
        RETURN OLD;

    ELSIF (TG_OP = 'UPDATE') THEN
        -- Updating or inserting data when JSON data is updated
        UPDATE {{ cfg.db_schema_vn }}.territorial_units SET
            id_country   = CAST(NEW.item->>'id_country' AS INTEGER),
            name         = NEW.item->>'name',
            short_name   = NEW.item->>'short_name'
        WHERE id = OLD.id AND site = OLD.site ;
        IF NOT FOUND THEN
            -- Inserting data in new row, usually after table re-creation
            INSERT INTO {{ cfg.db_schema_vn }}.territorial_units(site, id, id_country, name, short_name)
            VALUES (
                NEW.site,
                NEW.id,
                CAST(NEW.item->>'id_country' AS INTEGER),
                NEW.item->>'name',
                NEW.item->>'short_name'
            );
            END IF;
        RETURN NEW;

    ELSIF (TG_OP = 'INSERT') THEN
        -- Inserting data on src_vn.observations when raw data is inserted
        INSERT INTO {{ cfg.db_schema_vn }}.territorial_units(site, id, id_country, name, short_name)
        VALUES (
            NEW.site,
            NEW.id,
            CAST(NEW.item->>'id_country' AS INTEGER),
            NEW.item->>'name',
            NEW.item->>'short_name'
        );
        RETURN NEW;
    END IF;
END;
$$
LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS territorial_units_trigger ON {{ cfg.db_schema_import }}.territorial_units_json;
CREATE TRIGGER territorial_units_trigger
AFTER INSERT OR UPDATE OR DELETE ON {{ cfg.db_schema_import }}.territorial_units_json
    FOR EACH ROW EXECUTE PROCEDURE {{ cfg.db_schema_vn }}.update_territorial_units();


--------------
-- Validations
--------------
CREATE TABLE {{ cfg.db_schema_vn }}.validations(
    site                TEXT,
    id                  INTEGER,
    committee           TEXT,
    date_start          INTEGER,
    date_stop           INTEGER,
    id_species          INTEGER,
    PRIMARY KEY (site, id)
);

DROP INDEX IF EXISTS validations_idx_site;
CREATE INDEX validations_idx_site
    ON {{ cfg.db_schema_vn }}.validations USING btree(site);
DROP INDEX IF EXISTS validations_idx_id;
CREATE INDEX validations_idx_id
    ON {{ cfg.db_schema_vn }}.validations USING btree(id);

CREATE OR REPLACE FUNCTION validations_units() RETURNS TRIGGER AS $$
    BEGIN
    IF (TG_OP = 'DELETE') THEN
        -- Deleting data when JSON data is deleted
        DELETE FROM {{ cfg.db_schema_vn }}.validations
            WHERE id = OLD.id AND site = OLD.site;
        IF NOT FOUND THEN
            RETURN NULL;
        END IF;
        RETURN OLD;

    ELSIF (TG_OP = 'UPDATE') THEN
        -- Updating or inserting data when JSON data is updated
        UPDATE {{ cfg.db_schema_vn }}.validations SET
            committee    = NEW.item->>'name',
            date_start   = CAST(NEW.item->>'id_country' AS INTEGER),
            date_stop    = CAST(NEW.item->>'id_country' AS INTEGER),
            id_species   = CAST(NEW.item->>'id_country' AS INTEGER)
        WHERE id = OLD.id AND site = OLD.site ;
        IF NOT FOUND THEN
            -- Inserting data in new row, usually after table re-creation
            INSERT INTO {{ cfg.db_schema_vn }}.validations(site, id, committee, date_start, date_stop, id_species)
            VALUES (
                NEW.site,
                NEW.id,
                NEW.item->>'committee',
                CAST(NEW.item->>'date_start' AS INTEGER),
                CAST(NEW.item->>'date_stop' AS INTEGER),
                CAST(NEW.item->>'id_species' AS INTEGER)
            );
            END IF;
        RETURN NEW;

    ELSIF (TG_OP = 'INSERT') THEN
        -- Inserting data on src_vn.observations when raw data is inserted
        INSERT INTO {{ cfg.db_schema_vn }}.validations(site, id, committee, date_start, date_stop, id_species)
        VALUES (
            NEW.site,
            NEW.id,
            NEW.item->>'committee',
            CAST(NEW.item->>'date_start' AS INTEGER),
            CAST(NEW.item->>'date_stop' AS INTEGER),
            CAST(NEW.item->>'id_species' AS INTEGER)
        );
        RETURN NEW;
    END IF;
END;
$$
LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS validations_trigger ON {{ cfg.db_schema_import }}.validations_json;
CREATE TRIGGER validations_trigger
AFTER INSERT OR UPDATE OR DELETE ON {{ cfg.db_schema_import }}.validations_json
    FOR EACH ROW EXECUTE PROCEDURE {{ cfg.db_schema_vn }}.validations_units();


-- Dummy update of all rows to trigger new FUNCTION
UPDATE {{ cfg.db_schema_import }}.entities_json SET site=site;
UPDATE {{ cfg.db_schema_import }}.families_json SET site=site;
UPDATE {{ cfg.db_schema_import }}.field_details_json SET id=id;
UPDATE {{ cfg.db_schema_import }}.field_groups_json SET id=id;
UPDATE {{ cfg.db_schema_import }}.forms_json SET site=site;
UPDATE {{ cfg.db_schema_import }}.local_admin_units_json SET site=site;
UPDATE {{ cfg.db_schema_import }}.places_json SET site=site;
UPDATE {{ cfg.db_schema_import }}.observers_json SET site=site;
UPDATE {{ cfg.db_schema_import }}.observations_json SET site=site;
UPDATE {{ cfg.db_schema_import }}.species_json SET site=site;
UPDATE {{ cfg.db_schema_import }}.taxo_groups_json SET site=site;
UPDATE {{ cfg.db_schema_import }}.territorial_units_json SET site=site;
UPDATE {{ cfg.db_schema_import }}.validations_json SET site=site;

-- Final cleanup
VACUUM FULL ANALYZE {{ cfg.db_schema_import }}.entities_json, {{ cfg.db_schema_vn }}.entities;
VACUUM FULL ANALYZE {{ cfg.db_schema_import }}.families_json, {{ cfg.db_schema_vn }}.families;
VACUUM FULL ANALYZE {{ cfg.db_schema_import }}.field_details_json, {{ cfg.db_schema_vn }}.field_details;
VACUUM FULL ANALYZE {{ cfg.db_schema_import }}.field_groups_json, {{ cfg.db_schema_vn }}.field_groups;
VACUUM FULL ANALYZE {{ cfg.db_schema_import }}.forms_json, {{ cfg.db_schema_vn }}.forms;
VACUUM FULL ANALYZE {{ cfg.db_schema_import }}.local_admin_units_json, {{ cfg.db_schema_vn }}.local_admin_units;
VACUUM FULL ANALYZE {{ cfg.db_schema_import }}.observations_json, {{ cfg.db_schema_vn }}.observations;
VACUUM FULL ANALYZE {{ cfg.db_schema_import }}.observers_json, {{ cfg.db_schema_vn }}.observers;
VACUUM FULL ANALYZE {{ cfg.db_schema_import }}.places_json, {{ cfg.db_schema_vn }}.places;
VACUUM FULL ANALYZE {{ cfg.db_schema_import }}.species_json, {{ cfg.db_schema_vn }}.species;
VACUUM FULL ANALYZE {{ cfg.db_schema_import }}.taxo_groups_json, {{ cfg.db_schema_vn }}.taxo_groups;
VACUUM FULL ANALYZE {{ cfg.db_schema_import }}.territorial_units_json, {{ cfg.db_schema_vn }}.territorial_units;
-- VACUUM FULL ANALYZE {{ cfg.db_schema_import }}.uuid_xref;
VACUUM FULL ANALYZE {{ cfg.db_schema_import }}.validations_json, {{ cfg.db_schema_vn }}.validations;
