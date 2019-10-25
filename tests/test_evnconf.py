"""
Test each property of envconf module.
"""
from datetime import datetime
import logging
import shutil
from pathlib import Path

import pytest

from export_vn import __version__
from export_vn.evnconf import EvnConf
from strictyaml import YAMLValidationError

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
            "start_date": datetime(2019, 9, 1),
        },
        {
            "file": "evn_tst1.yaml",
            "site": "tst2",
            "site_enabled": False,
            "file_enabled": True,
            "start_date": datetime(2019, 9, 1),
        },
        {
            "file": "evn_tst2.yaml",
            "site": "tst3",
            "site_enabled": True,
            "file_enabled": False,
            "start_date": None,
        },
        {
            "file": "evn_tst3.yaml",
            "site": "tst4",
            "site_enabled": True,
            "file_enabled": False,
            "start_date": None,
        },
    ],
)
def create_file(request):
    cfg_file = "." + request.param["file"]
    # Copy test file to HOME
    in_file = Path.home() / "Client_API_VN" / "tests" / "data" / request.param["file"]
    out_file = Path.home() / cfg_file
    if (not out_file.is_file()) or (in_file.stat().st_mtime > out_file.stat().st_mtime):
        shutil.copy(in_file, out_file)
    # Instantiate configuration classes
    if request.param["file"] == "evn_tst3.yaml":
        try:
            cfg = EvnConf(cfg_file)
        except YAMLValidationError:
            pytest.skip("Expected YAML error")
    else:
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
    cfg_file = Path.home() / cfg_file
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


def test_ctrl_schedule_year(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    if params["site"] in ["tst1", "tst2"]:
        assert c_cfg.schedule_year == "*"
    else:
        assert c_cfg.schedule_year is None


def test_ctrl_schedule_month(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    if params["site"] in ["tst1", "tst2"]:
        assert c_cfg.schedule_month == "*"
    else:
        assert c_cfg.schedule_month is None


def test_ctrl_schedule_day(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    if params["site"] in ["tst1", "tst2"]:
        assert c_cfg.schedule_day == "*"
    else:
        assert c_cfg.schedule_day is None


def test_ctrl_schedule_week(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    if params["site"] in ["tst1", "tst2"]:
        assert c_cfg.schedule_week == "*"
    else:
        assert c_cfg.schedule_week is None


def test_ctrl_schedule_day_of_week(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    if params["site"] in ["tst1", "tst2"]:
        assert c_cfg.schedule_day_of_week == "*"
    else:
        assert c_cfg.schedule_day_of_week == "2"


def test_ctrl_schedule_hour(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    if params["site"] in ["tst1", "tst2"]:
        assert c_cfg.schedule_hour == "*"
    else:
        assert c_cfg.schedule_hour is None


def test_ctrl_schedule_minute(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    if params["site"] in ["tst1", "tst2"]:
        assert c_cfg.schedule_minute == "0"
    else:
        assert c_cfg.schedule_minute is None


def test_ctrl_schedule_second(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    if params["site"] in ["tst1", "tst2"]:
        assert c_cfg.schedule_second == "0"
    else:
        assert c_cfg.schedule_second is None


def test_taxo_exclude(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.taxo_exclude == ["TAXO_GROUP_ALIEN_PLANTS"]


def test_json_format(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.json_format == "short"


def test_start_date(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.start_date == params["start_date"]


def test_end_date(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    assert s_cfg.end_date is None


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
    assert s_cfg.tuning_pid_limit_min == 1


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


def test_tuning_sched_executors(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    if params["site"] in ["tst1", "tst2"]:
        assert s_cfg.tuning_sched_executors == 2
    else:
        assert s_cfg.tuning_sched_executors == 1

def test_pne_data_url(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    if params["site"] in ["tst1", "tst2"]:
        assert s_cfg.pne_data_url == "https://portail.ecrins-parcnational.fr/xxx/admin/xportcsv.php"
    else:
        assert s_cfg.pne_data_url == ""

def test_pne_db_schema(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    if params["site"] in ["tst1", "tst2"]:
        assert s_cfg.pne_db_schema == "import_pne"
    else:
        assert s_cfg.pne_db_schema == ""

def test_pne_db_in_table(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    if params["site"] in ["tst1", "tst2"]:
        assert s_cfg.pne_db_in_table == "in_pne"
    else:
        assert s_cfg.pne_db_in_table == ""

def test_pne_db_xref_table(create_file):
    """ Test property."""
    cfg, c_cfg, s_cfg, cfg_file, params = create_file
    if params["site"] in ["tst1", "tst2"]:
        assert s_cfg.pne_db_xref_table == "xref_pne"
    else:
        assert s_cfg.pne_db_xref_table == ""
