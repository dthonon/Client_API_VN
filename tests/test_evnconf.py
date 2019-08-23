"""
Test each property of envconf module.
"""
import logging
import os
import shutil
from pathlib import Path

import pytest

from export_vn import __version__
from export_vn.evnconf import EvnConf

# Testing constants
CRTL = "observations"


# Create test site configuration file
@pytest.fixture(
    scope="session",
    params=[
        {
            "file": "evn_tst1.yaml",
            "site": "tst1",
            "site_enabled": True,
            "file_enabled": True,
        },
        {
            "file": "evn_tst1.yaml",
            "site": "tst2",
            "site_enabled": False,
            "file_enabled": True,
        },
        {
            "file": "evn_tst2.yaml",
            "site": "tst3",
            "site_enabled": True,
            "file_enabled": False,
        },
    ],
)
def create_file(request):
    cfg_file = "." + request.param["file"]
    # Copy test file to HOME
    in_file = str(Path.home()) + "/Client_API_VN/tests/data/" + request.param["file"]
    out_file = str(Path.home()) + "/" + cfg_file
    if (not os.path.exists(out_file)) or (
        os.path.getctime(in_file) > os.path.getctime(out_file)
    ):
        shutil.copy(in_file, out_file)
    # Instantiate configuration classes
    cfg = EvnConf(cfg_file)
    c_cfg = cfg.ctrl_list[CRTL]
    s_cfg = cfg.site_list[request.param["site"]]
    return (cfg, c_cfg, s_cfg, cfg_file, request.param)


def test_version(create_file):
    """Check if version is defined."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    pkg_version = cfg.version
    logging.debug("package version: %s", pkg_version)
    assert pkg_version == __version__


def test_ctrl_list(create_file):
    """Check if list of controlers is complete."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    ctrl_list = cfg.ctrl_list
    for ctrl in {
        "entities",
        "fields",
        "local_admin_units",
        "observations",
        "observers",
        "places",
        "species",
        "taxo_groups",
        "territorial_units",
    }:
        assert ctrl in ctrl_list


def test_site(create_file):
    """Check if configuration file exists."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    cfg_file = Path(str(Path.home()) + "/" + cfg_file)
    assert cfg_file.is_file()


def test_site_name(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.site == params["site"]


def test_site_enabled(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.enabled == params["site_enabled"]


def test_ctrl_enabled(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert c_cfg.enabled


def test_ctrl_taxo_exclude(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert c_cfg.taxo_exclude == ["TAXO_GROUP_ALIEN_PLANTS"]


def test_base_url(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.base_url == "https://www.faune-xxx.org/"


def test_user_email(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.user_email == "nom.prenom@example.net"


def test_user_pw(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.user_pw == "user_pw"


def test_client_key(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.client_key == "client_key"


def test_client_secret(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.client_secret == "client_secret"


def test_file_enabled(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.file_enabled == params["file_enabled"]


def test_file_store(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    if s_cfg.file_enabled:
        assert s_cfg.file_store == "test_files" + "/" + params["site"] + "/"
    else:
        assert s_cfg.file_store == ""


def test_db_host(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.db_host == "localhost"


def test_db_port(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.db_port == "5432"


def test_db_name(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.db_name == "faune_xxx"


def test_db_schema_import(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.db_schema_import == "import"


def test_db_schema_vn(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.db_schema_vn == "src_vn"


def test_db_group(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.db_group == "lpo_xxx"


def test_db_user(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.db_user == "xferxx"


def test_db_pw(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.db_pw == "db_pw"


def test_db_secret_key(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.db_secret_key == "mySecretKey"


def test_tuning_max_chunks(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.tuning_max_chunks == 10


def test_tuning_max_retry(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.tuning_max_retry == 5


def test_tuning_max_requests(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.tuning_max_requests == 0


def test_tuning_lru_maxsize(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.tuning_lru_maxsize == 32


def test_tuning_min_year(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.tuning_min_year == 1901


def test_tuning_pid_kp(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.tuning_pid_kp == 0.0


def test_tuning_pid_ki(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.tuning_pid_ki == 0.003


def test_tuning_pid_kd(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.tuning_pid_kd == 0.0


def test_tuning_pid_setpoint(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.tuning_pid_setpoint == 10000


def test_tuning_pid_limit_min(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.tuning_pid_limit_min == 5


def test_tuning_pid_limit_max(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.tuning_pid_limit_max == 2000


def test_tuning_pid_delta_days(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.tuning_pid_delta_days == 15


def test_tuning_db_worker_threads(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.tuning_db_worker_threads == 2
