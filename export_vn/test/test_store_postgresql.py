#!/usr/bin/env python3
"""
Test each method of store_postgresql module.
"""
import sys
from pathlib import Path
import logging
import pytest
import json
import gzip

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

def test_site():
    """Check if configuration file exists."""
    cfg_file = Path(str(Path.home()) + '/.evn_' + SITE + '.ini')
    assert cfg_file.is_file()

# Get configuration for test site
CFG = EvnConf(SITE)
STORE_PG = StorePostgresql(CFG)

# ------------
# General data
# ------------
def test_general_data_pg_store(capsys):
    """Store general items_dict to file."""
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
    STORE_PG.store('general_data', str(1), items_dict)



# -------------
#  Observations
# -------------
