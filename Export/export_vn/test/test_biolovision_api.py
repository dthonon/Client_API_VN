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

def test_observations_diff(capsys):
    """Get list of diffs from last day."""
    since = (datetime.now() - timedelta(days=1)).strftime('%H:%M:%S %d.%m.%Y')
    # with capsys.disabled():
    #     print('\nGetting updates since {}'.format(since))
    diff = EVN_API.observations_diff('1', since)
    assert EVN_API.transfer_errors == 0
    assert len(diff) > 0
    diff = EVN_API.observations_diff('1', since, 'only_modified')
    assert EVN_API.transfer_errors == 0
    assert len(diff) > 0
    diff = EVN_API.observations_diff('1', since, 'only_deleted')
    assert EVN_API.transfer_errors == 0
    assert len(diff) > 0
