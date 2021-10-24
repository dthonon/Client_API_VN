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
from export_vn.evnconf import MissingConfigurationFile
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
            "db_enabled": True,
            "start_date": datetime(2019, 8, 1),
            "end_date": datetime(2019, 9, 1),
        },
        {
            "file": "evn_tst1.yaml",
            "site": "tst2",
            "site_enabled": False,
            "file_enabled": True,
            "db_enabled": True,
            "start_date": datetime(2019, 8, 1),
            "end_date": datetime(2019, 9, 1),
        },
        {
            "file": "evn_tst2.yaml",
            "site": "tst3",
            "site_enabled": True,
            "file_enabled": False,
            "db_enabled": False,
            "start_date": None,
            "end_date": None,
        },
        {
            "file": "evn_tst3.yaml",
            "site": "tst4",
            "site_enabled": True,
            "file_enabled": False,
            "db_enabled": False,
            "start_date": None,
            "end_date": None,
        },
    ],
)
def create_file(request):
    cfg_file = "." + request.param["file"]
    # Copy test file to HOME
    in_file = (
        Path.home()
        / "Code"
        / "Client_API_VN"
        / "tests"
        / "data"
        / request.param["file"]
    )
    out_file = Path.home() / cfg_file
    if (not out_file.is_file()) or (in_file.stat().st_mtime > out_file.stat().st_mtime):
        shutil.copy(in_file, out_file)
    # Instantiate configuration classes
    if request.param["file"] == "evn_tst3.yaml":
        try:
            cfg = EvnConf(cfg_file)
        except YAMLValidationError:
            pytest.skip("Found YAML error as expected")
            return
    else:
        cfg = EvnConf(cfg_file)
    c_cfg = cfg.ctrl_list[CRTL]
    s_cfg = cfg.site_list[request.param["site"]]
    return (cfg, c_cfg, s_cfg, cfg_file, request.param)


