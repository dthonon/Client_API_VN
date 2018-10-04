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

from export_vn.biolovision_api import BiolovisionAPI, BiolovisionApiException
from export_vn.biolovision_api import LocalAdminUnitsAPI, ObservationsAPI, PlacesAPI
from export_vn.biolovision_api import SpeciesAPI, TaxoGroupsAPI, TerritorialUnitsAPI
from export_vn.biolovision_api import HTTPError, MaxChunksError
from export_vn.evnconf import EvnConf

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level = logging.INFO)

def test_logging(cmdopt, capsys):
    with capsys.disabled():
        if cmdopt == 'DEBUG':
            logging.getLogger().setLevel(logging.DEBUG)
        logging.debug('Running with debug logging level')

# Using t38 site, that needs to be created first
SITE = 't38'

def test_site():
    """Check if configuration file exists."""
    cfg_file = Path(str(Path.home()) + '/.evn_' + SITE + '.ini')
    assert cfg_file.is_file()

# Get configuration for test site
CFG = EvnConf(SITE)
EVN_API = BiolovisionAPI(CFG, 'test_biolovision_api')
LOCAL_ADMIN_UNITS_API = LocalAdminUnitsAPI(CFG)
OBSERVATIONS_API = ObservationsAPI(CFG)
PLACES_API = PlacesAPI(CFG)
SPECIES_API = SpeciesAPI(CFG)
SPECIES_API_ERR = SpeciesAPI(CFG, max_retry=1, max_requests=1, max_chunks = 1)
TAXO_GROUPS_API = TaxoGroupsAPI(CFG)
TERRITORIAL_UNITS_API = TerritorialUnitsAPI(CFG)

# -----------------
#  Template methods
# -----------------
def test_template_get(capsys):
    """Get from template: a single local admin unit."""
    with capsys.disabled():
        logging.debug('Getting by template: local admin unit #s', '14693')
        local_admin_unit = EVN_API.api_get('local_admin_units', '14693')
    assert EVN_API.transfer_errors == 0
    assert local_admin_unit == {
        'data': [{
            'name': 'Allevard',
            'coord_lon': '6.11353081638029',
            'id_canton': '39',
            'coord_lat': '45.3801954314357',
            'id': '14693',
            'insee': '38006'}]}

def test_template_list_all(capsys):
    """Get from template: list of all local admin units."""
    with capsys.disabled():
        local_admin_units_list = EVN_API.api_list('local_admin_units')
        logging.debug('Received %d local admin units', len(local_admin_units_list['data']))
    assert EVN_API.transfer_errors == 0
    assert len(local_admin_units_list['data']) >= 534

def test_template_list_1(capsys):
    """Get from template: a list of local_admin_units from territorial unit 39 (Isère)."""
    with capsys.disabled():
        local_admin_units_list = EVN_API.api_list('local_admin_units', {'id_canton': '39'})
        logging.debug('territorial unit 39 ==> {} local admin unit '.format(len(local_admin_units_list['data'])))
    assert EVN_API.transfer_errors == 0
    assert len(local_admin_units_list['data']) >= 534
    assert local_admin_units_list['data'][0]['name'] == 'Abrets (Les)'

def test_template_list_2(capsys):
    """Get from template: a list of local_admin_units from territorial unit 2 (unknown)."""
    with capsys.disabled():
        local_admin_units_list = EVN_API.api_list('local_admin_units', {'id_canton': '2'})
        logging.debug('territorial unit 2 ==> {} local admin unit '.format(len(local_admin_units_list['data'])))
    assert EVN_API.transfer_errors == 0
    assert len(local_admin_units_list['data']) == 0

# ------------------------------------
#  Local admin units controler methods
# ------------------------------------
def test_controler(capsys):
    """Check controler name."""
    ctrl = LOCAL_ADMIN_UNITS_API.controler
    assert ctrl == 'local_admin_units'

def test_local_admin_units_get(capsys):
    """Get a single local admin unit."""
    logging.debug('Getting local admin unit #s', '14693')
    local_admin_unit = LOCAL_ADMIN_UNITS_API.api_get('14693')
    assert LOCAL_ADMIN_UNITS_API.transfer_errors == 0
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
    local_admin_units_list = LOCAL_ADMIN_UNITS_API.api_list()
    logging.debug('Received %d local admin units', len(local_admin_units_list['data']))
    assert LOCAL_ADMIN_UNITS_API.transfer_errors == 0
    assert len(local_admin_units_list['data']) >= 534

def test_local_admin_units_list_1(capsys):
    """Get a list of local_admin_units from territorial unit 39 (Isère)."""
    local_admin_units_list = LOCAL_ADMIN_UNITS_API.api_list({'id_canton': '39'})
    with capsys.disabled():
        print('territorial unit 39 ==> {} local admin unit '.format(len(local_admin_units_list['data'])))
    assert LOCAL_ADMIN_UNITS_API.transfer_errors == 0
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
    diff = OBSERVATIONS_API.api_diff('1', since)
    assert OBSERVATIONS_API.transfer_errors == 0
    assert len(diff) > 0
    diff = OBSERVATIONS_API.api_diff('1', since, 'only_modified')
    assert OBSERVATIONS_API.transfer_errors == 0
    diff = OBSERVATIONS_API.api_diff('1', since, 'only_deleted')
    assert OBSERVATIONS_API.transfer_errors == 0

