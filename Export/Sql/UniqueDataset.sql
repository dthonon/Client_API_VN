create extension if not exists "uuid-ossp"
;

create schema if not exists src_vn
;

drop table if exists src_vn.observations
;



create table src_vn.observations (
  id              serial primary key,
  uuid            uuid default uuid_generate_v4(
  ),
  id_sighting     integer
  ,
  id_universal    varchar(200)
  ,
  id_species      integer
  ,
  french_name     varchar(150
                  )
  ,
  latin_name      varchar(150
                  )
  ,
  tdate           date
  ,
  date_year       integer
  , -- Missing time_start & time_stop
  timing          timestamp
  ,
  id_place        integer
  ,
  place           varchar(150
                  )
  ,
  municipality    varchar(150
                  )
  ,
  county          varchar(150
                  )
  ,
  country         varchar(100
                  )
  ,
  insee           char(5
                  )
  , -- cast(((observations_json.sightings -> 'observers') -> 0) ->> 'coord_lat' AS double precision) AS coord_lat,
  coord_lat       float
  ,
  coord_lon       float
  ,
  coord_x_l93     integer
  ,
  coord_y_l93     integer
  ,
  precision       varchar(100
                  )
  ,
  atlas_grid_name varchar(50
                  )
  ,
  estimation_code varchar(100
                  )
  ,
  count           integer
  ,
  atlas_code      integer
  ,
  altitude        integer
  ,
  hidden          varchar(50
                  )
  ,
  admin_hidden    varchar(50
                  )
  ,
  name            varchar(100
                  )
  ,
  anonymous       varchar(50
                  )
  ,
  entity          varchar(50
                  )
  ,
  details         text
  ,
  comment         text
  ,
  hidden_comment  text
  ,
  mortality       text
  ,
  death_cause2    varchar(100)
  ,
  insert_date     timestamp
  ,
  update_date     timestamp
  ,
  geom            geometry(point, 2154)
  ,
  src             varchar(50)
)
;

