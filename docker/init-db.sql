-- Database bootstrap, run once by the Postgres entrypoint on first startup
-- (only when the data volume is empty). Executed as the `postgres` superuser
-- against the default `postgres` database.
--
-- Mirrors the manual server setup documented at
-- https://dthonon.github.io/Client_API_VN/apps/server_install/
-- so the dev stack behaves like a real install: extensions are enabled and a
-- dedicated application superuser (xfer38) is created. transfer_vn then connects
-- as xfer38 to create the roles/databases/schemas.

CREATE EXTENSION IF NOT EXISTS adminpack;
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Password for the built-in admin account (dev value).
ALTER ROLE postgres PASSWORD 'postgres';

-- Application account used by transfer_vn (matches DATABASE.db_user in evn.toml).
-- Created idempotently so the script can be replayed (e.g. `make test-db`).
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'xfer38') THEN
        CREATE ROLE xfer38 LOGIN PASSWORD 'xfer38pw' SUPERUSER CREATEDB CREATEROLE;
    END IF;
END
$$;
