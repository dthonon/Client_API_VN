select ((sightings -> 'observers') -> 0) ->> 'id_universal'
from vn_auv.observations_json
where id_sighting = 1779187
limit 100
;

delete from vn_auv.observations_json
where id_sighting = 1779187
;

select count(*)
from src_vn.observations
;

select *
from src_vn.observations
where id_sighting = 1779187
;

select jsonb_pretty(sightings)
from vn_auv.observations_json
where id_sighting = 1648228
;

update vn_auv.observations_json
set sightings = jsonb_set(sightings, '{observers,0,name}', '"nnnn"')
where ((sightings -> 'observers') -> 0) ->> 'id_universal' = '7_4187803'
;


truncate table src_vn.observations restart identity
;


insert into src_vn.observations (id_sighting, id_universal, id_species, french_name, latin_name, date, date_year, timing, id_place, place, municipality, county, country, insee, coord_lat, coord_lon, coord_x_l93, coord_y_l93, precision, atlas_grid_name, estimation_code, count, atlas_code, altitude, hidden, admin_hidden, name, anonymous, entity, details, comment, hidden_comment, mortality, death_cause2, insert_date, update_date, geom, src)
;
explain
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

from vn_auv.observations_json limit 10
;


insert into gn_synthese.synthese (
  unique_id_sinp,
  id_source,
  id_dataset,
  count_min,
  cd_nom,
  nom_cite,
  altitude_min,
  the_geom_4326,
  the_geom_point,
  the_geom_local,
  date_min,
  date_max,
  observers,
  comments,
  last_action)
  select
    o.uuid
    , 2
    , 3
    , count
    , cvt.taxref_id
    , taxref.lb_nom
    , altitude :: int
    , st_transform(geom, 4326)
    , st_transform(geom, 4326)
    , st_transform(geom, 2154)
    , date
    , date
    , name
    , comment
    , 'i'
  from src_vn.observations o left join src_vn.corresp_vn_taxref cvt
      on o.id_species = cvt.vn_id
    left join taxonomie.taxref
      on cvt.taxref_id = taxref.cd_nom
  where cvt.taxref_id is not null
;