#!/usr/bin/env python3
"""
evnconf: expose local configuration parameters as properties of class EvnConf

"""
import configparser
from pathlib import Path

# version of the program:
__version__ = "1.0.0" #VERSION#

class EvnConf:
    """
    Read config file and expose parameters
    """
    def __init__(self, site):
        self._site = site

        # Read configuration parameters
        self._config = configparser.ConfigParser()
        self._config.read(str(Path.home()) + '/.evn_' + site + '.ini')

        # Import parameters in properties
        self._client_key = self._config['site']['evn_client_key']
        self._client_secret = self._config['site']['evn_client_secret']
        self._user_email = self._config['site']['evn_user_email']
        self._user_pw = self._config['site']['evn_user_pw']
        self._base_url = self._config['site']['evn_site']
        self._file_store = self._config['site']['evn_file_store'] + '/' + site + '/'
        self._db_host = self._config['database']['evn_db_host']
        self._db_port = self._config['database']['evn_db_port']
        self._db_name = self._config['database']['evn_db_name']
        self._db_schema = self._config['database']['evn_db_schema']
        self._db_group = self._config['database']['evn_db_group']
        self._db_user = self._config['database']['evn_db_user']
        self._db_pw = self._config['database']['evn_db_pw']
        self._sql_scripts = self._config['database']['evn_sql_scripts']
        self._external1_name = self._config[site]['evn_external1_name']
        self._external1_pw = self._config[site]['evn_external1_pw']

    @property
    def site(self):
        """Return site name, used to identify configuration file."""
        return self._site

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
    def db_schema(self):
        """Return database schema where data is stored."""
        return self._db_schema

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
