# pylint: disable=too-many-instance-attributes
"""Expose local configuration parameters as properties.

Parameters are defined in a YAML file located in $HOME directory.
This file is created using --init option, and then customized by the user.
Each time the application is run, this parameter file is read and the
parameters are then available as properties of EvnCtrlConf and EvnSiteConf classes.

"""
import logging
from pathlib import Path

from typing import Any

from strictyaml import (Bool, Email, Float, Int, Map, MapPattern,
                        Optional, Seq, Str, Url, YAMLError,
                        YAMLValidationError, load)

from . import __version__

logger = logging.getLogger('transfer_vn.evn_conf')


class EvnConfException(Exception):
    """An exception occurred while loading parameters."""


class IncorrectParameter(EvnConfException):
    """Incorrect or missing parameter."""


ConfType = Any

class Conf:
    """Define YAML and typed schemas.
    """

    def __init__(self):
        # Define Python type
        self._ConfType = Any

        # Define strictyaml schema
        self._schema = Map({
            'main':
            Map({'admin_mail': Email()}),
            'controler':
            Map({
                'entities':
                Map({'enabled': Bool()}),
                'local_admin_units':
                Map({'enabled': Bool()}),
                'observations':
                Map({
                    'enabled': Bool(),
                    'taxo_exclude': Seq(Str())
                }),
                'observers':
                Map({'enabled': Bool()}),
                'places':
                Map({'enabled': Bool()}),
                'species':
                Map({'enabled': Bool()}),
                'taxo_group':
                Map({'enabled': Bool()}),
                'territorial_unit':
                Map({'enabled': Bool()})
            }),
            'site':
            MapPattern(
                Str(),
                Map({
                    'enabled': Bool(),
                    'site': Url(),
                    'user_email': Email(),
                    'user_pw': Str(),
                    'client_key': Str(),
                    'client_secret': Str()
                })),
            'file':
            Map({
                'enabled': Bool(),
                'file_store': Str()
            }),
            'database':
            Map({
                Optional('db_host', default='localhost'): Str(),
                Optional('db_port', default=5432): Int(),
                'db_name': Str(),
                'db_schema_import': Str(),
                'db_schema_vn': Str(),
                'db_group': Str(),
                'db_user': Str(),
                'db_pw': Str(),
                Optional('db_out_proj', default='2154'): Str()
            }),
            Optional('tuning'):
            Map({
                'max_chunks': Int(),
                'max_retry': Int(),
                'max_requests': Int(),
                'lru_maxsize': Int(),
                'min_year': Int(),
                'pid_kp': Float(),
                'pid_ki': Float(),
                'pid_kd': Float(),
                'pid_setpoint': Float(),
                'pid_limit_min': Float(),
                'pid_limit_max': Float(),
                'pid_delta_days': Float()
            })
        })

    @property
    def schema(self) -> Any:
        """Return strictYAML schema."""
        return self._schema

    @property
    def type(self) -> ConfType:
        """Return strictYAML schema."""
        return self._conf_type


class EvnCtrlConf:
    """Expose controler configuration as properties.
    """

    def __init__(self, ctrl, config):
        self._ctrl = ctrl

        # Import parameters in properties
        self._enabled = True
        if 'enabled' in config['controler'][ctrl]:
            self._enabled = config['controler'][ctrl]['enabled']
        self._taxo_exclude = []
        if 'taxo_exclude' in config['controler'][ctrl]:
            self._taxo_exclude = config['controler'][ctrl]['taxo_exclude']

    @property
    def enabled(self) -> Bool:
        """Return enabled flag, defining if controler should be used."""
        return self._enabled

    @property
    def taxo_exclude(self):
        """Return list of taxo_groups excluded from download."""
        return self._taxo_exclude


