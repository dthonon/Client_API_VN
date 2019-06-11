#!/usr/bin/env python3
"""
Test each API call of biolovision_api module.
"""
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest
import requests

from export_vn.biolovision_api import (EntitiesAPI, LocalAdminUnitsAPI,
                                       MaxChunksError, ObservationsAPI,
                                       ObserversAPI, PlacesAPI, SpeciesAPI,
                                       TaxoGroupsAPI, TerritorialUnitsAPI)
from export_vn.evnconf import EvnConf
from export_vn.store_file import StoreFile

# Using faune-ardeche or faune-isere site, that needs to be created first
SITE = 't07'
# SITE = 't38'
FILE = '.evn_test.yaml'

# Get configuration for test site
CFG = EvnConf(FILE).site_list[SITE]
STORE_FILE = StoreFile(CFG)
ENTITIES_API = EntitiesAPI(CFG)
LOCAL_ADMIN_UNITS_API = LocalAdminUnitsAPI(CFG)
OBSERVATIONS_API = ObservationsAPI(CFG)
OBSERVERS_API = ObserversAPI(CFG)
PLACES_API = PlacesAPI(CFG)
SPECIES_API = SpeciesAPI(CFG)
SPECIES_API_ERR = SpeciesAPI(CFG, max_retry=1, max_requests=1, max_chunks=1)
TAXO_GROUPS_API = TaxoGroupsAPI(CFG)
TERRITORIAL_UNITS_API = TerritorialUnitsAPI(CFG)


def test_version():
    """Check if version is defined."""
    logging.debug('package version: %s', ENTITIES_API.version)


# --------------------------
# Entities controler methods
# --------------------------
def test_entities_get():
    """Get an entity."""
    entity = ENTITIES_API.api_get('2')
    assert ENTITIES_API.transfer_errors == 0
    assert entity['data'][0]['short_name'] == 'LPO 07'


def test_entities_list():
    """Get list of entities."""
    entities = ENTITIES_API.api_list()
    assert ENTITIES_API.transfer_errors == 0
    assert len(entities['data']) >= 8
    assert entities['data'][0]['short_name'] == '-'


# --------------------------
# Fields controler methods
# --------------------------
def test_fields_get():
    """Get a field."""
    field = FIELDS_API.api_get('2')
    assert FIELDS_API.transfer_errors == 0
    assert entity['data'][0]['short_name'] == 'LPO 07'


def test_fields_list():
    """Get list of fields."""
    fields = FIELDS_API.api_list()
    assert FIELDS_API.transfer_errors == 0
    assert len(fields['data']) >= 8
    assert fields['data'][0]['short_name'] == '-'


# ------------------------------------
#  Local admin units controler methods
# ------------------------------------
def test_controler(capsys):
    """Check controler name."""
    ctrl = LOCAL_ADMIN_UNITS_API.controler
    assert ctrl == 'local_admin_units'


def test_local_admin_units_get(capsys):
    """Get a single local admin unit."""
    if SITE == 't38':
        a = '14693'
    elif SITE == 't07':
        a = '2096'
    else:
        assert False
    logging.debug('Getting local admin unit #s', a)
    local_admin_unit = LOCAL_ADMIN_UNITS_API.api_get(a)
    assert LOCAL_ADMIN_UNITS_API.transfer_errors == 0
    if SITE == 't38':
        assert local_admin_unit == {
            'data': [{
                'name': 'Allevard',
                'coord_lon': '6.11353081638029',
                'id_canton': '39',
                'coord_lat': '45.3801954314357',
                'id': '14693',
                'insee': '38006'
            }]
        }
    elif SITE == 't07':
        assert local_admin_unit == {
            'data': [{
                'coord_lat': '44.888464632099',
                'coord_lon': '4.39188200157809',
                'id': '2096',
                'id_canton': '7',
                'insee': '07001',
                'name': 'Accons'
            }]
        }


