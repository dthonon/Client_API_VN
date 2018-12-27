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
__version__ = "0.1.1" #VERSION#

class StoreFileException(Exception):
    """An exception occurred while handling download or store. """


class StoreFile:
    """Provides store to file method."""

    def __init__(self, config):
        self._config = config

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

        """
        # Store to file
        if (len(items_dict['data']) > 0):
            # Convert to json
            logging.debug('Converting to json %d items',
                          len(items_dict['data']))
            items_json = json.dumps(items_dict, sort_keys=True, indent=4, separators=(',', ': '))
            file_json_gz = str(Path.home()) + '/' + self._config.file_store + \
                controler + '_' + seq + '.json.gz'
            logging.debug('Received data, storing json to {}'.format(file_json_gz))
            with gzip.open(file_json_gz, 'wb', 9) as g:
                g.write(items_json.encode())

        return
