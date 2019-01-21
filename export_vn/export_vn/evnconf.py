#!/usr/bin/env python3
# pylint: disable=too-many-instance-attributes
"""
evnconf: expose local configuration parameters as properties of class EvnConf

"""
import yaml
from pathlib import Path

# version of the program:
from setuptools_scm import get_version
__version__ = get_version(root='../..', relative_to=__file__)

class EvnSiteConf:
    """Expose site configuration as properties
    """
    def __init__(self, site, config):
        self._site = site

        # Import parameters in properties
        self._enabled          = config['site'][site]['enabled']
        self._client_key       = config['site'][site]['evn_client_key']
        self._client_secret    = config['site'][site]['evn_client_secret']
        self._user_email       = config['site'][site]['evn_user_email']
        self._user_pw          = config['site'][site]['evn_user_pw']
        self._base_url         = config['site'][site]['evn_site']
        self._file_store       = config['site'][site]['evn_file_store'] + '/' + site + '/'
        self._db_host          = config['database']['evn_db_host']
        self._db_port          = str(config['database']['evn_db_port'])
        self._db_name          = config['database']['evn_db_name']
        self._db_schema_import = config['database']['evn_db_schema_import']
        self._db_schema_vn     = config['database']['evn_db_schema_vn']
        self._db_group         = config['database']['evn_db_group']
        self._db_user          = config['database']['evn_db_user']
        self._db_pw            = config['database']['evn_db_pw']
        self._sql_scripts      = config['database']['evn_sql_scripts']
        if site in config['local']:
            self._external1_name = config['local'][site]['evn_external1_name']
            self._external1_pw   = config['local'][site]['evn_external1_pw']

    @property
    def version(self):
        """Return version."""
        return __version__

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
        """Return base URL of VisioNature site, used as prefix for API calls."""
        return self._base_url

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
    def sql_scripts(self):
        """Return directory, under $HOME, where SQL scipts are stored."""
        return self._sql_scripts

    @property
    def external1_name(self):
        """Return user 1 for external access to database. Site specific."""
        return self._external1_name

    @property
    def external1_pw(self):
        """Return user 1 password."""
        return self._external1_pw

class EvnConf:
    """
    Read config file and expose list of sites configuration
    """
    def __init__(self, file):
        # Read configuration parameters
        with open(str(Path.home()) + '/' + file, 'r') as stream:
            try:
                self._config = yaml.load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        self._site_list = {}
        for site in self._config['site']:
            self._site_list[site] = EvnSiteConf(site, self._config)

    @property
    def site_list(self):
        """Return list of site configurations."""
        return self._site_list