def test_local_admin_units_list_all(capsys):
    """Get list of all local admin units."""
    logging.debug('Getting all local admin unit')
    local_admin_units_list = LOCAL_ADMIN_UNITS_API.api_list()
    with capsys.disabled():
        logging.debug('Received %d local admin units',
                      len(local_admin_units_list['data']))
    assert LOCAL_ADMIN_UNITS_API.transfer_errors == 0
    if SITE == 't38':
        assert len(local_admin_units_list['data']) >= 534
    elif SITE == 't07':
        assert len(local_admin_units_list['data']) >= 340


def test_local_admin_units_list_1(capsys):
    """Get a list of local_admin_units from territorial unit 39 (Isère)."""
    if SITE == 't38':
        logging.debug('Getting local admin unit from {id_canton: 39}')
        local_admin_units_list = LOCAL_ADMIN_UNITS_API.api_list(
            opt_params={'id_canton': '39'})
    elif SITE == 't07':
        logging.debug('Getting local admin unit from {id_canton: 07}')
        local_admin_units_list = LOCAL_ADMIN_UNITS_API.api_list(
            opt_params={'id_canton': '07'})
    with capsys.disabled():
        logging.debug('territorial unit ==> {} local admin unit '.format(
            len(local_admin_units_list['data'])))
    assert LOCAL_ADMIN_UNITS_API.transfer_errors == 0
    if SITE == 't38':
        assert len(local_admin_units_list['data']) >= 534
        assert local_admin_units_list['data'][0]['name'] == 'Abrets (Les)'
    elif SITE == 't07':
        assert len(local_admin_units_list['data']) >= 340
        assert local_admin_units_list['data'][0]['name'] == 'Accons'


# ------------------------------
# Observations controler methods
# ------------------------------
def test_observations_diff(capsys):
    """Get list of diffs from last day."""
    since = (datetime.now() - timedelta(days=1)).strftime('%H:%M:%S %d.%m.%Y')
    with capsys.disabled():
        logging.debug('Getting updates since {}'.format(since))
    diff = OBSERVATIONS_API.api_diff('1', since)
    assert OBSERVATIONS_API.transfer_errors == 0
    assert len(diff) > 0
    diff = OBSERVATIONS_API.api_diff('1', since, 'only_modified')
    assert OBSERVATIONS_API.transfer_errors == 0
    diff = OBSERVATIONS_API.api_diff('1', since, 'only_deleted')
    assert OBSERVATIONS_API.transfer_errors == 0


def test_observations_list_1(capsys):
    """Get the list of sightings, from taxo_group 18: Mantodea."""
    list = OBSERVATIONS_API.api_list('18')
    assert OBSERVATIONS_API.transfer_errors == 0
    assert len(list) > 0


@pytest.mark.slow
def test_observations_list_2_1(capsys):
    """Get the list of sightings, from taxo_group 1, specie 518."""
    file_json = str(Path.home(
    )) + '/' + CFG.file_store + 'test_observations_list_2_1.json.gz'
    if Path(file_json).is_file():
        Path(file_json).unlink()
    with capsys.disabled():
        list = OBSERVATIONS_API.api_list('1',
                                         id_species='518',
                                         short_version='1')
        logging.debug(
            'local test_observations_list_3_0 unit {} sightings/forms '.format(
                len(list)))
    assert OBSERVATIONS_API.transfer_errors == 0
    assert len(list) > 0
    STORE_FILE.store('test_observations_list_2', str(1), list)


def test_observations_list_3_0(capsys):
    """Get the list of sightings, from taxo_group 1, specie 382."""
    file_json = str(Path.home(
    )) + '/' + CFG.file_store + 'test_observations_list_3_0.json.gz'
    if Path(file_json).is_file():
        Path(file_json).unlink()
    with capsys.disabled():
        list = OBSERVATIONS_API.api_list('1', id_species='382')
        logging.debug(
            'local test_observations_list_3_0 unit {} sightings/forms '.format(
                len(list)))
    assert OBSERVATIONS_API.transfer_errors == 0
    assert len(list) > 0
    STORE_FILE.store('test_observations_list_3', str(0), list)


