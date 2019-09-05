# pylint: disable=too-many-instance-attributes
"""Expose local configuration parameters as properties.

Parameters are defined in a YAML file located in $HOME directory.
This file is created using --init option, and then customized by the user.
Each time the application is run, this parameter file is read and the
parameters are then available as properties of EvnCtrlConf and EvnSiteConf.

"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, cast

from strictyaml import (
    Bool,
    Datetime,
    Email,
    Enum,
    Float,
    Int,
    Map,
    MapPattern,
    Optional,
    Seq,
    Str,
    Url,
    YAMLError,
    YAMLValidationError,
    load,
)

from . import _, __version__

logger = logging.getLogger("transfer_vn.evn_conf")


class EvnConfException(Exception):
    """An exception occurred while loading parameters."""


class IncorrectParameter(EvnConfException):
    """Incorrect or missing parameter."""


# Define PEP 484 types, TODO: refine type
_CtrlType = Dict[str, Dict[str, Any]]
_ConfType = Dict[str, Any]

# Define strictyaml schema
_ConfSchema = Map(
    {
        "main": Map({"admin_mail": Email()}),
        "controler": Map(
            {
                "entities": Map({"enabled": Bool()}),
                "fields": Map({"enabled": Bool()}),
                "local_admin_units": Map({"enabled": Bool()}),
                "observations": Map(
                    {
                        "enabled": Bool(),
                        Optional("taxo_exclude"): Seq(Str()),
                        Optional("json_format", default="short"): Enum(
                            ["short", "long"]
                        ),
                        Optional("start_date"): Datetime(),
                        Optional("end_date"): Datetime(),
                    }
                ),
                "observers": Map({"enabled": Bool()}),
                "places": Map({"enabled": Bool()}),
                "species": Map({"enabled": Bool()}),
                "taxo_groups": Map({"enabled": Bool()}),
                "territorial_units": Map({"enabled": Bool()}),
            }
        ),
        "site": MapPattern(
            Str(),
            Map(
                {
                    "enabled": Bool(),
                    "site": Url(),
                    "user_email": Email(),
                    "user_pw": Str(),
                    "client_key": Str(),
                    "client_secret": Str(),
                }
            ),
        ),
        Optional("file"): Map({"enabled": Bool(), "file_store": Str()}),
        "database": Map(
            {
                Optional("db_host", default="localhost"): Str(),
                Optional("db_port", default=5432): Int(),
                "db_name": Str(),
                "db_schema_import": Str(),
                "db_schema_vn": Str(),
                "db_group": Str(),
                "db_user": Str(),
                "db_pw": Str(),
                "db_secret_key": Str(),
                Optional("db_out_proj", default="2154"): Str(),
            }
        ),
        Optional("tuning"): Map(
            {
                Optional("max_chunks", default=10): Int(),
                Optional("max_retry", default=5): Int(),
                Optional("max_requests", default=0): Int(),
                Optional("retry_delay", default=5): Int(),
                Optional("lru_maxsize", default=32): Int(),
                Optional("pid_kp", default=0.0): Float(),
                Optional("pid_ki", default=0.003): Float(),
                Optional("pid_kd", default=0.0): Float(),
                Optional("pid_setpoint", default=10000): Float(),
                Optional("pid_limit_min", default=5): Float(),
                Optional("pid_limit_max", default=2000): Float(),
                Optional("pid_delta_days", default=15): Int(),
                Optional("db_worker_threads", default=2): Int(),
                Optional("db_worker_queue", default=100000): Int(),
            }
        ),
    }
)


class EvnCtrlConf:
    """Expose controler configuration as properties.
    """

    def __init__(self, ctrl: str, config: _CtrlType) -> None:
        self._ctrl = ctrl

        # Import parameters in properties
        self._enabled = True
        if "enabled" in config["controler"][ctrl]:
            self._enabled = config["controler"][ctrl]["enabled"]
        self._taxo_exclude = []  # type: List[str]
        if "taxo_exclude" in config["controler"][ctrl]:
            self._taxo_exclude = config["controler"][ctrl]["taxo_exclude"]
        self._json_format = "short"  # type: str
        if "json_format" in config["controler"][ctrl]:
            self._json_format = config["controler"][ctrl]["json_format"]
        self._start_date = None  # type: datetime
        if "start_date" in config["controler"][ctrl]:
            self._start_date = config["controler"][ctrl]["start_date"]
        self._end_date = None  # type: datetime
        if "end_date" in config["controler"][ctrl]:
            self._end_date = config["controler"][ctrl]["end_date"]

    @property
    def enabled(self) -> bool:
        """Return enabled flag, defining if controler should be used."""
        return self._enabled

    @property
    def taxo_exclude(self) -> List[str]:
        """Return list of taxo_groups excluded from download."""
        return self._taxo_exclude

    @property
    def json_format(self) -> str:
        """Return json format (short/long) for download."""
        return self._json_format

    @property
    def start_date(self) -> datetime:
        """Return earliest date for download."""
        return self._start_date

    @property
    def end_date(self) -> datetime:
        """Return latest date for download."""
        return self._end_date


class EvnSiteConf:
    """Expose site configuration as properties.
    """

    def __init__(self, site: str, config: _ConfType) -> None:
        self._site = site
        # Import parameters in properties
        try:
            self._enabled = True
            if "enabled" in config["site"][site]:
                self._enabled = config["site"][site]["enabled"]
            self._client_key = config["site"][site]["client_key"]  # type: str
            self._client_secret = config["site"][site]["client_secret"]  # type: str
            self._user_email = config["site"][site]["user_email"]  # type: str
            self._user_pw = config["site"][site]["user_pw"]  # type: str
            self._base_url = config["site"][site]["site"]  # type: str

            self._file_enabled = False
            self._file_store = ""
            if "file" in config:
                if "enabled" in config["file"]:
                    self._file_enabled = config["file"]["enabled"]
                if self._file_enabled:
                    if "file_store" in config["file"]:
                        self._file_store = (
                            config["file"]["file_store"] + "/" + site + "/"
                        )
                    else:
                        logger.error(_("file:file_store must be defined"))
                        raise IncorrectParameter

            self._db_host = config["database"]["db_host"]  # type: str
            self._db_port = str(config["database"]["db_port"])  # type: str
            self._db_name = config["database"]["db_name"]  # type: str
            self._db_schema_import = config["database"]["db_schema_import"]  # type: str
            self._db_schema_vn = config["database"]["db_schema_vn"]  # type: str
            self._db_group = config["database"]["db_group"]  # type: str
            self._db_user = config["database"]["db_user"]  # type: str
            self._db_pw = config["database"]["db_pw"]  # type: str
            self._db_secret_key = config["database"]["db_secret_key"]  # type: str
            self._db_out_proj = config["database"]["db_out_proj"]  # type: str

            if "tuning" in config:
                self._max_chunks = config["tuning"]["max_chunks"]  # type: int
                self._max_retry = config["tuning"]["max_retry"]  # type: int
                self._max_requests = config["tuning"]["max_requests"]  # type: int
                self._retry_delay = config["tuning"]["retry_delay"]  # type: int
                self._lru_maxsize = config["tuning"]["lru_maxsize"]  # type: int
                self._pid_kp = config["tuning"]["pid_kp"]  # type: float
                self._pid_ki = config["tuning"]["pid_ki"]  # type: float
                self._pid_kd = config["tuning"]["pid_kd"]  # type: float
                self._pid_setpoint = config["tuning"]["pid_setpoint"]  # type: float
                self._pid_limit_min = config["tuning"]["pid_limit_min"]  # type: float
                self._pid_limit_max = config["tuning"]["pid_limit_max"]  # type: float
                self._pid_delta_days = config["tuning"]["pid_delta_days"]  # type: int
                self._db_worker_threads = config["tuning"][
                    "db_worker_threads"
                ]  # type: int
                self._db_worker_queue = config["tuning"]["db_worker_queue"]  # type: int
            else:
                # Provide default values
                self._max_chunks = 10  # type: int
                self._max_retry = 5  # type: int
                self._max_requests = 0  # type: int
                self._retry_delay = 5  # type: int
                self._lru_maxsize = 32  # type: int
                self._pid_kp = 0.0  # type: float
                self._pid_ki = 0.003  # type: float
                self._pid_kd = 0.0  # type: float
                self._pid_setpoint = 10000  # type: float
                self._pid_limit_min = 5  # type: float
                self._pid_limit_max = 2000  # type: float
                self._pid_delta_days = 15  # type: int
                self._db_worker_threads = 2  # type:int
                self._db_worker_queue = 100000  # type:int

        except Exception as e:
            logger.exception(_("Error creating %s configuration"), site)
            raise
        return None

    @property
    def site(self) -> str:
        """Return site name, used to identify configuration file."""
        return self._site

    @property
    def enabled(self) -> bool:
        """Return enabled flag, defining is site is to be downloaded."""
        return self._enabled

    @property
    def client_key(self) -> str:
        """Return oauth1 client_key, used to connect to VisioNature site."""
        return self._client_key

    @property
    def client_secret(self) -> str:
        """Return oauth1 client_secret, used to connect to VisioNature site."""
        return self._client_secret

    @property
    def user_email(self) -> str:
        """Return user email, used to connect to VisioNature site."""
        return self._user_email

    @property
    def user_pw(self) -> str:
        """Return user password, used to connect to VisioNature site."""
        return self._user_pw

    @property
    def base_url(self) -> str:
        """Return base URL of VisioNature site,
        used as prefix for API calls."""
        return self._base_url

    @property
    def file_enabled(self) -> bool:
        """Return flag to enable or not file storage
        on top of Postgresql storage."""
        return self._file_enabled

    @property
    def file_store(self) -> str:
        """Return directory, under $HOME, where downloaded files are stored."""
        return self._file_store

    @property
    def db_host(self) -> str:
        """Return hostname of Postgresql server."""
        return self._db_host

    @property
    def db_port(self) -> str:
        """Return IP port of Postgresql server."""
        return self._db_port

    @property
    def db_name(self) -> str:
        """Return database name."""
        return self._db_name

    @property
    def db_schema_import(self) -> str:
        """Return database schema where imported JSON data is stored."""
        return self._db_schema_import

    @property
    def db_schema_vn(self) -> str:
        """Return database schema where column data is stored."""
        return self._db_schema_vn

    @property
    def db_group(self) -> str:
        """Return group ROLE that gets access to tables."""
        return self._db_group

    @property
    def db_user(self) -> str:
        """Return user ROLE that owns the tables."""
        return self._db_user

    @property
    def db_pw(self) -> str:
        """Return db_user PASSWORD."""
        return self._db_pw

    @property
    def db_secret_key(self) -> str:
        """Return db SECRET KEY for Pseudonymization."""
        return self._db_secret_key

    @property
    def db_out_proj(self) -> str:
        """Return local EPSG coordinate system."""
        return self._db_out_proj

    @property
    def tuning_max_chunks(self) -> int:
        """Return tuning parameter."""
        return self._max_chunks

    @property
    def tuning_max_retry(self) -> int:
        """Return tuning parameter."""
        return self._max_retry

    @property
    def tuning_retry_delay(self) -> int:
        """Return tuning parameter."""
        return self._retry_delay

    @property
    def tuning_max_requests(self) -> int:
        """Return tuning parameter."""
        return self._max_requests

    @property
    def tuning_lru_maxsize(self) -> int:
        """Return tuning parameter."""
        return self._lru_maxsize

    @property
    def tuning_pid_kp(self) -> float:
        """Return tuning parameter."""
        return self._pid_kp

    @property
    def tuning_pid_ki(self) -> float:
        """Return tuning parameter."""
        return self._pid_ki

    @property
    def tuning_pid_kd(self) -> float:
        """Return tuning parameter."""
        return self._pid_kd

    @property
    def tuning_pid_setpoint(self) -> float:
        """Return tuning parameter."""
        return self._pid_setpoint

    @property
    def tuning_pid_limit_min(self) -> float:
        """Return tuning parameter."""
        return self._pid_limit_min

    @property
    def tuning_pid_limit_max(self) -> float:
        """Return tuning parameter."""
        return self._pid_limit_max

    @property
    def tuning_pid_delta_days(self) -> int:
        """Return tuning parameter."""
        return self._pid_delta_days

    @property
    def tuning_db_worker_threads(self) -> int:
        """Return tuning parameter."""
        return self._db_worker_threads

    @property
    def tuning_db_worker_queue(self) -> int:
        """Return tuning parameter."""
        return self._db_worker_queue


class EvnConf:
    """
    Read config file and expose list of sites configuration
    """

    def __init__(self, file: str) -> None:
        # Define configuration schema
        # Read configuration parameters
        p = Path.home() / file
        yaml_text = p.read_text()
        try:
            logger.info(_("Loading YAML configuration %s"), file)
            self._config = load(yaml_text, _ConfSchema).data
        except YAMLValidationError:
            logger.critical(_("Incorrect content in YAML configuration %s"), file)
            logger.critical(_("%s"), sys.exc_info()[1])
            raise
        except YAMLError:
            logger.critical(_("Error while reading YAML configuration %s"), file)
            raise

        self._ctrl_list = {}  # type: _CtrlType
        for ctrl in self._config["controler"]:
            self._ctrl_list[ctrl] = cast(_CtrlType, EvnCtrlConf(ctrl, self._config))

        self._site_list = {}  # type: _ConfType
        for site in self._config["site"]:
            self._site_list[site] = EvnSiteConf(site, self._config)

    @property
    def version(self) -> str:
        """Return version."""
        return __version__

    @property
    def ctrl_list(self) -> _CtrlType:
        """Return list of controler configurations."""
        return self._ctrl_list

    @property
    def site_list(self) -> _ConfType:
        """Return list of site configurations."""
        return self._site_list
