# Client_API_VN

[![Release](https://img.shields.io/github/v/release/dthonon/Client_API_VN)](https://img.shields.io/github/v/release/dthonon/Client_API_VN)
[![Build status](https://img.shields.io/github/actions/workflow/status/dthonon/Client_API_VN/main.yml?branch=main)](https://github.com/dthonon/Client_API_VN/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/dthonon/Client_API_VN/branch/main/graph/badge.svg)](https://codecov.io/gh/dthonon/Client_API_VN)
[![Commit activity](https://img.shields.io/github/commit-activity/m/dthonon/Client_API_VN)](https://img.shields.io/github/commit-activity/m/dthonon/Client_API_VN)
[![License](https://img.shields.io/github/license/dthonon/Client_API_VN)](https://img.shields.io/github/license/dthonon/Client_API_VN)

## Presentation

Python applications that use Biolovision/VisioNature (VN) API.
See <https://dthonon.github.io/Client_API_VN/>.

## Docker (development)

A `docker-compose.yml` provides a ready-to-use development stack: the CLI
(`transfer_vn`) plus a PostGIS database. On first startup, `docker/init-db.sql`
enables the PostGIS extensions and creates the `xfer38` application superuser,
mirroring the [server install guide](https://dthonon.github.io/Client_API_VN/apps/server_install/).

Start the stack and create the database and tables:

```bash
docker compose up -d --build
docker compose exec app transfer_vn --db_create --json_tables_create --col_tables_create evn.toml
```

Then run a download (requires real VN credentials, see below) or open a shell:

```bash
docker compose exec app transfer_vn --full evn.toml   # full download
docker compose exec app transfer_vn --status evn.toml # scheduling / status
docker compose exec app bash                          # interactive shell
```

The configuration lives in `docker/evn.toml`; its `[database]` section already
points at the `db` service. Replace the `[site.tff]` values with real Biolovision
credentials before running `--full` / `--update`. The project source is mounted
at `/code` and installed in editable mode, so host edits apply live; run
`cd /code` inside the container for `pytest` / `poetry` tasks.

Stop the stack with `docker compose down`, or `docker compose down -v` to also
drop the database volume (which re-runs `init-db.sql` on the next start).
