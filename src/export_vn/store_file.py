"""Methods to store Biolovision data to file.


Methods

- store_data      - Store generic data structure to file

Properties

-

"""
import gzip
import json
import logging
import os
from pathlib import Path

from . import __version__, _

logger = logging.getLogger("transfer_vn.store_file")


class StoreFileException(Exception):
    """An exception occurred while handling download or store. """


class StoreFile:
    """Provides store to file method."""

    def __init__(self, config):
        self._config = config

    def __enter__(self):
        logger.debug(_("Entry into StoreFile"))
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Finalize connections."""
        logger.debug(_("Exit from StoreFile"))

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
        # Store to file, if enabled
        if self._config.file_enabled:
            json_path = str(Path.home()) + "/" + self._config.file_store
            if not Path(json_path).is_dir():
                try:
                    os.makedirs(json_path)
                except OSError:
                    logger.error(_("Creation of the directory %s failed"), json_path)
                    raise
                else:
                    logger.info(_("Successfully created the directory %s"), json_path)

            if len(items_dict["data"]) > 0:
                # Convert to json
                logger.debug(_("Converting to json %d items"), len(items_dict["data"]))
                items_json = json.dumps(
                    items_dict, sort_keys=True, indent=4, separators=(",", ": ")
                )
                file_json_gz = json_path + controler + "_" + seq + ".json.gz"
                logger.debug(_("Received data, storing json to %s"), file_json_gz)
                with gzip.open(file_json_gz, "wb", 9) as g:
                    g.write(items_json.encode())
            return len(items_dict["data"])
        else:
            return 0

    def delete_obs(self, obs_list):
        """Delete observations stored in database.

        Parameters
        ----------
        obs_list : list
            Data returned from API call.

        Returns
        -------
        int
            Count of items deleted.
        """
        # Not implemented
        return None

    def log(self, site, controler, *args, **kwargs):
        """Write download log entries to database.

        Parameters
        ----------
        site : str
            VN site name.
        controler : str
            Name of API controler.
        """
        # Not implemented
        return None

    def increment_log(self, site, taxo_group, last_ts):
        """Write last increment timestamp to database.

        Parameters
        ----------
        site : str
            VN site name.
        taxo_group : str
            Taxo_group updated.
        last_ts : timestamp
            Timestamp of last update of this taxo_group.
        """
        # Not implemented
        return None

    def increment_get(self, site, taxo_group):
        """Get last increment timestamp from database.

        Parameters
        ----------
        site : str
            VN site name.
        taxo_group : str
            Taxo_group updated.

        Returns
        -------
        timestamp
            Timestamp of last update of this taxo_group.
        """
        # Not implemented
        return None
