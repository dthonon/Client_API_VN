-- Initialize Postgresql database, template for pyexpander3

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
  WITH OWNER = $(evn_db_group)
       -- ENCODING = 'UTF8'
       -- TABLESPACE = pg_default
       -- LC_COLLATE = 'fr_FR.UTF-8'
       -- LC_CTYPE = 'fr_FR.UTF-8'
       -- CONNECTION LIMIT = -1
       -- TEMPLATE template0
       ;
GRANT ALL ON DATABASE $(evn_db_name) TO $(evn_db_group);

\c $(evn_db_name)

-- Schema : $(evn_db_schema)
CREATE SCHEMA $(evn_db_schema)
  AUTHORIZATION $(evn_db_group);

-- Schema : reference, for external reference sources
CREATE SCHEMA reference
  AUTHORIZATION $(evn_db_group);

-- Extension d'administration pgAdmin
CREATE EXTENSION if not exists adminpack;

ALTER DEFAULT PRIVILEGES
    GRANT INSERT, SELECT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON TABLES
    TO postgres;

ALTER DEFAULT PRIVILEGES
    GRANT INSERT, SELECT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON TABLES
    TO $(evn_db_group);
