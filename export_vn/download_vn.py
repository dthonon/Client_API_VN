"""Methods to download from VisioNature and store to file.



Methods

- download_taxo_groups      - Download and store taxo groups

Properties

- transfer_errors            - Return number of errors

"""
import sys
import logging

# version of the program:
__version__ = "0.1.1" #VERSION#

class DownloadVnException(Exception):
    """An exception occurred while handling download or store. """


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
        """Return the number of HTTP errors during this session."""
        return self._transfer_errors

    # ----------------
    # Internal methods
    # ----------------

    # ------------------------------------
    #  Local admin units controler methods
    # ------------------------------------
