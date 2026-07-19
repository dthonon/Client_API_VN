"""Regression tests for the incremental-download data-loss bugs.

Several issues report that a database maintained by incremental updates diverges
from a full re-download (a few thousand observations out of ~31 million). This
module reproduces the root causes identified in the audit, **without any live
VisioNature account** — the API layer is mocked, so the tests are deterministic
and run anywhere (including forks, with no secrets).

They assert the *correct* behaviour, so several of them currently FAIL: that is
intentional (red first). Each failure pins a concrete bug to fix.

Bugs covered:
1. the synchronisation watermark is advanced before the data is persisted, so a
   failure loses observations forever  -> test_increment_watermark_*
2. empty server responses (e.g. after a Gateway Timeout) abort processing
   instead of being absorbed                -> test_empty_response_*
3. observation "forms" are not cleaned up on deletion -> test_delete_form_* (DB)
4. an incremental run must converge to the same state as a full download
                                             -> test_increment_matches_full (DB)
"""

import os
import re
from datetime import datetime
from unittest.mock import Mock

import pytest
from sqlalchemy import select, text

from biolovision.api import EntitiesAPI, HTTPError
from export_vn.download_vn import Observations

SITE = "tst"
DUMMY = "unused-in-mocked-tests"


class FakeBackend:
    """In-memory stand-in for StorePostgresql.

    Records the synchronisation watermark and the store/delete calls, so tests
    can assert the *ordering* between persistence and watermark advancement
    without needing a database.
    """

    def __init__(self, initial_ts=None):
        self._ts = {}
        if initial_ts is not None:
            self._ts[(SITE, "1")] = initial_ts
        self.stored = []
        self.deleted = []

    def increment_get(self, site, taxo_group):
        return self._ts.get((site, str(taxo_group)))

    def increment_log(self, site, taxo_group, last_ts):
        self._ts[(site, str(taxo_group))] = last_ts

    def store(self, controler, seq, items_dict):
        self.stored.append((controler, seq, items_dict))
        return len(items_dict.get("data", {}).get("sightings", []))

    def log(self, *args, **kwargs):
        pass

    def delete_obs(self, deleted):
        self.deleted.append(list(deleted))


def _make_observations(backend):
    """Build an Observations orchestrator wired to a fake backend."""
    return Observations(
        site=SITE,
        user_email="test@example.org",
        user_pw=DUMMY,
        base_url="https://example.org/",
        client_key=DUMMY,
        client_secret=DUMMY,
        db_enabled=False,
        db_user=DUMMY,
        db_pw=DUMMY,
        db_host=DUMMY,
        db_port="5432",
        db_name=DUMMY,
        db_schema_import="import",
        db_schema_vn="src_vn",
        db_group=DUMMY,
        db_out_proj="2154",
        backend=backend,
    )


# ---------------------------------------------------------------------------
# Bug 1: the watermark must not advance past data that was not persisted.
# ---------------------------------------------------------------------------
@pytest.mark.xfail(strict=True, reason="bug: increment_log(now) is called before store(); remove when fixed")
def test_increment_watermark_not_advanced_on_failure():
    """If fetching/persisting the updates fails, the watermark must stay put.

    Reproduces the core data-loss bug: Observations.update() calls
    increment_log(now) *before* api_diff() and store(). If the download then
    fails, the next run starts from `now` and never re-downloads the
    observations modified in between.
    """
    t0 = datetime(2024, 1, 1, 0, 0, 0)
    backend = FakeBackend(initial_ts=t0)
    obs = _make_observations(backend)

    api = Mock()
    api.controler = "observations"
    api.transfer_errors = 0
    api.http_status = 504
    api.api_diff.return_value = [
        {"id_sighting": "42", "id_universal": "1_42", "modification_type": "updated"},
    ]
    # Fetching the full observation fails mid-sync (e.g. Gateway Timeout).
    api.api_list.side_effect = HTTPError(504)
    obs._api_instance = api

    obs.update(id_taxo_group="1")

    assert backend.increment_get(SITE, "1") == t0, (
        f"watermark advanced past observations that were never stored: {backend.increment_get(SITE, '1')} != {t0}"
    )


def test_increment_watermark_advances_on_success():
    """On a successful run the watermark *does* move forward (guards the fix)."""
    t0 = datetime(2024, 1, 1, 0, 0, 0)
    backend = FakeBackend(initial_ts=t0)
    obs = _make_observations(backend)

    api = Mock()
    api.controler = "observations"
    api.transfer_errors = 0
    api.http_status = 200
    api.api_diff.return_value = [
        {"id_sighting": "42", "id_universal": "1_42", "modification_type": "updated"},
    ]
    api.api_list.return_value = {"data": {"sightings": [{"observers": [{"id_sighting": "42"}]}]}}
    obs._api_instance = api

    obs.update(id_taxo_group="1")

    assert backend.stored, "a successful update must have stored something"
    assert backend.increment_get(SITE, "1") > t0


# ---------------------------------------------------------------------------
# Bug 2: an empty server response must be absorbed, not abort the download.
# ---------------------------------------------------------------------------
@pytest.mark.xfail(strict=True, reason='bug: resp.json("{}") raises TypeError on empty body; remove when fixed')
def test_empty_response_does_not_abort(requests_mock):
    """A 200 response with an empty body must not raise.

    After a Gateway Timeout the server may return an empty body. In
    BiolovisionAPI._url the empty branch calls ``resp.json("{}")`` which raises
    TypeError (json() takes no positional argument), aborting the whole
    download instead of treating the chunk as "no data".
    """
    api = EntitiesAPI(
        user_email="test@example.org",
        user_pw=DUMMY,
        base_url="https://example.org/",
        client_key=DUMMY,
        client_secret=DUMMY,
        max_retry=2,
        max_requests=1,
        max_chunks=10,
        unavailable_delay=0,
        retry_delay=0,
    )
    requests_mock.get(re.compile(r"https://example\.org/"), text="", status_code=200)

    # Must not raise: an empty chunk means "no more data", not a fatal error.
    result = api.api_list()
    assert not result or "data" in result


