"""
Test each method of download_vn module, using file store.
"""

import gzip
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from dynaconf import Dynaconf

from export_vn.download_vn import (
    Entities,
    Families,
    Fields,
    LocalAdminUnits,
    Observations,
    Observers,
    Places,
    Species,
    TaxoGroup,
    TerritorialUnits,
    Validations,
)
from export_vn.store_file import StoreFile

# Using faune-france site, that needs to be defined in .evn_test.yaml
SITE = "tff"
FILE = ".evn_test.toml"

# Get configuration for test site
settings = Dynaconf(
    settings_files=[FILE],
)
cfg_site_list = settings.site
assert len(cfg_site_list) == 1, _("Only one site can be defined in configuration file")
for site, cfg in cfg_site_list.items():  # noqa: B007
    break


@pytest.mark.order(index=300)
def test_init():
    """Instantiate stores."""
    global STORE_FILE, ENTITIES, FAMILIES, FIELDS, LOCAL_ADMIN_UNITS
    global OBSERVATIONS, OBSERVERS, PLACES, SPECIES, TAXO_GROUP, TERRITORIAL_UNIT, VALIDATIONS
    STORE_FILE = StoreFile(file_enabled=settings.file.enabled, file_store=settings.file.file_store)
    ENTITIES = Entities(
        site=site,
        user_email=cfg.user_email,
        user_pw=cfg.user_pw,
        base_url=cfg.site,
        client_key=cfg.client_key,
        client_secret=cfg.client_secret,
        backend=STORE_FILE,
        max_retry=settings.tuning.max_retry,
        max_requests=settings.tuning.max_requests,
        max_chunks=settings.tuning.max_chunks,
        unavailable_delay=settings.tuning.unavailable_delay,
        retry_delay=settings.tuning.retry_delay,
    )
    FAMILIES = Families(
        site=site,
        user_email=cfg.user_email,
        user_pw=cfg.user_pw,
        base_url=cfg.site,
        client_key=cfg.client_key,
        client_secret=cfg.client_secret,
        backend=STORE_FILE,
        max_retry=settings.tuning.max_retry,
        max_requests=settings.tuning.max_requests,
        max_chunks=settings.tuning.max_chunks,
        unavailable_delay=settings.tuning.unavailable_delay,
        retry_delay=settings.tuning.retry_delay,
    )
    FIELDS = Fields(
        site=site,
        user_email=cfg.user_email,
        user_pw=cfg.user_pw,
        base_url=cfg.site,
        client_key=cfg.client_key,
        client_secret=cfg.client_secret,
        backend=STORE_FILE,
        max_retry=settings.tuning.max_retry,
        max_requests=settings.tuning.max_requests,
        max_chunks=settings.tuning.max_chunks,
        unavailable_delay=settings.tuning.unavailable_delay,
        retry_delay=settings.tuning.retry_delay,
    )
    LOCAL_ADMIN_UNITS = LocalAdminUnits(
        site=site,
        user_email=cfg.user_email,
        user_pw=cfg.user_pw,
        base_url=cfg.site,
        client_key=cfg.client_key,
        client_secret=cfg.client_secret,
        backend=STORE_FILE,
        max_retry=settings.tuning.max_retry,
        max_requests=settings.tuning.max_requests,
        max_chunks=settings.tuning.max_chunks,
        unavailable_delay=settings.tuning.unavailable_delay,
        retry_delay=settings.tuning.retry_delay,
    )
    OBSERVATIONS = Observations(
        site=site,
        user_email=cfg.user_email,
        user_pw=cfg.user_pw,
        base_url=cfg.site,
        client_key=cfg.client_key,
        client_secret=cfg.client_secret,
        db_enabled=False,
        start_date=settings.filter.start_date,
        end_date=settings.filter.end_date,
        type_date=settings.filter.type_date,
        backend=STORE_FILE,
        max_retry=settings.tuning.max_retry,
        max_requests=settings.tuning.max_requests,
        max_chunks=settings.tuning.max_chunks,
        unavailable_delay=settings.tuning.unavailable_delay,
        retry_delay=settings.tuning.retry_delay,
        pid_kp=settings.tuning.pid_kp,
        pid_ki=settings.tuning.pid_ki,
        pid_kd=settings.tuning.pid_kd,
        pid_setpoint=settings.tuning.pid_setpoint,
        pid_limit_max=settings.tuning.pid_limit_max,
        pid_limit_min=settings.tuning.pid_limit_min,
        pid_delta_days=settings.tuning.pid_delta_days,
    )
    OBSERVERS = Observers(
        site=site,
        user_email=cfg.user_email,
        user_pw=cfg.user_pw,
        base_url=cfg.site,
        client_key=cfg.client_key,
        client_secret=cfg.client_secret,
        backend=STORE_FILE,
        max_retry=settings.tuning.max_retry,
        max_requests=settings.tuning.max_requests,
        max_chunks=settings.tuning.max_chunks,
        unavailable_delay=settings.tuning.unavailable_delay,
        retry_delay=settings.tuning.retry_delay,
    )
    PLACES = Places(
        site=site,
        user_email=cfg.user_email,
        user_pw=cfg.user_pw,
        base_url=cfg.site,
        client_key=cfg.client_key,
        client_secret=cfg.client_secret,
        backend=STORE_FILE,
        max_retry=settings.tuning.max_retry,
        max_requests=settings.tuning.max_requests,
        max_chunks=settings.tuning.max_chunks,
        unavailable_delay=settings.tuning.unavailable_delay,
        retry_delay=settings.tuning.retry_delay,
    )
    SPECIES = Species(
        site=site,
        user_email=cfg.user_email,
        user_pw=cfg.user_pw,
        base_url=cfg.site,
        client_key=cfg.client_key,
        client_secret=cfg.client_secret,
        backend=STORE_FILE,
        max_retry=settings.tuning.max_retry,
        max_requests=settings.tuning.max_requests,
        max_chunks=settings.tuning.max_chunks,
        unavailable_delay=settings.tuning.unavailable_delay,
        retry_delay=settings.tuning.retry_delay,
    )
    TAXO_GROUP = TaxoGroup(
        site=site,
        user_email=cfg.user_email,
        user_pw=cfg.user_pw,
        base_url=cfg.site,
        client_key=cfg.client_key,
        client_secret=cfg.client_secret,
        backend=STORE_FILE,
        max_retry=settings.tuning.max_retry,
        max_requests=settings.tuning.max_requests,
        max_chunks=settings.tuning.max_chunks,
        unavailable_delay=settings.tuning.unavailable_delay,
        retry_delay=settings.tuning.retry_delay,
    )
    TERRITORIAL_UNIT = TerritorialUnits(
        site=site,
        user_email=cfg.user_email,
        user_pw=cfg.user_pw,
        base_url=cfg.site,
        client_key=cfg.client_key,
        client_secret=cfg.client_secret,
        backend=STORE_FILE,
        max_retry=settings.tuning.max_retry,
        max_requests=settings.tuning.max_requests,
        max_chunks=settings.tuning.max_chunks,
        unavailable_delay=settings.tuning.unavailable_delay,
        retry_delay=settings.tuning.retry_delay,
    )
    VALIDATIONS = Validations(
        site=site,
        user_email=cfg.user_email,
        user_pw=cfg.user_pw,
        base_url=cfg.site,
        client_key=cfg.client_key,
        client_secret=cfg.client_secret,
        backend=STORE_FILE,
        max_retry=settings.tuning.max_retry,
        max_requests=settings.tuning.max_requests,
        max_chunks=settings.tuning.max_chunks,
        unavailable_delay=settings.tuning.unavailable_delay,
        retry_delay=settings.tuning.retry_delay,
    )


