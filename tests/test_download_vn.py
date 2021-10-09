"""
Test each method of download_vn module, using file store.
"""
import gzip
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

import pytest
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
from export_vn.evnconf import EvnConf
from export_vn.store_file import StoreFile

# Using faune-ardeche or faune-isere site, that needs to be created first
# SITE = "t07"
SITE = "t38"
FILE = ".evn_test.yaml"

# Get configuration for test site
CFG = EvnConf(FILE).site_list[SITE]


@pytest.mark.order(index=300)
def test_init():
    """Instantiate stores."""
    global STORE_FILE, ENTITIES, FAMILIES, FIELDS, LOCAL_ADMIN_UNITS
    global OBSERVATIONS, OBSERVERS, PLACES, SPECIES, TAXO_GROUP, TERRITORIAL_UNIT, VALIDATIONS
    STORE_FILE = StoreFile(CFG)
    ENTITIES = Entities(CFG, STORE_FILE)
    FAMILIES = Families(CFG, STORE_FILE)
    FIELDS = Fields(CFG, STORE_FILE)
    LOCAL_ADMIN_UNITS = LocalAdminUnits(CFG, STORE_FILE)
    OBSERVATIONS = Observations(CFG, STORE_FILE)
    OBSERVERS = Observers(CFG, STORE_FILE)
    PLACES = Places(CFG, STORE_FILE)
    SPECIES = Species(CFG, STORE_FILE)
    TAXO_GROUP = TaxoGroup(CFG, STORE_FILE)
    TERRITORIAL_UNIT = TerritorialUnits(CFG, STORE_FILE)
    VALIDATIONS = Validations(CFG, STORE_FILE)


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
    file_json = str(Path.home()) + "/" + CFG.file_store + "taxo_groups_1.json.gz"
    if Path(file_json).is_file():
        Path(file_json).unlink()
    TAXO_GROUP.store()
    assert Path(file_json).is_file()
    with gzip.open(file_json, "rb") as g:
        items_dict = json.loads(g.read().decode("utf-8"))
    assert len(items_dict["data"]) > 30


# ---------
#  Families
# ---------
@pytest.mark.order(index=311)
def test_families_store(capsys):
    """Store families to file."""
    file_json = str(Path.home()) + "/" + CFG.file_store + "families_1.json.gz"
    if Path(file_json).is_file():
        Path(file_json).unlink()
    FAMILIES.store()
    assert Path(file_json).is_file()
    with gzip.open(file_json, "rb") as g:
        items_dict = json.loads(g.read().decode("utf-8"))
    if SITE == "t38":
        assert len(items_dict["data"]) >= 20
    elif SITE == "t07":
        assert len(items_dict["data"]) >= 8


# --------
#  Species
# --------
@pytest.mark.order(index=312)
@pytest.mark.slow
def test_species_store(capsys):
    """Store species to file."""
    file_json = str(Path.home()) + "/" + CFG.file_store + "species_1.json.gz"
    if Path(file_json).is_file():
        Path(file_json).unlink()
    SPECIES.store()
    assert Path(file_json).is_file()
    with gzip.open(file_json, "rb") as g:
        items_dict = json.loads(g.read().decode("utf-8"))
    assert len(items_dict["data"]) > 11180


# ------------------
#  Territorial units
# ------------------
@pytest.mark.order(index=320)
def test_territorial_units_store(capsys):
    """Store territorial units to file."""
    file_json = str(Path.home()) + "/" + CFG.file_store + "territorial_units_1.json.gz"
    if Path(file_json).is_file():
        Path(file_json).unlink()
    TERRITORIAL_UNIT.store()
    assert Path(file_json).is_file()
    with gzip.open(file_json, "rb") as g:
        items_dict = json.loads(g.read().decode("utf-8"))
    assert len(items_dict["data"]) == 1


# -----------------
#  LocalAdminUnits
# -----------------
@pytest.mark.order(index=321)
def test_local_admin_units_store(capsys):
    """Store local_admin_units to file."""
    file_json = str(Path.home()) + "/" + CFG.file_store + "local_admin_units_1.json.gz"
    if Path(file_json).is_file():
        Path(file_json).unlink()
    LOCAL_ADMIN_UNITS.store()
    assert Path(file_json).is_file()
    with gzip.open(file_json, "rb") as g:
        items_dict = json.loads(g.read().decode("utf-8"))
    if SITE == "t38":
        assert len(items_dict["data"]) >= 534
    elif SITE == "t07":
        assert len(items_dict["data"]) >= 340


