"""
Test the transactional behavior of store_postgresql (SQLAlchemy 2.0 semantics).

These tests only need the PostGIS database (tables created by
`transfer_vn --json_tables_create --col_tables_create`), no VisioNature
account: data is injected directly through the store API.

They cover the behavior introduced by the SQLAlchemy 2.0 migration:
- store() commits per batch and rolls the whole batch back on error;
- the connection stays usable after a failed batch;
- committed data is visible from other connections;
- read() and increment_get() do not leave the connection 'idle in transaction'.
"""

import pytest
from dynaconf import Dynaconf
from sqlalchemy import create_engine, exc, text
from sqlalchemy.engine.url import URL

from export_vn.store_postgresql import ReadPostgresql, StorePostgresql

FILE = "evn_test.toml"

# Get configuration for test site
settings = Dynaconf(
    settings_files=[FILE],
)

# Test ids, far above any real VisioNature id, cleaned up after each test
TEST_IDS = [999999901, 999999902]


def _pg_params():
    return dict(  # noqa: C408
        site=settings["SITE"]["name"],
        db_enabled=settings["DATABASE"]["enabled"],
        db_user=settings["DATABASE"]["db_user"],
        db_pw=settings["DATABASE"]["db_pw"],
        db_host=settings["DATABASE"]["db_host"],
        db_port=settings["DATABASE"]["db_port"],
        db_name=settings["DATABASE"]["db_name"],
        db_schema_import=settings["DATABASE"]["db_schema_import"],
        db_schema_vn=settings["DATABASE"]["db_schema_vn"],
        db_group=settings["DATABASE"]["db_group"],
        db_out_proj=settings["DATABASE"]["db_out_proj"],
    )


@pytest.fixture(scope="module")
def monitor():
    """Independent engine, to observe the database from a separate connection."""
    db_url = {
        "drivername": "postgresql+psycopg2",
        "username": settings["DATABASE"]["db_user"],
        "password": settings["DATABASE"]["db_pw"],
        "host": settings["DATABASE"]["db_host"],
        "port": settings["DATABASE"]["db_port"],
        "database": settings["DATABASE"]["db_name"],
    }
    db = create_engine(URL.create(**db_url), echo=False, future=True)
    yield db
    db.dispose()


@pytest.fixture()
def store_pg(monitor):
    """A fresh store, with test rows cleaned up on teardown."""
    store = StorePostgresql(**_pg_params())
    yield store
    store.__exit__(None, None, None)
    schema = settings["DATABASE"]["db_schema_import"]
    with monitor.begin() as conn:
        conn.execute(
            text(f"DELETE FROM {schema}.entities_json WHERE id = ANY(:ids)"),  # noqa: S608
            {"ids": TEST_IDS},
        )


def _count_test_rows(monitor):
    schema = settings["DATABASE"]["db_schema_import"]
    with monitor.connect() as conn:
        return conn.execute(
            text(f"SELECT COUNT(*) FROM {schema}.entities_json WHERE id = ANY(:ids)"),  # noqa: S608
            {"ids": TEST_IDS},
        ).scalar()


def test_store_commits_batch(store_pg, monitor):
    """A stored batch must be committed, i.e. visible from another connection."""
    items = {"data": [{"id": TEST_IDS[0], "short_name": "pytest entity"}]}
    assert store_pg.store("entities", "1", items) == 1
    assert _count_test_rows(monitor) == 1


def test_store_rolls_back_failed_batch(store_pg, monitor):
    """On error, the whole batch is rolled back, and the connection stays usable."""
    bad_batch = {
        "data": [
            {"id": TEST_IDS[0], "short_name": "stored before the error"},
            {"id": None, "short_name": "violates NOT NULL"},
        ]
    }
    with pytest.raises(exc.SQLAlchemyError):
        store_pg.store("entities", "1", bad_batch)
    # The first, valid element must not survive the failed batch
    assert _count_test_rows(monitor) == 0

    # The connection must remain usable after the rollback
    items = {"data": [{"id": TEST_IDS[1], "short_name": "stored after the error"}]}
    assert store_pg.store("entities", "1", items) == 1
    assert _count_test_rows(monitor) == 1


def _backend_state(monitor, backend_pid):
    with monitor.connect() as conn:
        return conn.execute(
            text("SELECT state FROM pg_stat_activity WHERE pid = :pid"),
            {"pid": backend_pid},
        ).scalar()


def _backend_pid(pg):
    pid = pg._conn.execute(text("SELECT pg_backend_pid()")).scalar()
    pg._conn.rollback()
    return pid


def test_reads_release_transaction(store_pg, monitor):
    """read() and increment_get() must not leave the connection 'idle in transaction'."""
    read_pg = ReadPostgresql(**_pg_params())
    try:
        read_pid = _backend_pid(read_pg)
        read_pg.read("entities")
        assert _backend_state(monitor, read_pid) == "idle"
    finally:
        read_pg.__exit__(None, None, None)

    store_pid = _backend_pid(store_pg)
    store_pg.increment_get(settings["SITE"]["name"], 1)
    assert _backend_state(monitor, store_pid) == "idle"
