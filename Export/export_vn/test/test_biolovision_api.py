#!/usr/bin/env python3
"""
Test each API call of biolovision_api module.
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path
import logging
import requests
import pytest

from export_vn.biolovision_api import BiolovisionAPI, HTTPError, MaxChunksError
from export_vn.evnconf import EvnConf

def test_logging(cmdopt):
    if cmdopt == 'DEBUG':
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level = logging.DEBUG)
    else:
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level = logging.INFO)

# Using t38 site, that needs to be created first
SITE = 't38'

def test_site():
    """Check if configuration file exists."""
    cfg_file = Path(str(Path.home()) + '/.evn_' + SITE + '.ini')
    assert cfg_file.is_file()

# Get configuration for test site
CFG = EvnConf(SITE)
EVN_API = BiolovisionAPI(CFG, max_retry=5,
                         max_requests=sys.maxsize, max_chunks = 10)
EVN_API_ERR = BiolovisionAPI(CFG, max_retry=1,
                             max_requests=1, max_chunks = 1)

# ------------------------------------
#  Local admin units controler methods
# ------------------------------------
def test_local_admin_units_get(capsys):
    """Get a single local admin unit."""
    logging.debug('Getting local admin unit #s', '14693')
    local_admin_unit = EVN_API.local_admin_units_get('14693')
    assert EVN_API.transfer_errors == 0
    assert local_admin_unit == {
        'data': [{
            'name': 'Allevard',
            'coord_lon': '6.11353081638029',
            'id_canton': '39',
            'coord_lat': '45.3801954314357',
            'id': '14693',
            'insee': '38006'}]}

def test_local_admin_units_list_all(capsys):
    """Get list of all local admin units."""
    local_admin_units_list = EVN_API.local_admin_units_list()
    logging.info('Received %d local admin units', len(local_admin_units_list['data']))
    assert EVN_API.transfer_errors == 0
    assert len(local_admin_units_list['data']) >= 534

def test_local_admin_units_list_1(capsys):
    """Get a list of local_admin_units from territorial unit 39 (Isère)."""
    local_admin_units_list = EVN_API.local_admin_units_list('39')
    with capsys.disabled():
        print('territorial unit 39 ==> {} local admin unit '.format(len(local_admin_units_list['data'])))
    assert EVN_API.transfer_errors == 0
    assert len(local_admin_units_list['data']) >= 534
    assert local_admin_units_list['data'][0]['name'] == 'Abrets (Les)'

# ------------------------------
# Observations controler methods
# ------------------------------

def test_observations_diff(capsys):
    """Get list of diffs from last day."""
    since = (datetime.now() - timedelta(days=1)).strftime('%H:%M:%S %d.%m.%Y')
    with capsys.disabled():
        print('\nGetting updates since {}'.format(since))
    diff = EVN_API.observations_diff('1', since)
    assert EVN_API.transfer_errors == 0
    assert len(diff) > 0
    diff = EVN_API.observations_diff('1', since, 'only_modified')
    assert EVN_API.transfer_errors == 0
    diff = EVN_API.observations_diff('1', since, 'only_deleted')
    assert EVN_API.transfer_errors == 0

def test_observations_get(capsys):
    """Get a specific sighting."""
    sighting = EVN_API.observations_get('2246086')
    # with capsys.disabled():
    #     timing = sighting['data']['sightings'][0]['observers'][0]['timing']['@timestamp']
    #     timing_datetime = datetime.fromtimestamp(float(timing))
    #     print('\ntiming_datetime datetime = {}'.format(
    #         timing_datetime.strftime('%Y-%m-%d %H:%M:%S')))
    #     insert_date = sighting['data']['sightings'][0]['observers'][0]['insert_date']['@timestamp']
    #     insert_datetime = datetime.fromtimestamp(float(insert_date))
    #     print('insert_date datetime = {}'.format(insert_datetime.strftime('%Y-%m-%d %H:%M:%S')))
    assert sighting == {
        'data':{
            'sightings': [{
                'place': {
                    'county': '38',
                    'insee': '38185',
                    'municipality': 'Grenoble',
                    'country': '',
                    'altitude': '215',
                    'coord_lat': '45.187677239404',
                    'name': 'Museum (Parc du Museum)',
                    'coord_lon': '5.735372035327',
                    '@id': '100197',
                    'loc_precision': '0',
                    'place_type': 'precise'},
                'date': {
                    '@notime': '1',
                    '@offset': '7200',
                    '@ISO8601': '2018-09-15T00:00:00+02:00',
                    '@timestamp': '1536962400',
                    '#text': 'samedi 15 septembre 2018'},
                'species': {
                    'latin_name': 'Anas platyrhynchos',
                    'rarity': 'verycommon',
                    'sys_order': '262',
                    'name': 'Canard colvert',
                    '@id': '86',
                    'taxonomy': '1'},
                'observers':[{
                    'estimation_code': 'MINIMUM',
                    'count': '15',
                    'id_sighting': '2246086',
                    'insert_date':  {
                        '#text': 'samedi 15 septembre 2018, 19:45:01',
                        '@ISO8601': '2018-09-15T19:45:01+02:00',
                        '@notime': '0',
                        '@offset': '7200',
                        '@timestamp': '1537033501'},
                    'atlas_grid_name': 'E091N645',
                    'name': 'Daniel Thonon',
                    'medias':[{
                        'media_is_hidden': '0',
                        'filename': '3_1537024802877-15194452-5272.jpg',
                        'path': 'http://media.biolovision.net/data.biolovision.net/2018-09',
                        'insert_date': {
                            '@notime': '0',
                            '@offset': '3600',
                            '@ISO8601': '1970-01-01T01:33:38+01:00',
                            '@timestamp': '2018',
                            '#text': 'jeudi 1 janvier 1970, 01:33:38'},
                        'metadata': '',
                        'type': 'PHOTO',
                        '@id': '49174'}],
                    '@uid': '11675',
                    'precision': 'precise',
                    'id_universal': '65_71846872',
                    'traid': '33',
                    'timing': {
                        '@notime': '0',
                        '@offset': '7200',
                        '@ISO8601': '2018-09-15T17:19:16+02:00',
                        '@timestamp': '1537024756',
                        '#text': 'samedi 15 septembre 2018, 17:19:16'},
                    'altitude': '215',
                    'source': 'WEB',
                    'coord_lat': '45.18724',
                    'flight_number': '1',
                    'anonymous': '0',
                    'coord_lon': '5.735458',
                    '@id': '33'}]}]}}

# -------------------------
#  Places controler methods
# -------------------------
def test_places_get(capsys):
    """Get a single place."""
    logging.debug('Getting place #s', '14693')
    place = EVN_API.places_get('14693')
    assert EVN_API.transfer_errors == 0
    assert place == {'data': [{'altitude': '1106',
                               'coord_lat': '44.805686318298',
                               'coord_lon': '5.8792190569144',
                               'id': '14693',
                               'id_commune': '14966',
                               'id_region': '63',
                               'is_private': '0',
                               'loc_precision': '750',
                               'name': 'Rochachon',
                               'place_type': 'place',
                               'visible': '1'}]}


def test_places_list_all(capsys):
    """Get list of all places."""
    places_list = EVN_API.places_list()
    logging.info('Received %d places', len(places_list['data']))
    assert EVN_API.transfer_errors == 0
    assert len(places_list['data']) >= 31930

def test_places_list_1(capsys):
    """Get a list of places from local admin unit 14693 (Allevard)."""
    places_list = EVN_API.places_list('14693')
    with capsys.disabled():
        print('local admin unit 14693 ==> {} place '.format(len(places_list['data'])))
    assert EVN_API.transfer_errors == 0
    assert len(places_list['data']) >= 534
    assert places_list['data'][0]['name'] == 'ESRF-synchrotron'

# -------------------------
# Species controler methods
# -------------------------
def test_species_get(capsys):
    """Get a single specie."""
    logging.debug('Getting species from taxo_group #s', '2')
    specie = EVN_API.species_get('2')
    assert EVN_API.transfer_errors == 0
    assert specie['data'][0]['french_name'] == 'Plongeon arctique'

def test_species_list_all(capsys):
    """Get list of all species."""
    species_list = EVN_API.species_list()
    logging.info('Received %d species', len(species_list['data']))
    assert EVN_API.transfer_errors == 0
    assert len(species_list['data']) >= 38820

def test_species_list_1(capsys):
    """Get a list of species from taxo_group 1."""
    species_list = EVN_API.species_list('1')
    with capsys.disabled():
        print('Taxo_group 1 ==> {} species'.format(len(species_list['data'])))
    assert EVN_API.transfer_errors == 0
    assert len(species_list['data']) >= 11150
    assert species_list['data'][0]['french_name'] == 'Plongeon catmarin'

def test_species_list_30(capsys):
    """Get a list of species from taxo_group 30."""
    species_list = EVN_API.species_list('30')
    with capsys.disabled():
        print('Taxo_group 30 ==> {} species'.format(len(species_list['data'])))
    assert EVN_API.transfer_errors == 0
    assert species_list['data'][0]['french_name'] == 'Aucune espèce'

def test_species_list_error(capsys):
    """Get a list of species from taxo_group 1."""
    with pytest.raises(MaxChunksError) as excinfo:
        species_list = EVN_API_ERR.species_list('1')

# ----------------------------
# Taxo_group controler methods
# ----------------------------
def test_taxo_groups_list():
    """Get list of taxo_groups."""
    # First call, should return from API call if not called before
    taxo_groups = EVN_API.taxo_groups_list()
    assert EVN_API.transfer_errors == 0
    assert len(taxo_groups['data']) >= 30
    assert taxo_groups['data'][0]['name'] == 'Oiseaux'
    # Second call, must return from cache
    taxo_groups = EVN_API.taxo_groups_list()
    assert EVN_API.transfer_errors == 0
    assert len(taxo_groups['data']) >= 30
    assert taxo_groups['data'][0]['name'] == 'Oiseaux'

def test_taxo_groups_get():
    """Get a taxo_groups."""
    taxo_group = EVN_API.taxo_groups_get('2')
    assert EVN_API.transfer_errors == 0
    assert taxo_group['data'][0]['name'] == 'Chauves-souris'

# -----------------------------------
# Territorial_units controler methods
# -----------------------------------
def test_territorial_units_list():
    """Get list of territorial_units."""
    # First call, should return from API call if not called before
    territorial_units = EVN_API.territorial_units_list()
    assert EVN_API.transfer_errors == 0
    assert len(territorial_units['data']) == 1
    assert territorial_units['data'][0]['name'] == 'Isère'

def test_territorial_units_get():
    """Get a territorial_units."""
    territorial_unit = EVN_API.territorial_units_get('39')
    assert EVN_API.transfer_errors == 0
    assert territorial_unit['data'][0]['name'] == 'Isère'

# -------------
# Error testing
# -------------
@pytest.mark.skip
def test_wrong_api():
    """Raise an exception."""
    with pytest.raises(requests.HTTPError) as excinfo:
        error = EVN_API.wrong_api()
    assert EVN_API.transfer_errors != 0
    logging.info('HTTPError code %s', excinfo)
