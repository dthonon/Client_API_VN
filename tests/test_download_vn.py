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

# Using faune-aura site, that needs to be defined in .evn_test.toml
FILE = ".evn_test.toml"
SITE = "aura"

# Get configuration for test site
settings = Dynaconf(
    settings_files=[FILE],
)


@pytest.mark.order(index=300)
def test_init():
    """Instantiate stores."""
    global STORE_FILE, ENTITIES, FAMILIES, FIELDS, LOCAL_ADMIN_UNITS
    global OBSERVATIONS, OBSERVERS, PLACES, SPECIES, TAXO_GROUP, TERRITORIAL_UNIT, VALIDATIONS
    STORE_FILE = StoreFile(file_enabled=settings["FILE"]["enabled"], file_store=settings["FILE"]["file_store"])
    ENTITIES = Entities(
        site=settings["SITE"]["name"],
        user_email=settings["SITE"]["user_email"],
        user_pw=settings["SITE"]["user_pw"],
        base_url=settings["SITE"]["URL"],
        client_key=settings["SITE"]["client_key"],
        client_secret=settings["SITE"]["client_secret"],
        backend=STORE_FILE,
        max_retry=settings["TUNING"]["max_retry"],
        max_requests=settings["TUNING"]["max_requests"],
        max_chunks=settings["TUNING"]["max_chunks"],
        unavailable_delay=settings["TUNING"]["unavailable_delay"],
        retry_delay=settings["TUNING"]["retry_delay"],
    )
    FAMILIES = Families(
        site=settings["SITE"]["name"],
        user_email=settings["SITE"]["user_email"],
        user_pw=settings["SITE"]["user_pw"],
        base_url=settings["SITE"]["URL"],
        client_key=settings["SITE"]["client_key"],
        client_secret=settings["SITE"]["client_secret"],
        backend=STORE_FILE,
        max_retry=settings["TUNING"]["max_retry"],
        max_requests=settings["TUNING"]["max_requests"],
        max_chunks=settings["TUNING"]["max_chunks"],
        unavailable_delay=settings["TUNING"]["unavailable_delay"],
        retry_delay=settings["TUNING"]["retry_delay"],
    )
    FIELDS = Fields(
        site=settings["SITE"]["name"],
        user_email=settings["SITE"]["user_email"],
        user_pw=settings["SITE"]["user_pw"],
        base_url=settings["SITE"]["URL"],
        client_key=settings["SITE"]["client_key"],
        client_secret=settings["SITE"]["client_secret"],
        backend=STORE_FILE,
        max_retry=settings["TUNING"]["max_retry"],
        max_requests=settings["TUNING"]["max_requests"],
        max_chunks=settings["TUNING"]["max_chunks"],
        unavailable_delay=settings["TUNING"]["unavailable_delay"],
        retry_delay=settings["TUNING"]["retry_delay"],
    )
    LOCAL_ADMIN_UNITS = LocalAdminUnits(
        site=settings["SITE"]["name"],
        user_email=settings["SITE"]["user_email"],
        user_pw=settings["SITE"]["user_pw"],
        base_url=settings["SITE"]["URL"],
        client_key=settings["SITE"]["client_key"],
        client_secret=settings["SITE"]["client_secret"],
        backend=STORE_FILE,
        max_retry=settings["TUNING"]["max_retry"],
        max_requests=settings["TUNING"]["max_requests"],
        max_chunks=settings["TUNING"]["max_chunks"],
        unavailable_delay=settings["TUNING"]["unavailable_delay"],
        retry_delay=settings["TUNING"]["retry_delay"],
    )
    OBSERVATIONS = Observations(
        site=settings["SITE"]["name"],
        user_email=settings["SITE"]["user_email"],
        user_pw=settings["SITE"]["user_pw"],
        base_url=settings["SITE"]["URL"],
        client_key=settings["SITE"]["client_key"],
        client_secret=settings["SITE"]["client_secret"],
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
        backend=STORE_FILE,
        start_date=settings["FILTER"].get("start_date", None),
        end_date=settings["FILTER"].get("end_date", None),
        type_date=settings["FILTER"].get("type_date", "sighting"),
        max_list_length=settings["TUNING"]["max_list_length"],
        max_retry=settings["TUNING"]["max_retry"],
        max_requests=settings["TUNING"]["max_requests"],
        max_chunks=settings["TUNING"]["max_chunks"],
        unavailable_delay=settings["TUNING"]["unavailable_delay"],
        retry_delay=settings["TUNING"]["retry_delay"],
        pid_kp=settings["TUNING"]["pid_kp"],
        pid_ki=settings["TUNING"]["pid_ki"],
        pid_kd=settings["TUNING"]["pid_kd"],
        pid_setpoint=settings["TUNING"]["pid_setpoint"],
        pid_limit_min=settings["TUNING"]["pid_limit_min"],
        pid_limit_max=settings["TUNING"]["pid_limit_max"],
        pid_delta_days=settings["TUNING"]["pid_delta_days"],
    )
    OBSERVERS = Observers(
        site=settings["SITE"]["name"],
        user_email=settings["SITE"]["user_email"],
        user_pw=settings["SITE"]["user_pw"],
        base_url=settings["SITE"]["URL"],
        client_key=settings["SITE"]["client_key"],
        client_secret=settings["SITE"]["client_secret"],
        backend=STORE_FILE,
        max_retry=settings["TUNING"]["max_retry"],
        max_requests=settings["TUNING"]["max_requests"],
        max_chunks=settings["TUNING"]["max_chunks"],
        unavailable_delay=settings["TUNING"]["unavailable_delay"],
        retry_delay=settings["TUNING"]["retry_delay"],
    )
    PLACES = Places(
        site=settings["SITE"]["name"],
        user_email=settings["SITE"]["user_email"],
        user_pw=settings["SITE"]["user_pw"],
        base_url=settings["SITE"]["URL"],
        client_key=settings["SITE"]["client_key"],
        client_secret=settings["SITE"]["client_secret"],
        backend=STORE_FILE,
        max_retry=settings["TUNING"]["max_retry"],
        max_requests=settings["TUNING"]["max_requests"],
        max_chunks=settings["TUNING"]["max_chunks"],
        unavailable_delay=settings["TUNING"]["unavailable_delay"],
        retry_delay=settings["TUNING"]["retry_delay"],
    )
    SPECIES = Species(
        site=settings["SITE"]["name"],
        user_email=settings["SITE"]["user_email"],
        user_pw=settings["SITE"]["user_pw"],
        base_url=settings["SITE"]["URL"],
        client_key=settings["SITE"]["client_key"],
        client_secret=settings["SITE"]["client_secret"],
        backend=STORE_FILE,
        max_retry=settings["TUNING"]["max_retry"],
        max_requests=settings["TUNING"]["max_requests"],
        max_chunks=settings["TUNING"]["max_chunks"],
        unavailable_delay=settings["TUNING"]["unavailable_delay"],
        retry_delay=settings["TUNING"]["retry_delay"],
    )
    TAXO_GROUP = TaxoGroup(
        site=settings["SITE"]["name"],
        user_email=settings["SITE"]["user_email"],
        user_pw=settings["SITE"]["user_pw"],
        base_url=settings["SITE"]["URL"],
        client_key=settings["SITE"]["client_key"],
        client_secret=settings["SITE"]["client_secret"],
        backend=STORE_FILE,
        max_retry=settings["TUNING"]["max_retry"],
        max_requests=settings["TUNING"]["max_requests"],
        max_chunks=settings["TUNING"]["max_chunks"],
        unavailable_delay=settings["TUNING"]["unavailable_delay"],
        retry_delay=settings["TUNING"]["retry_delay"],
    )
    TERRITORIAL_UNIT = TerritorialUnits(
        site=settings["SITE"]["name"],
        user_email=settings["SITE"]["user_email"],
        user_pw=settings["SITE"]["user_pw"],
        base_url=settings["SITE"]["URL"],
        client_key=settings["SITE"]["client_key"],
        client_secret=settings["SITE"]["client_secret"],
        backend=STORE_FILE,
        max_retry=settings["TUNING"]["max_retry"],
        max_requests=settings["TUNING"]["max_requests"],
        max_chunks=settings["TUNING"]["max_chunks"],
        unavailable_delay=settings["TUNING"]["unavailable_delay"],
        retry_delay=settings["TUNING"]["retry_delay"],
    )
    VALIDATIONS = Validations(
        site=settings["SITE"]["name"],
        user_email=settings["SITE"]["user_email"],
        user_pw=settings["SITE"]["user_pw"],
        base_url=settings["SITE"]["URL"],
        client_key=settings["SITE"]["client_key"],
        client_secret=settings["SITE"]["client_secret"],
        backend=STORE_FILE,
        max_retry=settings["TUNING"]["max_retry"],
        max_requests=settings["TUNING"]["max_requests"],
        max_chunks=settings["TUNING"]["max_chunks"],
        unavailable_delay=settings["TUNING"]["unavailable_delay"],
        retry_delay=settings["TUNING"]["retry_delay"],
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
    file_json = Path.home() / settings["FILE"]["file_store"] / "taxo_groups_1.json.gz"
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
    file_json = Path.home() / settings["FILE"]["file_store"] / "families_1.json.gz"
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
    file_json = Path.home() / settings["FILE"]["file_store"] / "species_1.json.gz"
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
    file_json = Path.home() / settings["FILE"]["file_store"] / "territorial_units_1.json.gz"
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
    file_json = Path.home() / settings["FILE"]["file_store"] / "local_admin_units_1.json.gz"
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
    file_json = Path.home() / settings["FILE"]["file_store"] / "places_1.json.gz"
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
    file_json = Path.home() / settings["FILE"]["file_store"] / "field_details_1.json.gz"
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
    file_json = Path.home() / settings["FILE"]["file_store"] / "entities_1.json.gz"
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
    file_json = Path.home() / settings["FILE"]["file_store"] / "observers_1.json.gz"
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
    file_json = Path.home() / settings["FILE"]["file_store"] / "validations_1.json.gz"
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
    """Store observations from taxo_group 28, territorial_unit 38 to file, using search."""
    file_json = Path.home() / settings["FILE"]["file_store"] / "observations_28_138_1.json.gz"
    if file_json.is_file():
        file_json.unlink()
    OBSERVATIONS.store(id_taxo_group=28, territorial_unit_ids=["38"], method="search")
    assert file_json.is_file()


@pytest.mark.order(index=341)
@pytest.mark.slow
def test_observations_store_search_1_2(capsys):
    """Store observations from taxo_group 2 by specie to file, using search."""
    file_json = Path.home() / settings["FILE"]["file_store"] / "observations_2_138_1.json.gz"
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
