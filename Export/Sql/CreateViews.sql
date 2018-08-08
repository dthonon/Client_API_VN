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
    observations_json.id_sighting AS id_sighting,
    cast(observations_json.sightings #>> '{species,@id}' AS INTEGER) AS id_species,
    observations_json.sightings #>> '{species,name}' AS name_species,
    observations_json.sightings #>> '{species,latin_name}' AS latin_species,
    to_date(observations_json.sightings #>> '{date,@ISO8601}', 'YYYY-MM-DD') AS date,
    cast(extract(YEAR from
      to_date(observations_json.sightings #>> '{date,@ISO8601}', 'YYYY-MM-DD'))
      AS INTEGER) AS date_year,
    -- Missing time_start & time_stop
    to_timestamp(((observations_json.sightings -> 'observers') -> 0) #>> '{timing,@ISO8601}', 'YYYY-MM-DD"T"HH24:MI:SS')
      AS timing,
    cast(observations_json.sightings #>> '{place,@id}'
      AS INTEGER) AS id_place,
    observations_json.sightings #>> '{place,name}' AS place,
    observations_json.sightings #>> '{place,municipality}' AS municipality,
    observations_json.sightings #>> '{place,county}' AS county,
    observations_json.sightings #>> '{place,country}' AS country,
    observations_json.sightings #>> '{place,insee}' AS insee,
    -- cast(((observations_json.sightings -> 'observers') -> 0) ->> 'coord_lat' AS double precision) AS coord_lat,
    observations_json.coord_lat AS coord_lat,
    observations_json.coord_lon AS coord_lon,
    ST_X(the_geom) AS coord_x_l93,
    ST_Y(the_geom) AS coord_y_l93,
    ((observations_json.sightings -> 'observers') -> 0) ->> 'precision' AS precision,
    ((observations_json.sightings -> 'observers') -> 0) ->> 'atlas_grid_name' AS atlas_grid_name,
    ((observations_json.sightings -> 'observers') -> 0) ->> 'estimation_code' AS estimation_code,
    ((observations_json.sightings -> 'observers') -> 0) ->> 'count' AS count,
    ((observations_json.sightings -> 'observers') -> 0) #>> '{atlas_code,#text}' AS atlas_code,
    ((observations_json.sightings -> 'observers') -> 0) ->> 'altitude' AS altitude,
    ((observations_json.sightings -> 'observers') -> 0) ->> 'hidden' AS hidden,
    ((observations_json.sightings -> 'observers') -> 0) ->> 'details' AS details,
    (((observations_json.sightings -> 'observers'::text) -> 0) #>> '{extended_info,mortality}'::text[]) IS NOT NULL AS mortality,
    ((observations_json.sightings -> 'observers') -> 0) #>> '{extended_info, mortality, death_cause2}' AS death_cause2,
    to_timestamp(((observations_json.sightings -> 'observers') -> 0) #>> '{insert_date,@ISO8601}', 'YYYY-MM-DD"T"HH24:MI:SS')
      AS insert_date,
    to_timestamp(((observations_json.sightings -> 'observers') -> 0) #>> '{update_date,@ISO8601}', 'YYYY-MM-DD"T"HH24:MI:SS')
      AS update_date,
    observations_json.the_geom AS the_geom
   FROM $(evn_db_schema).observations_json
WITH DATA;


-- Species table
-- Delete existing table
DROP MATERIALIZED VIEW IF EXISTS $(evn_db_schema).species CASCADE;

CREATE MATERIALIZED VIEW $(evn_db_schema).species
TABLESPACE pg_default
AS
 SELECT
    species_json.id_specie AS id_specie,
    species_json.specie #>> '{french_name}' AS french_name
   FROM $(evn_db_schema).species_json
WITH DATA;

-- Places table
-- Delete existing table
DROP MATERIALIZED VIEW IF EXISTS $(evn_db_schema).placees CASCADE;

CREATE MATERIALIZED VIEW $(evn_db_schema).places
TABLESPACE pg_default
AS
 SELECT
    places_json.id_place AS id_place,
    places_json.place #>> '{name}' AS name,
    places_json.place #>> '{coord_lat}' AS coord_lat,
    places_json.place #>> '{coord_lon}' AS coord_lon,
    ST_X(the_geom) AS coord_x_l93,
    ST_Y(the_geom) AS coord_y_l93,
    places_json.place #>> '{altitude}' AS altitude,
    places_json.place #>> '{visible}' AS visible,
    places_json.place #>> '{is_private}' AS is_private,
    places_json.place #>> '{place_type}' AS place_type
  FROM $(evn_db_schema).places_json
WITH DATA;
