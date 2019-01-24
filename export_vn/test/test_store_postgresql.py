#!/usr/bin/env python3
"""
Test each method of store_postgresql module.
Also test them as backend to download_vn.
"""
import logging
import pytest

from export_vn.download_vn import Entities, LocalAdminUnits, Observations, Places
from export_vn.download_vn import Species, TaxoGroup, TerritorialUnits
from export_vn.store_postgresql import StorePostgresql
from export_vn.evnconf import EvnConf

# Using faune-ardeche or faune-isere site, that needs to be created first
SITE = 't07'
#SITE = 't38'
FILE = '.evn_test.yaml'

# Get configuration for test site
CFG = EvnConf(FILE).site_list[SITE]
STORE_PG = StorePostgresql(CFG)
ENTITIES = Entities(CFG, STORE_PG.store)
LOCAL_ADMIN_UNITS = LocalAdminUnits(CFG, STORE_PG.store)
OBSERVATIONS = Observations(CFG, STORE_PG.store)
PLACES = Places(CFG, STORE_PG.store)
SPECIES = Species(CFG, STORE_PG.store)
TAXO_GROUP = TaxoGroup(CFG, STORE_PG.store)
TERRITORIAL_UNIT = TerritorialUnits(CFG, STORE_PG.store)

def test_version():
    """Check if version is defined."""
    logging.debug('package version: %s', STORE_PG.version)

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
def test_observations_api_pg_store():
    """Store observations of a taxo_group to database."""
    OBSERVATIONS.store(18, method='search')

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
