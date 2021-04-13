"""Methods to store Biolovision data to different stores.

For the moment, quick and dirty call to StoreFile and StorePostgresql.

Methods

- store_data      - Store generic data structure to file

Properties

-

"""

import logging

from . import _, __version__

logger = logging.getLogger("transfer_vn.store_all")


class StoreAll:
    """Provides store to backend storage."""

    def __init__(self, config, file_backend, db_backend):
        self._config = config
        self._file_backend = file_backend
        self._db_backend = db_backend

    def __enter__(self):
        logger.debug(_("Entry into StoreAll"))
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Finalize connections."""
        logger.debug(_("Exit from StoreAll"))

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
        # Call backends if needed
        nb_item = 0
        if self._config.file_enabled:
            nb_item = self._file_backend.store(controler, seq, items_dict)
        if self._config.db_enabled:
            nb_item = self._db_backend.store(controler, seq, items_dict)
        return nb_item

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
        # Call backends if needed
        nb_delete = 0
        if self._config.file_enabled:
            nb_delete = self._file_backend.delete_obs(obs_list)
        if self._config.db_enabled:
            nb_delete = self._db_backend.delete_obs(obs_list)
        return nb_delete

    def log(
        self,
        site,
        controler,
        error_count=0,
        http_status=0,
        comment="",
        length=0,
        duration=0,
    ):
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
        length : integer
            Optional length of data transfer
        duration : integer
            Optional duration of data transfer, in ms
        """
        # Call backends if needed
        if self._config.file_enabled:
            self._file_backend.log(
                site, controler, error_count, http_status, comment, length, duration
            )
        if self._config.db_enabled:
            self._db_backend.log(
                site, controler, error_count, http_status, comment, length, duration
            )
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
        # Call backends if needed
        if self._config.file_enabled:
            self._file_backend.increment_log(site, taxo_group, last_ts)
        if self._config.db_enabled:
            self._db_backend.increment_log(site, taxo_group, last_ts)
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
        # Call backends if needed
        incr = None
        if self._config.file_enabled:
            incr = self._file_backend.increment_get(site, taxo_group)
        if self._config.db_enabled:
            incr = self._db_backend.increment_get(site, taxo_group)
        return incr
