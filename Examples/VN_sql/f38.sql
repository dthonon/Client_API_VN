
-- Create local views for faune-isere.org, template for pyexpander3
--  - nature-isere.fr views

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
SET search_path TO public;


-- Delete and create nature_isere role 
DROP OWNED BY nature_isere;
DROP ROLE IF EXISTS nature_isere;
CREATE ROLE nature_isere LOGIN PASSWORD 'o57TED5Ugqft';

-- View: public.espece_nature_isere 
CREATE OR REPLACE VIEW public.espece_nature_isere AS
    SELECT species.id_specie AS id_species,
        species.french_name AS name,
        species.french_name_plur AS name_plural,
        species.latin_name AS name_latin,
        species.sempach_id_family AS family,
        species.category_1 AS category,
        species.rarity AS rarity
    FROM $(evn_db_schema).species
    WHERE species.is_used::text ~~ '1'::text;

ALTER TABLE public.espece_nature_isere
    OWNER TO lpo_isere;

GRANT SELECT ON TABLE public.espece_nature_isere TO nature_isere;
GRANT ALL ON TABLE public.espece_nature_isere TO lpo_isere;

-- View: public.espece_nature_isere
CREATE OR REPLACE VIEW public.lieu_nature_isere AS
    SELECT places.id_place AS id,
        places.name AS nom,
        places.coord_lat AS latitude__d_d_,
        places.coord_lon AS longitude__d_d_,
        places.coord_x_l93 AS lambert_93_e__m_,
        places.coord_y_l93 AS lambert_93_n__m_,
        places.altitude AS altitude,
        places.visible AS visible,
        local_admin_units.insee AS insee,
        local_admin_units.name AS commune
    FROM $(evn_db_schema).places, $(evn_db_schema).local_admin_units
    WHERE local_admin_units.id_local_admin_unit = places.id_commune;

ALTER TABLE public.lieu_nature_isere
    OWNER TO lpo_isere;

GRANT SELECT ON TABLE public.lieu_nature_isere TO nature_isere;
GRANT ALL ON TABLE public.lieu_nature_isere TO lpo_isere;

-- View: public.espece_nature_isere
CREATE OR REPLACE VIEW public.obs_nature_isere AS
    SELECT observations.id_sighting AS id_sighting,
        observations.french_name AS name_species,
        observations.latin_name AS latin_species,
        tabesp.cdnom_taxref AS "CD_REF",
        observations.date AS date,
        observations.date_year AS date_year,
            CASE
                WHEN observations.hidden IS NULL THEN observations.place
                ELSE observations.atlas_grid_name
            END AS place,
        observations.municipality AS municipality,
        observations.insee AS insee,
        observations.atlas_grid_name AS grid_name,
        observations.estimation_code AS estimation_code,
        observations.count AS total_count,
        observations.details AS detail,
        observations.atlas_code AS atlas_code,
        observations.altitude AS altitude,
        observations.hidden AS hidden,
        observations.insert_date AS insert_date,
        observations.update_date AS update_date,
        tabx_code_atlas.code19
    FROM $(evn_db_schema).observations
        LEFT JOIN reference.tabx_code_atlas ON observations.atlas_code = tabx_code_atlas.code50
        LEFT JOIN reference.tabesp ON observations.id_species = tabesp.id_species
    WHERE ((observations.entity IS NULL) OR
           (observations.entity IN (
             SELECT nature_isere_entity.entity_short_name FROM public.nature_isere_entity)))
          AND (observations.admin_hidden IS NULL)
          AND observations.count > 0;

ALTER TABLE public.obs_nature_isere
    OWNER TO lpo_isere;

GRANT SELECT ON TABLE public.obs_nature_isere TO nature_isere;
GRANT ALL ON TABLE public.obs_nature_isere TO lpo_isere;