# -------
#  Places
# -------
@pytest.mark.order(index=322)
@pytest.mark.slow
def test_places_store(capsys):
    """Store places to file."""
    file_json = str(Path.home()) + "/" + CFG.file_store + "places_1.json.gz"
    if Path(file_json).is_file():
        Path(file_json).unlink()
    PLACES.store()
    assert Path(file_json).is_file()
    with gzip.open(file_json, "rb") as g:
        items_dict = json.loads(g.read().decode("utf-8"))
    if SITE == "t38":
        assert len(items_dict["data"]) >= 31930
    elif SITE == "t07":
        assert len(items_dict["data"]) >= 23566


# ---------
#  Fields
# ---------
@pytest.mark.order(index=330)
@pytest.mark.slow
def test_fields_store(capsys):
    """Store fields to file."""
    file_json = str(Path.home()) + "/" + CFG.file_store + "field_details_1.json.gz"
    if Path(file_json).is_file():
        Path(file_json).unlink()
    FIELDS.store()
    assert Path(file_json).is_file()
    with gzip.open(file_json, "rb") as g:
        items_dict = json.loads(g.read().decode("utf-8"))
    if SITE == "t38":
        assert len(items_dict["data"]) >= 4
    elif SITE == "t07":
        assert len(items_dict["data"]) >= 8


# ---------
#  Entities
# ---------
@pytest.mark.order(index=331)
def test_entities_store(capsys):
    """Store entities to file."""
    file_json = str(Path.home()) + "/" + CFG.file_store + "entities_1.json.gz"
    if Path(file_json).is_file():
        Path(file_json).unlink()
    ENTITIES.store()
    assert Path(file_json).is_file()
    with gzip.open(file_json, "rb") as g:
        items_dict = json.loads(g.read().decode("utf-8"))
    if SITE == "t38":
        assert len(items_dict["data"]) >= 16
    elif SITE == "t07":
        assert len(items_dict["data"]) >= 8


# ----------
#  Observers
# ----------
@pytest.mark.order(index=332)
@pytest.mark.slow
def test_observers_store(capsys):
    """Store places to file."""
    file_json = str(Path.home()) + "/" + CFG.file_store + "observers_1.json.gz"
    if Path(file_json).is_file():
        Path(file_json).unlink()
    OBSERVERS.store()
    assert Path(file_json).is_file()
    with gzip.open(file_json, "rb") as g:
        items_dict = json.loads(g.read().decode("utf-8"))
    if SITE == "t38":
        assert len(items_dict["data"]) >= 4500
    elif SITE == "t07":
        assert len(items_dict["data"]) >= 2400


# ------------
#  Validations
# ------------
@pytest.mark.order(index=333)
@pytest.mark.slow
def test_validations_store(capsys):
    """Store territorial units to file."""
    file_json = str(Path.home()) + "/" + CFG.file_store + "validations_1.json.gz"
    if Path(file_json).is_file():
        Path(file_json).unlink()
    VALIDATIONS.store()
    assert Path(file_json).is_file()
    with gzip.open(file_json, "rb") as g:
        items_dict = json.loads(g.read().decode("utf-8"))
    assert len(items_dict["data"]) > 100


# -------------
#  Observations
# -------------
@pytest.mark.order(index=340)
def test_observations_store_search_1_1(capsys):
    """Store observations from taxo_group 2 by specie to file, using search."""
    file_json = str(Path.home()) + "/" + CFG.file_store + "observations_2_1.json.gz"
    if Path(file_json).is_file():
        Path(file_json).unlink()
    OBSERVATIONS.store(2, method="search")
    assert Path(file_json).is_file()


@pytest.mark.order(index=341)
@pytest.mark.slow
def test_observations_store_search_1_2(capsys):
    """Store observations from taxo_group 2 by specie to file, using search."""
    file_json = str(Path.home()) + "/" + CFG.file_store + "observations_2_1.json.gz"
    if Path(file_json).is_file():
        Path(file_json).unlink()
    OBSERVATIONS.store(2, method="search", short_version="1")
    assert Path(file_json).is_file()


@pytest.mark.order(index=342)
@pytest.mark.slow
def test_observations_store_update_1_2(capsys):
    """Get updates for 0.5 day of observations from taxo_group 2
    by specie to file."""
    since = (datetime.now() - timedelta(days=0.5)).strftime("%H:%M:%S %d.%m.%Y")
    OBSERVATIONS.update(2, since)
    assert OBSERVATIONS.transfer_errors == 0