def test_observations_get(capsys):
    """Get a specific sighting."""
    sighting = OBSERVATIONS_API.api_get('2246086')
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
    place = PLACES_API.api_get('14693')
    assert PLACES_API.transfer_errors == 0
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
    places_list = PLACES_API.api_list()
    logging.debug('Received %d places', len(places_list['data']))
    assert EVN_API.transfer_errors == 0
    assert len(places_list['data']) >= 31930
    assert places_list['data'][0]['name'] == 'ESRF-synchrotron'

def test_places_list_1(capsys):
    """Get a list of places from local admin unit 14693 (Allevard)."""
    with capsys.disabled():
        places_list = PLACES_API.api_list({'id_commune': '14693'})
        logging.debug('local admin unit 14693 ==> {} place '.format(len(places_list['data'])))
    assert EVN_API.transfer_errors == 0
    assert len(places_list['data']) >= 164
    assert len(places_list['data']) <= 200
    assert places_list['data'][0]['name'] == 'le Repos (S)'

# -------------------------
# Species controler methods
# -------------------------
def test_species_get(capsys):
    """Get a single specie."""
    logging.debug('Getting species from taxo_group #s', '2')
    specie = SPECIES_API.api_get('2')
    assert SPECIES_API.transfer_errors == 0
    assert specie['data'][0]['french_name'] == 'Plongeon arctique'

def test_species_list_all(capsys):
    """Get list of all species."""
    species_list = SPECIES_API.api_list()
    logging.debug('Received %d species', len(species_list['data']))
    assert SPECIES_API.transfer_errors == 0
    assert len(species_list['data']) >= 38820

def test_species_list_1(capsys):
    """Get a list of species from taxo_group 1."""
    species_list = SPECIES_API.api_list({'id_taxo_group': '1'})
    with capsys.disabled():
        print('Taxo_group 1 ==> {} species'.format(len(species_list['data'])))
    assert SPECIES_API.transfer_errors == 0
    assert len(species_list['data']) >= 11150
    assert species_list['data'][0]['french_name'] == 'Plongeon catmarin'

def test_species_list_30(capsys):
    """Get a list of species from taxo_group 30."""
    species_list = SPECIES_API.api_list({'id_taxo_group': '30'})
    with capsys.disabled():
        print('Taxo_group 30 ==> {} species'.format(len(species_list['data'])))
    assert SPECIES_API.transfer_errors == 0
    assert species_list['data'][0]['french_name'] == 'Aucune espèce'

def test_species_list_error(capsys):
    """Get a list of species from taxo_group 1, limited to 1 chunk."""
    with pytest.raises(MaxChunksError) as excinfo:
        species_list = SPECIES_API_ERR.api_list({'id_taxo_group': '1'})

# ----------------------------
# Taxo_group controler methods
# ----------------------------
def test_taxo_groups_get():
    """Get a taxo_groups."""
    taxo_group = TAXO_GROUPS_API.api_get('2')
    assert TAXO_GROUPS_API.transfer_errors == 0
    assert taxo_group['data'][0]['name'] == 'Chauves-souris'

def test_taxo_groups_list():
    """Get list of taxo_groups."""
    # First call, should return from API call if not called before
    taxo_groups = TAXO_GROUPS_API.api_list()
    assert TAXO_GROUPS_API.transfer_errors == 0
    assert len(taxo_groups['data']) >= 30
    assert taxo_groups['data'][0]['name'] == 'Oiseaux'
    # Second call, must return from cache
    taxo_groups = TAXO_GROUPS_API.api_list()
    assert TAXO_GROUPS_API.transfer_errors == 0
    assert len(taxo_groups['data']) >= 30
    assert taxo_groups['data'][0]['name'] == 'Oiseaux'

# -----------------------------------
# Territorial_units controler methods
# -----------------------------------
def test_territorial_units_get():
    """Get a territorial_units."""
    territorial_unit = TERRITORIAL_UNITS_API.api_get('39')
    assert TERRITORIAL_UNITS_API.transfer_errors == 0
    assert territorial_unit['data'][0]['name'] == 'Isère'

def test_territorial_units_list():
    """Get list of territorial_units."""
    # First call, should return from API call if not called before
    territorial_units = TERRITORIAL_UNITS_API.api_list()
    assert TERRITORIAL_UNITS_API.transfer_errors == 0
    assert len(territorial_units['data']) == 1
    assert territorial_units['data'][0]['name'] == 'Isère'

# -------------
# Error testing
# -------------
@pytest.mark.skip
def test_wrong_api():
    """Raise an exception."""
    with pytest.raises(requests.HTTPError) as excinfo:
        error = EVN_API.wrong_api()
    assert EVN_API.transfer_errors != 0
    logging.debug('HTTPError code %s', excinfo)
