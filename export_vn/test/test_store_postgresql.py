#!/usr/bin/env python3
"""
Test each method of store_postgresql module.
Also test them as backend to download_vn.
"""
import sys
from pathlib import Path
import logging
import pytest
import json
import gzip

from export_vn.download_vn import DownloadVn, DownloadVnException
from export_vn.download_vn import Entities, LocalAdminUnits, Observations, Places
from export_vn.download_vn import Species, TaxoGroup, TerritorialUnits
from export_vn.store_postgresql import StorePostgresql
from export_vn.evnconf import EvnConf

# Using faune-ardeche or faune-isere site, that needs to be created first
SITE = 't07'
#SITE = 't38'
FILE = '.evn_test.yaml'

# Get configuration for test site
CFG = EvnConf(SITE, FILE)
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
def test_entities_api_pg_store(capsys):
    """Store entities to database."""
    ENTITIES.store()

# -----------------
# Local_admin_units
# -----------------
def test_local_admin_units_api_pg_store(capsys):
    """Store local_admin_units to database."""
    LOCAL_ADMIN_UNITS.store()

# -------------
#  Observations
# -------------
def test_observations_api_pg_store(capsys):
    """Store observations of a taxo_group to database."""
    OBSERVATIONS.store(18, method='search')

# -------
#  Places
# -------
def test_places_api_pg_store(capsys):
    """Store places to database."""
    PLACES.store()

# --------
#  Species
# --------
def test_species_api_pg_store(capsys):
    """Store species to database."""
    SPECIES.store()

# ------------
#  Taxo_groups
# ------------
def test_taxo_groups_api_pg_store(capsys):
    """Store taxonomic groups to database."""
    TAXO_GROUP.store()

# ------------------
#  Territorial units
# ------------------
def test_territorial_units_api_pg_store(capsys):
    """Store territorial units to database."""
    TERRITORIAL_UNIT.store()
