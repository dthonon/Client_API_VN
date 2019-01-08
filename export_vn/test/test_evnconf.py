#!/usr/bin/env python3
"""
Test each property of envconf module.
"""
import shutil
from pathlib import Path
import logging
from export_vn.evnconf import EvnConf

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level = logging.INFO)


def test_logging(cmdopt, capsys):
    with capsys.disabled():
        if cmdopt == 'DEBUG':
            logging.getLogger().setLevel(logging.DEBUG)
        logging.debug('Running with debug logging level')

# Create test site configuration file
SITE = 'tst'
shutil.copy(str(Path.home()) + '/Client_API_VN/Export/evn_template.ini',
            str(Path.home()) + '/.evn_' + SITE + '.ini')

CFG = EvnConf(SITE)

def test_version():
    """Check if version is defined."""
    logging.info('package version: %s', CFG.version)

def test_site():
    """Check if configuration file exists."""
    cfg_file = Path(str(Path.home()) + '/.evn_' + SITE + '.ini')
    assert cfg_file.is_file()

def test_site_name():
    """ Test property. """
    assert CFG.site == SITE

def test_base_url():
    """ Test property. """
    assert CFG.base_url == 'https://www.faune-xxx.org/'

def test_user_email():
    """ Test property. """
    assert CFG.user_email == 'nom.prenom@example.net'

def test_user_pw():
    """ Test property. """
    assert CFG.user_pw == '*evn_user_pw*'

def test_client_key():
    """ Test property. """
    assert CFG.client_key == '*evn_client_key*'

def test_client_secret():
    """ Test property. """
    assert CFG.client_secret == '*evn_client_secret*'

def test_file_store():
    """ Test property. """
    assert CFG.file_store == 'VN_files' + '/' + SITE + '/'

def test_db_host():
    """ Test property. """
    assert CFG.db_host == 'localhost'

def test_db_port():
    """ Test property. """
    assert CFG.db_port == '5432'

def test_db_name():
    """ Test property. """
    assert CFG.db_name == '*faune_xxx*'

def test_db_schema():
    """ Test property. """
    assert CFG.db_schema == 'import'

def test_db_group():
    """ Test property. """
    assert CFG.db_group == '*lpo_xxx*'

def test_db_user():
    """ Test property. """
    assert CFG.db_user == '*xferxx*'

def test_db_pw():
    """ Test property. """
    assert CFG.db_pw == '*evn_db_pw*'

def test_sql_scripts():
    """ Test property. """
    assert CFG.sql_scripts == 'Client_API_VN/Examples/VN_sql'

def test_external1_name():
    """ Test property. """
    assert CFG.external1_name == '*evn_external1_name*'

def test_external1_pw():
    """ Test property. """
    assert CFG.external1_pw == '*evn_external1_pw*'