@pytest.mark.order(index=301)
def test_version():
    """Check if version is defined."""
    logging.debug("package version: %s", ENTITIES.version)


# ------------
#  Taxo groups
# ------------
@pytest.mark.order(index=310)
def test_taxo_groups_store(capsys):
    """Store taxo groups to file."""
    file_json = Path.home() / settings.file.file_store / "taxo_groups_1.json.gz"
    if file_json.is_file():
        file_json.unlink()
    TAXO_GROUP.store()
    assert file_json.is_file()
    with gzip.open(file_json, "rb") as g:
        items_dict = json.loads(g.read().decode("utf-8"))
    assert len(items_dict["data"]) > 30


# ---------
#  Families
# ---------
@pytest.mark.order(index=311)
def test_families_store(capsys):
    """Store families to file."""
    file_json = Path.home() / settings.file.file_store / "families_1.json.gz"
    if file_json.is_file():
        file_json.unlink()
    FAMILIES.store()
    assert file_json.is_file()
    with gzip.open(file_json, "rb") as g:
        items_dict = json.loads(g.read().decode("utf-8"))
    assert len(items_dict["data"]) >= 20


# --------
#  Species
# --------
@pytest.mark.order(index=312)
@pytest.mark.slow
def test_species_store(capsys):
    """Store species to file."""
    file_json = Path.home() / settings.file.file_store / "species_1.json.gz"
    if file_json.is_file():
        file_json.unlink()
    SPECIES.store()
    assert file_json.is_file()
    with gzip.open(file_json, "rb") as g:
        items_dict = json.loads(g.read().decode("utf-8"))
    assert len(items_dict["data"]) > 11180


