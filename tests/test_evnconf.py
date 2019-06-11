#!/usr/bin/env python3
"""
Test each property of envconf module.
"""
import logging
import shutil
from pathlib import Path

import pytest
from export_vn import __version__
from export_vn.evnconf import EvnConf

# Testing constants
CRTL = 'observations'
FILE = '.evn_tst.yaml'

# Create test site configuration file
@pytest.fixture(scope="session", params=['tst1', 'tst2'])
def create_file(request):
    site = request.param
    # Copy test file to HOME
    shutil.copy(
        str(Path.home()) +
        '/Client_API_VN/src/export_vn/data/evn_template.yaml',
        str(Path.home()) + '/' + FILE)
    # Instantiate configuration classes
    cfg = EvnConf(FILE)
    c_cfg = cfg.ctrl_list[CRTL]
    s_cfg = cfg.site_list[site]
    return (cfg, c_cfg, s_cfg, site)


def test_version(create_file):
    """Check if version is defined."""
    cfg, c_cfg, s_cfg, site = create_file
    pkg_version = cfg.version
    logging.debug('package version: %s', pkg_version)
    assert pkg_version == __version__


def test_site(create_file):
    """Check if configuration file exists."""
    cfg, c_cfg, s_cfg, site = create_file
    cfg_file = Path(str(Path.home()) + '/' + FILE)
    assert cfg_file.is_file()


def test_site_name(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, site = create_file
    assert s_cfg.site == site


def test_site_enabled(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, site = create_file
    if site == 'tst1':
        assert s_cfg.enabled
    elif site == 'tst2':
        assert not s_cfg.enabled
    else:
        assert False


def test_ctrl_enabled(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, site = create_file
    assert c_cfg.enabled


def test_ctrl_taxo_exclude(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, site = create_file
    assert c_cfg.taxo_exclude == ['TAXO_GROUP_ALIEN_PLANTS']


def test_base_url(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, site = create_file
    assert s_cfg.base_url == 'https://www.faune-xxx.org/'


def test_user_email(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, site = create_file
    assert s_cfg.user_email == 'nom.prenom@example.net'


def test_user_pw(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, site = create_file
    assert s_cfg.user_pw == 'user_pw'


def test_client_key(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, site = create_file
    assert s_cfg.client_key == 'client_key'


def test_client_secret(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, site = create_file
    assert s_cfg.client_secret == 'client_secret'


def test_file_enabled(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, site = create_file
    assert not s_cfg.file_enabled


def test_file_store(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, site = create_file
    if s_cfg.file_enabled:
        assert s_cfg.file_store == 'VN_files' + '/' + site + '/'
    else:
        assert s_cfg.file_store == ''


def test_db_host(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, site = create_file
    assert s_cfg.db_host == 'localhost'


def test_db_port(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, site = create_file
    assert s_cfg.db_port == '5432'


def test_db_name(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, site = create_file
    assert s_cfg.db_name == 'faune_xxx'


def test_db_schema_import(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, site = create_file
    assert s_cfg.db_schema_import == 'import'


def test_db_schema_vn(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, site = create_file
    assert s_cfg.db_schema_vn == 'src_vn'


def test_db_group(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, site = create_file
    assert s_cfg.db_group == 'lpo_xxx'


def test_db_user(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, site = create_file
    assert s_cfg.db_user == 'xferxx'


def test_db_pw(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, site = create_file
    assert s_cfg.db_pw == 'db_pw'


def test_tuning_max_chunks(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, site = create_file
    assert s_cfg.tuning_max_chunks == 10


def test_tuning_max_retry(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, site = create_file
    assert s_cfg.tuning_max_retry == 5


def test_tuning_max_requests(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, site = create_file
    assert s_cfg.tuning_max_requests == 0


def test_tuning_lru_maxsize(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, site = create_file
    assert s_cfg.tuning_lru_maxsize == 32


def test_tuning_min_year(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, site = create_file
    assert s_cfg.tuning_min_year == 1901


def test_tuning_pid_kp(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, site = create_file
    assert s_cfg.tuning_pid_kp == 0.0


def test_tuning_pid_ki(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, site = create_file
    assert s_cfg.tuning_pid_ki == 0.003


def test_tuning_pid_kd(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, site = create_file
    assert s_cfg.tuning_pid_kd == 0.0


def test_tuning_pid_setpoint(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, site = create_file
    assert s_cfg.tuning_pid_setpoint == 10000


def test_tuning_pid_limit_min(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, site = create_file
    assert s_cfg.tuning_pid_limit_min == 10


def test_tuning_pid_limit_max(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, site = create_file
    assert s_cfg.tuning_pid_limit_max == 2000


def test_tuning_pid_delta_days(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, site = create_file
    assert s_cfg.tuning_pid_delta_days == 15
