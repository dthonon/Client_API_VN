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

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level = logging.INFO)

def test_logging(cmdopt, capsys):
    with capsys.disabled():
        if cmdopt == 'DEBUG':
            logging.getLogger().setLevel(logging.DEBUG)
        logging.debug('Running with debug logging level')

# Using faune-ardeche or faune-isere site, that needs to be created first
#SITE = 't07'
SITE = 't38'

# Get configuration for test site
CFG = EvnConf(SITE)
STORE_PG = StorePostgresql(CFG)
ENTITIES = Entities(CFG, STORE_PG.store)
LOCAL_ADMIN_UNITS = LocalAdminUnits(CFG, STORE_PG.store)
OBSERVATIONS = Observations(CFG, STORE_PG.store)
PLACES = Places(CFG, STORE_PG.store)
SPECIES = Species(CFG, STORE_PG.store)
TAXO_GROUP = TaxoGroup(CFG, STORE_PG.store)
TERRITORIAL_UNIT = TerritorialUnits(CFG, STORE_PG.store)

# --------
# Entities
# --------
def test_entities_api_pg_store(capsys):
    """Store entities to file."""
    ENTITIES.store()

# -----------------
# Local_admin_units
# -----------------
def test_local_admin_units_api_pg_store(capsys):
    """Store local_admin_units to file."""
    LOCAL_ADMIN_UNITS.store()

# -------------
#  Observations
# -------------

# --------
#  Species
# --------
def test_species_api_pg_store(capsys):
    """Store species to file."""
    SPECIES.store()

# ------------------
#  Territorial units
# ------------------
def test_territorial_units_api_pg_store(capsys):
    """Store territorial units to file."""
    TERRITORIAL_UNIT.store()
