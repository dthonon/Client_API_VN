"""Provide python interface to Biolovision API.

Thin Python binding to Biolovision API, returning dict instead of JSON.
Currently, only a subset of API controlers are implemented, and only a subset
of functions and parameters for implemented controlers. See details in each class.

Each API controler is mapped to a python class.
Class name is derived from controler name by removing '_' and using CamelCase.
Methods names are similar to the corresponding API call, prefixed by api_.
For example, method api_list in class LocalAdminUnits will call local_admin_units.

Most notable difference is that API chunks are grouped under 'data', i.e.
calling species_list('1') will return all birds in one array under 'data' key.
This means that requests returning lots of chunks (all bird sightings !) must be
avoided, as memory could be insufficient. max_chunks __init__ parameter controls
the maximum number of chunks allowed and raises

Classes
- BiolovisionAPI         - Top class, not for direct use
- LocalAdminUnitsAPI     - Controls local_admin_units
- ObservationsAPI        - Controls observations
- PlacesAPI              - Controls places
- SpeciesAPI             - Controls species
- TaxoGroupsAPI          - Controls taxo_groups
- TerritorialUnitsAPI    - Controls territorial_units

Methods, see each class

Properties
- transfer_errors            - Return number of HTTP errors

Exceptions
- BiolovisionApiException    - General exception
- HTTPError                  - HTTP protocol error
- MaxChunksError             - Too many chunks returned from API calls
- IncorrectParameter         - Incorrect or missing parameter
"""
import sys
import logging

import urllib
import requests
from requests_oauthlib import OAuth1

# version of the program:
__version__ = "0.1.1" #VERSION#

class BiolovisionApiException(Exception):
    """An exception occurred while handling your request."""

class HTTPError(BiolovisionApiException):
    """An HTTP error occurred."""

class MaxChunksError(BiolovisionApiException):
    """Too many chunks returned from API calls."""

class IncorrectParameter(BiolovisionApiException):
    """Incorrect or missing parameter."""

