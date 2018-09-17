#!/usr/bin/env python3
"""
Test each API call of biolovision_api module.
"""
from pathlib import Path
from export_vn.biolovision_api import BiolovisionAPI
from export_vn.evnconf import EvnConf

# Using t38 site, that needs to be created first
SITE = 't38'

def test_site():
    """ Check if configuration file exists. """
    cfg_file = Path(str(Path.home()) + '/.evn_' + SITE + '.ini')
    assert cfg_file.is_file()

CFG = EvnConf(SITE)
EVN_API = BiolovisionAPI(CFG, 2, 5)

def test_taxo_groups_list():
    """ Get list of taxo_groups. """
    taxo_groups = EVN_API.taxo_groups_list()
    assert EVN_API.transfer_errors == 0
    assert len(taxo_groups['data']) > 30