def test_observations_list_3_1(capsys):
    """Get the list of sightings, from taxo_group 1, specie 382."""
    file_json = str(Path.home(
    )) + '/' + CFG.file_store + 'test_observations_list_3_1.json.gz'
    if Path(file_json).is_file():
        Path(file_json).unlink()
    with capsys.disabled():
        list = OBSERVATIONS_API.api_list('1',
                                         id_species='382',
                                         short_version='1')
        logging.debug(
            'local test_observations_list_3_0 unit {} sightings/forms '.format(
                len(list)))
    assert OBSERVATIONS_API.transfer_errors == 0
    assert len(list) > 0
    STORE_FILE.store('test_observations_list_3', str(1), list)


def test_observations_get(capsys):
    """Get a specific sighting."""
    if SITE == 't38':
        sighting = OBSERVATIONS_API.api_get('2246086')
        assert sighting == {
            'data': {
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
                        'place_type': 'precise'
                    },
                    'date': {
                        '@notime': '1',
                        '@offset': '7200',
                        '@ISO8601': '2018-09-15T00:00:00+02:00',
                        '@timestamp': '1536962400',
                        '#text': 'samedi 15 septembre 2018'
                    },
                    'species': {
                        'latin_name': 'Anas platyrhynchos',
                        'rarity': 'verycommon',
                        'sys_order': '262',
                        'name': 'Canard colvert',
                        '@id': '86',
                        'taxonomy': '1'
                    },
                    'observers': [{
                        'estimation_code':
                        'MINIMUM',
                        'count':
                        '15',
                        'id_sighting':
                        '2246086',
                        'insert_date': {
                            '#text': 'samedi 15 septembre 2018, 19:45:01',
                            '@ISO8601': '2018-09-15T19:45:01+02:00',
                            '@notime': '0',
                            '@offset': '7200',
                            '@timestamp': '1537033501'
                        },
                        'atlas_grid_name':
                        'E091N645',
                        'name':
                        'Daniel Thonon',
                        'medias': [{
                            'media_is_hidden': '0',
                            'filename': '3_1537024802877-15194452-5272.jpg',
                            'path':
                            'http://media.biolovision.net/data.biolovision.net/2018-09',  # noqa: E501
                            'insert_date': {
                                '@notime': '0',
                                '@offset': '3600',
                                '@ISO8601': '1970-01-01T01:33:38+01:00',
                                '@timestamp': '2018',
                                '#text': 'jeudi 1 janvier 1970, 01:33:38'
                            },
                            'metadata': '',
                            'type': 'PHOTO',
                            '@id': '49174'
                        }],
                        '@uid':
                        '11675',
                        'precision':
                        'precise',
                        'id_universal':
                        '65_71846872',
                        'traid':
                        '33',
                        'timing': {
                            '@notime': '0',
                            '@offset': '7200',
                            '@ISO8601': '2018-09-15T17:19:16+02:00',
                            '@timestamp': '1537024756',
                            '#text': 'samedi 15 septembre 2018, 17:19:16'
                        },
                        'altitude':
                        '215',
                        'source':
                        'WEB',
                        'coord_lat':
                        '45.18724',
                        'flight_number':
                        '1',
                        'anonymous':
                        '0',
                        'coord_lon':
                        '5.735458',
                        '@id':
                        '33'
                    }]
                }]
            }
        }
    if SITE == 't07':
        sighting = OBSERVATIONS_API.api_get('274830')
        assert sighting == {
            'data': {
                'sightings': [{
                    'date': {
                        '#text': 'mercredi 29 avril 2015',
                        '@ISO8601': '2015-04-29T00:00:00+02:00',
                        '@notime': '1',
                        '@offset': '7200',
                        '@timestamp': '1430258400'
                    },
                    'observers': [{
                        '@id': '104',
                        '@uid': '4040',
                        'altitude': '99',
                        'anonymous': '0',
                        'atlas_grid_name': 'E081N636',
                        'comment': 'juv',
                        'coord_lat': '44.373198',
                        'coord_lon': '4.428607',
                        'count': '1',
                        'estimation_code': 'MINIMUM',
                        'flight_number': '1',
                        'hidden_comment': 'RNNGA',
                        'id_sighting': '274830',
                        'id_universal': '30_274830',
                        'insert_date': {
                            '#text': 'dimanche 1 novembre 2015, 22:30:37',
                            '@ISO8601': '2015-11-01T22:30:37+01:00',
                            '@notime': '0',
                            '@offset': '3600',
                            '@timestamp': '1446413437'
                        },
                        'name': 'Nicolas Bazin',
                        'precision': 'precise',
                        'source': 'WEB',
                        'timing': {
                            '#text': 'mercredi 29 avril 2015',
                            '@ISO8601': '2015-04-29T00:00:00+02:00',
                            '@notime': '1',
                            '@offset': '7200',
                            '@timestamp': '1430258400'
                        },
                        'traid': '104',
                        'update_date': {
                            '#text': 'lundi 26 mars 2018, 18:01:23',
                            '@ISO8601': '2018-03-26T18:01:23+02:00',
                            '@notime': '0',
                            '@offset': '7200',
                            '@timestamp': '1522080083'
                        }
                    }],
                    'place': {
                        '@id': '122870',
                        'altitude': '99',
                        'coord_lat': '44.371928319497',
                        'coord_lon': '4.4273367833997',
                        'country': '',
                        'county': '07',
                        'insee': '07330',
                        'loc_precision': '0',
                        'municipality': 'Vallon-Pont-d\'Arc',
                        'name': 'Rapide des Trois Eaux',
                        'place_type': 'precise'
                    },
                    'species': {
                        '@id': '19703',
                        'latin_name': 'Empusa pennata',
                        'name': 'Empuse penn\u00e9e',
                        'rarity': 'unusual',
                        'sys_order': '80',
                        'taxonomy': '18'
                    }
                }]
            }
        }


