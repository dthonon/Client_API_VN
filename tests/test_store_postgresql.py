"""
Test each method of store_postgresql module.
Also test them as backend to download_vn.
"""
import logging
from datetime import datetime
from unittest.mock import patch

import pytest
from export_vn import transfer_vn

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
from export_vn.store_postgresql import PostgresqlUtils, ReadPostgresql, StorePostgresql

# Using faune-ardeche or faune-isere site, that needs to be created first
# SITE = "t07"
SITE = "t38"
FILE = ".evn_test.yaml"

# Get configuration for test site
CFG = EvnConf(FILE).site_list[SITE]
MANAGE_PG = PostgresqlUtils(CFG)


@pytest.mark.order(index=200)
def test_init():
    """Initialize test database"""
    with patch("sys.argv", ["py.test", "--db_drop", ".evn_test.yaml"]):
        transfer_vn.run()
    with patch("sys.argv", ["py.test", "--db_create", ".evn_test.yaml"]):
        transfer_vn.run()
    MANAGE_PG.create_json_tables()
    with patch("sys.argv", ["py.test", "--col_tables_create", ".evn_test.yaml"]):
        transfer_vn.run()
    # Instantiate stores.
    global STORE_PG, READ_PG, ENTITIES, FAMILIES, FIELDS, LOCAL_ADMIN_UNITS
    global OBSERVATIONS, OBSERVERS, PLACES, SPECIES, TAXO_GROUP, TERRITORIAL_UNIT, VALIDATIONS
    STORE_PG = StorePostgresql(CFG)
    READ_PG = ReadPostgresql(CFG)
    ENTITIES = Entities(CFG, STORE_PG)
    FAMILIES = Families(CFG, STORE_PG)
    FIELDS = Fields(CFG, STORE_PG)
    LOCAL_ADMIN_UNITS = LocalAdminUnits(CFG, STORE_PG)
    OBSERVATIONS = Observations(CFG, STORE_PG)
    OBSERVERS = Observers(CFG, STORE_PG)
    PLACES = Places(CFG, STORE_PG)
    SPECIES = Species(CFG, STORE_PG)
    TAXO_GROUP = TaxoGroup(CFG, STORE_PG)
    TERRITORIAL_UNIT = TerritorialUnits(CFG, STORE_PG)
    VALIDATIONS = Validations(CFG, STORE_PG)


@pytest.mark.order(index=201)
def test_version():
    """Check if version is defined."""
    logging.debug("package version: %s", STORE_PG.version)


# ----
# Logs
# ----
@pytest.mark.order(index=220)
class TestLogs:
    def test_log_pg_store(self):
        """Create a log entry."""
        STORE_PG.log(SITE, "Test", 0, 0, comment="Test")

    def test_increment_log_pg_store(self):
        """Create an increment entry."""
        STORE_PG.increment_log(SITE, 1, datetime.now())

    def test_increment_get_pg_store(self):
        """Get an increment entry."""
        last_ts = STORE_PG.increment_get(SITE, 1)
        if last_ts is not None:
            assert last_ts < datetime.now()


# ------------
#  Taxo_groups
# ------------
@pytest.mark.order(index=230)
def test_taxo_groups_api_pg_store():
    """Store taxonomic groups to database."""
    TAXO_GROUP.store()


# --------
# Families
# --------
@pytest.mark.order(index=231)
@pytest.mark.slow
def test_families_api_pg_store():
    """Store families to database."""
    FAMILIES.store()


# --------
#  Species
# --------
@pytest.mark.order(index=232)
@pytest.mark.slow
def test_species_api_pg_store():
    """Store species to database."""
    SPECIES.store()


# ------------------
#  Territorial units
# ------------------
@pytest.mark.order(index=240)
def test_terr_u_api_pg_store():
    """Store territorial units to database."""
    TERRITORIAL_UNIT.store()


@pytest.mark.order(index=241)
def test_terr_u_api_pg_read():
    """Read territorial units from database."""
    t_u = READ_PG.read("territorial_units")
    assert len(t_u) == 1


# -----------------
# Local_admin_units
# -----------------
@pytest.mark.order(index=242)
@pytest.mark.slow
def test_local_adm_u_api_pg_store():
    """Store local_admin_units to database."""
    LOCAL_ADMIN_UNITS.store()


@pytest.mark.order(index=243)
@pytest.mark.slow
def test_local_adm_u_api_pg_read():
    """Read local admin units from database."""
    l_a_u = READ_PG.read("local_admin_units")
    assert len(l_a_u) > 339


# -------
#  Places
# -------
@pytest.mark.order(index=244)
@pytest.mark.slow
def test_places_api_pg_store():
    """Store places to database."""
    PLACES.store()


# ------
# Fields
# ------
@pytest.mark.order(index=250)
@pytest.mark.slow
def test_fields_api_pg_store():
    """Store fields to database."""
    FIELDS.store()


# --------
# Entities
# --------
@pytest.mark.order(index=251)
def test_entities_api_pg_store():
    """Store entities to database."""
    ENTITIES.store()


# ---------
# Observers
# ---------
@pytest.mark.order(index=252)
@pytest.mark.slow
def test_observers_api_pg_store():
    """Store observers to database."""
    OBSERVERS.store()


# -------------
#  Observations
# -------------
@pytest.mark.order(index=260)
@pytest.mark.slow
def test_observations_api_pg_store(capsys):
    """Store observations of a taxo_group to database."""
    with capsys.disabled():
        OBSERVATIONS.store(18, method="search")


# -------------
#  Finalization
# -------------
@pytest.mark.order(index=299)
def test_finish_pg_store():
    """Finalize tasks."""
    STORE_PG.__exit__(0, 1, 2)
