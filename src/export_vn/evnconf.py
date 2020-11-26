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
from typing import Any, Dict, List, Union, cast

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


class MissingConfigurationFile(EvnConfException):
    """Incorrect or missing parameter."""


class IncorrectParameter(EvnConfException):
    """Incorrect or missing parameter."""


# Define PEP 484 types, TODO: refine type
_ConfType = Dict[str, Any]

# Define strictyaml schema
_ConfSchema = Map(
    {
        "main": Map({"admin_mail": Email()}),
        "controler": Map(
            {
                "entities": Map(
                    {
                        "enabled": Bool(),
                        "schedule": Map(
                            {
                                Optional("year"): Str(),
                                Optional("month"): Str(),
                                Optional("day"): Str(),
                                Optional("week"): Str(),
                                Optional("day_of_week"): Str(),
                                Optional("hour"): Str(),
                                Optional("minute"): Str(),
                                Optional("second"): Str(),
                            }
                        ),
                    }
                ),
                "families": Map(
                    {
                        "enabled": Bool(),
                        "schedule": Map(
                            {
                                Optional("year"): Str(),
                                Optional("month"): Str(),
                                Optional("day"): Str(),
                                Optional("week"): Str(),
                                Optional("day_of_week"): Str(),
                                Optional("hour"): Str(),
                                Optional("minute"): Str(),
                                Optional("second"): Str(),
                            }
                        ),
                    }
                ),
                "fields": Map(
                    {
                        "enabled": Bool(),
                        "schedule": Map(
                            {
                                Optional("year"): Str(),
                                Optional("month"): Str(),
                                Optional("day"): Str(),
                                Optional("week"): Str(),
                                Optional("day_of_week"): Str(),
                                Optional("hour"): Str(),
                                Optional("minute"): Str(),
                                Optional("second"): Str(),
                            }
                        ),
                    }
                ),
                "local_admin_units": Map(
                    {
                        "enabled": Bool(),
                        "schedule": Map(
                            {
                                Optional("year"): Str(),
                                Optional("month"): Str(),
                                Optional("day"): Str(),
                                Optional("week"): Str(),
                                Optional("day_of_week"): Str(),
                                Optional("hour"): Str(),
                                Optional("minute"): Str(),
                                Optional("second"): Str(),
                            }
                        ),
                    }
                ),
                "observations": Map(
                    {
                        "enabled": Bool(),
                        "schedule": Map(
                            {
                                Optional("year"): Str(),
                                Optional("month"): Str(),
                                Optional("day"): Str(),
                                Optional("week"): Str(),
                                Optional("day_of_week"): Str(),
                                Optional("hour"): Str(),
                                Optional("minute"): Str(),
                                Optional("second"): Str(),
                            }
                        ),
                    }
                ),
                "observers": Map(
                    {
                        "enabled": Bool(),
                        "schedule": Map(
                            {
                                Optional("year"): Str(),
                                Optional("month"): Str(),
                                Optional("day"): Str(),
                                Optional("week"): Str(),
                                Optional("day_of_week"): Str(),
                                Optional("hour"): Str(),
                                Optional("minute"): Str(),
                                Optional("second"): Str(),
                            }
                        ),
                    }
                ),
                "places": Map(
                    {
                        "enabled": Bool(),
                        "schedule": Map(
                            {
                                Optional("year"): Str(),
                                Optional("month"): Str(),
                                Optional("day"): Str(),
                                Optional("week"): Str(),
                                Optional("day_of_week"): Str(),
                                Optional("hour"): Str(),
                                Optional("minute"): Str(),
                                Optional("second"): Str(),
                            }
                        ),
                    }
                ),
                "species": Map(
                    {
                        "enabled": Bool(),
                        "schedule": Map(
                            {
                                Optional("year"): Str(),
                                Optional("month"): Str(),
                                Optional("day"): Str(),
                                Optional("week"): Str(),
                                Optional("day_of_week"): Str(),
                                Optional("hour"): Str(),
                                Optional("minute"): Str(),
                                Optional("second"): Str(),
                            }
                        ),
                    }
                ),
                "taxo_groups": Map(
                    {
                        "enabled": Bool(),
                        "schedule": Map(
                            {
                                Optional("year"): Str(),
                                Optional("month"): Str(),
                                Optional("day"): Str(),
                                Optional("week"): Str(),
                                Optional("day_of_week"): Str(),
                                Optional("hour"): Str(),
                                Optional("minute"): Str(),
                                Optional("second"): Str(),
                            }
                        ),
                    }
                ),
                "territorial_units": Map(
                    {
                        "enabled": Bool(),
                        "schedule": Map(
                            {
                                Optional("year"): Str(),
                                Optional("month"): Str(),
                                Optional("day"): Str(),
                                Optional("week"): Str(),
                                Optional("day_of_week"): Str(),
                                Optional("hour"): Str(),
                                Optional("minute"): Str(),
                                Optional("second"): Str(),
                            }
                        ),
                    }
                ),
                "validations": Map(
                    {
                        "enabled": Bool(),
                        "schedule": Map(
                            {
                                Optional("year"): Str(),
                                Optional("month"): Str(),
                                Optional("day"): Str(),
                                Optional("week"): Str(),
                                Optional("day_of_week"): Str(),
                                Optional("hour"): Str(),
                                Optional("minute"): Str(),
                                Optional("second"): Str(),
                            }
                        ),
                    }
                ),
            }
        ),
        Optional("filter"): Map(
            {
                Optional("taxo_exclude"): Seq(Str()),
                Optional("territorial_unit_ids"): Seq(Str()),
                Optional("json_format", default="short"): Enum(["short", "long"]),
                Optional("start_date"): Datetime(),
                Optional("end_date"): Datetime(),
                Optional("type_date", default="sighting"): Enum(["sighting", "entry"]),
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
        Optional("database"): Map(
            {
                "enabled": Bool(),
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
                Optional("max_list_length", default=100): Int(),
                Optional("max_chunks", default=10): Int(),
                Optional("max_retry", default=5): Int(),
                Optional("max_requests", default=0): Int(),
                Optional("retry_delay", default=5): Int(),
                Optional("unavailable_delay", default=600): Int(),
                Optional("lru_maxsize", default=32): Int(),
                Optional("pid_kp", default=0.0): Float(),
                Optional("pid_ki", default=0.003): Float(),
                Optional("pid_kd", default=0.0): Float(),
                Optional("pid_setpoint", default=10000): Float(),
                Optional("pid_limit_min", default=5): Float(),
                Optional("pid_limit_max", default=2000): Float(),
                Optional("pid_delta_days", default=15): Int(),
                Optional("sched_executors", default=1): Int(),
            }
        ),
    }
)


class EvnCtrlConf:
    """Expose controler configuration as properties."""

    @staticmethod
    def _schedule_param(cfg: Dict, param: str) -> Union[str, int, None]:
        return (
            None
            if ("schedule" not in cfg)
            else None
            if (param not in cfg["schedule"])
            else cfg["schedule"][param]
        )

    def __init__(self, ctrl: str, config: _ConfType) -> None:
        self._ctrl = ctrl

        # Import parameters in properties
        self._enabled = (
            True
            if "enabled" not in config["controler"][ctrl]
            else config["controler"][ctrl]["enabled"]
        )  # type: bool

        self._schedule_year = self._schedule_param(config["controler"][ctrl], "year")
        self._schedule_month = self._schedule_param(config["controler"][ctrl], "month")
        self._schedule_day = self._schedule_param(config["controler"][ctrl], "day")
        self._schedule_week = self._schedule_param(config["controler"][ctrl], "week")
        self._schedule_day_of_week = self._schedule_param(
            config["controler"][ctrl], "day_of_week"
        )
        self._schedule_hour = self._schedule_param(config["controler"][ctrl], "hour")
        self._schedule_minute = self._schedule_param(
            config["controler"][ctrl], "minute"
        )
        self._schedule_second = self._schedule_param(
            config["controler"][ctrl], "second"
        )

    @property
    def enabled(self) -> bool:
        """Return enabled flag, defining if controler should be used."""
        return self._enabled

    @property
    def schedule_year(self) -> Union[str, int, None]:
        """Return scheduling parameter."""
        return self._schedule_year

    @property
    def schedule_month(self) -> Union[str, int, None]:
        """Return scheduling parameter."""
        return self._schedule_month

    @property
    def schedule_day(self) -> Union[str, int, None]:
        """Return scheduling parameter."""
        return self._schedule_day

    @property
    def schedule_week(self) -> Union[str, int, None]:
        """Return scheduling parameter."""
        return self._schedule_week

    @property
    def schedule_day_of_week(self) -> Union[str, int, None]:
        """Return scheduling parameter."""
        return self._schedule_day_of_week

    @property
    def schedule_hour(self) -> Union[str, int, None]:
        """Return scheduling parameter."""
        return self._schedule_hour

    @property
    def schedule_minute(self) -> Union[str, int, None]:
        """Return scheduling parameter."""
        return self._schedule_minute

    @property
    def schedule_second(self) -> Union[str, int, None]:
        """Return scheduling parameter."""
        return self._schedule_second


class EvnSiteConf:
    """Expose site configuration as properties."""

    def __init__(self, site: str, config: _ConfType) -> None:
        self._site = site
        # Import parameters in properties
        try:
            self._enabled = (
                True
                if "enabled" not in config["site"][site]
                else config["site"][site]["enabled"]
            )
            self._client_key = config["site"][site]["client_key"]  # type: str
            self._client_secret = config["site"][site]["client_secret"]  # type: str
            self._user_email = config["site"][site]["user_email"]  # type: str
            self._user_pw = config["site"][site]["user_pw"]  # type: str
            self._base_url = config["site"][site]["site"]  # type: str

            self._taxo_exclude = []  # type: List[str]
            self._territorial_unit_ids = []  # type: List[str]
            self._json_format = "short"  # type: str
            self._start_date = None  # type: Union[datetime, None]
            self._end_date = None  # type: Union[datetime, None]
            self._type_date = None  # type: Union[str, None]
            if "filter" in config:
                if "taxo_exclude" in config["filter"]:
                    self._taxo_exclude = config["filter"]["taxo_exclude"]
                if "territorial_unit_ids" in config["filter"]:
                    self._territorial_unit_ids = config["filter"][
                        "territorial_unit_ids"
                    ]
                if "json_format" in config["filter"]:
                    self._json_format = config["filter"]["json_format"]
                if "start_date" in config["filter"]:
                    self._start_date = config["filter"]["start_date"]
                if "end_date" in config["filter"]:
                    self._end_date = config["filter"]["end_date"]
                if "type_date" in config["filter"]:
                    self._type_date = config["filter"]["type_date"]
            if (self._start_date is not None) and (self._end_date is not None):
                if self._start_date > self._end_date:
                    logger.error(_("start_date must be before end_date"))
                    raise IncorrectParameter

            self._file_enabled = False  # type: bool
            self._file_store = ""  # type: str
            if "file" in config:
                self._file_enabled = (
                    False
                    if "enabled" not in config["file"]
                    else config["file"]["enabled"]
                )
                if self._file_enabled:
                    if "file_store" in config["file"]:
                        self._file_store = (
                            config["file"]["file_store"] + "/" + site + "/"
                        )
                    else:
                        logger.error(_("file:file_store must be defined"))
                        raise IncorrectParameter

            self._database_enabled = False  # type: bool
            self._db_host = ""  # type: str
            self._db_port = ""  # type: str
            self._db_name = ""  # type: str
            self._db_schema_import = ""  # type: str
            self._db_schema_vn = ""  # type: str
            self._db_group = ""  # type: str
            self._db_user = ""  # type: str
            self._db_pw = ""  # type: str
            self._db_secret_key = ""  # type: str
            self._db_out_proj = ""  # type: str
            if "database" in config:
                self._database_enabled = (
                    False
                    if "enabled" not in config["database"]
                    else config["database"]["enabled"]
                )
                self._db_host = config["database"]["db_host"]  # type: str
                self._db_port = str(config["database"]["db_port"])  # type: str
                self._db_name = config["database"]["db_name"]  # type: str
                self._db_schema_import = config["database"][
                    "db_schema_import"
                ]  # type: str
                self._db_schema_vn = config["database"]["db_schema_vn"]  # type: str
                self._db_group = config["database"]["db_group"]  # type: str
                self._db_user = config["database"]["db_user"]  # type: str
                self._db_pw = config["database"]["db_pw"]  # type: str
                self._db_secret_key = config["database"]["db_secret_key"]  # type: str
                self._db_out_proj = config["database"]["db_out_proj"]  # type: str

            if "tuning" in config:
                self._max_list_length = config["tuning"]["max_list_length"]  # type: int
                self._max_chunks = config["tuning"]["max_chunks"]  # type: int
                self._max_retry = config["tuning"]["max_retry"]  # type: int
                self._max_requests = config["tuning"]["max_requests"]  # type: int
                self._retry_delay = config["tuning"]["retry_delay"]  # type: int
                self._unavailable_delay = config["tuning"][
                    "unavailable_delay"
                ]  # type: int
                self._lru_maxsize = config["tuning"]["lru_maxsize"]  # type: int
                self._pid_kp = config["tuning"]["pid_kp"]  # type: float
                self._pid_ki = config["tuning"]["pid_ki"]  # type: float
                self._pid_kd = config["tuning"]["pid_kd"]  # type: float
                self._pid_setpoint = config["tuning"]["pid_setpoint"]  # type: float
                self._pid_limit_min = config["tuning"]["pid_limit_min"]  # type: float
                self._pid_limit_max = config["tuning"]["pid_limit_max"]  # type: float
                self._pid_delta_days = config["tuning"]["pid_delta_days"]  # type: int
                self._sched_executors = config["tuning"]["sched_executors"]  # type: int
            else:
                # Provide default values
                self._max_list_length = 100  # type: int
                self._max_chunks = 10  # type: int
                self._max_retry = 5  # type: int
                self._max_requests = 0  # type: int
                self._retry_delay = 5  # type: int
                self._unavailable_delay = 600  # type: int
                self._lru_maxsize = 32  # type: int
                self._pid_kp = 0.0  # type: float
                self._pid_ki = 0.003  # type: float
                self._pid_kd = 0.0  # type: float
                self._pid_setpoint = 10000  # type: float
                self._pid_limit_min = 1  # type: float
                self._pid_limit_max = 2000  # type: float
                self._pid_delta_days = 15  # type: int
                self._sched_executors = 1  # type: int

        except Exception:  # pragma: no cover
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
    def taxo_exclude(self) -> List[str]:
        """Return list of taxo_groups excluded from download."""
        return self._taxo_exclude

    @property
    def territorial_unit_ids(self) -> List[str]:
        """Return list of territorial_unit_ids selected for download."""
        return self._territorial_unit_ids

    @property
    def json_format(self) -> str:
        """Return json format (short/long) for download."""
        return self._json_format

    @property
    def start_date(self) -> Union[datetime, None]:
        """Return earliest date for download."""
        return self._start_date

    @property
    def end_date(self) -> Union[datetime, None]:
        """Return latest date for download."""
        return self._end_date

    @property
    def type_date(self) -> Union[str, None]:
        """Return type of date ("sighting" or "entry") for download."""
        return self._type_date

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
    def db_enabled(self) -> bool:
        """Return flag to enable or not database storage
        on top of Postgresql storage."""
        return self._database_enabled

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
    def tuning_max_list_length(self) -> int:
        """Return tuning parameter."""
        return self._max_list_length

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
    def tuning_unavailable_delay(self) -> int:
        """Return tuning parameter."""
        return self._unavailable_delay

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
    def tuning_sched_executors(self) -> int:
        """Return tuning parameter."""
        return self._sched_executors


class EvnConf:
    """
    Read config file and expose list of sites configuration
    """

    def __init__(self, file: str) -> None:
        # Define configuration schema
        # Read configuration parameters
        p = Path.home() / file
        if not p.is_file():
            logger.critical(_("File %s does not exist"), str(p))
            raise MissingConfigurationFile

        yaml_text = p.read_text()
        try:
            logger.info(_("Loading YAML configuration %s"), file)
            self._config = load(yaml_text, _ConfSchema).data
        except YAMLValidationError:
            logger.critical(_("Incorrect content in YAML configuration %s"), file)
            logger.critical(_("%s"), sys.exc_info()[1])
            raise
        except YAMLError:  # pragma: no cover
            logger.critical(_("Error while reading YAML configuration %s"), file)
            raise

        self._ctrl_list = {}  # type: _ConfType
        for ctrl in self._config["controler"]:
            self._ctrl_list[ctrl] = cast(_ConfType, EvnCtrlConf(ctrl, self._config))

        self._site_list = {}  # type: _ConfType
        for site in self._config["site"]:
            self._site_list[site] = EvnSiteConf(site, self._config)

    @property
    def version(self) -> str:
        """Return version."""
        return __version__

    @property
    def ctrl_list(self) -> _ConfType:
        """Return list of controler configurations."""
        return self._ctrl_list

    @property
    def site_list(self) -> _ConfType:
        """Return list of site configurations."""
        return self._site_list