def test_observations_search_1(capsys):
    """Query sightings, from taxo_group 18: Mantodea and date range."""
    q_param = {
        'period_choice': 'range',
        'date_from': '01.09.2017',
        'date_to': '30.09.2017',
        'species_choice': 'all',
        'taxonomic_group': '18'
    }
    list = OBSERVATIONS_API.api_search(q_param)
    assert OBSERVATIONS_API.transfer_errors == 0
    if SITE == 't38':
        assert len(list['data']['sightings']) >= 17
    elif SITE == 't07':
        assert len(list['data']['sightings']) >= 3
    else:
        assert False


def test_observations_search_2(capsys):
    """Query sightings, from taxo_group 18: Mantodea and date range."""
    q_param = {
        'period_choice': 'range',
        'date_from': '01.09.2017',
        'date_to': '30.09.2017',
        'species_choice': 'all',
        'taxonomic_group': '18'
    }
    list = OBSERVATIONS_API.api_search(q_param, short_version='1')
    assert OBSERVATIONS_API.transfer_errors == 0
    if SITE == 't38':
        assert len(list['data']['sightings']) >= 17
    elif SITE == 't07':
        assert len(list['data']['sightings']) >= 3
    else:
        assert False


# ----------------------------
#  Observers controler methods
# ----------------------------
def test_observers_get(capsys):
    """Get a single observer."""
    if SITE == 't38':
        o = '33'
    elif SITE == 't07':
        o = '1084'
    else:
        assert False
    logging.debug('Getting observer #s', o)
    observer = OBSERVERS_API.api_get(o)
    assert OBSERVERS_API.transfer_errors == 0
    if SITE == 't38':
        assert observer == {
            'data': [{
                'anonymous': '0',
                'archive_account': '0',
                'atlas_list': '16',
                'birth_year': '1959',
                'bypass_purchase': '0',
                'collectif': '0',
                'debug_file_upload': '0',
                'default_hidden': '0',
                'display_order': 'DATE_PLACE_SPECIES',
                'email': 'd.thonon9@gmail.com',
                'external_id': '0',
                'has_search_access': '0',
                'hide_email': '0',
                'id': '1084',
                'id_entity': '1',
                'id_universal': '11675',
                'item_per_page_gallery': '12',
                'item_per_page_obs': '20',
                'langu': 'fr',
                'last_inserted_data': {
                    '#text': 'mardi 1 novembre 2016, 17:03:06',
                    '@ISO8601': '2016-11-01T17:03:06+01:00',
                    '@notime': '0',
                    '@offset': '3600',
                    '@timestamp': '1478016186'
                },
                'last_login': {
                    '#text': 'dimanche 6 janvier 2019, 21:32:23',
                    '@ISO8601': '2019-01-06T21:32:23+01:00',
                    '@notime': '0',
                    '@offset': '3600',
                    '@timestamp': '1546806743'
                },
                'lat': '44.7221149943671',
                'lon': '4.59373711385036',
                'mobile_phone': '0675291894',
                'mobile_use_form': '0',
                'mobile_use_mortality': '0',
                'mobile_use_protocol': '0',
                'mobile_use_trace': '0',
                'municipality': 'Meylan',
                'name': 'Thonon',
                'number': '',
                'photo': '',
                'postcode': '38240',
                'presentation': '',
                'private_phone': '09 53 74 56 59',
                'private_website': '',
                'registration_date': {
                    '#text': 'vendredi 1 mai 2015',
                    '@ISO8601': '2015-05-01T19:11:31+02:00',
                    '@notime': '1',
                    '@offset': '7200',
                    '@timestamp': '1430500291'
                },
                'show_precise': '0',
                'species_order': 'ALPHA',
                'street': '13, Av. du Vercors',
                'surname': 'Daniel',
                'use_latin_search': 'N',
                'work_phone': ''
            }]
        }
    elif SITE == 't07':
        assert observer == {
            'data': [{
                'anonymous': '0',
                'archive_account': '0',
                'atlas_list': '16',
                'birth_year': '1959',
                'bypass_purchase': '0',
                'collectif': '0',
                'debug_file_upload': '0',
                'default_hidden': '0',
                'display_order': 'DATE_PLACE_SPECIES',
                'email': 'd.thonon9@gmail.com',
                'external_id': '0',
                'has_search_access': '0',
                'hide_email': '0',
                'id': '1084',
                'id_entity': '1',
                'id_universal': '11675',
                'item_per_page_gallery': '12',
                'item_per_page_obs': '20',
                'langu': 'fr',
                'last_inserted_data': {
                    '#text': 'mardi 1 novembre 2016, 17:03:06',
                    '@ISO8601': '2016-11-01T17:03:06+01:00',
                    '@notime': '0',
                    '@offset': '3600',
                    '@timestamp': '1478016186'
                },
                'last_login': {
                    '#text': 'dimanche 6 janvier 2019, 21:32:23',
                    '@ISO8601': '2019-01-06T21:32:23+01:00',
                    '@notime': '0',
                    '@offset': '3600',
                    '@timestamp': '1546806743'
                },
                'lat': '44.7221149943671',
                'lon': '4.59373711385036',
                'mobile_phone': '0675291894',
                'mobile_use_form': '0',
                'mobile_use_mortality': '0',
                'mobile_use_protocol': '0',
                'mobile_use_trace': '0',
                'municipality': 'Meylan',
                'name': 'Thonon',
                'number': '',
                'photo': '',
                'postcode': '38240',
                'presentation': '',
                'private_phone': '09 53 74 56 59',
                'private_website': '',
                'registration_date': {
                    '#text': 'vendredi 1 mai 2015',
                    '@ISO8601': '2015-05-01T19:11:31+02:00',
                    '@notime': '1',
                    '@offset': '7200',
                    '@timestamp': '1430500291'
                },
                'show_precise': '0',
                'species_order': 'ALPHA',
                'street': '13, Av. du Vercors',
                'surname': 'Daniel',
                'use_latin_search': 'N',
                'work_phone': ''
            }]
        }


