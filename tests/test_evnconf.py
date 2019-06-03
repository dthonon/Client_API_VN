#!/usr/bin/env python3
"""
Test each property of envconf module.
"""
import shutil
from pathlib import Path
import logging
from export_vn.evnconf import EvnConf
from export_vn import __version__

# Create test site configuration file
CRTL = 'observations'
SITE = 'tst1'
FILE = '.evn_tst.yaml'
shutil.copy(
    str(Path.home()) + '/Client_API_VN/src/export_vn/data/evn_template.yaml',
    str(Path.home()) + '/' + FILE)

CFG = EvnConf(FILE)
CCFG = CFG.ctrl_list[CRTL]
SCFG = CFG.site_list[SITE]


def test_version():
    """Check if version is defined."""
    pkg_version = CFG.version
    logging.debug('package version: %s', pkg_version)
    assert pkg_version == __version__


def test_site():
    """Check if configuration file exists."""
    cfg_file = Path(str(Path.home()) + '/' + FILE)
    assert cfg_file.is_file()


def test_site_name():
    """ Test property."""
    assert SCFG.site == SITE


def test_site_enabled():
    """ Test property."""
    assert SCFG.enabled


def test_ctrl_enabled():
    """ Test property."""
    assert CCFG.enabled


def test_ctrl_taxo_exclude():
    """ Test property."""
    assert CCFG.taxo_exclude == ['TAXO_GROUP_ALIEN_PLANTS']


def test_base_url():
    """ Test property."""
    assert SCFG.base_url == 'https://www.faune-xxx.org/'


def test_user_email():
    """ Test property."""
    assert SCFG.user_email == 'nom.prenom@example.net'


def test_user_pw():
    """ Test property."""
    assert SCFG.user_pw == 'user_pw'


def test_client_key():
    """ Test property."""
    assert SCFG.client_key == 'client_key'


def test_client_secret():
    """ Test property."""
    assert SCFG.client_secret == 'client_secret'


def test_file_enabled():
    """ Test property."""
    assert not SCFG.file_enabled


def test_file_store():
    """ Test property."""
    assert SCFG.file_store == 'VN_files' + '/' + SITE + '/'


def test_db_host():
    """ Test property."""
    assert SCFG.db_host == 'localhost'


def test_db_port():
    """ Test property."""
    assert SCFG.db_port == '5432'


def test_db_name():
    """ Test property."""
    assert SCFG.db_name == 'faune_xxx'


def test_db_schema_import():
    """ Test property."""
    assert SCFG.db_schema_import == 'import'


def test_db_schema_vn():
    """ Test property."""
    assert SCFG.db_schema_vn == 'src_vn'


def test_db_group():
    """ Test property."""
    assert SCFG.db_group == 'lpo_xxx'


def test_db_user():
    """ Test property."""
    assert SCFG.db_user == 'xferxx'


def test_db_pw():
    """ Test property."""
    assert SCFG.db_pw == 'db_pw'


def test_tuning_max_chunks():
    """ Test property."""
    assert SCFG.tuning_max_chunks == 10


def test_tuning_max_retry():
    """ Test property."""
    assert SCFG.tuning_max_retry == 5


def test_tuning_max_requests():
    """ Test property."""
    assert SCFG.tuning_max_requests == 0


def test_tuning_lru_maxsize():
    """ Test property."""
    assert SCFG.tuning_lru_maxsize == 32


def test_tuning_min_year():
    """ Test property."""
    assert SCFG.tuning_min_year == 1901


def test_tuning_pid_kp():
    """ Test property."""
    assert SCFG.tuning_pid_kp == 0.0


def test_tuning_pid_ki():
    """ Test property."""
    assert SCFG.tuning_pid_ki == 0.003


def test_tuning_pid_kd():
    """ Test property."""
    assert SCFG.tuning_pid_kd == 0.0


def test_tuning_pid_setpoint():
    """ Test property."""
    assert SCFG.tuning_pid_setpoint == 10000


def test_tuning_pid_limit_min():
    """ Test property."""
    assert SCFG.tuning_pid_limit_min == 10


def test_tuning_pid_limit_max():
    """ Test property."""
    assert SCFG.tuning_pid_limit_max == 2000


def test_tuning_pid_delta_days():
    """ Test property."""
    assert SCFG.tuning_pid_delta_days == 15
