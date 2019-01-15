-- Initialize Postgresql database, template for pyexpander3
-- - Delete and create database and roles
-- - Create JSON tables

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
\$body\$ LANGUAGE plpgsql;

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

-- Add trigger
DROP TRIGGER IF EXISTS trg_geom ON observations_json ;
CREATE TRIGGER trg_geom BEFORE INSERT or UPDATE
    ON observations FOR EACH ROW
    EXECUTE PROCEDURE update_geom_triggerfn();


-- Indexes on $(evn_db_schema_vn).observations;
DROP INDEX IF EXISTS $(evn_db_schema_vn).observations_idx_id_universal;
CREATE UNIQUE INDEX observations_idx_id_universal
    ON $(evn_db_schema_vn).observations USING btree
    (id_universal)
    TABLESPACE pg_default;

CREATE OR REPLACE FUNCTION update_vn_sights() RETURNS TRIGGER AS \$\$
    BEGIN
    /*
    update continously src_vn.observations table from raw json data tables after insert/update/delete events.
    You just need to add this trigger to source table
    */
    IF (TG_OP = 'DELETE') THEN
        /* Deleting data on src_vn.observations when raw data is deleted */
        DELETE FROM src_vn.observations
            WHERE id_sighting = OLD.id_sighting AND site=OLD.site;
        IF NOT FOUND THEN
            RETURN NULL;
        END IF;
        RETURN OLD;

    ELSIF (TG_OP = 'UPDATE') THEN
        /* Updating data on src_vn.observations when raw data is updated */
        UPDATE src_vn.observations SET
            id_universal    = (((NEW.item->>0)::json -> 'observers') -> 0) ->> 'id_universal',
            id_species      = cast((NEW.item->>0)::json #>> '{species,@id}' AS INTEGER),
            french_name     = (NEW.item->>0)::json #>> '{species,name}',
            latin_name      = (NEW.item->>0)::json #>> '{species,latin_name}',
            "date"          = to_date((NEW.item->>0)::json #>> '{date,@ISO8601}', 'YYYY-MM-DD'),
            date_year       = cast(extract(year from to_date((NEW.item->>0)::json #>> '{date,@ISO8601}', 'YYYY-MM-DD')) AS INTEGER),
            timing          = to_timestamp((((NEW.item->>0)::json -> 'observers') -> 0) #>> '{timing,@ISO8601}', 'YYYY-MM-DD"T"HH24:MI:SS'),
            id_place        = CAST((NEW.item->>0)::json #>> '{place,@id}' AS INTEGER),
            place           = (NEW.item->>0)::json #>> '{place,name}',
            municipality    = (NEW.item->>0)::json #>> '{place,municipality}',
            county          = (NEW.item->>0)::json #>> '{place,county}',
            country         = (NEW.item->>0)::json #>> '{place,country}',
            insee           = (NEW.item->>0)::json #>> '{place,insee}',
            coord_lat       = CAST((((NEW.item->>0)::json -> 'observers') -> 0) ->> 'coord_lat' AS FLOAT),
            coord_lon       = CAST((((NEW.item->>0)::json -> 'observers') -> 0) ->> 'coord_lon' AS FLOAT),
            coord_x_l93     = CAST((((NEW.item->>0)::json -> 'observers') -> 0) ->> 'coord_x_l93' AS FLOAT),
            coord_y_l93     = CAST((((NEW.item->>0)::json -> 'observers') -> 0) ->> 'coord_y_l93' AS FLOAT),
            precision       = (((NEW.item->>0)::json -> 'observers') -> 0) ->> 'precision',
            atlas_grid_name = (((NEW.item->>0)::json -> 'observers') -> 0) ->> 'atlas_grid_name',
            estimation_code = (((NEW.item->>0)::json -> 'observers') -> 0) ->> 'estimation_code',
            count           = CAST((((NEW.item->>0)::json -> 'observers') -> 0) ->> 'count' AS INTEGER),
            atlas_code      = CAST((((NEW.item->>0)::json -> 'observers') -> 0) #>> '{atlas_code,#text}' AS INTEGER),
            altitude        = CAST((((NEW.item->>0)::json -> 'observers') -> 0) ->> 'altitude' AS INTEGER),
            project_code    = (((NEW.item->>0)::json -> 'observers') -> 0) ->> 'project_code',
            hidden          = (((NEW.item->>0)::json -> 'observers') -> 0) ->> 'hidden',
            admin_hidden    = (((NEW.item->>0)::json -> 'observers') -> 0) ->> 'admin_hidden',
            name            = (((NEW.item->>0)::json -> 'observers') -> 0) ->> 'name',
            anonymous       = (((NEW.item->>0)::json -> 'observers') -> 0) ->> 'anonymous',
            entity          = (((NEW.item->>0)::json -> 'observers') -> 0) ->> 'entity',
            details         = (((NEW.item->>0)::json -> 'observers') -> 0) ->> 'details',
            comment         = (((NEW.item->>0)::json -> 'observers') -> 0) ->> 'comment',
            hidden_comment  = (((NEW.item->>0)::json -> 'observers') -> 0) ->> 'hidden_comment',
            mortality       = ((((NEW.item->>0)::json -> 'observers'::text) -> 0) #>> '{extended_info,mortality}'::text []) is not null,
            death_cause2    = (((NEW.item->>0)::json -> 'observers') -> 0) #>> '{extended_info, mortality, death_cause2}',
            insert_date     = to_timestamp((((NEW.item->>0)::json -> 'observers') -> 0) #>> '{insert_date,@ISO8601}', 'YYYY-MM-DD"T"HH24:MI:SS'),
            update_date     = to_timestamp((((NEW.item->>0)::json -> 'observers') -> 0) #>> '{update_date,@ISO8601}', 'YYYY-MM-DD"T"HH24:MI:SS')
        WHERE id_sighting = OLD.id AND site = OLD.site ;
        IF NOT FOUND THEN
            RETURN NULL;
        END IF;
        RETURN NEW;

    ELSIF (TG_OP = 'INSERT') THEN
        /* Inserting data on src_vn.observations when raw data is inserted */
        INSERT INTO src_vn.observations (site, id_sighting, pseudo_id_sighting, id_universal, id_species, french_name, latin_name,
                                         date, date_year, timing, id_place, place, municipality, county, country, insee,
                                         coord_lat, coord_lon, coord_x_l93, coord_y_l93, precision, atlas_grid_name, estimation_code,
                                         count, atlas_code, altitude, project_code, hidden, admin_hidden, name, anonymous, entity, details, 
                                         comment, hidden_comment, mortality, death_cause2, insert_date, update_date)
        VALUES (
            NEW.site,
            NEW.id,
            encode(hmac(NEW.id::text, '8Zz9C*%I*gY&eM*Ei', 'sha1'), 'hex'),
            (((NEW.item->>0)::json -> 'observers') -> 0) ->> 'id_universal',
            CAST((NEW.item->>0)::json #>> '{species,@id}' AS INTEGER),
            (NEW.item->>0)::json #>> '{species,name}',
            (NEW.item->>0)::json #>> '{species,latin_name}',
            to_date((NEW.item->>0)::json #>> '{date,@ISO8601}', 'YYYY-MM-DD'),
            CAST(extract(year from to_date((NEW.item->>0)::json #>> '{date,@ISO8601}', 'YYYY-MM-DD')) AS INTEGER),
            -- Missing time_start & time_stop
            to_timestamp((((NEW.item->>0)::json -> 'observers') -> 0) #>> '{timing,@ISO8601}', 'YYYY-MM-DD"T"HH24:MI:SS'),
            CAST((NEW.item->>0)::json #>> '{place,@id}' AS INTEGER),
            (NEW.item->>0)::json #>> '{place,name}',
            (NEW.item->>0)::json #>> '{place,municipality}',
            (NEW.item->>0)::json #>> '{place,county}',
            (NEW.item->>0)::json #>> '{place,country}',
            (NEW.item->>0)::json #>> '{place,insee}',
            CAST((((NEW.item->>0)::json -> 'observers') -> 0) ->> 'coord_lat' AS FLOAT),
            CAST((((NEW.item->>0)::json -> 'observers') -> 0) ->> 'coord_lon' AS FLOAT),
            CAST((((NEW.item->>0)::json -> 'observers') -> 0) ->> 'coord_x_l93' AS FLOAT),
            CAST((((NEW.item->>0)::json -> 'observers') -> 0) ->> 'coord_y_l93' AS FLOAT),
            (((NEW.item->>0)::json -> 'observers') -> 0) ->> 'precision',
            (((NEW.item->>0)::json -> 'observers') -> 0) ->> 'atlas_grid_name',
            (((NEW.item->>0)::json -> 'observers') -> 0) ->> 'estimation_code',
            CAST((((NEW.item->>0)::json -> 'observers') -> 0) ->> 'count' AS INTEGER),
            CAST((((NEW.item->>0)::json -> 'observers') -> 0) #>> '{atlas_code,#text}' AS INTEGER),
            CAST((((NEW.item->>0)::json -> 'observers') -> 0) ->> 'altitude' AS INTEGER),
            (((NEW.item->>0)::json -> 'observers') -> 0) ->> 'project_code',
            (((NEW.item->>0)::json -> 'observers') -> 0) ->> 'hidden',
            (((NEW.item->>0)::json -> 'observers') -> 0) ->> 'admin_hidden',
            (((NEW.item->>0)::json -> 'observers') -> 0) ->> 'name',
            (((NEW.item->>0)::json -> 'observers') -> 0) ->> 'anonymous',
            (((NEW.item->>0)::json -> 'observers') -> 0) ->> 'entity',
            (((NEW.item->>0)::json -> 'observers') -> 0) ->> 'details',
            (((NEW.item->>0)::json -> 'observers') -> 0) ->> 'comment',
            (((NEW.item->>0)::json -> 'observers') -> 0) ->> 'hidden_comment',
            ((((NEW.item->>0)::json -> 'observers' :: text) -> 0) #>> '{extended_info,mortality}' :: text []) is not null,
            (((NEW.item->>0)::json -> 'observers') -> 0) #>> '{extended_info, mortality, death_cause2}',
            to_timestamp((((NEW.item->>0)::json -> 'observers') -> 0) #>> '{insert_date,@ISO8601}', 'YYYY-MM-DD"T"HH24:MI:SS'),
            to_timestamp((((NEW.item->>0)::json -> 'observers') -> 0) #>> '{update_date,@ISO8601}', 'YYYY-MM-DD"T"HH24:MI:SS'));
        RETURN NEW;
    END IF;
END;
\$\$
LANGUAGE plpgsql
;

DROP TRIGGER IF EXISTS observation_trigger ON $(evn_db_schema_import).observations_json;
CREATE TRIGGER observation_trigger
AFTER INSERT OR UPDATE OR DELETE ON $(evn_db_schema_import).observations_json
    FOR EACH ROW EXECUTE FUNCTION update_vn_sights();
