#!/usr/bin/env python3
"""
Test each method of download_vn module.
"""
import sys
from pathlib import Path
import logging
import pytest

from export_vn.download_vn import DownloadVn, DownloadVnException
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
DOWNLOAD_VN = DownloadVn(CFG, max_requests=1)

# -----------------
#  Template methods
# -----------------
def test_transfer_error(capsys):
    """Get from template: a single local admin unit."""
    assert DOWNLOAD_VN.transfer_errors == 0