# ---------------------------------------------------------------------------
# PostGIS harness for the DB-backed regression tests (bugs 3 and 4).
# Uses a dedicated, throw-away database; no VisioNature account is involved.
# ---------------------------------------------------------------------------
DB = {
    "db_user": os.environ.get("DB_USER", "xfer38"),
    "db_pw": os.environ.get("DB_PW", "xfer38pw"),
    "db_host": os.environ.get("DB_HOST", "localhost"),
    "db_port": os.environ.get("DB_PORT", "5432"),
    "db_name": "faune_regression",
    "db_schema_import": "import",
    "db_schema_vn": "src_vn",
    "db_group": "lpo_regression",
    "db_out_proj": "2154",
}


@pytest.fixture(scope="module")
def pg():
    """A StorePostgresql backed by a fresh, disposable PostGIS database."""
    from export_vn.store_postgresql import PostgresqlUtils, StorePostgresql

    utils = PostgresqlUtils(
        True,
        DB["db_user"],
        DB["db_pw"],
        DB["db_host"],
        DB["db_port"],
        DB["db_name"],
        DB["db_schema_import"],
        DB["db_schema_vn"],
        DB["db_group"],
    )
    try:
        utils.drop_database()
        utils.create_database()
        utils.create_json_tables()
        store = StorePostgresql(
            SITE,
            True,
            DB["db_user"],
            DB["db_pw"],
            DB["db_host"],
            DB["db_port"],
            DB["db_name"],
            DB["db_schema_import"],
            DB["db_schema_vn"],
            DB["db_group"],
            DB["db_out_proj"],
        )
    except Exception as e:
        pytest.skip(f"PostGIS test database unavailable: {e!r}")
    yield store
    store._conn.close()
    utils.drop_database()


def _sighting(id_sighting, ts=1700000000, uid="1"):
    """Minimal well-formed sighting element accepted by store_1_observation."""
    return {
        "date": {"@timestamp": str(ts)},
        "species": {"@id": "1"},
        "observers": [
            {
                "@uid": uid,
                "id_sighting": str(id_sighting),
                "id_universal": f"1_{id_sighting}",
                "update_date": ts,
                "coord_lon": 5.72,
                "coord_lat": 45.18,
            }
        ],
    }


def _form_payload(form_id, sightings):
    """An observations payload made of a single form and its sightings."""
    return {
        "data": {
            "sightings": [],
            "forms": [{"@id": str(form_id), "id_form_universal": f"1_{form_id}", "sightings": sightings}],
        }
    }


def _reset(store):
    store._conn.execute(
        text(f"TRUNCATE {DB['db_schema_import']}.observations_json, {DB['db_schema_import']}.forms_json")
    )


def _obs_ids(store):
    md = store._table_defs["observations"]["metadata"]
    rows = store._conn.execute(select([md.c.item]).where(md.c.site == SITE)).fetchall()
    return {r[0]["observers"][0]["id_sighting"] for r in rows}


def _form_ids(store):
    md = store._table_defs["forms"]["metadata"]
    rows = store._conn.execute(select([md.c.item]).where(md.c.site == SITE)).fetchall()
    return {r[0]["@id"] for r in rows}


# ---------------------------------------------------------------------------
# Bug 3: deleting the observations of a form must clean up the form.
# ---------------------------------------------------------------------------
@pytest.mark.xfail(strict=True, reason="bug: delete_obs never cleans forms_json; remove when fixed")
def test_delete_form_removes_orphan_forms(pg):
    """Storing a form then deleting all its sightings must leave no orphan form."""
    store = pg
    _reset(store)
    store.store("observations", "f", _form_payload(1000, [_sighting(101), _sighting(102)]))
    assert _obs_ids(store) == {"101", "102"}
    assert _form_ids(store) == {"1000"}

    store.delete_obs(["101", "102"])

    assert _obs_ids(store) == set()
    assert _form_ids(store) == set(), "orphan form left in forms_json after deleting all its sightings"


# ---------------------------------------------------------------------------
# Bug 4: incremental must converge to the same state as a full download.
# ---------------------------------------------------------------------------
@pytest.mark.xfail(strict=True, reason="bug: orphan form makes the incremental state diverge; remove when fixed")
def test_increment_matches_full(pg):
    """A full download and the equivalent incremental run must be identical.

    Final server state: form 1000 has been deleted, form 2000 persists.
    """
    store = pg

    # Full download of the final state (only form 2000 exists).
    _reset(store)
    store.store("observations", "full", _form_payload(2000, [_sighting(103)]))
    full = (_obs_ids(store), _form_ids(store))

    # Incremental path reaching the same final state.
    _reset(store)
    store.store("observations", "i1", _form_payload(1000, [_sighting(101), _sighting(102)]))
    store.store("observations", "i2", _form_payload(2000, [_sighting(103)]))
    store.delete_obs(["101", "102"])  # form 1000 fully deleted
    incr = (_obs_ids(store), _form_ids(store))

    assert incr == full, f"incremental diverged from full: {incr} != {full}"
