
-- Create views, template for pyexpander3
--  - observations, with selected fields from obs_json

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

$py(
import configparser
from pathlib import Path
# Read configuration parameters
config = configparser.ConfigParser()
config.read(str(Path.home()) + '/.evn.ini')

# Import parameters in local variables
evn_db_name = config['database']['evn_db_name']
evn_db_schema = config['database']['evn_db_schema']
evn_db_group = config['database']['evn_db_group']
evn_db_user = config['database']['evn_db_user']
evn_db_pw = config['database']['evn_db_pw']
)

\c $(evn_db_name)
SET search_path TO $(evn_db_schema),public,topology;

-- Delete existing table
DROP MATERIALIZED VIEW IF EXISTS $(evn_db_schema).observations CASCADE;

CREATE MATERIALIZED VIEW $(evn_db_schema).observations
TABLESPACE pg_default
AS
 SELECT obs_json.id_sighting,
    obs_json.sightings #>> '{species,@id}'::text[] AS id_species,
    obs_json.sightings #>> '{species,name}'::text[] AS name_species,
    obs_json.sightings #>> '{species,latin_name}'::text[] AS latin_species,
    to_date(obs_json.sightings #>> '{date,@ISO8601}'::text[], 'YYYY-MM-DD'::text) AS date,
    ((obs_json.sightings -> 'observers'::text) -> 0) ->> 'name'::text AS name,
    obs_json.sightings #>> '{place,@id}'::text[] AS id_place,
    obs_json.sightings #>> '{place,name}'::text[] AS place,
    obs_json.sightings #>> '{place,municipality}'::text[] AS municipality
   FROM import.obs_json
WITH DATA;
