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

## Tests

Unit tests (no external dependency) run with `make test`.

The **integration tests** exercise the live VisioNature API and a PostGIS
database. They need a running Postgres/PostGIS (the `db` service above works) and
VisioNature credentials exported in the environment:

```bash
export VN_SITE_URL=https://www.faune-xxx.org/
export VN_USER_EMAIL=... VN_USER_PW=... VN_CLIENT_KEY=... VN_CLIENT_SECRET=...
make test-integration        # renders the config, sets up the DB, runs pytest
```

`make test-integration` renders `~/.evn_test.{yaml,toml}` from the templates in
`tests/data/*.tmpl`, creates the database and tables, then runs the suite.

Two pytest markers control what runs:

- **`write`** — tests that create/update/delete data on the *live* site. They are
  skipped unless `VN_ENABLE_WRITE_TESTS=1` is explicitly set, so they can never run
  by accident.
- **`faune_france`** — tests asserting data (ids, counts) specific to the
  faune-france site. Deselected by default (`PYTEST_MARKERS="not slow and not
  faune_france"`); run them against a faune-france account with
  `make test-integration PYTEST_MARKERS="not slow"`.

In CI, the `Integration tests` workflow runs the site-agnostic suite on every PR
using the `VN_AURA_*` secrets, plus a manually-triggered job that runs the
`faune_france` tests with the `VN_FF_*` secrets.