def test_observers_list_all(capsys):
    """Get list of all observers."""
    observers_list = OBSERVERS_API.api_list()
    logging.debug('Received %d observers', len(observers_list['data']))
    assert OBSERVERS_API.transfer_errors == 0
    if SITE == 't38':
        assert len(observers_list['data']) >= 4500
        assert observers_list['data'][0]['name'] == 'Biolovision'
    elif SITE == 't07':
        assert len(observers_list['data']) >= 2400
        assert observers_list['data'][0]['name'] == 'Biolovision'


# -------------------------
#  Places controler methods
# -------------------------
def test_places_get(capsys):
    """Get a single place."""
    if SITE == 't38':
        p = '14693'
    elif SITE == 't07':
        p = '100694'
    else:
        assert False
    logging.debug('Getting place #s', p)
    place = PLACES_API.api_get(p)
    assert PLACES_API.transfer_errors == 0
    if SITE == 't38':
        assert place == {
            'data': [{
                'altitude': '1106',
                'coord_lat': '44.805686318298',
                'coord_lon': '5.8792190569144',
                'id': '14693',
                'id_commune': '14966',
                'id_region': '63',
                'is_private': '0',
                'loc_precision': '750',
                'name': 'Rochachon',
                'place_type': 'place',
                'visible': '1'
            }]
        }
    elif SITE == 't07':
        assert place == {
            'data': [{
                'altitude': '285',
                'coord_lat': '45.2594824523633',
                'coord_lon': '4.7766923904419',
                'id': '100694',
                'id_commune': '2316',
                'id_region': '16',
                'is_private': '0',
                'loc_precision': '750',
                'name': 'Ruisseau de Lantizon (ravin)',
                'place_type': 'place',
                'visible': '1'
            }]
        }


