"""Methods to download from VisioNature and store to file.


Methods

- download_taxo_groups      - Download and store taxo groups

Properties

-

"""
import sys
from datetime import datetime, timedelta
import logging
import json

from export_vn.biolovision_api import EntitiesAPI, LocalAdminUnitsAPI, ObservationsAPI, PlacesAPI
from export_vn.biolovision_api import SpeciesAPI, TaxoGroupsAPI, TerritorialUnitsAPI
from export_vn.biolovision_api import BiolovisionApiException, HTTPError, MaxChunksError
from export_vn.regulator import PID

# version of the program:
from setuptools_scm import get_version
__version__ = get_version(root='../..', relative_to=__file__)

class DownloadVnException(Exception):
    """An exception occurred while handling download or store. """

class NotImplementedException(DownloadVnException):
    """Feature not implemented."""


class DownloadVn:
    """Top class, not for direct use. Provides internal and template methods."""

    def __init__(self, config, api_instance, backend,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        self._config = config
        self._api_instance = api_instance
        self._backend = backend
        self._limits = {
            'max_retry': max_retry,
            'max_requests': max_requests,
            'max_chunks': max_chunks
        }

    @property
    def version(self):
        """Return version."""
        return __version__

    # ----------------
    # Internal methods
    # ----------------


    # ---------------
    # Generic methods
    # ---------------
    def store(self, opt_params_iter=None):
        """Download from VN by API and store json to file.

        Calls  biolovision_api, convert to json and store to file.

        Parameters
        ----------
        opt_params_iter : iterable or None
            Provides opt_params values.

        """
        # GET from API
        logging.debug('Getting items from controler %s',
                      self._api_instance.controler)
        i = 0
        if opt_params_iter == None:
            opt_params_iter = iter([None])
        for opt_params in opt_params_iter:
            i += 1
            logging.debug('Iteration %s, opt_params = %s',
                          i, opt_params)
            items_dict = self._api_instance.api_list(opt_params=opt_params)
            # Call backend to store results
            self._backend(self._api_instance.controler, str(i), items_dict)

        return

class Entities(DownloadVn):
    """ Implement store from entities controler.

    Methods
    - store               - Download and store to json

    """

    def __init__(self, config, backend,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        super().__init__(config, EntitiesAPI(config), backend,
                         max_retry, max_requests, max_chunks)



class LocalAdminUnits(DownloadVn):
    """ Implement store from local_admin_units controler.

    Methods
    - store               - Download and store to json

    """

    def __init__(self, config, backend,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        super().__init__(config, LocalAdminUnitsAPI(config), backend,
                         max_retry, max_requests, max_chunks)


class Observations(DownloadVn):
    """ Implement store from observations controler.

    Methods
    - store               - Download (by date interval) and store to json
    - update              - Download (by date interval) and store to json

    """

    def __init__(self, config, backend,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        super().__init__(config, ObservationsAPI(config), backend,
                         max_retry, max_requests, max_chunks)

    def _store_list(self, id_taxo_group, by_specie):
        """Download from VN by API list and store json to file.

        Calls biolovision_api to get observation, convert to json and store.
        If id_taxo_group is defined, downloads only this taxo_group
        Else if id_taxo_group is None, downloads all database
        If by_specie, iterate on species
        Else download all taxo_group in 1 call

        Parameters
        ----------
        id_taxo_group : str or None
            If not None, taxo_group to be downloaded.
        by_specie : bool
            If True, downloading by specie.

        """
        # GET from API
        logging.debug('Getting items from controler %s, using API list',
                      self._api_instance.controler)
        if id_taxo_group == None:
            taxo_groups = TaxoGroupsAPI(self._config).api_list()['data']
        else:
            taxo_groups = [{'id': id_taxo_group, 'access_mode': 'full'}]
        for taxo in taxo_groups:
            if taxo['access_mode'] != 'none':
                id_taxo_group = taxo['id']
                logging.info('Getting observations from taxo_group %s',
                             id_taxo_group)
                if by_specie:
                    species = SpeciesAPI(self._config).api_list({'id_taxo_group':
                                                                 str(id_taxo_group)})['data']
                    for specie in species:
                        if specie['is_used'] == '1':
                            logging.info('Getting observations from taxo_group %s, species %s',
                                         id_taxo_group, specie['id'])
                            items_dict = self._api_instance.api_list(id_taxo_group, specie['id'])
                            # Call backend to store results
                            self._backend(self._api_instance.controler,
                                          str(id_taxo_group) + '_' + specie['id'],
                                          items_dict)
                else:
                    items_dict = self._api_instance.api_list(id_taxo_group)
                    # Call backend to store results
                    self._backend(self._api_instance.controler, str(id_taxo_group) + '_1',
                                  items_dict)


        return

    def _store_search(self, id_taxo_group):
        """Download from VN by API search and store json to file.

        Calls biolovision_api to get observation, convert to json and store.
        If id_taxo_group is defined, downloads only this taxo_group
        Else if id_taxo_group is None, downloads all database
        Moves back in date range, starting from now
        Date range is adapted to regulate flow

        Parameters
        ----------
        id_taxo_group : str or None
            If not None, taxo_group to be downloaded.

        """
        # GET from API
        logging.debug('Getting items from controler %s, using API search',
                      self._api_instance.controler)
        if id_taxo_group == None:
            taxo_groups = TaxoGroupsAPI(self._config).api_list()['data']
        else:
            taxo_groups = [{'id': id_taxo_group, 'access_mode': 'full'}]
        for taxo in taxo_groups:
            if taxo['access_mode'] != 'none':
                id_taxo_group = taxo['id']
                end_date = datetime.now()
                start_date = end_date
                min_date = datetime(1901, 1, 1)
                seq = 1
                pid = PID(kp=0.0, ki=0.003, kd=0.0,
                          setpoint=10000, output_limits=(10, 2000))
                delta_days = 15
                while start_date > min_date:
                    start_date = end_date - timedelta(days=delta_days)
                    q_param = {'period_choice': 'range',
                               'date_from': start_date.strftime('%d.%m.%Y'),
                               'date_to': end_date.strftime('%d.%m.%Y'),
                               'species_choice':'all',
                               'taxonomic_group': taxo['id']}
                    items_dict = self._api_instance.api_search(q_param)
                    # Call backend to store results
                    self._backend(self._api_instance.controler, str(id_taxo_group) + '_' + str(seq),
                                  items_dict)
                    nb_obs = len(items_dict['data']['sightings'])
                    logging.info('Iter: %s, %s obs, taxo_group: %s, date: %s, interval: %s',
                                 seq, nb_obs, id_taxo_group,
                                 start_date.strftime('%d/%m/%Y'), str(delta_days))
                    seq += 1
                    end_date = start_date
                    delta_days = int(pid(nb_obs))
        return

    def store(self, id_taxo_group=None, by_specie=False, method='search'):
        """Download from VN by API, looping on taxo_group if None and store json to file.

        Calls  biolovision_api, convert to json and store to file.
        Downloads all database if id_taxo_group is None.
        If id_taxo_group is defined, downloads only this taxo_group

        Parameters
        ----------
        id_taxo_group : str or None
            If not None, taxo_group to be downloaded.
        by_specie : bool
            If True, downloading by specie.
        method : str
            API used to download, either 'search' or 'list'.

        """
        # GET from API
        logging.debug('Getting items from controler %s, using API %s',
                      self._api_instance.controler, method)

        if id_taxo_group == None:
            # Get all active taxo_groups
            taxo_groups = TaxoGroupsAPI(self._config).api_list()
            taxo_list = []
            for taxo in taxo_groups['data']:
                if taxo['access_mode'] != 'none':
                    logging.debug('Will download observations from taxo_group %s: %s',
                                  taxo['id'], taxo['name'])
                    taxo_list.append(taxo['id'])
        else:
            if isinstance(id_taxo_group, list):
                # A list of taxo_group given as parameter
                taxo_list = id_taxo_group
            else:
                # Only 1 taxo_group given as parameter
                taxo_list = [id_taxo_group]

        if method == 'search':
            for taxo in taxo_list:
                self._store_search(taxo)
        elif method == 'list':
            for taxo in taxo_list:
                self._store_list(taxo, by_specie=by_specie)
        else:
            raise NotImplemented

        return

    def update(self):
        """Download increment from VN by API and store json to file.
        WIP WIP WIP
        Calls  biolovision_api, convert to json and store to file.

        """
        # GET from API
        logging.debug('Getting items from controler %s',
                      self._api_instance.controler)
        since = (datetime.now() - timedelta(days=1)).strftime('%H:%M:%S %d.%m.%Y')
        logging.debug('Getting updates since {}'.format(since))
        items_dict = self._api_instance.api_diff('2', since)

        # Convert to json
        logging.debug('Received %d modified or updated items',
                      len(items_dict))
        # TODO: process changes
        return


class Places(DownloadVn):
    """ Implement store from places controler.

    Methods
    - store               - Download and store to json

    """

    def __init__(self, config, backend,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        super().__init__(config, PlacesAPI(config), backend,
                         max_retry, max_requests, max_chunks)


class Species(DownloadVn):
    """ Implement store from species controler.

    Methods
    - store               - Download and store to json

    """

    def __init__(self, config, backend,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        super().__init__(config, SpeciesAPI(config), backend,
                         max_retry, max_requests, max_chunks)

    def store(self):
        """Store species, iterating over taxo_groups
        """
        taxo_groups = TaxoGroupsAPI(self._config).api_list()
        taxo_list = []
        for taxo in taxo_groups['data']:
            if taxo['access_mode'] != 'none':
                logging.debug('Storing species from taxo_group %s', taxo['id'])
                taxo_list.append({'id_taxo_group': taxo['id']})
        super().store(iter(taxo_list))

class TaxoGroup(DownloadVn):
    """ Implement store from taxo_groups controler.

    Methods
    - store               - Download and store to json

    """

    def __init__(self, config, backend,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        super().__init__(config, TaxoGroupsAPI(config), backend,
                         max_retry, max_requests, max_chunks)


class TerritorialUnits(DownloadVn):
    """ Implement store from territorial_units controler.

    Methods
    - store               - Download and store to json

    """

    def __init__(self, config, backend,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        super().__init__(config, TerritorialUnitsAPI(config), backend,
                         max_retry, max_requests, max_chunks)
