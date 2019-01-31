"""Methods to store Biolovision data to file.


Methods

- store_data      - Store generic data structure to file

Properties

-

"""
import sys
from pathlib import Path
import logging
import json
import gzip

# version of the program:
from setuptools_scm import get_version
__version__ = get_version(root='../..', relative_to=__file__)

class StoreFileException(Exception):
    """An exception occurred while handling download or store. """


class StoreFile:
    """Provides store to file method."""

    def __init__(self, config):
        self._config = config

    @property
    def version(self):
        """Return version."""
        return __version__

    # ---------------
    # Generic methods
    # ---------------
    def store(self, controler, seq, items_dict):
        """Write data to file.

        Processing depends on controler, as items_dict structure varies.
        Converts to JSON and store to file, named from
        controler and seq.

        Parameters
        ----------
        controler : str
            Name of API controler.
        seq : str
            (Composed) sequence of data stream.
        controler : dict
            Data returned from API call.

        Returns
        -------
        int
            Count of items stored (not exact for observations, due to forms).
        """
        # Store to file
        nb_obs = len(items_dict['data'])
        if nb_obs > 0:
            # Convert to json
            logging.debug('Converting to json %d items',
                          len(items_dict['data']))
            items_json = json.dumps(items_dict, sort_keys=True, indent=4, separators=(',', ': '))
            file_json_gz = str(Path.home()) + '/' + self._config.file_store + \
                controler + '_' + seq + '.json.gz'
            logging.debug('Received data, storing json to {}'.format(file_json_gz))
            with gzip.open(file_json_gz, 'wb', 9) as g:
                g.write(items_json.encode())

        return nb_obs

    def log(self, site, controler,
            error_count=0, http_status=0, comment=''):
        """Write download log entries to database.

        Parameters
        ----------
        site : str
            VN site name.
        controler : str
            Name of API controler.
        error_count : integer
            Number of errors during download.
        http_status : integer
            HTTP status of latest download.
        comment : str
            Optional comment, in free text.

        """
        # Not implemented
        return
