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

import re
from datetime import datetime
from unittest.mock import Mock

import pytest

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
# Bug 3: deleting the observations of a form must clean up the form. (needs DB)
# ---------------------------------------------------------------------------
@pytest.mark.skip(reason="needs the PostGIS test harness — next step of the plan")
def test_delete_form_removes_orphan_forms():
    """Storing a form then deleting all its sightings must leave no orphan.

    To be implemented against a StorePostgresql backend on the local PostGIS:
    store an observations payload containing a form with 2 sightings, then
    delete_obs() both sightings, and assert forms_json no longer references the
    now-empty form.
    """


# ---------------------------------------------------------------------------
# Bug 4: incremental must converge to the same state as a full download. (DB)
# ---------------------------------------------------------------------------
@pytest.mark.skip(reason="needs the PostGIS test harness — next step of the plan")
def test_increment_matches_full():
    """A full download and the equivalent incremental run must be identical.

    Golden regression: build state S_full from a canned full payload, build
    S_incr by replaying the same changes as increments, and assert the
    observations tables are row-for-row identical.
    """