class EvnSiteConf:
    """Expose site configuration as properties.
    """

    def __init__(self, site, config):
        self._site = site
        # Import parameters in properties
        try:
            self._enabled = True
            if 'enabled' in config['site'][site]:
                self._enabled = config['site'][site]['enabled']
            self._client_key = config['site'][site]['client_key']
            self._client_secret = config['site'][site]['client_secret']
            self._user_email = config['site'][site]['user_email']
            self._user_pw = config['site'][site]['user_pw']
            self._base_url = config['site'][site]['site']

            self._file_enabled = False
            if 'enabled' in config['file']:
                self._file_enabled = config['file']['enabled']
            self._file_store = None
            if 'file_store' in config['file']:
                self._file_store = config['file'][
                    'file_store'] + '/' + site + '/'
            else:
                if self._file_enabled:
                    logger.error(_('file:file_store must be defined'))
                    raise IncorrectParameter

            self._db_host = config['database']['db_host']
            self._db_port = str(config['database']['db_port'])
            self._db_name = config['database']['db_name']
            self._db_schema_import = config['database']['db_schema_import']
            self._db_schema_vn = config['database']['db_schema_vn']
            self._db_group = config['database']['db_group']
            self._db_user = config['database']['db_user']
            self._db_pw = config['database']['db_pw']

            if 'tuning' in config:
                self._max_chunks = config['tuning']['max_chunks']
                self._max_retry = config['tuning']['max_retry']
                self._max_requests = config['tuning']['max_requests']
                self._lru_maxsize = config['tuning']['lru_maxsize']
                self._min_year = config['tuning']['min_year']
                self._pid_kp = config['tuning']['pid_kp']
                self._pid_ki = config['tuning']['pid_ki']
                self._pid_kd = config['tuning']['pid_kd']
                self._pid_setpoint = config['tuning']['pid_setpoint']
                self._pid_limit_min = config['tuning']['pid_limit_min']
                self._pid_limit_max = config['tuning']['pid_limit_max']
                self._pid_delta_days = config['tuning']['pid_delta_days']

        except Exception as e:
            logger.error(e, exc_info=True)
            raise
        return None

    @property
    def site(self):
        """Return site name, used to identify configuration file."""
        return self._site

    @property
    def enabled(self):
        """Return enabled flag, defining is site is to be downloaded."""
        return self._enabled

    @property
    def client_key(self):
        """Return oauth1 client_key, used to connect to VisioNature site."""
        return self._client_key

    @property
    def client_secret(self):
        """Return oauth1 client_secret, used to connect to VisioNature site."""
        return self._client_secret

    @property
    def user_email(self):
        """Return user email, used to connect to VisioNature site."""
        return self._user_email

    @property
    def user_pw(self):
        """Return user password, used to connect to VisioNature site."""
        return self._user_pw

    @property
    def base_url(self):
        """Return base URL of VisioNature site,
        used as prefix for API calls."""
        return self._base_url

    @property
    def file_enabled(self):
        """Return flag to enable or not file storage
        on top of Postgresql storage."""
        return self._file_enabled

    @property
    def file_store(self):
        """Return directory, under $HOME, where downloaded files are stored."""
        return self._file_store

    @property
    def db_host(self):
        """Return hostname of Postgresql server."""
        return self._db_host

    @property
    def db_port(self):
        """Return IP port of Postgresql server."""
        return self._db_port

    @property
    def db_name(self):
        """Return database name."""
        return self._db_name

    @property
    def db_schema_import(self):
        """Return database schema where imported JSON data is stored."""
        return self._db_schema_import

    @property
    def db_schema_vn(self):
        """Return database schema where column data is stored."""
        return self._db_schema_vn

    @property
    def db_group(self):
        """Return group ROLE that gets access to tables."""
        return self._db_group

    @property
    def db_user(self):
        """Return user ROLE that owns the tables."""
        return self._db_user

    @property
    def db_pw(self):
        """Return db_user PASSWORD."""
        return self._db_pw

    @property
    def tuning_max_chunks(self):
        """Return tuning parameter."""
        return self._max_chunks

    @property
    def tuning_max_retry(self):
        """Return tuning parameter."""
        return self._max_retry

    @property
    def tuning_max_requests(self):
        """Return tuning parameter."""
        return self._max_requests

    @property
    def tuning_lru_maxsize(self):
        """Return tuning parameter."""
        return self._lru_maxsize

    @property
    def tuning_min_year(self):
        """Return tuning parameter."""
        return self._min_year

    @property
    def tuning_pid_kp(self):
        """Return tuning parameter."""
        return self._pid_kp

    @property
    def tuning_pid_ki(self):
        """Return tuning parameter."""
        return self._pid_ki

    @property
    def tuning_pid_kd(self):
        """Return tuning parameter."""
        return self._pid_kd

    @property
    def tuning_pid_setpoint(self):
        """Return tuning parameter."""
        return self._pid_setpoint

    @property
    def tuning_pid_limit_min(self):
        """Return tuning parameter."""
        return self._pid_limit_min

    @property
    def tuning_pid_limit_max(self):
        """Return tuning parameter."""
        return self._pid_limit_max

    @property
    def tuning_pid_delta_days(self):
        """Return tuning parameter."""
        return self._pid_delta_days


class EvnConf:
    """
    Read config file and expose list of sites configuration
    """

    def __init__(self, file):
        # Define configuration schema
        # Read configuration parameters
        p = Path.home() / file
        yaml_text = p.read_text()
        try:
            logger.info(_('Loading YAML configuration %s'), file)
            self._config = load(yaml_text, Conf().schema).data
        except YAMLValidationError as error:
            logger.exception(_('Incorrect content in YAML configuration %s'),
                             file)
        except YAMLError as error:
            logger.exception(_('Error while reading YAML configuration %s'),
                             file)

        self._ctrl_list = {}
        for ctrl in self._config['controler']:
            self._ctrl_list[ctrl] = EvnCtrlConf(ctrl, self._config)

        self._site_list = {}
        for site in self._config['site']:
            self._site_list[site] = EvnSiteConf(site, self._config)

    @property
    def version(self):
        """Return version."""
        return __version__

    @property
    def ctrl_list(self):
        """Return list of controler configurations."""
        return self._ctrl_list

    @property
    def site_list(self):
        """Return list of site configurations."""
        return self._site_list
