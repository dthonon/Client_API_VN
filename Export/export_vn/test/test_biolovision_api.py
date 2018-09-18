#!/usr/bin/env python3
"""
Test each API call of biolovision_api module.
"""
from datetime import datetime, timedelta
from pathlib import Path
from export_vn.biolovision_api import BiolovisionAPI
from export_vn.evnconf import EvnConf

# Using t38 site, that needs to be created first
SITE = 't38'

def test_site():
    """Check if configuration file exists."""
    cfg_file = Path(str(Path.home()) + '/.evn_' + SITE + '.ini')
    assert cfg_file.is_file()

# Get configuration for test site
CFG = EvnConf(SITE)
EVN_API = BiolovisionAPI(CFG, 2, 5)

def test_taxo_groups_list():
    """Get list of taxo_groups."""
    taxo_groups = EVN_API.taxo_groups_list()
    assert EVN_API.transfer_errors == 0
    assert len(taxo_groups['data']) > 30
    assert taxo_groups['data'][0]['name'] == 'Oiseaux'

def test_taxo_groups_get():
    """Get a taxo_groups."""
    taxo_groups = EVN_API.taxo_groups_get('2')
    assert EVN_API.transfer_errors == 0
    assert taxo_groups['data'][0]['name'] == 'Chauves-souris'

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
    with capsys.disabled():
        timing = sighting['data']['sightings'][0]['observers'][0]['timing']['@timestamp']
        timing_datetime = datetime.fromtimestamp(float(timing))
        print('\ntiming_datetime datetime = {}'.format(timing_datetime.strftime('%Y-%m-%d %H:%M:%S')))
        insert_date = sighting['data']['sightings'][0]['observers'][0]['insert_date']
        insert_datetime = datetime.fromtimestamp(float(insert_date))
        print('insert_date datetime = {}'.format(insert_datetime.strftime('%Y-%m-%d %H:%M:%S')))
    assert sighting == {'data':
                {'sightings':
                 [{'place':
                   {'county': '38',
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
                   'date': {'@notime': '1',
                            '@offset': '7200',
                            '@ISO8601': '2018-09-15T00:00:00+02:00',
                            '@timestamp': '1536962400',
                            '#text': 'samedi 15 septembre 2018'},
                   'species':
                   {'latin_name': 'Anas platyrhynchos',
                    'rarity': 'verycommon',
                    'sys_order': '262',
                    'name': 'Canard colvert',
                    '@id': '86',
                    'taxonomy': '1'},
                   'observers':
                   [{'estimation_code': 'MINIMUM',
                     'count': '15',
                     'id_sighting': '2246086',
                     'insert_date': '1537033501',
                     'atlas_grid_name': 'E091N645',
                     'name': 'Daniel Thonon',
                     'medias':
                     [{'media_is_hidden': '0',
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
