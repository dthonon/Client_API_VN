"""Methods to download from VisioNature and store to file.



Methods

- download_taxo_groups      - Download and store taxo groups

Properties

- transfer_errors            - Return number of errors

"""
import sys
from pathlib import Path
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
    def store(self):
        """Download from VN by API and store json to file.

        Calls  biolovision_api, convert to json and store to file.

        """
        # GET from API
        logging.debug('Getting items from controler %s',
                      self._api_instance.controler)
        items_dict = self._api_instance.api_list()
        # Convert to json
        logging.debug('Converting to json %d items',
                      len(items_dict['data']))
        items_json = json.dumps(items_dict, sort_keys=True, indent=4, separators=(',', ': '))
        # Store to file
        if (len(items_dict['data']) > 0):
            file_json_gz = str(Path.home()) + '/' + self._config.file_store + \
                self._api_instance.controler + '_1.json.gz'
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
