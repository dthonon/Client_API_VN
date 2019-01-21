-- Initialize Postgresql database, template for pyexpander3
-- - Delete and create database and roles
-- - Create JSON tables

-- Delete existing DB and roles
DROP DATABASE IF EXISTS $(db_name);
DROP ROLE IF EXISTS $(db_group);

-- Group role:
CREATE ROLE $(db_group)
  NOSUPERUSER INHERIT NOCREATEDB NOCREATEROLE NOREPLICATION;

-- Import role:
GRANT $(db_group) TO $(db_user);

-- Database:
CREATE DATABASE $(db_name)
  WITH OWNER = $(db_group);
GRANT ALL ON DATABASE $(db_name) TO $(db_group);

\c $(db_name)

-- Schema
CREATE SCHEMA $(db_schema_import)
  AUTHORIZATION $(db_group);

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
    TO $(db_group);

SET search_path TO $(db_schema_import),public;

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
