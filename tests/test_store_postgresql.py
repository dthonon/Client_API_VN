"""
Test each method of store_postgresql module.
Also test them as backend to download_vn.
"""
import logging
from datetime import datetime

import pytest

from export_vn.download_vn import (Entities, LocalAdminUnits, Observations,
                                   Places, Species, TaxoGroup,
                                   TerritorialUnits)
from export_vn.evnconf import EvnConf
from export_vn.store_postgresql import PostgresqlUtils, StorePostgresql

# Using faune-ardeche or faune-isere site, that needs to be created first
SITE = 't07'
# SITE = 't38'
FILE = '.evn_test.yaml'

# Get configuration for test site
CFG = EvnConf(FILE).site_list[SITE]
MANAGE_PG = PostgresqlUtils(CFG)
# Skip exception if json tables are not yet created
# Need to run test_create_json_tables first
try:
    STORE_PG = StorePostgresql(CFG)
    ENTITIES = Entities(CFG, STORE_PG)
    LOCAL_ADMIN_UNITS = LocalAdminUnits(CFG, STORE_PG)
    OBSERVATIONS = Observations(CFG, STORE_PG)
    PLACES = Places(CFG, STORE_PG)
    SPECIES = Species(CFG, STORE_PG)
    TAXO_GROUP = TaxoGroup(CFG, STORE_PG)
    TERRITORIAL_UNIT = TerritorialUnits(CFG, STORE_PG)
except Exception:
    pass


def test_version():
    """Check if version is defined."""
    logging.debug('package version: %s', STORE_PG.version)


# --------
# Database
# --------
def test_create_json_tables():
    """Create the tables, if not exists."""
    MANAGE_PG.create_json_tables()


# ----
# Logs
# ----
def test_log_pg_store():
    """Create a log entry."""
    STORE_PG.log(SITE, 'Test', 0, 0, comment='Test')


def test_increment_log_pg_store():
    """Create an increment entry."""
    STORE_PG.increment_log(SITE, 1, datetime.now())


def test_increment_get_pg_store():
    """Get an increment entry."""
    last_ts = STORE_PG.increment_get(SITE, 1)
    assert last_ts < datetime.now()


# --------
# Entities
# --------
def test_entities_api_pg_store():
    """Store entities to database."""
    ENTITIES.store()


# -----------------
# Local_admin_units
# -----------------
def test_local_adm_u_api_pg_store():
    """Store local_admin_units to database."""
    LOCAL_ADMIN_UNITS.store()


# -------------
#  Observations
# -------------
def test_observations_api_pg_store(capsys):
    """Store observations of a taxo_group to database."""
    with capsys.disabled():
        OBSERVATIONS.store(18, method='search')


def test_observations_api_pg_delete(capsys):
    """Delete some observations of a taxo_group to database."""
    nb_delete = STORE_PG.delete_obs([274830, 289120])
    assert nb_delete == 2


# -------
#  Places
# -------
@pytest.mark.slow
def test_places_api_pg_store():
    """Store places to database."""
    PLACES.store()


# --------
#  Species
# --------
@pytest.mark.slow
def test_species_api_pg_store():
    """Store species to database."""
    SPECIES.store()


# ------------
#  Taxo_groups
# ------------
def test_taxo_groups_api_pg_store():
    """Store taxonomic groups to database."""
    TAXO_GROUP.store()


# ------------------
#  Territorial units
# ------------------
def test_terr_u_api_pg_store():
    """Store territorial units to database."""
    TERRITORIAL_UNIT.store()


# -------------
#  Finalization
# -------------
def test_finish_pg_store():
    """Finalize tasks."""
    STORE_PG.__exit__(0, 1, 2)
