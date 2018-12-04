
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

-- Create tables, template for pyexpander3
--  - observations_json is loaded with id, json, coordinates and then other columns are created by json queries
--  - species_json is loaded with id, json and then other columns are created by json queries
--  - places_json is loaded with id, json, coordinates and then other columns are created by json queries

\c $(evn_db_name)
SET search_path TO $(evn_db_schema),public,topology;

-- Trigger function to add or update geometry
CREATE OR REPLACE FUNCTION update_geom_triggerfn()
RETURNS trigger AS \$body\$
    BEGIN
    NEW.the_geom := ST_Transform(ST_SetSRID(ST_MakePoint(NEW.coord_lon, NEW.coord_lat), 4326), 2154);
    RETURN NEW;
    END;
\$body\$ LANGUAGE plpgsql;

-- Observations table in json format
-- Delete existing table
DROP TABLE IF EXISTS observations_json CASCADE;

-- Create observations table and access rights
CREATE TABLE observations_json (
    id_sighting integer,
    sightings jsonb,   -- Complete json as downloaded
    update_ts integer,  -- Last update of json data timestamp
    coord_lat double precision, -- WGS84 coordinates
    coord_lon double precision
);
-- Add geometry column
\o /dev/null
SELECT AddGeometryColumn('observations_json', 'the_geom', 2154, 'POINT', 2);
\o

-- Add trigger
DROP TRIGGER IF EXISTS trg_geom ON observations_json ;
CREATE TRIGGER trg_geom BEFORE INSERT or UPDATE
    ON observations_json FOR EACH ROW
    EXECUTE PROCEDURE update_geom_triggerfn();

DROP TRIGGER IF EXISTS sights_to_dataset ON observations_json ;
create trigger sights_to_dataset
  After insert or update or delete
  on observations_json
  for each row execute procedure update_vn_sights()
;

-- Species table in json format
-- Delete existing table
DROP TABLE IF EXISTS species_json CASCADE;

-- Create observations table and access rights
CREATE TABLE species_json (
    id_specie integer PRIMARY KEY,
    specie jsonb   -- Complete json as downloaded
);

-- Taxo_groups table in json format
-- Delete existing table
DROP TABLE IF EXISTS taxo_groups_json CASCADE;

-- Create observations table and access rights
CREATE TABLE taxo_groups_json (
    id_taxo_group integer PRIMARY KEY,
    taxo_group jsonb   -- Complete json as downloaded
);

-- local_admin_units table in json format
-- Delete existing table
DROP TABLE IF EXISTS local_admin_units_json CASCADE;

-- Create local_admin_units table and access rights
CREATE TABLE local_admin_units_json (
    id_local_admin_unit integer PRIMARY KEY,
    local_admin_unit jsonb,   -- Complete json as downloaded
    coord_lat double precision, -- WGS84 coordinates
    coord_lon double precision
);
-- Add geometry column
\o /dev/null
SELECT AddGeometryColumn('local_admin_units_json', 'the_geom', 2154, 'POINT', 2);
\o

-- Add trigger
DROP TRIGGER IF EXISTS trg_geom ON local_admin_units_json ;
CREATE TRIGGER trg_geom BEFORE INSERT or UPDATE
    ON local_admin_units_json FOR EACH ROW
    EXECUTE PROCEDURE update_geom_triggerfn();

-- Places table in json format
-- Delete existing table
DROP TABLE IF EXISTS places_json CASCADE;

-- Create places table and access rights
CREATE TABLE places_json (
    id_place integer PRIMARY KEY,
    place jsonb,   -- Complete json as downloaded
    coord_lat double precision, -- WGS84 coordinates
    coord_lon double precision
);
-- Add geometry column
\o /dev/null
SELECT AddGeometryColumn('places_json', 'the_geom', 2154, 'POINT', 2);
\o

-- Add trigger
DROP TRIGGER IF EXISTS trg_geom ON places_json ;
CREATE TRIGGER trg_geom BEFORE INSERT or UPDATE
    ON places_json FOR EACH ROW
    EXECUTE PROCEDURE update_geom_triggerfn();
