-- Copyright (c) 2018 Daniel Thonon <d.thonon9@gmail.com>
-- All rights reserved.

-- Redistribution and use in source and binary forms, with or without modification,
-- are permitted provided that the following conditions are met:
-- 1. Redistributions of source code must retain the above copyright notice,
-- this list of conditions and the following disclaimer.
-- 2. Redistributions in binary form must reproduce the above copyright notice,
-- this list of conditions and the following disclaimer in the documentation and/or
-- other materials provided with the distribution.
-- 3. Neither the name of the copyright holder nor the names of its contributors
-- may be used to endorse or promote products derived from this software without
-- specific prior written permission.

-- THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 -- ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
-- WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
-- IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
-- INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
-- BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
-- OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
-- WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
-- ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
-- POSSIBILITY OF SUCH DAMAGE.

-- @license http://www.opensource.org/licenses/mit-license.html MIT License

-- Create views, template for pyexpander3
--  - observations, with selected fields from observations_json

\c $(evn_db_name)
SET search_path TO $(evn_db_schema),public,topology;

-- Observations table
-- Delete existing table
DROP MATERIALIZED VIEW IF EXISTS $(evn_db_schema).observations CASCADE;

CREATE MATERIALIZED VIEW $(evn_db_schema).observations
TABLESPACE pg_default
AS
 SELECT
    id_sighting AS id_sighting,
    cast(sightings #>> '{species,@id}' AS INTEGER) AS id_species,
    sightings #>> '{species,name}' AS french_name,
    sightings #>> '{species,latin_name}' AS latin_name,
    to_date(sightings #>> '{date,@ISO8601}', 'YYYY-MM-DD') AS date,
    cast(extract(YEAR from
      to_date(sightings #>> '{date,@ISO8601}', 'YYYY-MM-DD'))
      AS INTEGER) AS date_year,
    -- Missing time_start & time_stop
    to_timestamp(((sightings -> 'observers') -> 0) #>> '{timing,@ISO8601}', 'YYYY-MM-DD"T"HH24:MI:SS')
      AS timing,
    cast(sightings #>> '{place,@id}' AS INTEGER) AS id_place,
    sightings #>> '{place,name}' AS place,
    sightings #>> '{place,municipality}' AS municipality,
    sightings #>> '{place,county}' AS county,
    sightings #>> '{place,country}' AS country,
    sightings #>> '{place,insee}' AS insee,
    -- cast(((observations_json.sightings -> 'observers') -> 0) ->> 'coord_lat' AS double precision) AS coord_lat,
    coord_lat AS coord_lat,
    coord_lon AS coord_lon,
    ST_X(the_geom) AS coord_x_l93,
    ST_Y(the_geom) AS coord_y_l93,
    ((sightings -> 'observers') -> 0) ->> 'precision' AS precision,
    ((sightings -> 'observers') -> 0) ->> 'atlas_grid_name' AS atlas_grid_name,
    ((sightings -> 'observers') -> 0) ->> 'estimation_code' AS estimation_code,
    cast(((sightings -> 'observers') -> 0) ->> 'count' AS INTEGER) AS count,
    cast(((sightings -> 'observers') -> 0) #>> '{atlas_code,#text}' AS INTEGER) AS atlas_code,
    cast(((sightings -> 'observers') -> 0) ->> 'altitude' AS INTEGER) AS altitude,
    ((sightings -> 'observers') -> 0) ->> 'hidden' AS hidden,
    ((sightings -> 'observers') -> 0) ->> 'admin_hidden' AS admin_hidden,
    ((sightings -> 'observers') -> 0) ->> 'entity' AS entity,
    ((sightings -> 'observers') -> 0) ->> 'details' AS details,
    (((sightings -> 'observers'::text) -> 0) #>> '{extended_info,mortality}'::text[]) IS NOT NULL AS mortality,
    ((sightings -> 'observers') -> 0) #>> '{extended_info, mortality, death_cause2}' AS death_cause2,
    to_timestamp(((sightings -> 'observers') -> 0) #>> '{insert_date,@ISO8601}', 'YYYY-MM-DD"T"HH24:MI:SS')
      AS insert_date,
    to_timestamp(((sightings -> 'observers') -> 0) #>> '{update_date,@ISO8601}', 'YYYY-MM-DD"T"HH24:MI:SS')
      AS update_date,
    the_geom AS the_geom
   FROM $(evn_db_schema).observations_json
WITH DATA;


-- Species table
-- Delete existing table
DROP MATERIALIZED VIEW IF EXISTS $(evn_db_schema).species CASCADE;

CREATE MATERIALIZED VIEW $(evn_db_schema).species
TABLESPACE pg_default
AS
 SELECT
    id_specie AS id_specie,
    specie #>> '{french_name}' AS french_name,
    specie #>> '{french_name_plur}' AS french_name_plur,
    specie #>> '{latin_name}' AS latin_name,
    specie #>> '{is_used}' AS is_used,
    specie #>> '{sempach_id_family}' AS sempach_id_family,
    specie #>> '{category_1}' AS category_1,
    specie #>> '{id_taxo_group}' AS id_taxo_group,
    specie #>> '{rarity}' AS rarity,
    specie #>> '{sys_order}' AS sys_order,
    specie #>> '{atlas_start}' AS atlas_start,
    specie #>> '{atlas_end}' AS atlas_end
   FROM $(evn_db_schema).species_json
WITH DATA;

-- Local_admin_units table
-- Delete existing table
DROP MATERIALIZED VIEW IF EXISTS $(evn_db_schema).local_admin_units CASCADE;

CREATE MATERIALIZED VIEW $(evn_db_schema).local_admin_units
TABLESPACE pg_default
AS
 SELECT
    id_local_admin_unit AS id_local_admin_unit,
    local_admin_unit #>> '{name}' AS name,
    local_admin_unit #>> '{insee}' AS insee,
    local_admin_unit #>> '{coord_lat}' AS coord_lat,
    local_admin_unit #>> '{coord_lon}' AS coord_lon,
    ST_X(the_geom) AS coord_x_l93,
    ST_Y(the_geom) AS coord_y_l93,
    the_geom AS the_geom
  FROM $(evn_db_schema).local_admin_units_json
WITH DATA;

-- Places table
-- Delete existing table
DROP MATERIALIZED VIEW IF EXISTS $(evn_db_schema).places CASCADE;

CREATE MATERIALIZED VIEW $(evn_db_schema).places
TABLESPACE pg_default
AS
 SELECT
    id_place AS id_place,
    place #>> '{name}' AS name,
    place #>> '{coord_lat}' AS coord_lat,
    place #>> '{coord_lon}' AS coord_lon,
    ST_X(the_geom) AS coord_x_l93,
    ST_Y(the_geom) AS coord_y_l93,
    place #>> '{altitude}' AS altitude,
    place #>> '{visible}' AS visible,
    place #>> '{is_private}' AS is_private,
    place #>> '{place_type}' AS place_type,
    (place #>> '{id_commune}')::INTEGER AS id_commune,
    (place #>> '{id_region}')::INTEGER AS id_region,
    the_geom AS the_geom
  FROM $(evn_db_schema).places_json
WITH DATA;
