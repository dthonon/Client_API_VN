#!/usr/bin/env python3
"""
Test each method of download_vn module.
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
from export_vn.evnconf import EvnConf

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level = logging.INFO)

def test_logging(cmdopt, capsys):
    with capsys.disabled():
        if cmdopt == 'DEBUG':
            logging.getLogger().setLevel(logging.DEBUG)
        logging.debug('Running with debug logging level')

# Using t07 site, that needs to be created first
SITE = 't07'

def test_site():
    """Check if configuration file exists."""
    cfg_file = Path(str(Path.home()) + '/.evn_' + SITE + '.ini')
    assert cfg_file.is_file()

# Get configuration for test site
CFG = EvnConf(SITE)
LOCAL_ADMIN_UNITS = LocalAdminUnits(CFG)
OBSERVATIONS = Observations(CFG)
PLACES = Places(CFG)
SPECIES = Species(CFG)
TAXO_GROUP = TaxoGroup(CFG)
TERRITORIAL_UNIT = TerritorialUnits(CFG)


# -----------------
#  LocalAdminUnits
# -----------------
def test_local_admin_units_store(capsys):
    """Store local_admin_units to file."""
    file_json = str(Path.home()) + '/' + CFG.file_store + 'local_admin_units_1.json.gz'
    if Path(file_json).is_file():
        Path(file_json).unlink()
    LOCAL_ADMIN_UNITS.store()
    assert Path(file_json).is_file()
    with gzip.open(file_json, 'rb') as g:
        items_dict = json.loads(g.read().decode('utf-8'))
    if SITE == 't38':
        assert len(items_dict['data']) >= 534
    elif SITE == 't07':
        assert len(items_dict['data']) >= 340

# -------------
#  Observations
# -------------
def test_observations_store_l_18(capsys):
    """Store observations to file, using list."""
    file_json = str(Path.home()) + '/' + CFG.file_store + 'observations_18_1.json.gz'
    if Path(file_json).is_file():
        Path(file_json).unlink()
    OBSERVATIONS.store(18, method='list')
    assert Path(file_json).is_file()
    with gzip.open(file_json, 'rb') as g:
     items_dict = json.loads(g.read().decode('utf-8'))
    assert len(items_dict['data']['sightings']) > 440


# -------
#  Places
# -------
def test_places_store(capsys):
    """Store places to file."""
    file_json = str(Path.home()) + '/' + CFG.file_store + 'places_1.json.gz'
    if Path(file_json).is_file():
        Path(file_json).unlink()
    PLACES.store()
    assert Path(file_json).is_file()
    with gzip.open(file_json, 'rb') as g:
        items_dict = json.loads(g.read().decode('utf-8'))
    if SITE == 't38':
        assert len(items_dict['data']) >= 31930
    elif SITE == 't07':
        assert len(items_dict['data']) >= 23566

# --------
#  Species
# --------
def test_species_store(capsys):
    """Store species to file."""
    file_json = str(Path.home()) + '/' + CFG.file_store + 'species_1.json.gz'
    if Path(file_json).is_file():
        Path(file_json).unlink()
    SPECIES.store()
    assert Path(file_json).is_file()
    with gzip.open(file_json, 'rb') as g:
        items_dict = json.loads(g.read().decode('utf-8'))
    assert len(items_dict['data']) > 11180

# ------------
#  Taxo groups
# ------------
def test_taxo_groups_store(capsys):
    """Store taxo groups to file."""
    file_json = str(Path.home()) + '/' + CFG.file_store + 'taxo_groups_1.json.gz'
    if Path(file_json).is_file():
        Path(file_json).unlink()
    TAXO_GROUP.store()
    assert Path(file_json).is_file()
    with gzip.open(file_json, 'rb') as g:
        items_dict = json.loads(g.read().decode('utf-8'))
    assert len(items_dict['data']) > 30

# ------------------
#  Territorial units
# ------------------
def test_territorial_units_store(capsys):
    """Store territorial units to file."""
    file_json = str(Path.home()) + '/' + CFG.file_store + 'territorial_units_1.json.gz'
    if Path(file_json).is_file():
        Path(file_json).unlink()
    TERRITORIAL_UNIT.store()
    assert Path(file_json).is_file()
    with gzip.open(file_json, 'rb') as g:
        items_dict = json.loads(g.read().decode('utf-8'))
    assert len(items_dict['data']) == 1
