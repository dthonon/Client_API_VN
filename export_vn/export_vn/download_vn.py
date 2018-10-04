"""Methods to download from VisioNature and store to file.



Methods

- download_taxo_groups      - Download and store taxo groups

Properties

- transfer_errors            - Return number of errors

"""
import sys
import logging
import json

# version of the program:
__version__ = "0.1.1" #VERSION#

class DownloadVnException(Exception):
    """An exception occurred while handling download or store. """

class DownloadVn:
    """Top class, not for direct use. Provides internal and template methods."""

    def __init__(self, config,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        self._config = config
        self._limits = {
            'max_retry': max_retry,
            'max_requests': max_requests,
            'max_chunks': max_chunks
        }
        self._transfer_errors = 0

    @property
    def transfer_errors(self):
        """Return the number of API errors during this session."""
        return self._transfer_errors

    # ----------------
    # Internal methods
    # ----------------
    def store(self, ctrl):
        """Download from VN by API and store json to file.

        Calls  biolovision_api, convert to json and store to file.

        Parameters
        ----------
        ctrl : str
            controler to query.

        """
        # GET from API
        # Convert to json
        # Store to file
        return


class LocalAdminUnits(DownloadVn):
    """ Implement store from local_admin_units controler.

    Methods
    - api_list               - Download and store to json

    """

    def __init__(self, config,
                 max_retry=5, max_requests=sys.maxsize, max_chunks=10):
        super().__init__(config, max_retry, max_requests, max_chunks)
        self.__ctrl = 'local_admin_units'

    def store(self):
        """Query for a list of entities from local_admin_units controler.

        Calls  /local_admin_units API.

        """
        super().store(self.__ctrl)
        return
