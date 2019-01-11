-- Initialize Postgresql database, template for pyexpander3
-- - Delete and create database and roles
-- - Create JSON tables

DROP SCHEMA IF EXISTS $(evn_db_schema_vn) CASCADE ;
CREATE SCHEMA $(evn_db_schema_vn);

SET search_path TO $(evn_db_schema_vn),public;

CREATE TABLE observations (
  id              SERIAL PRIMARY KEY,
  uuid            UUID DEFAULT uuid_generate_v4(),
  site            VARCHAR(50),
  id_sighting     INTEGER,
  id_universal    VARCHAR(200),
  id_species      INTEGER,
  french_name     VARCHAR(150),
  latin_name      VARCHAR(150),
  date            DATE,
  date_year       INTEGER, -- Missing time_start & time_stop
  timing          TIMESTAMP,
  id_place        INTEGER,
  place           VARCHAR(150),
  municipality    VARCHAR(150),
  county          VARCHAR(150),
  country         VARCHAR(100),
  insee           CHAR(5),
  coord_lat       FLOAT,
  coord_lon       FLOAT,
  coord_x_l93     INTEGER,
  coord_y_l93     INTEGER,
  precision       VARCHAR(100),
  atlas_grid_name VARCHAR(50),
  estimation_code VARCHAR(100),
  count           INTEGER,
  atlas_code      INTEGER,
  altitude        INTEGER,
  hidden          VARCHAR(50),
  admin_hidden    VARCHAR(50),
  name            VARCHAR(100),
  anonymous       VARCHAR(50),
  entity          VARCHAR(50),
  details         VARCHAR(10000),
  comment         VARCHAR(10000),
  hidden_comment  VARCHAR(10000),
  mortality       VARCHAR(10000),
  death_cause2    VARCHAR(100),
  insert_date     TIMESTAMP,
  update_date     TIMESTAMP,
  geom            GEOMETRY(POINT, 2154),
  src             VARCHAR(50))
;

CREATE OR REPLACE FUNCTION update_vn_sights()
  returns trigger AS \$\$
BEGIN
/*
update continously src_vn.observations table from raw json data tables after insert/update/delete events.
You just need to add this trigger to source table
*/
  if (TG_OP = 'DELETE')
  /* Deleting data on src_vn.observations when raw data is deleted */
  then
    delete from src_vn.observations
    where id_sighting = OLD.id_sighting and site=OLD.site
    ;

    if not FOUND
    then return null
      ; end if
    ;

    return OLD
    ;
  elsif (TG_OP = 'UPDATE')
  /* Updating data on src_vn.observations when raw data is updated */
    then
      UPDATE src_vn.observations
      SET
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
      WHERE id_sighting = OLD.id_sighting AND site=OLD.site ;

      if not FOUND
      then return null
        ; end if
      ;

      return NEW
      ;
  elsif (TG_OP = 'INSERT')
  /* Inserting data on src_vn.observations when raw data is inserted */
    then
      INSERT INTO src_vn.observations (site, id_sighting, id_universal, id_species, french_name, latin_name, date, date_year, timing, id_place, place, municipality, county, country, insee, coord_lat, coord_lon, coord_x_l93, coord_y_l93, precision, atlas_grid_name, estimation_code, count, atlas_code, altitude, hidden, admin_hidden, name, anonymous, entity, details, comment, hidden_comment, mortality, death_cause2, insert_date, update_date)
      VALUES (
        NEW.site,
        NEW.id,
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
        to_timestamp((((NEW.item->>0)::json -> 'observers') -> 0) #>> '{update_date,@ISO8601}', 'YYYY-MM-DD"T"HH24:MI:SS'))
      ;

      return NEW
      ;
  end if
  ;

end
;
\$\$
LANGUAGE plpgsql
;

CREATE TRIGGER my_trigger_name
  AFTER INSERT OR UPDATE OR DELETE
  ON $(evn_db_schema_import).observations_json
  FOR EACH ROW EXECUTE PROCEDURE update_vn_sights();
