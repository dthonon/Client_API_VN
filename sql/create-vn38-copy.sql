DROP EXTENSION IF EXISTS postgres_fdw CASCADE;
DROP SERVER IF EXISTS aura_server CASCADE;
DROP USER MAPPING IF EXISTS FOR xfer38 SERVER aura_server;

CREATE EXTENSION IF NOT EXISTS postgres_fdw;

CREATE SERVER aura_server
    FOREIGN DATA WRAPPER postgres_fdw
    OPTIONS (host 'geonature.fauneauvergnerhonealpes.org', port '5432', dbname 'gnlpoaura');
ALTER SERVER aura_server
    OWNER TO postgres;

CREATE USER MAPPING FOR xfer38 SERVER aura_server
    OPTIONS ("user" 'dthonon', password 'zh$4zJv4tq');

DROP SCHEMA IF EXISTS src_vn_copy ;
CREATE SCHEMA src_vn_copy
    AUTHORIZATION lpo_isere;

IMPORT FOREIGN SCHEMA src_vn
    FROM SERVER aura_server INTO src_vn_copy;

DROP MATERIALIZED VIEW IF EXISTS src_vn_copy.mv_local_admin_units;
CREATE MATERIALIZED VIEW src_vn_copy.mv_local_admin_units
    AS SELECT *
        FROM src_vn_copy.local_admin_units
        WHERE local_admin_units.site LIKE 'vn38'
    WITH DATA;

ALTER TABLE src_vn_copy.mv_local_admin_units
    OWNER TO xfer38;

GRANT ALL ON TABLE src_vn_copy.mv_local_admin_units TO postgres;
GRANT SELECT ON TABLE src_vn_copy.mv_local_admin_units TO lpo_isere;

DROP MATERIALIZED VIEW IF EXISTS src_vn_copy.mv_observations;
CREATE MATERIALIZED VIEW src_vn_copy.mv_observations
    AS SELECT *
        FROM src_vn_copy.observations
        WHERE observations.site LIKE 'vn38'
    WITH DATA;

ALTER TABLE src_vn_copy.mv_observations
    OWNER TO xfer38;

GRANT ALL ON TABLE src_vn_copy.mv_observations TO postgres;
GRANT SELECT ON TABLE src_vn_copy.mv_observations TO lpo_isere;

DROP MATERIALIZED VIEW src_vn_copy.mv_places;
CREATE MATERIALIZED VIEW src_vn_copy.mv_places
    AS SELECT *
        FROM src_vn_copy.places
        WHERE places.site LIKE 'vn38'
    WITH DATA;

ALTER TABLE src_vn_copy.mv_places
    OWNER TO xfer38;

GRANT ALL ON TABLE src_vn_copy.mv_places TO postgres;
GRANT SELECT ON TABLE src_vn_copy.mv_places TO lpo_isere;

CREATE INDEX idx_mv_places_id
    ON src_vn_copy.mv_places USING btree (id);

DROP MATERIALIZED VIEW src_vn_copy.mv_species;
CREATE MATERIALIZED VIEW src_vn_copy.mv_species
    AS SELECT *
        FROM src_vn_copy.species
        WHERE species.site LIKE 'vn38'
    WITH DATA;

ALTER TABLE src_vn_copy.mv_species
    OWNER TO xfer38;

GRANT ALL ON TABLE src_vn_copy.mv_species TO postgres;
GRANT SELECT ON TABLE src_vn_copy.mv_species TO lpo_isere;

DROP MATERIALIZED VIEW src_vn_copy.mv_taxo_groups;
CREATE MATERIALIZED VIEW src_vn_copy.mv_taxo_groups
    AS SELECT *
        FROM src_vn_copy.taxo_groups
        WHERE taxo_groups.site LIKE 'vn38'
    WITH DATA;

ALTER TABLE src_vn_copy.mv_taxo_groups
    OWNER TO xfer38;

GRANT ALL ON TABLE src_vn_copy.mv_taxo_groups TO postgres;
GRANT SELECT ON TABLE src_vn_copy.mv_taxo_groups TO lpo_isere;