class BiolovisionAPI:
    """Provide python functions for Biolovision API functions."""

    def __init__(self, config,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        self._config = config
        self._limits = {
            'max_retry': max_retry,
            'max_requests': max_requests,
            'max_chunks': max_chunks
        }
        self._transfer_errors = 0

        # Using OAuth1 auth helper to get access
        self._api_url = config.base_url + 'api/'  # URL of API
        self._oauth = OAuth1(config.client_key,
                             client_secret=config.client_secret)

        # Caches for typical query parameters
        self.__taxo_groups_list = dict()
        self.__territorial_units_list = dict()

    @property
    def transfer_errors(self):
        """Return the number of HTTP errors during this session."""
        return self._transfer_errors

    # ----------------
    # Internal methods
    # ----------------
    def _url_get(self, params, scope):
        """Internal function used to GET from Biolovision API.

        Prepare the URL header, perform HTTP GET and return json content.
        Test HTTP status and returns None if error, else retrun decoded json content.
        Increments _transfer_errors in case of error.

        Parameters
        ----------
        params : dict of 'parameter name': 'parameter value'.
            params is used to build URL GET string.
        scope : str
            scope is the api to be queried, for example 'taxo_groups/'.

        Returns
        -------
        json : dict
            dict decoded from json if status OK, else None.

        Raises
        ------
        HTTPError
            HTTP protocol error, returned as argument.
        MaxChunksError
            Loop on chunks exceeded max_chunks limit.

        """
        # Loop on chunks
        nb_chunks = 0
        data_rec = dict()
        while nb_chunks < self._limits['max_chunks']:
            # GET from API
            payload = urllib.parse.urlencode(params,
                                             quote_via=urllib.parse.quote)
            logging.debug('Params: %s', payload)
            headers = {'Content-Type': 'application/json;charset=UTF-8'}
            protected_url = self._api_url + scope
            resp = requests.get(url=protected_url, auth=self._oauth,
                                params=payload, headers=headers)
            if nb_chunks == 0:
                # First chunk
                data_rec = resp.json()
            else:
                # Next chunks, appending
                data_rec['data'] += resp.json()['data']

            logging.debug(resp.headers)
            logging.debug('Status code from GET request: %s', resp.status_code)
            if resp.status_code != 200:
                logging.error('GET status code = %s, for URL %s',
                              resp.status_code, protected_url)
                self._transfer_errors += 1
                raise HTTPError(resp.status_code)

            # Is there more data to come?
            if (('transfer-encoding' in resp.headers) and
                (resp.headers['transfer-encoding'] == 'chunked') and
                ('pagination_key' in resp.headers)):
                logging.debug('Chunked transfer => requesting for more, with key: %s',
                              resp.headers['pagination_key'])
                # Update request parameters to get next chunk
                params['pagination_key'] = resp.headers['pagination_key']
                nb_chunks += 1
            else:
                logging.debug('Non-chunked transfer => finished requests')
                if 'pagination_key' in params:
                    del params['pagination_key']
                break

        logging.debug('Received %d chunks', nb_chunks)
        if nb_chunks < self._limits['max_chunks']:
            return data_rec
        else:
            raise MaxChunksError

    def _taxo_groups_list(self):
        """Return list of taxo groups, from cache or site."""
        if len(self.__taxo_groups_list) == 0:
            # No cache, get from site
            logging.debug('First call to taxo_groups_list, getting from site to cache')
            params = {'user_email': self._config.user_email,
                      'user_pw': self._config.user_pw}
            self.__taxo_groups_list = self._url_get(params, 'taxo_groups')
        return self.__taxo_groups_list

    def _territorial_units_list(self):
        """Return list of territorial units, from cache or site."""
        if len(self.__territorial_units_list) == 0:
            # No cache, get from site
            logging.debug('First call to territorial_units_list, getting from site to cache')
            params = {'user_email': self._config.user_email,
                      'user_pw': self._config.user_pw}
            self.__territorial_units_list = self._url_get(params, 'territorial_units')
        return self.__territorial_units_list

    # ---------------------------------
    #  Template methods for subclassing
    # ---------------------------------
    def api_get(self, ctrl, id):
        """Query for a single entity of the given controler.

        Calls  /ctrl/id API.

        Parameters
        ----------
        ctrl : str
            controler to query.
        id : str
            entity to retrieve.

        Returns
        -------
        json : dict or None
            dict decoded from json if status OK, else None
        """
        # Mandatory parameters.
        params = {'user_email': self._config.user_email,
                  'user_pw': self._config.user_pw}
        # GET from API
        return self._url_get(params, ctrl + '/' + str(id))

    def api_list(self, ctrl, opt_params=dict()):
        """Query for a list of entities of the given controler.

        Calls /ctrl API.

        Parameters
        ----------
        ctrl : str
            controler to query.
        opt_params : dict
            optional URL parameters, empty by default. See Biolovision API documentation.

        Returns
        -------
        json : dict or None
            dict decoded from json if status OK, else None
        """
        # Mandatory parameters.
        params = {'user_email': self._config.user_email,
                  'user_pw': self._config.user_pw}
        params.update(opt_params)
        # GET from API
        logging.debug('List from %s, with option %s',
                      ctrl, opt_params)
        entities = self._url_get(params, ctrl)['data']
        logging.debug('Number of entities = %i',
                      len(entities))
        return {'data': entities}

    # -------------------------
    # Exception testing methods
    # -------------------------
    def wrong_api(self):
        """Query for a wrong api.

        Calls /error API to raise an exception.

        """
        # Mandatory parameters.
        params = {'user_email': self._config.user_email, 'user_pw': self._config.user_pw}
        # GET from API
        return self._url_get(params, 'error/')

class LocalAdminUnitsAPI(BiolovisionAPI):
    """ Implement api calls to local_admin_units controler.

    Methods
    - api_get                - Return a single entity from the controler
    - api_list               - Return a single entity from the controler

    """

    def __init__(self, config,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        super().__init__(config, max_retry, max_requests, max_chunks)
        self.__ctrl = 'local_admin_units'

    def api_get(self, id):
        """Query for a single entity from local_admin_units controler.

        Calls  /local_admin_units/id API.

        Parameters
        ----------
        id : str
            entity to retrieve.

        Returns
        -------
        json : dict or None
            dict decoded from json if status OK, else None
        """
        return super().api_get(self.__ctrl, id)

    def api_list(self, opt_params=dict()):
        """Query for a list of entities from local_admin_units controler.

        Calls  /local_admin_units API.

        Parameters
        ----------
        opt_params : dict
            optional URL parameters, empty by default. See Biolovision API documentation.

        Returns
        -------
        json : dict or None
            dict decoded from json if status OK, else None
        """
        return super().api_list(self.__ctrl, opt_params)

class ObservationsAPI(BiolovisionAPI):
    """ Implement api calls to observations controler.

    Methods
    - api_get                - Return a single observations from the controler
    - api_list               - Return all observations from the controler
    - api_diff               - Return all changes in observations since a given date
    """


    def __init__(self, config,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        super().__init__(config, max_retry, max_requests, max_chunks)
        self.__ctrl = 'observations'

    def api_get(self, id):
        """Query for a single observations from the controler.

        Calls  /observations/id API.

        Parameters
        ----------
        id : str
            entity to retrieve.

        Returns
        -------
        json : dict or None
            dict decoded from json if status OK, else None
        """
        return super().api_get(self.__ctrl, id)

    def api_list(self, opt_params=dict()):
        """Query for a list of observations from the controler.

        Calls  /observations API.

        Parameters
        ----------
        opt_params : dict
            optional URL parameters, empty by default. See Biolovision API documentation.

        Returns
        -------
        json : dict or None
            dict decoded from json if status OK, else None
        """
        return super().api_list(self.__ctrl, 'id_taxo_group', opt_params)

    def api_diff(self, id_taxo_group, delta_time, modification_type='all'):
        """Query for a list of updates or deletions since a given date.

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
        params = {'user_email': self._config.user_email,
                  'user_pw': self._config.user_pw}
        # Specific parameters.
        params['id_taxo_group'] = str(id_taxo_group)
        params['modification_type'] = modification_type
        params['date'] = delta_time
        # GET from API
        return super()._url_get(params, 'observations/diff/')

class PlacesAPI(BiolovisionAPI):
    """ Implement api calls to places controler.

    Methods
    - api_get                - Return a single place from the controler
    - api_list               - Return all places from the controler

    """

    def __init__(self, config,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        super().__init__(config, max_retry, max_requests, max_chunks)
        self.__ctrl = 'places'

    def api_get(self, id):
        """Query for a single place from the controler.

        Calls  /places/id API.

        Parameters
        ----------
        id : str
            entity to retrieve.

        Returns
        -------
        json : dict or None
            dict decoded from json if status OK, else None
        """
        return super().api_get(self.__ctrl, id)

    def api_list(self, opt_params=dict()):
        """Query for a list of places from the controler.

        Calls  /places API.

        Parameters
        ----------
        opt_params : dict
            optional URL parameters, empty by default. See Biolovision API documentation.

        Returns
        -------
        json : dict or None
            dict decoded from json if status OK, else None
        """
        return super().api_list(self.__ctrl, opt_params)

class SpeciesAPI(BiolovisionAPI):
    """ Implement api calls to species controler.

    Methods
    - api_get                - Return a single specie from the controler
    - api_list               - Return all species from the controler

    """

    def __init__(self, config,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        super().__init__(config, max_retry, max_requests, max_chunks)
        self.__ctrl = 'species'

    def api_get(self, id):
        """Query for a single specie from the controler.

        Calls  /species/id API.

        Parameters
        ----------
        id : str
            entity to retrieve.

        Returns
        -------
        json : dict or None
            dict decoded from json if status OK, else None
        """
        return super().api_get(self.__ctrl, id)

    def api_list(self, opt_params=dict()):
        """Query for a list of species from the controler.

        Calls  /species API.

        Parameters
        ----------
        opt_params : dict
            optional URL parameters, empty by default. See Biolovision API documentation.

        Returns
        -------
        json : dict or None
            dict decoded from json if status OK, else None
        """
        return super().api_list(self.__ctrl, opt_params)

class TaxoGroupsAPI(BiolovisionAPI):
    """ Implement api calls to taxo_groups controler.

    Methods
    - api_get                - Return a single taxo group from the controler
    - api_list               - Return all taxo groups from the controler

    """

    def __init__(self, config,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        super().__init__(config, max_retry, max_requests, max_chunks)
        self.__ctrl = 'taxo_groups'

    def api_get(self, id):
        """Query for a single taxo group from the controler.

        Calls  /taxo_groups/id API.

        Parameters
        ----------
        id : str
            entity to retrieve.

        Returns
        -------
        json : dict or None
            dict decoded from json if status OK, else None
        """
        return super().api_get(self.__ctrl, id)

    def api_list(self, opt_params=dict()):
        """Query for a list of taxo groups from the controler.

        Calls  /taxo_groups API.

        Parameters
        ----------
        opt_params : dict
            optional URL parameters, empty by default. See Biolovision API documentation.

        Returns
        -------
        json : dict or None
            dict decoded from json if status OK, else None
        """
        return super().api_list(self.__ctrl, opt_params)

class TerritorialUnitsAPI(BiolovisionAPI):
    """ Implement api calls to territorial_units controler.

    Methods
    - api_get                - Return a single territorial unit from the controler
    - api_list               - Return all territorial units from the controler

    """

    def __init__(self, config,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        super().__init__(config, max_retry, max_requests, max_chunks)
        self.__ctrl = 'territorial_units'

    def api_get(self, id):
        """Query for a single territorial unit from the controler.

        Calls  /territorial_units/id API.

        Parameters
        ----------
        id : str
            entity to retrieve.

        Returns
        -------
        json : dict or None
            dict decoded from json if status OK, else None
        """
        return super().api_get(self.__ctrl, id)

    def api_list(self, opt_params=dict()):
        """Query for a list of territorial units from the controler.

        Calls  /territorial_units API.

        Parameters
        ----------
        opt_params : dict
            optional URL parameters, empty by default. See Biolovision API documentation.

        Returns
        -------
        json : dict or None
            dict decoded from json if status OK, else None
        """
        return super().api_list(self.__ctrl, opt_params)
