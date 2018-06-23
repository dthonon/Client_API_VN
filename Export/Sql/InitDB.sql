
-- Initialize Postgresql database, template for pyexpander3

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

-- Extension d'administration pgAdmin
CREATE EXTENSION adminpack;

-- Extensions postgis
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;

ALTER DEFAULT PRIVILEGES
    GRANT INSERT, SELECT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON TABLES
    TO postgres;

ALTER DEFAULT PRIVILEGES
    GRANT INSERT, SELECT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON TABLES
    TO $(evn_db_group);
