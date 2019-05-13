#!/usr/bin/env python3
"""
Test each method of download_vn module, using file store.
"""
import gzip
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from export_vn.download_vn import (DownloadVn, DownloadVnException, Entities,
                                   LocalAdminUnits, Observations, Observers,
                                   Places, Species, TaxoGroup,
                                   TerritorialUnits)
from export_vn.evnconf import EvnConf
from export_vn.store_file import StoreFile

# Using faune-ardeche or faune-isere site, that needs to be created first
SITE = 't07'
#SITE = 't38'
FILE = '.evn_test.yaml'

# Get configuration for test site
CFG = EvnConf(FILE).site_list[SITE]
STORE_FILE = StoreFile(CFG)
ENTITIES = Entities(CFG, STORE_FILE)
LOCAL_ADMIN_UNITS = LocalAdminUnits(CFG, STORE_FILE)
OBSERVATIONS = Observations(CFG, STORE_FILE)
OBSERVERS = Observers(CFG, STORE_FILE)
PLACES = Places(CFG, STORE_FILE)
SPECIES = Species(CFG, STORE_FILE)
TAXO_GROUP = TaxoGroup(CFG, STORE_FILE)
TERRITORIAL_UNIT = TerritorialUnits(CFG, STORE_FILE)


def test_version():
    """Check if version is defined."""
    logging.debug('package version: %s', ENTITIES.version)


# ---------
#  Entities
# ---------
def test_entities_store(capsys):
    """Store entities to file."""
    file_json = str(Path.home()) + '/' + CFG.file_store + 'entities_1.json.gz'
    if Path(file_json).is_file():
        Path(file_json).unlink()
    ENTITIES.store()
    assert Path(file_json).is_file()
    with gzip.open(file_json, 'rb') as g:
        items_dict = json.loads(g.read().decode('utf-8'))
    if SITE == 't38':
        assert len(items_dict['data']) >= 20
    elif SITE == 't07':
        assert len(items_dict['data']) >= 8


# -----------------
#  LocalAdminUnits
# -----------------
def test_local_admin_units_store(capsys):
    """Store local_admin_units to file."""
    file_json = str(
        Path.home()) + '/' + CFG.file_store + 'local_admin_units_1.json.gz'
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
def test_observations_store_list_l_18(capsys):
    """Store observations from taxo_group 18 in 1 call to file, using list."""
    file_json = str(
        Path.home()) + '/' + CFG.file_store + 'observations_18_1.json.gz'
    if Path(file_json).is_file():
        Path(file_json).unlink()
    OBSERVATIONS.store(18, method='list')
    assert Path(file_json).is_file()
    with gzip.open(file_json, 'rb') as g:
        items_dict = json.loads(g.read().decode('utf-8'))
    if SITE == 't38':
        assert len(items_dict['data']['sightings']) >= 440
    elif SITE == 't07':
        assert len(items_dict['data']['sightings']) >= 82


def test_observations_store_list_2_18(capsys):
    """Store observations from taxo_group 18 by specie to file, using list."""
    file_json = str(
        Path.home()) + '/' + CFG.file_store + 'observations_18_19703.json.gz'
    if Path(file_json).is_file():
        Path(file_json).unlink()
    OBSERVATIONS.store(18, method='list', by_specie=True)
    assert Path(file_json).is_file()
    with gzip.open(file_json, 'rb') as g:
        items_dict = json.loads(g.read().decode('utf-8'))
    if SITE == 't38':
        assert len(items_dict['data']['sightings']) >= 440
    elif SITE == 't07':
        assert len(items_dict['data']['sightings']) >= 18


def test_observations_store_search_1_1(capsys):
    """Store observations from taxo_group 2 by specie to file, using search."""
    file_json = str(
        Path.home()) + '/' + CFG.file_store + 'observations_2_1.json.gz'
    if Path(file_json).is_file():
        Path(file_json).unlink()
    OBSERVATIONS.store(2, method='search')
    assert Path(file_json).is_file()


def test_observations_store_search_1_2(capsys):
    """Store observations from taxo_group 2 by specie to file, using search."""
    file_json = str(
        Path.home()) + '/' + CFG.file_store + 'observations_2_1.json.gz'
    if Path(file_json).is_file():
        Path(file_json).unlink()
    OBSERVATIONS.store(2, method='search', short_version='1')
    assert Path(file_json).is_file()


def test_observations_store_update_1_2(capsys):
    """Get updates for 0.5 day of observations from taxo_group 2 by specie to file."""
    since = (datetime.now() -
             timedelta(days=0.5)).strftime('%H:%M:%S %d.%m.%Y')
    OBSERVATIONS.update(2, since)
    assert OBSERVATIONS.transfer_errors == 0


# ----------
#  Observers
# ----------
def test_observers_store(capsys):
    """Store places to file."""
    file_json = str(Path.home()) + '/' + CFG.file_store + 'observers_1.json.gz'
    if Path(file_json).is_file():
        Path(file_json).unlink()
    OBSERVERS.store()
    assert Path(file_json).is_file()
    with gzip.open(file_json, 'rb') as g:
        items_dict = json.loads(g.read().decode('utf-8'))
    if SITE == 't38':
        assert len(items_dict['data']) >= 4500
    elif SITE == 't07':
        assert len(items_dict['data']) >= 2400


# -------
#  Places
# -------
@pytest.mark.slow
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
@pytest.mark.slow
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
    file_json = str(
        Path.home()) + '/' + CFG.file_store + 'taxo_groups_1.json.gz'
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
    file_json = str(
        Path.home()) + '/' + CFG.file_store + 'territorial_units_1.json.gz'
    if Path(file_json).is_file():
        Path(file_json).unlink()
    TERRITORIAL_UNIT.store()
    assert Path(file_json).is_file()
    with gzip.open(file_json, 'rb') as g:
        items_dict = json.loads(g.read().decode('utf-8'))
    assert len(items_dict['data']) == 1