# ---------------
# Various testing
# ---------------
@pytest.mark.order(index=10)
class TestVarious:
    def test_no_file(self):
        """Check for exception is no configuration file."""
        cfg_file = ".QfB7F0jvnC7V.yaml"
        try:
            EvnConf(cfg_file)
        except MissingConfigurationFile:
            pytest.skip("Expected evnconf MissingConfigurationFile error")

    def test_version(self, create_file):
        """Check if version is defined."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        pkg_version = cfg.version
        logging.debug("package version: %s", pkg_version)
        assert pkg_version == __version__


# -------------
# Basic testing
# -------------
@pytest.mark.order(index=10)
class TestBase:
    def test_ctrl_list(self, create_file):
        """Check if list of controlers is complete."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        ctrl_list = cfg.ctrl_list
        for ctrl in {
            "entities",
            "families",
            "fields",
            "local_admin_units",
            "observations",
            "observers",
            "places",
            "species",
            "taxo_groups",
            "territorial_units",
            "validations",
        }:
            assert ctrl in ctrl_list

    def test_site(self, create_file):
        """Check if configuration file exists."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        cfg_file = Path.home() / cfg_file
        assert cfg_file.is_file()


# --------------
# Params testing
# --------------
@pytest.mark.order(index=20)
class TestParams:
    def test_site_name(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.site == params["site"]

    def test_site_enabled(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.enabled == params["site_enabled"]

    def test_ctrl_enabled(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert c_cfg.enabled

    def test_ctrl_schedule_year(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        if params["site"] in ["tst1", "tst2"]:
            assert c_cfg.schedule_year == "*"
        else:
            assert c_cfg.schedule_year is None

    def test_ctrl_schedule_month(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        if params["site"] in ["tst1", "tst2"]:
            assert c_cfg.schedule_month == "*"
        else:
            assert c_cfg.schedule_month is None

    def test_ctrl_schedule_day(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        if params["site"] in ["tst1", "tst2"]:
            assert c_cfg.schedule_day == "*"
        else:
            assert c_cfg.schedule_day is None

    def test_ctrl_schedule_week(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        if params["site"] in ["tst1", "tst2"]:
            assert c_cfg.schedule_week == "*"
        else:
            assert c_cfg.schedule_week is None

    def test_ctrl_schedule_day_of_week(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        if params["site"] in ["tst1", "tst2"]:
            assert c_cfg.schedule_day_of_week == "*"
        else:
            assert c_cfg.schedule_day_of_week == "2"

    def test_ctrl_schedule_hour(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        if params["site"] in ["tst1", "tst2"]:
            assert c_cfg.schedule_hour == "*"
        else:
            assert c_cfg.schedule_hour is None

    def test_ctrl_schedule_minute(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        if params["site"] in ["tst1", "tst2"]:
            assert c_cfg.schedule_minute == "0"
        else:
            assert c_cfg.schedule_minute is None

    def test_ctrl_schedule_second(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        if params["site"] in ["tst1", "tst2"]:
            assert c_cfg.schedule_second == "0"
        else:
            assert c_cfg.schedule_second is None

    def test_taxo_exclude(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.taxo_exclude == ["TAXO_GROUP_ALIEN_PLANTS"]

    def test_territorial_unit_ids(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.territorial_unit_ids == ["7"]

    def test_json_format(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.json_format == "short"

    def test_start_date(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.start_date == params["start_date"]

    def test_end_date(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.end_date == params["end_date"]

    def test_type_date(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        if s_cfg.type_date is not None:
            assert s_cfg.type_date == "sighting" or s_cfg.type_date == "entry"

    def test_base_url(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.base_url == "https://www.faune-xxx.org/"

    def test_user_email(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.user_email == "nom.prenom@example.net"

    def test_user_pw(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.user_pw == "user_pw"

    def test_client_key(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.client_key == "client_key"

    def test_client_secret(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.client_secret == "client_secret"

    def test_file_enabled(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.file_enabled == params["file_enabled"]

    def test_file_store(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        if s_cfg.file_enabled:
            assert s_cfg.file_store == "test_files" + "/" + params["site"] + "/"
        else:
            assert s_cfg.file_store == ""

    def test_db_enabled(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.db_enabled == params["db_enabled"]

    def test_db_host(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.db_host == "localhost"

    def test_db_port(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.db_port == "5432"

    def test_db_name(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.db_name == "faune_xxx"

    def test_db_schema_import(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.db_schema_import == "import"

    def test_db_schema_vn(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.db_schema_vn == "src_vn"

    def test_db_group(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.db_group == "lpo_xxx"

    def test_db_user(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.db_user == "xferxx"

    def test_db_pw(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.db_pw == "db_pw"

    def test_db_secret_key(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.db_secret_key == "mySecretKey"

    def test_tuning_max_list_length(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.tuning_max_list_length == 100

    def test_tuning_max_chunks(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.tuning_max_chunks == 10

    def test_tuning_max_retry(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.tuning_max_retry == 5

    def test_tuning_retry_delay(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.tuning_retry_delay == 5

    def test_tuning_unavailable_delay(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.tuning_unavailable_delay == 600

    def test_tuning_max_requests(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.tuning_max_requests == 0

    def test_tuning_lru_maxsize(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.tuning_lru_maxsize == 32

    def test_tuning_pid_kp(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.tuning_pid_kp == 0.0

    def test_tuning_pid_ki(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.tuning_pid_ki == 0.003

    def test_tuning_pid_kd(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.tuning_pid_kd == 0.0

    def test_tuning_pid_setpoint(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.tuning_pid_setpoint == 10000

    def test_tuning_pid_limit_min(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.tuning_pid_limit_min == 1

    def test_tuning_pid_limit_max(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.tuning_pid_limit_max == 2000

    def test_tuning_pid_delta_days(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        assert s_cfg.tuning_pid_delta_days == 15

    def test_tuning_sched_executors(self, create_file):
        """Test property."""
        cfg, c_cfg, s_cfg, cfg_file, params = create_file
        if params["site"] in ["tst1", "tst2"]:
            assert s_cfg.tuning_sched_executors == 2
        else:
            assert s_cfg.tuning_sched_executors == 1