@pytest.mark.slow
def test_places_list_all(capsys):
    """Get list of all places."""
    places_list = PLACES_API.api_list()
    logging.debug('Received %d places', len(places_list['data']))
    assert PLACES_API.transfer_errors == 0
    if SITE == 't38':
        assert len(places_list['data']) >= 31930
        assert places_list['data'][0]['name'] == 'ESRF-synchrotron'
    elif SITE == 't07':
        assert len(places_list['data']) >= 23566
        assert places_list['data'][0][
            'name'] == 'Accons - sans lieu-dit défini'


def test_places_list_1(capsys):
    """Get a list of places from a single local admin unit."""
    if SITE == 't38':
        place = '14693'
    elif SITE == 't07':
        place = '2096'
    else:
        assert False
    with capsys.disabled():
        places_list = PLACES_API.api_list({'id_commune': place})
        logging.debug('local admin unit {} ==> {} place '.format(
            place, len(places_list['data'])))
    assert PLACES_API.transfer_errors == 0
    if SITE == 't38':
        assert len(places_list['data']) >= 164
        assert len(places_list['data']) <= 200
        assert places_list['data'][0]['name'] == 'le Repos (S)'
    elif SITE == 't07':
        assert len(places_list['data']) >= 38
        assert len(places_list['data']) <= 50
        assert places_list['data'][0][
            'name'] == 'Accons - sans lieu-dit défini'


# -------------------------
# Species controler methods
# -------------------------
def test_species_get(capsys):
    """Get a single specie."""
    logging.debug('Getting species from taxo_group #s', '2')
    specie = SPECIES_API.api_get('2')
    assert SPECIES_API.transfer_errors == 0
    assert specie['data'][0]['french_name'] == 'Plongeon arctique'


@pytest.mark.slow
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
        logging.debug('Taxo_group 1 ==> {} species'.format(
            len(species_list['data'])))
    assert SPECIES_API.transfer_errors == 0
    assert len(species_list['data']) >= 11150
    assert species_list['data'][0]['french_name'] == 'Plongeon catmarin'


