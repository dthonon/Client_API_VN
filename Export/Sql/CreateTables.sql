
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
SET search_path TO $(evn_db_schema),public;

-- Entities table in json format
-- Delete existing table
DROP TABLE IF EXISTS entities_json CASCADE;
CREATE TABLE entities_json (
    id integer,
    site character varying(100),
    item jsonb,   -- Complete json as downloaded
    PRIMARY KEY (id, site)
);

-- Forms table in json format
-- Delete existing table
DROP TABLE IF EXISTS forms_json CASCADE;
CREATE TABLE forms_json (
    id integer,
    site character varying(100),
    item jsonb,   -- Complete json as extracted from observations
    PRIMARY KEY (id, site)
);

-- Observations table in json format
-- Delete existing table
DROP TABLE IF EXISTS observations_json CASCADE;
CREATE TABLE observations_json (
    id integer,
    site character varying(100),
    item jsonb,   -- Complete json as downloaded
    update_ts integer,
    PRIMARY KEY (id, site)
);

DROP TRIGGER IF EXISTS sights_to_dataset ON observations_json ;
create trigger sights_to_dataset
  After insert or update or delete
  on observations_json
  for each row execute procedure update_vn_sights()
;

-- Species table in json format
-- Delete existing table
DROP TABLE IF EXISTS species_json CASCADE;
CREATE TABLE species_json (
    id integer,
    site character varying(100),
    item jsonb,   -- Complete json as downloaded
    PRIMARY KEY (id, site)
);

-- Taxo_groups table in json format
-- Delete existing table
DROP TABLE IF EXISTS taxo_groups_json CASCADE;
CREATE TABLE taxo_groups_json (
    id integer,
    site character varying(100),
    item jsonb,   -- Complete json as downloaded
    PRIMARY KEY (id, site)
);

-- local_admin_units table in json format
-- Delete existing table
DROP TABLE IF EXISTS local_admin_units_json CASCADE;
CREATE TABLE local_admin_units_json (
    id integer,
    site character varying(100),
    item jsonb,   -- Complete json as downloaded
    PRIMARY KEY (id, site)
);

-- Places table in json format
-- Delete existing table
DROP TABLE IF EXISTS places_json CASCADE;
CREATE TABLE places_json (
    id integer,
    site character varying(100),
    item jsonb,   -- Complete json as downloaded
    PRIMARY KEY (id, site)
);

-- Territorial_units table in json format
-- Delete existing table
DROP TABLE IF EXISTS territorial_units_json CASCADE;
CREATE TABLE territorial_units_json (
    id integer,
    site character varying(100),
    item jsonb,   -- Complete json as downloaded
    PRIMARY KEY (id, site)
);
