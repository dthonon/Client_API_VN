"""Methods to download from VisioNature and store to file.


Methods

- download_taxo_groups      - Download and store taxo groups

Properties

- transfer_errors            - Return number of errors

"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import logging
import json
import gzip

from export_vn.biolovision_api import LocalAdminUnitsAPI, ObservationsAPI, PlacesAPI
from export_vn.biolovision_api import SpeciesAPI, TaxoGroupsAPI, TerritorialUnitsAPI
from export_vn.biolovision_api import BiolovisionApiException, HTTPError, MaxChunksError
from export_vn.evnconf import EvnConf

# version of the program:
__version__ = "0.1.1" #VERSION#

class DownloadVnException(Exception):
    """An exception occurred while handling download or store. """

class NotImplemented(DownloadVnException):
    """Feature not implemented."""


class DownloadVn:
    """Top class, not for direct use. Provides internal and template methods."""

    def __init__(self, config, api_instance,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        self._config = config
        self._limits = {
            'max_retry': max_retry,
            'max_requests': max_requests,
            'max_chunks': max_chunks
        }
        self._transfer_errors = 0
        self._api_instance = api_instance

    @property
    def transfer_errors(self):
        """Return the number of API errors during this session."""
        return self._transfer_errors

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
            # Convert to json
            logging.debug('Converting to json %d items',
                          len(items_dict['data']))
            items_json = json.dumps(items_dict, sort_keys=True, indent=4, separators=(',', ': '))
            # Store to file
            if (len(items_dict['data']) > 0):
                file_json_gz = str(Path.home()) + '/' + self._config.file_store + \
                    self._api_instance.controler + '_' + str(i) + '.json.gz'
                logging.debug('Received data, storing json to {}'.format(file_json_gz))
                with gzip.open(file_json_gz, 'wb', 9) as g:
                    g.write(items_json.encode())

        return


class LocalAdminUnits(DownloadVn):
    """ Implement store from local_admin_units controler.

    Methods
    - store               - Download and store to json

    """

    def __init__(self, config,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        super().__init__(config, LocalAdminUnitsAPI(config),
                         max_retry, max_requests, max_chunks)


class Observations(DownloadVn):
    """ Implement store from observations controler.

    Methods
    - store               - Download (by date interval) and store to json
    - update              - Download (by date interval) and store to json

    """

    def __init__(self, config,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        super().__init__(config, ObservationsAPI(config),
                         max_retry, max_requests, max_chunks)

    def _store_list(self, id_taxo_group=None):
        """Download from VN by API list and store json to file.

        Calls biolovision_api, iterating on species, convert to json and store to file.
        Downloads all database is id_taxo_group is None.
        If id_taxo_group is defined, downloads only this taxo_group

        Parameters
        ----------
        id_taxo_group : str or None
            If not None, taxo_group to be downloaded.

        """
        # GET from API
        logging.debug('Getting items from controler %s, using API list',
                      self._api_instance.controler)
        items_dict = self._api_instance.api_list(id_taxo_group)
        # Convert to json
        logging.debug('Converting to json %d items',
                      len(items_dict['data']))
        items_json = json.dumps(items_dict, sort_keys=True, indent=4, separators=(',', ': '))
        # Store to file
        if (len(items_dict['data']) > 0):
            file_json_gz = str(Path.home()) + '/' + self._config.file_store + \
                self._api_instance.controler + '_' + str(id_taxo_group) + '_1.json.gz'
            logging.debug('Received data, storing json to {}'.format(file_json_gz))
            with gzip.open(file_json_gz, 'wb', 9) as g:
                g.write(items_json.encode())

        return

    def store(self, id_taxo_group=None, method='search'):
        """Download from VN by API and store json to file.

        Calls  biolovision_api, convert to json and store to file.
        Downloads all database is id_taxo_group is None.
        If id_taxo_group is defined, downloads only this taxo_group

        Parameters
        ----------
        id_taxo_group : str or None
            If not None, taxo_group to be downloaded.
        method : str
            API used to download, either 'search' or 'list'.

        """
        # GET from API
        logging.debug('Getting items from controler %s, using API %s',
                      self._api_instance.controler, method)
        if method == 'search':
            self._store_search(id_taxo_group)
        elif method == 'list':
            self._store_list(id_taxo_group)
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
        # items_json = json.dumps(items_dict, sort_keys=True, indent=4, separators=(',', ': '))
        # # Store to file
        # if (len(items_dict['data']) > 0):
        #     file_json_gz = str(Path.home()) + '/' + self._config.file_store + \
        #         self._api_instance.controler + '_1.json.gz'
        #     logging.debug('Received data, storing json to {}'.format(file_json_gz))
        #     with gzip.open(file_json_gz, 'wb', 9) as g:
        #         g.write(items_json.encode())

        return


class Places(DownloadVn):
    """ Implement store from places controler.

    Methods
    - store               - Download and store to json

    """

    def __init__(self, config,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        super().__init__(config, PlacesAPI(config),
                         max_retry, max_requests, max_chunks)


class Species(DownloadVn):
    """ Implement store from species controler.

    Methods
    - store               - Download and store to json

    """

    def __init__(self, config,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        super().__init__(config, SpeciesAPI(config),
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

    def __init__(self, config,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        super().__init__(config, TaxoGroupsAPI(config),
                         max_retry, max_requests, max_chunks)


class TerritorialUnits(DownloadVn):
    """ Implement store from territorial_units controler.

    Methods
    - store               - Download and store to json

    """

    def __init__(self, config,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        super().__init__(config, TerritorialUnitsAPI(config),
                         max_retry, max_requests, max_chunks)