def test_species_list_30(capsys):
    """Get a list of species from taxo_group 30."""
    species_list = SPECIES_API.api_list({'id_taxo_group': '30'})
    with capsys.disabled():
        logging.debug('Taxo_group 30 ==> {} species'.format(
            len(species_list['data'])))
    assert SPECIES_API.transfer_errors == 0
    assert species_list['data'][0]['french_name'] == 'Aucune espèce'


def test_species_list_error(capsys):
    """Get a list of species from taxo_group 1, limited to 1 chunk."""
    with pytest.raises(MaxChunksError) as excinfo:  # noqa: F841
        species_list = SPECIES_API_ERR.api_list(    # noqa: F841
            {'id_taxo_group': '1'})


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
    start = time.perf_counter()
    taxo_groups = TAXO_GROUPS_API.api_list()
    took = (time.perf_counter() - start) * 1000.0
    logging.debug('taxo_groups_list, call 1 took: ' + str(took) + ' ms')
    assert TAXO_GROUPS_API.transfer_errors == 0
    assert len(taxo_groups['data']) >= 30
    assert taxo_groups['data'][0]['name'] == 'Oiseaux'
    # Second call, must return from cache
    start = time.perf_counter()
    taxo_groups = TAXO_GROUPS_API.api_list()
    took = (time.perf_counter() - start) * 1000.0
    logging.debug('taxo_groups_list, call 2 took: ' + str(took) + ' ms')
    start = time.perf_counter()
    taxo_groups = TAXO_GROUPS_API.api_list()
    took = (time.perf_counter() - start) * 1000.0
    logging.debug('taxo_groups_list, call 3 took: ' + str(took) + ' ms')
    assert TAXO_GROUPS_API.transfer_errors == 0
    assert len(taxo_groups['data']) >= 30
    assert taxo_groups['data'][0]['name'] == 'Oiseaux'


# -----------------------------------
# Territorial_units controler methods
# -----------------------------------
def test_territorial_units_get():
    """Get a territorial_units."""
    if SITE == 't38':
        territorial_unit = TERRITORIAL_UNITS_API.api_get('39')
    elif SITE == 't07':
        territorial_unit = TERRITORIAL_UNITS_API.api_get('07')
    assert TERRITORIAL_UNITS_API.transfer_errors == 0
    if SITE == 't38':
        assert territorial_unit['data'][0]['name'] == 'Isère'
    elif SITE == 't07':
        assert territorial_unit['data'][0]['name'] == 'Ardèche'


def test_territorial_units_list():
    """Get list of territorial_units."""
    # First call, should return from API call if not called before
    start = time.perf_counter()
    territorial_units = TERRITORIAL_UNITS_API.api_list()
    took = (time.perf_counter() - start) * 1000.0
    logging.debug('territorial_units_list, call 1 took: ' + str(took) + ' ms')
    assert TERRITORIAL_UNITS_API.transfer_errors == 0
    assert len(territorial_units['data']) == 1
    logging.debug(territorial_units['data'])
    if SITE == 't38':
        assert territorial_units['data'][0]['name'] == 'Isère'
    elif SITE == 't07':
        assert territorial_units['data'][0]['name'] == 'Ardèche'
    start = time.perf_counter()
    territorial_units = TERRITORIAL_UNITS_API.api_list()
    took = (time.perf_counter() - start) * 1000.0
    logging.debug('territorial_units_list, call 2 took: ' + str(took) + ' ms')
    assert TERRITORIAL_UNITS_API.transfer_errors == 0


# -------------
# Error testing
# -------------
@pytest.mark.skip
def test_wrong_api():
    """Raise an exception."""
    with pytest.raises(requests.HTTPError) as excinfo:  # noqa: F841
        error = PLACES_API.wrong_api()  # noqa: F841
    assert PLACES_API.transfer_errors != 0
    logging.debug('HTTPError code %s', excinfo)
