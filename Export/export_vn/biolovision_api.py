"""Provide python interface to Biolovision APIself.

Methods

-   observations_diff          - Return list of updates or deletions since a given date
-   taxo_groups_list           - Return list of taxo groups

Properties

-   transfer_errors            - Return number of HTTP errors

"""
import sys
import logging

import urllib
import requests
from requests_oauthlib import OAuth1

# version of the program:
__version__ = "0.1.1" #VERSION#

class BiolovisionAPI:
    """Provide python functions for Biolovision API functions.
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
        """Return the number of HTTP errors during this session."""
        return self._transfer_errors

    def _url_get(self, params, scope):
        """Internal function used to GET from Biolovision API.

        Prepare the URL header, perform HTTP GET and return json content.
        Test HTTP status and returns None if error, else retrun decoded json content.
        Increments _transfer_errors in case of error.

        Parameters
        ----------
        params : dict of 'parameter name': 'parameter value'
            params is used to build URL GET string.
        scope : str
            scope is the api to be queried, for example 'taxo_groups/'.

        Returns
        -------
        json : dict or None
            dict decoded from json if status OK, else None

        """
        # GET from API
        payload = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        logging.debug('Params: %s', payload)
        headers = {'Content-Type': 'application/json;charset=UTF-8'}
        protected_url = self._api_url + scope
        resp = requests.get(url=protected_url, auth=self._oauth, params=payload, headers=headers)
        logging.debug(resp.headers)
        logging.debug('Status code from GET request: %s', resp.status_code)
        if resp.status_code != 200:
            logging.error('GET status code = %s, for URL %s', resp.status_code, protected_url)
            self._transfer_errors += 1
            return None
        else:
            return resp.json()

    def observations_diff(self, id_taxo_group, delta_time, modification_type='all'):
        """Return list of updates or deletions since a given date.

        Calls /observations/diff to get list of created/updated or deleted observations
        since a given date (max 10 weeks backward).

        Parameters
        ----------
        id_taxo_group : str
            taxo group from which to query diff.
        delta_time : str
            Start of time interval to query.
        modification_type : str
            Type of diff queried : can be only_modified, only_deleted or all (default).

        Returns
        -------
        json : dict or None
            dict decoded from json if status OK, else None

        """
        # Mandatory parameters.
        params = {'user_email': self._config.user_email, 'user_pw': self._config.user_pw}
        # Specific parameters.
        params['id_taxo_group'] = str(id_taxo_group)
        params['modification_type'] = modification_type
        params['date'] = delta_time
        # GET from API
        return self._url_get(params, 'observations/diff/')

    def taxo_groups_list(self):
        """Return list of taxo groups.

        Calls /taxo_groups API to get the list of all taxo groups.

        Returns
        -------
        json : dict or None
            dict decoded from json if status OK, else None
        """
        # Mandatory parameters.
        params = {'user_email': self._config.user_email, 'user_pw': self._config.user_pw}
        # GET from API
        return self._url_get(params, 'taxo_groups/')

    def taxo_groups_get(self, id_taxo_group):
        """Return list of taxo groups.

        Calls /taxo_groups/%id% API to get a taxo group.

        Parameters
        ----------
        id_taxo_group : str
            taxo group from which to query diff.

        Returns
        -------
        json : dict or None
            dict decoded from json if status OK, else None
        """
        # Mandatory parameters.
        params = {'user_email': self._config.user_email, 'user_pw': self._config.user_pw}
        # GET from API
        return self._url_get(params, 'taxo_groups/' + str(id_taxo_group))
