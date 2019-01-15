-- Initialize Postgresql database, template for pyexpander3
-- - Delete and create database and roles
-- - Create JSON tables

-- Delete existing DB and roles
DROP DATABASE IF EXISTS $(evn_db_name);
DROP ROLE IF EXISTS $(evn_db_group);

-- Group role: $(evn_db_group)
CREATE ROLE $(evn_db_group)
  NOSUPERUSER INHERIT NOCREATEDB NOCREATEROLE NOREPLICATION;

-- Import role: $(evn_db_user)
GRANT $(evn_db_group) TO $(evn_db_user);

-- Database: $(evn_db_name)
CREATE DATABASE $(evn_db_name)
  WITH OWNER = $(evn_db_group);
GRANT ALL ON DATABASE $(evn_db_name) TO $(evn_db_group);

\c $(evn_db_name)

-- Schema : $(evn_db_schema_import)
CREATE SCHEMA $(evn_db_schema_import)
  AUTHORIZATION $(evn_db_group);

-- Add extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto; -- To generate pseudo ids
CREATE EXTENSION IF NOT EXISTS adminpack; -- For PgAdmin
CREATE EXTENSION IF NOT EXISTS "uuid-ossp"; -- For uuid_generate_v4
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Enable privileges
ALTER DEFAULT PRIVILEGES
    GRANT INSERT, SELECT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON TABLES
    TO postgres;
ALTER DEFAULT PRIVILEGES
    GRANT INSERT, SELECT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON TABLES
    TO $(evn_db_group);

SET search_path TO $(evn_db_schema_import),public;

------------------
-- Internal tables
------------------
-- Table download_log, updated at each download or update from site
DROP TABLE IF EXISTS download_log CASCADE;
-- Create table, indexes and access rights
CREATE TABLE download_log (
    id SERIAL PRIMARY KEY,
    site character varying(100),
    controler character varying(100),
    download_ts TIMESTAMP,
    error_count INTEGER,
    warning_count INTEGER,
    comment character varying(1000)
);
CREATE INDEX download_log_idx_site
    ON download_log (site);
CREATE INDEX download_log_idx_controler
    ON download_log (controler);
CREATE INDEX download_log_idx_download_ts
    ON download_log (download_ts);

INSERT INTO download_log (download_ts) VALUES (current_timestamp);

-----------
-- Entities
-----------
DROP TABLE IF EXISTS entities_json CASCADE;
CREATE TABLE entities_json (
    id integer,
    site character varying(100),
    item jsonb,   -- Complete json as downloaded
    PRIMARY KEY (id, site)
);

--------
-- Forms
--------
DROP TABLE IF EXISTS forms_json CASCADE;
CREATE TABLE forms_json (
    id integer,
    site character varying(100),
    item jsonb,   -- Complete json as extracted from observations
    PRIMARY KEY (id, site)
);

--------------------
-- local_admin_units
--------------------
DROP TABLE IF EXISTS local_admin_units_json CASCADE;
CREATE TABLE local_admin_units_json (
    id integer,
    site character varying(100),
    item jsonb,   -- Complete json as downloaded
    PRIMARY KEY (id, site)
);

---------------
-- Observations
---------------
DROP TABLE IF EXISTS observations_json CASCADE;
CREATE TABLE observations_json (
    id integer,
    site character varying(100),
    item jsonb,   -- Complete json as downloaded
    update_ts integer,
    PRIMARY KEY (id, site)
);

---------
-- Places
---------
DROP TABLE IF EXISTS places_json CASCADE;
CREATE TABLE places_json (
    id integer,
    site character varying(100),
    item jsonb,   -- Complete json as downloaded
    PRIMARY KEY (id, site)
);

----------
-- Species
----------
DROP TABLE IF EXISTS species_json CASCADE;
CREATE TABLE species_json (
    id integer,
    site character varying(100),
    item jsonb,   -- Complete json as downloaded
    PRIMARY KEY (id, site)
);

--------------
-- Taxo_groups
--------------
DROP TABLE IF EXISTS taxo_groups_json CASCADE;
CREATE TABLE taxo_groups_json (
    id integer,
    site character varying(100),
    item jsonb,   -- Complete json as downloaded
    PRIMARY KEY (id, site)
);

--------------------
-- Territorial_units
--------------------
DROP TABLE IF EXISTS territorial_units_json CASCADE;
CREATE TABLE territorial_units_json (
    id integer,
    site character varying(100),
    item jsonb,   -- Complete json as downloaded
    PRIMARY KEY (id, site)
);
