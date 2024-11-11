# Database usage examples

## Nature-isere export

The following SQL code creates view on the database for Nature-isere.
It can be used as a base for defining views on the database, for export.

```psql
--
-- Initialisation de la base pour export vers nature_isere
--  - Création des roles (mots de passes à définir). xfer38 est créé lors de l'installation du serveur debian
--  - Création de la base, des extensions et des schémas
--  - Création du FOREIGN DATA WRAPPER et des tables FOREIGN
--  - Création des vues matérialisées
--  - Création des vues publiques
--
-- A utiliser depuis le compte SUPERUSER:
--  $ sudo -iu xfer38
--  $ psql postgres
--
-- Role: lpo_isere

CREATE ROLE lpo_isere WITH
    NOLOGIN
    NOSUPERUSER
    INHERIT
    NOCREATEDB
    NOCREATEROLE
    NOREPLICATION;
    GRANT lpo_isere TO xfer38;

-- Role: nature_isere
-- DROP ROLE nature_isere;

CREATE ROLE nature_isere WITH
LOGIN
NOSUPERUSER
INHERIT
NOCREATEDB
NOCREATEROLE
NOREPLICATION
PASSWORD '???';

-- Database: faune_isere

ALTER DATABASE faune_isere
    SET search_path TO "$user", public, topology;

\c faune_isere

ALTER DEFAULT PRIVILEGES
GRANT ALL ON TABLES TO lpo_isere;

ALTER DEFAULT PRIVILEGES
GRANT ALL ON TABLES TO postgres;

ALTER DEFAULT PRIVILEGES
GRANT ALL ON TABLES TO xfer38;

-- DROP EXTENSION IF EXISTS adminpack CASCADE;
-- CREATE EXTENSION adminpack;
-- DROP EXTENSION IF EXISTS postgis CASCADE;
-- CREATE EXTENSION postgis;
-- DROP EXTENSION IF EXISTS postgis_topology CASCADE;
-- CREATE EXTENSION postgis_topology;

DROP EXTENSION IF EXISTS postgres_fdw CASCADE;
DROP SERVER IF EXISTS aura_server CASCADE;
DROP USER MAPPING IF EXISTS FOR xfer38 SERVER aura_server;

CREATE EXTENSION IF NOT EXISTS postgres_fdw;

CREATE SERVER aura_server
    FOREIGN DATA WRAPPER postgres_fdw
    OPTIONS (host 'geonature.fauneauvergnerhonealpes.org', port '5432', dbname 'gnlpoaura');
-- ALTER SERVER aura_server
--     OWNER TO postgres;

CREATE USER MAPPING FOR xfer38 SERVER aura_server
    OPTIONS ("user" 'xxx', password '???');

-- SCHEMA and FOREIGN SCHEMA
CREATE SCHEMA IF NOT EXISTS taxonomie
    AUTHORIZATION lpo_isere;
COMMENT ON SCHEMA taxonomie
    IS 'Schéma contenant les réferentiels officiels (TAXREF, Mailles, etc.)';

IMPORT FOREIGN SCHEMA taxonomie
    FROM SERVER aura_server INTO taxonomie;

-- TABLES for public access
DROP TABLE IF EXISTS public.nature_isere_entity;
CREATE TABLE public.nature_isere_entity (
    entity_short_name character varying(1000) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT nature_isere_entity_pkey PRIMARY KEY (entity_short_name)
);
ALTER TABLE public.nature_isere_entity OWNER to lpo_isere;

-- MATERIALIZED VIEWS and TABLES for referentiel
DROP TABLE IF EXISTS taxonomie.tabx_code_atlas;
CREATE TABLE taxonomie.tabx_code_atlas (
    code50 integer NOT NULL,
    code19 real,
    CONSTRAINT tabx_code_atlas_pkey PRIMARY KEY (code50)
);
ALTER TABLE taxonomie.tabx_code_atlas OWNER TO xfer38;
INSERT INTO taxonomie.tabx_code_atlas VALUES
    (0, 0),
    (1, 1),
    (2, 2),
    (3, 3),
    (4, 4),
    (5, 5),
    (6, 6),
    (7, 7),
    (8, 8),
    (9, 9),
    (10, 10),
    (11, 11),
    (12, 12),
    (13, 13),
    (14, 14),
    (15, 15),
    (16, 16),
    (17, 17),
    (18, 18),
    (19, 19),
    (30, 3.5),
    (40, 4.5),
    (50, 11.5),
    (99, NULL);

-- VIEWS

DROP VIEW IF EXISTS public.obs_nature_isere;
CREATE OR REPLACE VIEW public.obs_nature_isere AS
SELECT observations.id_sighting,
    species.french_name AS name_species,
    species.latin_name AS latin_species,
    cor_c_vn_taxref.taxref_id AS "CD_REF",
    observations.date,
    observations.date_year,
        CASE
            WHEN observations.hidden IS NULL THEN observations.place::text
            ELSE format('E0%sN%s'::text, (observations.coord_x_local / 10000::double precision)::integer, (observations.coord_y_local / 10000::double precision)::integer)
        END AS place,
    local_admin_units.name AS municipality,
    local_admin_units.insee,
    format('E0%sN%s'::text, (observations.coord_x_local / 10000::double precision)::integer, (observations.coord_y_local / 10000::double precision)::integer) AS grid_name,
    observations.estimation_code,
    observations.count AS total_count,
    observations.details AS detail,
    observations.atlas_code,
    observations.altitude,
    observations.hidden,
    observations.insert_date,
    observations.update_date,
    tabx_code_atlas.code19
FROM src_vn.observations
    LEFT JOIN src_vn.species ON observations.id_species = species.id
    LEFT JOIN src_vn.places ON places.id = observations.id_place
    LEFT JOIN src_vn.local_admin_units ON places.id_commune = local_admin_units.id
    LEFT JOIN taxonomie.tabx_code_atlas ON observations.atlas_code = tabx_code_atlas.code50
    LEFT JOIN taxonomie.cor_c_vn_taxref ON observations.id_species = cor_c_vn_taxref.vn_id
WHERE (observations.admin_hidden IS NULL) AND observations.count > 0 AND (local_admin_units.name IS NOT NULL);
ALTER TABLE public.obs_nature_isere OWNER TO lpo_isere;
GRANT SELECT ON TABLE public.obs_nature_isere TO nature_isere;
GRANT ALL ON TABLE public.obs_nature_isere TO postgres;
GRANT ALL ON TABLE public.obs_nature_isere TO lpo_isere;

DROP VIEW IF EXISTS public.lieu_nature_isere;
CREATE OR REPLACE VIEW public.lieu_nature_isere AS
SELECT places.id AS id,
    places.name AS nom,
    places.coord_lat AS latitude__d_d_,
    places.coord_lon AS longitude__d_d_,
    places.coord_x_local AS lambert_93_e__m_,
    places.coord_y_local AS lambert_93_n__m_,
    places.altitude,
    places.visible,
    local_admin_units.insee,
    local_admin_units.name AS commune
FROM src_vn.places, src_vn.local_admin_units
WHERE local_admin_units.id = places.id_commune;
ALTER TABLE public.lieu_nature_isere OWNER TO lpo_isere;
GRANT SELECT ON TABLE public.lieu_nature_isere TO nature_isere;
GRANT ALL ON TABLE public.lieu_nature_isere TO lpo_isere;

DROP VIEW IF EXISTS public.espece_nature_isere;
CREATE OR REPLACE VIEW public.espece_nature_isere AS
SELECT species.id AS id_species,
    species.french_name AS name,
    species.latin_name AS name_latin,
    species.category_1 AS category,
    species.rarity
FROM src_vn.species
WHERE species.is_used;
ALTER TABLE public.espece_nature_isere OWNER TO lpo_isere;
GRANT SELECT ON TABLE public.espece_nature_isere TO nature_isere;
GRANT ALL ON TABLE public.espece_nature_isere TO postgres;
GRANT ALL ON TABLE public.espece_nature_isere TO lpo_isere;
```
