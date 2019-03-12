#!/usr/bin/env python3
"""
Test each property of envconf module.
"""
import shutil
from pathlib import Path
import logging
from export_vn.evnconf import EvnConf

# Create test site configuration file
CRTL = 'observations'
SITE = 'tst1'
FILE = '.evn_tst.yaml'
shutil.copy(str(Path.home()) + '/Client_API_VN/export_vn/evn_template.yaml',
            str(Path.home()) + '/' + FILE)

CFG = EvnConf(FILE)
CCFG = CFG.ctrl_list[CRTL]
SCFG = CFG.site_list[SITE]

def test_version():
    """Check if version is defined."""
    logging.debug('package version: %s', CFG.version)

def test_site():
    """Check if configuration file exists."""
    cfg_file = Path(str(Path.home()) + '/' + FILE)
    assert cfg_file.is_file()

def test_site_name():
    """ Test property. """
    assert SCFG.site == SITE

def test_enabled():
    """ Test property. """
    assert SCFG.enabled == True

def test_base_url():
    """ Test property. """
    assert SCFG.base_url == 'https://www.faune-xxx.org/'

def test_user_email():
    """ Test property. """
    assert SCFG.user_email == 'nom.prenom@example.net'

def test_user_pw():
    """ Test property. """
    assert SCFG.user_pw == 'user_pw'

def test_client_key():
    """ Test property. """
    assert SCFG.client_key == 'client_key'

def test_client_secret():
    """ Test property. """
    assert SCFG.client_secret == 'client_secret'

def test_file_store():
    """ Test property. """
    assert SCFG.file_store == 'VN_files' + '/' + SITE + '/'

def test_db_host():
    """ Test property. """
    assert SCFG.db_host == 'localhost'

def test_db_port():
    """ Test property. """
    assert SCFG.db_port == '5432'

def test_db_name():
    """ Test property. """
    assert SCFG.db_name == 'faune_xxx'

def test_db_schema_import():
    """ Test property. """
    assert SCFG.db_schema_import == 'import'

def test_db_schema_vn():
    """ Test property. """
    assert SCFG.db_schema_vn == 'src_vn'

def test_db_group():
    """ Test property. """
    assert SCFG.db_group == 'lpo_xxx'

def test_db_user():
    """ Test property. """
    assert SCFG.db_user == 'xferxx'

def test_db_pw():
    """ Test property. """
    assert SCFG.db_pw == 'db_pw'

def test_sql_scripts():
    """ Test property. """
    assert SCFG.sql_scripts == 'Client_API_VN/Examples/VN_sql'

def test_external1_name():
    """ Test property. """
    assert SCFG.external1_name == 'external1_name'

def test_external1_pw():
    """ Test property. """
    assert SCFG.external1_pw == 'external1_pw'