# ------------------
#  Territorial units
# ------------------
@pytest.mark.order(index=320)
def test_territorial_units_store(capsys):
    """Store territorial units to file."""
    file_json = Path.home() / settings.file.file_store / "territorial_units_1.json.gz"
    if file_json.is_file():
        file_json.unlink()
    TERRITORIAL_UNIT.store()
    assert file_json.is_file()
    with gzip.open(file_json, "rb") as g:
        items_dict = json.loads(g.read().decode("utf-8"))
    assert len(items_dict["data"]) > 100


# -----------------
#  LocalAdminUnits
# -----------------
@pytest.mark.order(index=321)
def test_local_admin_units_store(capsys):
    """Store local_admin_units to file."""
    file_json = Path.home() / settings.file.file_store / "local_admin_units_1.json.gz"
    if file_json.is_file():
        file_json.unlink()
    LOCAL_ADMIN_UNITS.store()
    assert file_json.is_file()
    with gzip.open(file_json, "rb") as g:
        items_dict = json.loads(g.read().decode("utf-8"))
    assert len(items_dict["data"]) >= 534


# -------
#  Places
# -------
@pytest.mark.order(index=322)
@pytest.mark.slow
def test_places_store(capsys):
    """Store places to file."""
    file_json = Path.home() / settings.file.file_store / "places_1.json.gz"
    if file_json.is_file():
        file_json.unlink()
    PLACES.store()
    assert file_json.is_file()
    with gzip.open(file_json, "rb") as g:
        items_dict = json.loads(g.read().decode("utf-8"))
    assert len(items_dict["data"]) >= 61


# ---------
#  Fields
# ---------
@pytest.mark.order(index=330)
@pytest.mark.slow
def test_fields_store(capsys):
    """Store fields to file."""
    file_json = Path.home() / settings.file.file_store / "field_details_1.json.gz"
    if file_json.is_file():
        file_json.unlink()
    FIELDS.store()
    assert file_json.is_file()
    with gzip.open(file_json, "rb") as g:
        items_dict = json.loads(g.read().decode("utf-8"))
    assert len(items_dict["data"]) >= 1


# ---------
#  Entities
# ---------
@pytest.mark.order(index=331)
def test_entities_store(capsys):
    """Store entities to file."""
    file_json = Path.home() / settings.file.file_store / "entities_1.json.gz"
    if file_json.is_file():
        file_json.unlink()
    ENTITIES.store()
    assert file_json.is_file()
    with gzip.open(file_json, "rb") as g:
        items_dict = json.loads(g.read().decode("utf-8"))
    assert len(items_dict["data"]) >= 16


# ----------
#  Observers
# ----------
@pytest.mark.order(index=332)
@pytest.mark.slow
def test_observers_store(capsys):
    """Store places to file."""
    file_json = Path.home() / settings.file.file_store / "observers_1.json.gz"
    if file_json.is_file():
        file_json.unlink()
    OBSERVERS.store()
    assert file_json.is_file()
    with gzip.open(file_json, "rb") as g:
        items_dict = json.loads(g.read().decode("utf-8"))
    assert len(items_dict["data"]) >= 4500


# ------------
#  Validations
# ------------
@pytest.mark.order(index=333)
@pytest.mark.slow
def test_validations_store(capsys):
    """Store territorial units to file."""
    file_json = Path.home() / settings.file.file_store / "validations_1.json.gz"
    if file_json.is_file():
        file_json.unlink()
    VALIDATIONS.store()
    assert file_json.is_file()
    with gzip.open(file_json, "rb") as g:
        items_dict = json.loads(g.read().decode("utf-8"))
    assert len(items_dict["data"]) > 100


# -------------
#  Observations
# -------------
@pytest.mark.order(index=340)
def test_observations_store_search_1_1(capsys):
    """Store observations from taxo_group 2 by specie to file, using search."""
    file_json = Path.home() / settings.file.file_store / "observations_2_138_1.json.gz"
    if file_json.is_file():
        file_json.unlink()
    OBSERVATIONS.store(2, method="search")
    assert file_json.is_file()


@pytest.mark.order(index=341)
@pytest.mark.slow
def test_observations_store_search_1_2(capsys):
    """Store observations from taxo_group 2 by specie to file, using search."""
    file_json = Path.home() / settings.file.file_store / "observations_2_138_1.json.gz"
    if file_json.is_file():
        file_json.unlink()
    OBSERVATIONS.store(2, method="search", short_version="1")
    assert file_json.is_file()


@pytest.mark.order(index=342)
@pytest.mark.slow
def test_observations_store_update_1_2(capsys):
    """Get updates for 0.5 day of observations from taxo_group 2
    by specie to file."""
    since = (datetime.now() - timedelta(days=0.5)).strftime("%H:%M:%S %d.%m.%Y")
    OBSERVATIONS.update(2, since)
    assert OBSERVATIONS.transfer_errors == 0