insert into src_vn.observations (id_sighting, id_universal, id_species, french_name, latin_name, tdate, date_year, timing, id_place, place, municipality, county, country, insee, coord_lat, coord_lon, coord_x_l93, coord_y_l93, precision, atlas_grid_name, estimation_code, count, atlas_code, altitude, hidden, admin_hidden, name, anonymous, entity, details, comment, hidden_comment, mortality, death_cause2, insert_date, update_date, geom, src)
  select
      id_sighting                                                                                        as id_sighting
    , ((sightings -> 'observers') -> 0) ->> 'id_universal'                                               as id_universal
    , cast(sightings #>> '{species,@id}' as integer)                                                     as id_species
    , sightings #>> '{species,name}'                                                                     as french_name
    , sightings #>> '{species,latin_name}'                                                               as latin_name
    , to_date(sightings #>> '{date,@ISO8601}', 'YYYY-MM-DD')                                             as date
    , cast(extract(year from
                   to_date(sightings #>> '{date,@ISO8601}', 'YYYY-MM-DD'))
           as integer)                                                                                   as date_year
    , -- Missing time_start & time_stop
      to_timestamp(((sightings -> 'observers') -> 0) #>> '{timing,@ISO8601}', 'YYYY-MM-DD"T"HH24:MI:SS')
                                                                                                         as timing
    , cast(sightings #>> '{place,@id}' as integer)                                                       as id_place
    , sightings #>> '{place,name}'                                                                       as place
    , sightings #>> '{place,municipality}'                                                               as municipality
    , sightings #>> '{place,county}'                                                                     as county
    , sightings #>> '{place,country}'                                                                    as country
    , sightings #>> '{place,insee}'                                                                      as insee
    , -- cast(((observations_json.sightings -> 'observers') -> 0) ->> 'coord_lat' AS double precision) AS coord_lat,
      coord_lat                                                                                          as coord_lat
    , coord_lon                                                                                          as coord_lon
    , ST_X(the_geom)                                                                                     as coord_x_l93
    , ST_Y(the_geom)                                                                                     as coord_y_l93
    , ((sightings -> 'observers') -> 0) ->> 'precision'                                                  as precision
    , ((sightings -> 'observers') -> 0) ->>
      'atlas_grid_name'                                                                                  as atlas_grid_name
    , ((sightings -> 'observers') -> 0) ->>
      'estimation_code'                                                                                  as estimation_code
    , cast(((sightings -> 'observers') -> 0) ->> 'count' as integer)                                     as count
    , cast(((sightings -> 'observers') -> 0) #>> '{atlas_code,#text}' as integer)                        as atlas_code
    , cast(((sightings -> 'observers') -> 0) ->> 'altitude' as integer)                                  as altitude
    , ((sightings -> 'observers') -> 0) ->> 'hidden'                                                     as hidden
    , ((sightings -> 'observers') -> 0) ->> 'admin_hidden'                                               as admin_hidden
    , ((sightings -> 'observers') -> 0) ->> 'name'                                                       as name
    , ((sightings -> 'observers') -> 0) ->> 'anonymous'                                                  as anonymous
    , ((sightings -> 'observers') -> 0) ->> 'entity'                                                     as entity
    , ((sightings -> 'observers') -> 0) ->> 'details'                                                    as details
    , ((sightings -> 'observers') -> 0) ->> 'comment'                                                    as comment
    , ((sightings -> 'observers') -> 0) ->>
      'hidden_comment'                                                                                   as hidden_comment
    , (((sightings -> 'observers' :: text) -> 0) #>> '{extended_info,mortality}' :: text []) is not null as mortality
    , ((sightings -> 'observers') -> 0) #>> '{extended_info, mortality, death_cause2}'                   as death_cause2
    , to_timestamp(((sightings -> 'observers') -> 0) #>> '{insert_date,@ISO8601}', 'YYYY-MM-DD"T"HH24:MI:SS')
                                                                                                         as insert_date
    , to_timestamp(((sightings -> 'observers') -> 0) #>> '{update_date,@ISO8601}', 'YYYY-MM-DD"T"HH24:MI:SS')
                                                                                                         as update_date
    , the_geom                                                                                           as the_geom
    , 'lpoauv'                                                                                           as src

  from vn_auv.observations_json
;

create or replace function update_vn_sights()
  returns trigger as $$
begin
  --
  -- Perform the required operation on emp, and create a row in emp_audit
  -- to reflect the change made to emp.
  --
  if (TG_OP = 'DELETE')
  then
    delete from src_vn.observations
    where id_universal = ((OLD.sightings -> 'observers') -> 0) ->> 'id_universal'
    ;

    if not FOUND
    then return null
      ; end if
    ;

    return OLD
    ;
  elsif (TG_OP = 'UPDATE')
    then
      update src_vn.observations
      set
        id_species        = cast(NEW.sightings #>> '{species,@id}' as integer),
        french_name       = NEW.sightings #>> '{species,name}',
        latin_name        = NEW.sightings #>> '{species,latin_name}',
        "date"            = to_date(NEW.sightings #>> '{date,@ISO8601}', 'YYYY-MM-DD'),
        date_year         = cast(extract(year from
                                         to_date(NEW.sightings #>> '{date,@ISO8601}', 'YYYY-MM-DD'))
                                 as integer),
        timing            = to_timestamp(((NEW.sightings -> 'observers') -> 0) #>> '{timing,@ISO8601}',
                                         'YYYY-MM-DD"T"HH24:MI:SS')
        , id_place        = cast(NEW.sightings #>> '{place,@id}' as integer)
        , place           = NEW.sightings #>> '{place,name}'
        , municipality    = NEW.sightings #>> '{place,municipality}'
        , county          = NEW.sightings #>> '{place,county}'
        , country         = NEW.sightings #>> '{place,country}'
        , insee           = NEW.sightings #>> '{place,insee}'
        -- cast(((observations_json.sightings -> 'observers') -> 0) ->> 'coord_lat' AS double precision) AS coord_lat,
        , coord_lat       = NEW.coord_lat
        , coord_lon       = NEW.coord_lon
        , coord_x_l93     = ST_X(NEW.the_geom)
        , coord_y_l93     = ST_Y(NEW.the_geom)
        , precision       = ((NEW.sightings -> 'observers') -> 0) ->> 'precision'
        , atlas_grid_name = ((NEW.sightings -> 'observers') -> 0) ->> 'atlas_grid_name'
        , estimation_code = ((NEW.sightings -> 'observers') -> 0) ->> 'estimation_code'
        , count           = cast(((NEW.sightings -> 'observers') -> 0) ->> 'count' as integer)
        , atlas_code      = cast(((NEW.sightings -> 'observers') -> 0) #>> '{atlas_code,#text}' as integer)
        , altitude        = cast(((NEW.sightings -> 'observers') -> 0) ->> 'altitude' as integer)
        , hidden          = ((NEW.sightings -> 'observers') -> 0) ->> 'hidden'
        , admin_hidden    = ((NEW.sightings -> 'observers') -> 0) ->> 'admin_hidden'
        , name            = ((NEW.sightings -> 'observers') -> 0) ->> 'name'
        , anonymous       = ((NEW.sightings -> 'observers') -> 0) ->> 'anonymous'
        , entity          = ((NEW.sightings -> 'observers') -> 0) ->> 'entity'
        , details         = ((NEW.sightings -> 'observers') -> 0) ->> 'details'
        , comment         = ((NEW.sightings -> 'observers') -> 0) ->> 'comment'
        , hidden_comment  = ((NEW.sightings -> 'observers') -> 0) ->>
                            'hidden_comment'
        , mortality       = (((NEW.sightings -> 'observers' :: text) -> 0) #>> '{extended_info,mortality}' :: text [])
                            is not null
        , death_cause2    = ((NEW.sightings -> 'observers') -> 0) #>> '{extended_info, mortality, death_cause2}'
        , insert_date     = to_timestamp(((NEW.sightings -> 'observers') -> 0) #>> '{insert_date,@ISO8601}',
                                         'YYYY-MM-DD"T"HH24:MI:SS')
        , update_date     = to_timestamp(((NEW.sightings -> 'observers') -> 0) #>> '{update_date,@ISO8601}',
                                         'YYYY-MM-DD"T"HH24:MI:SS')
        , geom            = NEW.the_geom
      where id_universal = ((OLD.sightings -> 'observers') -> 0) ->> 'id_universal'
      ;

      if not FOUND
      then return null
        ; end if
      ;

      return NEW
      ;
  elsif (TG_OP = 'INSERT')
    then
      insert into src_vn.observations (id_sighting, id_universal, id_species, french_name, latin_name, tdate, date_year, timing, id_place, place, municipality, county, country, insee, coord_lat, coord_lon, coord_x_l93, coord_y_l93, precision, atlas_grid_name, estimation_code, count, atlas_code, altitude, hidden, admin_hidden, name, anonymous, entity, details, comment, hidden_comment, mortality, death_cause2, insert_date, update_date, geom)
      values (
        NEW.id_sighting
        , ((NEW.sightings -> 'observers') -> 0) ->>
          'id_universal'
        , cast(NEW.sightings #>> '{species,@id}' as
               integer)
        , NEW.sightings #>>
          '{species,name}'
        , NEW.sightings #>>
          '{species,latin_name}'
        , to_date(NEW.sightings #>> '{date,@ISO8601}', 'YYYY-MM-DD')
        , cast(extract(year from
                       to_date(NEW.sightings #>> '{date,@ISO8601}', 'YYYY-MM-DD'))
               as
               integer)
        , -- Missing time_start & time_stop
          to_timestamp(((NEW.sightings -> 'observers') -> 0) #>> '{timing,@ISO8601}', 'YYYY-MM-DD"T"HH24:MI:SS')

        , cast(NEW.sightings #>> '{place,@id}' as
               integer)
        , NEW.sightings #>> '{place,name}'
        , NEW.sightings #>>
          '{place,municipality}'
        , NEW.sightings #>> '{place,county}'
        , NEW.sightings #>>
          '{place,country}'
        , NEW.sightings #>> '{place,insee}'
        ,
          -- cast(((observations_json.NEW.sightings -> 'observers') -> 0) ->> 'coord_lat' AS double precision) AS coord_lat,
          NEW.coord_lat
        ,
          NEW.coord_lon
        , ST_X(
              NEW.the_geom)
        , ST_Y(
              NEW.the_geom)
        , ((NEW.sightings -> 'observers') -> 0) ->>
          'precision'
        , ((NEW.sightings -> 'observers') -> 0) ->>
          'atlas_grid_name'
        , ((NEW.sightings -> 'observers') -> 0) ->>
          'estimation_code'
        , cast(((NEW.sightings -> 'observers') -> 0) ->> 'count' as integer)
        , cast(((NEW.sightings -> 'observers') -> 0) #>> '{atlas_code,#text}' as
               integer)
        , cast(((NEW.sightings -> 'observers') -> 0) ->> 'altitude' as
               integer)
        , ((NEW.sightings -> 'observers') -> 0) ->> 'hidden'
        , ((NEW.sightings -> 'observers') -> 0) ->>
          'admin_hidden'
        , ((NEW.sightings -> 'observers') -> 0) ->> 'name'
        , ((NEW.sightings -> 'observers') -> 0) ->>
          'anonymous'
        , ((NEW.sightings -> 'observers') -> 0) ->> 'entity'
        , ((NEW.sightings -> 'observers') -> 0) ->>
          'details'
        , ((NEW.sightings -> 'observers') -> 0) ->>
          'comment'
        , ((NEW.sightings -> 'observers') -> 0) ->>
          'hidden_comment'
        , (((NEW.sightings -> 'observers' :: text) -> 0) #>> '{extended_info,mortality}' :: text []) is not
          null
        , ((NEW.sightings -> 'observers') -> 0) #>>
          '{extended_info, mortality, death_cause2}'
        , to_timestamp(((NEW.sightings -> 'observers') -> 0) #>> '{insert_date,@ISO8601}', 'YYYY-MM-DD"T"HH24:MI:SS')
        , to_timestamp(((NEW.sightings -> 'observers') -> 0) #>> '{update_date,@ISO8601}', 'YYYY-MM-DD"T"HH24:MI:SS')
        ,
        NEW.the_geom)
      ;

      return NEW
      ;
  end if
  ;

end
;
$$
language plpgsql
;
--
-- create trigger auv_obs
--   After insert or update or delete
--   on observations_json
--   for each row execute procedure update_vn_sights()
-- ;
