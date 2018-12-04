
-- Create or update indexes, template for pyexpander3
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

\c $(evn_db_name)
SET search_path TO $(evn_db_schema),public,topology;

-- Indexes on $(evn_db_schema).observations;
REFRESH MATERIALIZED VIEW $(evn_db_schema).observations WITH DATA;

ALTER TABLE $(evn_db_schema).observations_json DROP CONSTRAINT IF EXISTS observations_pkey;
ALTER TABLE $(evn_db_schema).observations_json ADD PRIMARY KEY (id_sighting);

-- Indexes on $(evn_db_schema).observations;
DROP INDEX IF EXISTS $(evn_db_schema).observations_idx_id_sighting;
CREATE INDEX observations_idx_id_sighting
    ON $(evn_db_schema).observations USING btree
    (id_sighting)
    TABLESPACE pg_default;

DROP INDEX IF EXISTS $(evn_db_schema).observations_idx_date_year;
CREATE INDEX observations_idx_date_year
    ON $(evn_db_schema).observations USING btree
    (date_year)
    TABLESPACE pg_default;

DROP INDEX IF EXISTS $(evn_db_schema).observations_idx_id_species;
CREATE INDEX observations_idx_id_species
    ON $(evn_db_schema).observations USING btree
    (id_species)
    TABLESPACE pg_default;

DROP INDEX IF EXISTS $(evn_db_schema).observations_idx_french_name;
CREATE INDEX observations_idx_french_name
    ON $(evn_db_schema).observations USING btree
    (french_name COLLATE pg_catalog."default" varchar_pattern_ops)
    TABLESPACE pg_default;

DROP INDEX IF EXISTS $(evn_db_schema).observations_idx_latin_name;
CREATE INDEX observations_idx_latin_name
    ON $(evn_db_schema).observations USING btree
    (latin_name COLLATE pg_catalog."default" varchar_pattern_ops)
    TABLESPACE pg_default;

DROP INDEX IF EXISTS $(evn_db_schema).observations_idx_place;
CREATE INDEX observations_idx_place
    ON $(evn_db_schema).observations USING btree
    (place COLLATE pg_catalog."default" varchar_pattern_ops)
    TABLESPACE pg_default;

DROP INDEX IF EXISTS $(evn_db_schema).observations_idx_the_geom;
CREATE INDEX observations_idx_the_geom
    ON $(evn_db_schema).observations USING spgist
    (the_geom)
    TABLESPACE pg_default;

-- Indexes on $(evn_db_schema).species;
REFRESH MATERIALIZED VIEW $(evn_db_schema).species WITH DATA;

DROP INDEX IF EXISTS $(evn_db_schema).species_idx_id_specie;
CREATE UNIQUE INDEX species_idx_id_specie
    ON $(evn_db_schema).species USING btree
    (id_specie)
    TABLESPACE pg_default;

-- Indexes on $(evn_db_schema).local_admin_units;
REFRESH MATERIALIZED VIEW $(evn_db_schema).local_admin_units WITH DATA;

DROP INDEX IF EXISTS $(evn_db_schema).local_admin_units_idx_id_local_admin_unit;
CREATE UNIQUE INDEX local_admin_units_idx_id_local_admin_unit
    ON $(evn_db_schema).local_admin_units USING btree
    (id_local_admin_unit)
    TABLESPACE pg_default;

-- Indexes on $(evn_db_schema).places;
REFRESH MATERIALIZED VIEW $(evn_db_schema).places WITH DATA;

DROP INDEX IF EXISTS $(evn_db_schema).places_idx_id_place;
CREATE UNIQUE INDEX places_idx_id_place
    ON $(evn_db_schema).places USING btree
    (id_place)
    TABLESPACE pg_default;

DROP INDEX IF EXISTS $(evn_db_schema).places_idx_the_geom;
CREATE INDEX places_idx_the_geom
    ON $(evn_db_schema).places USING spgist
    (the_geom)
    TABLESPACE pg_default;