DROP VIEW IF EXISTS public.obs_nature_isere;
CREATE OR REPLACE VIEW public.obs_nature_isere AS
 SELECT mv_observations.id_sighting,
    mv_species.french_name AS name_species,
    mv_species.latin_name AS latin_species,
    tabesp.cdnom_taxref AS "CD_REF",
    mv_observations.date,
    mv_observations.date_year,
        CASE
            WHEN mv_observations.hidden IS NULL THEN mv_observations.place::text
            ELSE format('E0%sN%s'::text, (mv_observations.coord_x_l93 / 10000::double precision)::integer, (mv_observations.coord_y_l93 / 10000::double precision)::integer)
        END AS place,
    mv_local_admin_units.name AS municipality,
    mv_local_admin_units.insee,
    format('E0%sN%s'::text, (mv_observations.coord_x_l93 / 10000::double precision)::integer, (mv_observations.coord_y_l93 / 10000::double precision)::integer) AS grid_name,
    mv_observations.estimation_code,
    mv_observations.count AS total_count,
    mv_observations.details AS detail,
    mv_observations.atlas_code,
    mv_observations.altitude,
    mv_observations.hidden,
    mv_observations.insert_date,
    mv_observations.update_date,
    tabx_code_atlas.code19
   FROM src_vn_copy.mv_observations
     LEFT JOIN src_vn_copy.mv_species ON mv_observations.id_species = mv_species.id
     LEFT JOIN src_vn_copy.mv_places ON mv_places.id = mv_observations.id_place
     LEFT JOIN src_vn_copy.mv_local_admin_units ON mv_places.id_commune = mv_local_admin_units.id
     LEFT JOIN reference.tabx_code_atlas ON mv_observations.atlas_code = tabx_code_atlas.code50
     LEFT JOIN reference.tabesp ON mv_observations.id_species = tabesp.id_species
  WHERE (mv_observations.entity IS NULL OR (mv_observations.entity::text IN ( SELECT nature_isere_entity.entity_short_name
           FROM nature_isere_entity))) AND mv_observations.admin_hidden IS NULL AND mv_observations.count > 0;

ALTER TABLE public.obs_nature_isere
    OWNER TO lpo_isere;

GRANT SELECT ON TABLE public.obs_nature_isere TO nature_isere;
GRANT ALL ON TABLE public.obs_nature_isere TO postgres;
GRANT ALL ON TABLE public.obs_nature_isere TO lpo_isere;

DROP VIEW IF EXISTS public.lieu_nature_isere;
CREATE OR REPLACE VIEW public.lieu_nature_isere AS
 SELECT mv_places.id AS id,
    mv_places.name AS nom,
    mv_places.coord_lat AS latitude__d_d_,
    mv_places.coord_lon AS longitude__d_d_,
    mv_places.coord_x_l93 AS lambert_93_e__m_,
    mv_places.coord_y_l93 AS lambert_93_n__m_,
    mv_places.altitude,
    mv_places.visible,
    mv_local_admin_units.insee,
    mv_local_admin_units.name AS commune
   FROM src_vn_copy.mv_places, src_vn_copy.mv_local_admin_units
  WHERE mv_local_admin_units.id = mv_places.id_commune;

ALTER TABLE public.lieu_nature_isere
    OWNER TO lpo_isere;

GRANT SELECT ON TABLE public.lieu_nature_isere TO nature_isere;
GRANT ALL ON TABLE public.lieu_nature_isere TO lpo_isere;

DROP VIEW IF EXISTS public.espece_nature_isere;
CREATE OR REPLACE VIEW public.espece_nature_isere AS
 SELECT mv_species.id AS id_species,
    mv_species.french_name AS name,
    mv_species.latin_name AS name_latin,
    mv_species.category_1 AS category,
    mv_species.rarity
   FROM src_vn_copy.mv_species
  WHERE mv_species.is_used = 1;

ALTER TABLE public.espece_nature_isere
    OWNER TO lpo_isere;

GRANT SELECT ON TABLE public.espece_nature_isere TO nature_isere;
GRANT ALL ON TABLE public.espece_nature_isere TO postgres;
GRANT ALL ON TABLE public.espece_nature_isere TO lpo_isere;
