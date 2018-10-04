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
from export_vn.download_vn import LocalAdminUnits
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
LOCAL_ADMIN_UNITS = LocalAdminUnits(CFG, max_requests=1)

# -----------------
#  LocalAdminUnits
# -----------------
def test_local_admin_units_init(capsys):
    """Get from template: a single local admin unit."""
    assert LOCAL_ADMIN_UNITS.transfer_errors == 0

def test_local_admin_units_store(capsys):
    """Store local_admin_units to file."""
    LOCAL_ADMIN_UNITS.store()
    file_json = str(Path.home()) + '/' + CFG.file_store + 'local_admin_units_1.json.gz'
    assert Path(file_json).is_file()
    with gzip.open(file_json, 'rb') as g:
        items_dict = json.loads(g.read().decode('utf-8'))
    assert len(items_dict['data']) > 530
