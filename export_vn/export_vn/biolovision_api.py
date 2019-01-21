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
import json
from requests_oauthlib import OAuth1
from functools import lru_cache

# version of the program:
from setuptools_scm import get_version
__version__ = get_version(root='../..', relative_to=__file__)

class HashableDict(dict):
    """Provide hashable dict type, to enable @lru_cache."""
    def __hash__(self):
        return hash(frozenset(self))

class BiolovisionApiException(Exception):
    """An exception occurred while handling your request."""

class HTTPError(BiolovisionApiException):
    """An HTTP error occurred."""

class MaxChunksError(BiolovisionApiException):
    """Too many chunks returned from API calls."""

class NotImplemented(BiolovisionApiException):
    """Feature not implemented."""

class IncorrectParameter(BiolovisionApiException):
    """Incorrect or missing parameter."""

class BiolovisionAPI:
    """Top class, not for direct use. Provides internal and template methods."""

    def __init__(self, config, controler,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        self._config = config
        self._limits = {
            'max_retry': max_retry,
            'max_requests': max_requests,
            'max_chunks': max_chunks
        }
        self._transfer_errors = 0
        self._ctrl = controler

        # Using OAuth1 auth helper to get access
        self._api_url = config.base_url + 'api/'  # URL of API
        self._oauth = OAuth1(config.client_key,
                             client_secret=config.client_secret)

    @property
    def version(self):
        """Return version."""
        return __version__

    @property
    def transfer_errors(self):
        """Return the number of HTTP errors during this session."""
        return self._transfer_errors

    @property
    def controler(self):
        """Return the number of HTTP errors during this session."""
        return self._ctrl

    # ----------------
    # Internal methods
    # ----------------
    def _url_get(self, params, scope, method='GET', body=None):
        """Internal function used to request from Biolovision API.

        Prepare the URL header, perform HTTP request and get json content.
        Test HTTP status and returns None if error, else return decoded json content.
        Increments _transfer_errors in case of error.

        Parameters
        ----------
        params : dict of 'parameter name': 'parameter value'.
            params is used to build URL GET string.
        scope : str
            scope is the api to be queried, for example 'taxo_groups/'.
        method : str
            HTTP method to use: GET/POST/DELETE/PUT. Default to GET
        body : str
            Optional body for POST or PUT

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
        while nb_chunks < self._limits['max_chunks']:
            # GET from API
            payload = urllib.parse.urlencode(params,
                                             quote_via=urllib.parse.quote)
            logging.debug('Params: %s', payload)
            headers = {'Content-Type': 'application/json;charset=UTF-8'}
            protected_url = self._api_url + scope
            if method == 'GET':
                resp = requests.get(url=protected_url, auth=self._oauth,
                                    params=payload, headers=headers)
            elif method == 'POST':
                resp = requests.post(url=protected_url, auth=self._oauth,
                                    params=payload, headers=headers, data=body)
            else:
                raise NotImplemented

            logging.debug(resp.headers)
            logging.debug('Status code from %s request: %s', method, resp.status_code)
            if resp.status_code != 200:
                logging.error('%s status code = %s, for URL %s',
                              method, resp.status_code, protected_url)
                self._transfer_errors += 1
                raise HTTPError(resp.status_code)

            resp_chunk = resp.json()
            # Initialize or append to response dict, depending on content
            if 'data' in resp_chunk:
                if 'sightings' in resp_chunk['data']:
                    logging.debug('Received %d sightings in chunk %d',
                                 len(resp_chunk['data']['sightings']), nb_chunks)
                    if nb_chunks == 0:
                        data_rec = resp_chunk
                    else:
                        data_rec['data']['sightings'] += resp_chunk['data']['sightings']
                elif 'forms'  in resp_chunk['data']:
                    logging.debug('Received %d forms in chunk %d',
                                 len(resp_chunk['data']['forms']), nb_chunks)
                    if nb_chunks == 0:
                        data_rec = resp_chunk
                    else:
                        data_rec['data']['forms'] += resp_chunk['data']['forms']
                else:
                    logging.debug('Received %d data items in chunk %d',
                                 len(resp_chunk), nb_chunks)
                    if nb_chunks == 0:
                        data_rec = resp_chunk
                    else:
                        data_rec['data'] += resp_chunk['data']
            else:
                logging.debug('Received %d items without data in chunk %d',
                             len(resp_chunk), nb_chunks)
                if nb_chunks == 0:
                    data_rec = resp_chunk
                else:
                    data_rec += resp_chunk

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


    def _api_list(self, opt_params=None):
        """Query for a list of entities of the given controler.

        Calls /ctrl API.

        Parameters
        ----------
        opt_params : HashableDict (to enable lru_cache)
            optional URL parameters, empty by default. See Biolovision API documentation.

        Returns
        -------
        json : dict or None
            dict decoded from json if status OK, else None
        """
        # Mandatory parameters.
        params = {'user_email': self._config.user_email,
                  'user_pw': self._config.user_pw}
        if opt_params is not None:
            params.update(opt_params)
        logging.debug('List from %s, with option %s',
                      self._ctrl, params)
        # GET from API
        entities = self._url_get(params, self._ctrl)['data']
        logging.debug('Number of entities = %i',
                      len(entities))
        return {'data': entities}


    # -----------------------------------------
    #  Generic methods, used by most subclasses
    # -----------------------------------------
    def api_get(self, id):
        """Query for a single entity of the given controler.

        Calls  /ctrl/id API.

        Parameters
        ----------
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
        return self._url_get(params, self._ctrl + '/' + str(id))

    def api_list(self, opt_params=None):
        """Query for a list of entities of the given controler.

        Calls /ctrl API.

        Parameters
        ----------
        opt_params : dict
            optional URL parameters, empty by default. See Biolovision API documentation.

        Returns
        -------
        json : dict or None
            dict decoded from json if status OK, else None
        """
        if opt_params == None:
            return self._api_list()
        else:
            return self._api_list(HashableDict(opt_params))

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


class EntitiesAPI(BiolovisionAPI):
    """ Implement api calls to entities controler.

    Methods
    - api_get                - Return a single entity from the controler
    - api_list               - Return a list of entity from the controler

    """

    def __init__(self, config,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        super().__init__(config, 'entities',
                         max_retry, max_requests, max_chunks)


class LocalAdminUnitsAPI(BiolovisionAPI):
    """ Implement api calls to local_admin_units controler.

    Methods
    - api_get                - Return a single entity from the controler
    - api_list               - Return a list of entity from the controler

    """

    def __init__(self, config,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        super().__init__(config, 'local_admin_units',
                         max_retry, max_requests, max_chunks)


class ObservationsAPI(BiolovisionAPI):
    """ Implement api calls to observations controler.

    Methods
    - api_get                - Return a single observations from the controler
    - api_list               - Return a list of observations from the controler
    - api_diff               - Return all changes in observations since a given date
    - api_search             - Search for observations based on parameter value
    """


    def __init__(self, config,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        super().__init__(config, 'observations',
                         max_retry, max_requests, max_chunks)

    def api_list(self, id_taxo_group, id_species=None, opt_params=dict()):
        """Query for list of observations by taxo_group from the controler.

        Calls  /observations API.

        Parameters
        ----------
        id_taxo_group : integer
            taxo_group to query for observations
        id_species : integer
            optional specie to query for observations
        opt_params : dict
            optional URL parameters, empty by default. See Biolovision API documentation.

        Returns
        -------
        json : dict or None
            dict decoded from json if status OK, else None
        """
        opt_params['id_taxo_group'] = str(id_taxo_group)
        if id_species != None:
            opt_params['id_species'] = str(id_species)
        return super().api_list(HashableDict(opt_params))

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

    def api_search(self, q_params):
        """Search for observations, based on parameter conditions.

        Calls /observations/search to get observations
        same parameters than in online version can be used

        Parameters
        ----------
        q_params : dict
            Query parameters,same than in online version.

        Returns
        -------
        json : dict or None
            dict decoded from json if status OK, else None

        """
        # Mandatory parameters.
        params = {'user_email': self._config.user_email,
                  'user_pw': self._config.user_pw}
        # Specific parameters.
        if q_params is not None:
            body = json.dumps(q_params)
        else:
            raise IncorrectParameter
        logging.debug('Search from %s, with option %s and body %s',
                      self._ctrl, params, body)
        # GET from API
        return super()._url_get(params, 'observations/search/', 'POST', body)

class PlacesAPI(BiolovisionAPI):
    """ Implement api calls to places controler.

    Methods
    - api_get                - Return a single place from the controler
    - api_list               - Return a list of places from the controler

    """

    def __init__(self, config,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        super().__init__(config, 'places',
                         max_retry, max_requests, max_chunks)


class SpeciesAPI(BiolovisionAPI):
    """ Implement api calls to species controler.

    Methods
    - api_get                - Return a single specie from the controler
    - api_list               - Return a list of species from the controler

    """

    def __init__(self, config,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        super().__init__(config, 'species',
                         max_retry, max_requests, max_chunks)


class TaxoGroupsAPI(BiolovisionAPI):
    """ Implement api calls to taxo_groups controler.

    Methods
    - api_get                - Return a single taxo group from the controler
    - api_list               - Return a list of taxo groups from the controler

    """

    def __init__(self, config,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        super().__init__(config, 'taxo_groups',
                         max_retry, max_requests, max_chunks)

    @lru_cache(maxsize=32)
    def api_list(self, opt_params=None):
        """Return list of taxo groups, from cache or site."""
        return super().api_list()


class TerritorialUnitsAPI(BiolovisionAPI):
    """ Implement api calls to territorial_units controler.

    Methods
    - api_get                - Return a single territorial unit from the controler
    - api_list               - Return a list of territorial units from the controler

    """

    def __init__(self, config,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        super().__init__(config, 'territorial_units',
                         max_retry, max_requests, max_chunks)

    @lru_cache(maxsize=32)
    def api_list(self, opt_params=None):
        """Return list of taxo groups, from cache or site."""
        return super().api_list()
