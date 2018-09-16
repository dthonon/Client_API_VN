#!/usr/bin/env python3
"""
Provide python interface to Biolovision API

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
import logging

import requests
import urllib
from requests_oauthlib import OAuth1
import json

from evnconf import EvnConf

# version of the program:
__version__= "0.1.1" #VERSION#

class BiolovisionAPI:
    """
    Provide python iterators over Biolovision API functions.
    """

    def __init__(self, config, max_retry=5, max_requests=sys.maxsize):
        self._config = config
        self._max_retry = max_retry
        self._max_requests = max_requests
        self._transfer_errors = 0

        # Using OAuth1 auth helper to get access
        self._api_url = config.base_url + 'api/'  # URL of API
        self._oauth = OAuth1(config.client_key, client_secret=config.client_secret)

    @property
    def transfer_errors(self):
        return self._transfer_errors

    def _url_get(self, params, scope):
        # GET from API
        payload = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        logging.debug('Params: {}'.format(payload))
        headers = {'Content-Type': 'application/json;charset=UTF-8'}
        protected_url = self._api_url + scope
        resp = requests.get(url=protected_url, auth=self._oauth, params=payload, headers=headers)
        logging.debug(resp.headers)
        logging.debug('Status code from GET request: {}'.format(resp.status_code))
        if resp.status_code != 200:
            logging.error('GET status code = {}, for URL {}'.format(resp.status_code, protected_url))
            self._transfer_errors += 1
            return None
        else:
            return resp.json()

    def observations_diff(self, taxo_group, delta_time):
        # Mandatory parameters.
        params = {'user_email': self._config.user_email, 'user_pw': self._config.user_pw}
        # Specific parameters.
        params['id_taxo_group'] = str(taxo_group)
        params['modification_type'] = 'all'
        params['date'] = delta_time
        # GET from API
        return self._url_get(params, 'observations/diff/')

    def taxo_groups_list(self):
        # Mandatory parameters.
        params = {'user_email': self._config.user_email, 'user_pw': self._config.user_pw}
        # GET from API
        return self._url_get(params, 'taxo_groups/')
