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
from export_vn.download_vn import LocalAdminUnits, Observations, Places
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
SITE = 't07'
#SITE = 't38'

# Get configuration for test site
CFG = EvnConf(SITE)
STORE_PG = StorePostgresql(CFG)
LOCAL_ADMIN_UNITS = LocalAdminUnits(CFG, STORE_PG.store)
OBSERVATIONS = Observations(CFG, STORE_PG.store)
PLACES = Places(CFG, STORE_PG.store)
SPECIES = Species(CFG, STORE_PG.store)
TAXO_GROUP = TaxoGroup(CFG, STORE_PG.store)
TERRITORIAL_UNIT = TerritorialUnits(CFG, STORE_PG.store)

# -----------------
# Local_admin_units
# -----------------
def test_local_admin_units_pg_store(capsys):
    """Store local_admin_units items_dict to database."""
    items_dict = {'data': [
        {
            'coord_lat': '44.888464632099',
            'coord_lon': '4.39188200157809',
            'id': '2096',
            'id_canton': '7',
            'insee': '07001',
            'name': 'Accons'
        },
        {
            'coord_lat': '44.5978645499893',
            'coord_lon': '4.33293707873124',
            'id': '2097',
            'id_canton': '7',
            'insee': '07002',
            'name': 'Ailhon'
        }]}
    STORE_PG.store('local_admin_units', str(1), items_dict)


# -------------
#  Observations
# -------------
