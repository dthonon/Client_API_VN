#!/usr/bin/env python3
"""
evnconf: expose local configuration parameters as properties of class EvnConf

Copyright (C) 2018, Daniel Thonon

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import sys
from optparse import OptionParser
import configparser
from pathlib import Path

# version of the program:
__version__= "1.0.0" #VERSION#

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

    @property
    def site(self):
        return self._site

    @property
    def client_key(self):
        return self._client_key

    @property
    def client_secret(self):
        return self._client_secret

    @property
    def user_email(self):
        return self._user_email

    @property
    def user_pw(self):
        return self._user_pw

    @property
    def base_url(self):
        return self._base_url

    @property
    def file_store(self):
        return self._file_store

    @property
    def db_host(self):
        return self._db_host

    @property
    def db_port(self):
        return self._db_port

    @property
    def db_name(self):
        return self._db_name

    @property
    def db_schema(self):
        return self._db_schema

    @property
    def db_group(self):
        return self._db_group

    @property
    def db_user(self):
        return self._db_user

    @property
    def db_pw(self):
        return self._db_pw
