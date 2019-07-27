"""Methods to download from VisioNature and store to file.


Methods

- download_taxo_groups      - Download and store taxo groups

Properties

-

"""
import logging
from datetime import datetime, timedelta

from export_vn.biolovision_api import (
    EntitiesAPI,
    FieldsAPI,
    LocalAdminUnitsAPI,
    ObservationsAPI,
    ObserversAPI,
    PlacesAPI,
    SpeciesAPI,
    TaxoGroupsAPI,
    TerritorialUnitsAPI,
)
from export_vn.regulator import PID

from . import _, __version__

logger = logging.getLogger("transfer_vn.download_vn")


class DownloadVnException(Exception):
    """An exception occurred while handling download or store. """


class NotImplementedException(DownloadVnException):
    """Feature not implemented."""


class DownloadVn:
    """Top class, not for direct use.
    Provides internal and template methods."""

    def __init__(
        self,
        config,
        api_instance,
        backend,
        max_retry=None,
        max_requests=None,
        max_chunks=None,
    ):
        self._config = config
        self._api_instance = api_instance
        self._backend = backend
        if max_retry is None:
            max_retry = config.tuning_max_retry
        if max_requests is None:
            max_requests = config.tuning_max_requests
        if max_chunks is None:
            max_chunks = config.tuning_max_chunks
        self._limits = {
            "max_retry": max_retry,
            "max_requests": max_requests,
            "max_chunks": max_chunks,
        }
        return None

    @property
    def version(self):
        """Return version."""
        return __version__

    @property
    def transfer_errors(self):
        """Return the number of HTTP errors during this session."""
        return self._api_instance.transfer_errors

    # ----------------
    # Internal methods
    # ----------------

    # ---------------
    # Generic methods
    # ---------------
    def store(self, opt_params_iter=None):
        """Download from VN by API and store json to file.

        Calls  biolovision_api, convert to json and call backend to store.

        Parameters
        ----------
        opt_params_iter : iterable or None
            Provides opt_params values.

        """
        # GET from API
        logger.debug(_("Getting items from controler %s"), self._api_instance.controler)
        i = 0
        if opt_params_iter is None:
            opt_params_iter = iter([None])
        for opt_params in opt_params_iter:
            i += 1
            log_msg = _("Iteration {}, opt_params = {}").format(i, opt_params)
            logger.debug(log_msg)
            items_dict = self._api_instance.api_list(opt_params=opt_params)
            # Call backend to store generic log
            self._backend.log(
                self._config.site,
                self._api_instance.controler,
                self._api_instance.transfer_errors,
                self._api_instance.http_status,
                log_msg,
            )
            # Call backend to store results
            self._backend.store(self._api_instance.controler, str(i), items_dict)

        return None


class Entities(DownloadVn):
    """ Implement store from entities controler.

    Methods
    - store               - Download and store to json

    """

    def __init__(
        self, config, backend, max_retry=None, max_requests=None, max_chunks=None
    ):
        super().__init__(
            config, EntitiesAPI(config), backend, max_retry, max_requests, max_chunks
        )
        return None


class Fields(DownloadVn):
    """ Implement store from fields controler.

    Methods
    - store               - Download and store to json

    """

    def __init__(
        self, config, backend, max_retry=None, max_requests=None, max_chunks=None
    ):
        super().__init__(
            config, FieldsAPI(config), backend, max_retry, max_requests, max_chunks
        )
        return None


class LocalAdminUnits(DownloadVn):
    """ Implement store from local_admin_units controler.

    Methods
    - store               - Download and store to json

    """

    def __init__(
        self, config, backend, max_retry=None, max_requests=None, max_chunks=None
    ):
        super().__init__(
            config,
            LocalAdminUnitsAPI(config),
            backend,
            max_retry,
            max_requests,
            max_chunks,
        )
        return None


class Observations(DownloadVn):
    """ Implement store from observations controler.

    Methods
    - store               - Download (by date interval) and store to json
    - update              - Download (by date interval) and store to json

    """

    def __init__(
        self, config, backend, max_retry=None, max_requests=None, max_chunks=None
    ):
        super().__init__(
            config,
            ObservationsAPI(config),
            backend,
            max_retry,
            max_requests,
            max_chunks,
        )
        return None

    def _store_list(self, id_taxo_group, by_specie, short_version="1"):
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
        short_version : str
            '0' for long JSON and '1' for short_version.
        """
        # GET from API
        logger.debug(
            _("Getting observations from controler %s, using API list"),
            self._api_instance.controler,
        )
        if id_taxo_group is None:
            taxo_groups = TaxoGroupsAPI(self._config).api_list()["data"]
        else:
            taxo_groups = [{"id": id_taxo_group, "access_mode": "full"}]
        for taxo in taxo_groups:
            if taxo["access_mode"] != "none":
                id_taxo_group = taxo["id"]
                self._backend.increment_log(
                    self._config.site, id_taxo_group, datetime.now()
                )
                logger.info(
                    _("Getting observations from taxo_group %s, in _store_list"),
                    id_taxo_group,
                )
                if by_specie:
                    species = SpeciesAPI(self._config).api_list(
                        {"id_taxo_group": str(id_taxo_group)}
                    )["data"]
                    for specie in species:
                        if specie["is_used"] == "1":
                            logger.info(
                                _(
                                    "Getting observations from taxo_group %s, species %s"
                                ),
                                id_taxo_group,
                                specie["id"],
                            )
                            items_dict = self._api_instance.api_list(
                                id_taxo_group,
                                id_species=specie["id"],
                                short_version=short_version,
                            )
                            # Call backend to store list by taxo_group, species log
                            self._backend.log(
                                self._config.site,
                                self._api_instance.controler,
                                self._api_instance.transfer_errors,
                                self._api_instance.http_status,
                                (
                                    _("observations from taxo_group %s, species %s"),
                                    id_taxo_group,
                                    specie["id"],
                                ),
                            )
                            # Call backend to store results
                            self._backend.store(
                                self._api_instance.controler,
                                str(id_taxo_group) + "_" + specie["id"],
                                items_dict,
                            )
                else:
                    items_dict = self._api_instance.api_list(
                        id_taxo_group, short_version=short_version
                    )
                    # Call backend to store list by taxo_group log
                    self._backend.log(
                        self._config.site,
                        self._api_instance.controler,
                        self._api_instance.transfer_errors,
                        self._api_instance.http_status,
                        (_("observations from taxo_group %s"), id_taxo_group),
                    )
                    # Call backend to store results
                    self._backend.store(
                        self._api_instance.controler,
                        str(id_taxo_group) + "_1",
                        items_dict,
                    )

        return None

    def _store_search(self, id_taxo_group, short_version="1"):
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
        short_version : str
            '0' for long JSON and '1' for short_version.
        """
        # GET from API
        logger.debug(
            _("Getting observations from controler %s, using API search"),
            self._api_instance.controler,
        )
        if id_taxo_group is None:
            taxo_groups = TaxoGroupsAPI(self._config).api_list()["data"]
        else:
            taxo_groups = [{"id": id_taxo_group, "access_mode": "full"}]
        for taxo in taxo_groups:
            if taxo["access_mode"] != "none":
                id_taxo_group = taxo["id"]
                self._backend.increment_log(
                    self._config.site, id_taxo_group, datetime.now()
                )
                end_date = datetime.now()
                start_date = end_date
                min_date = datetime(self._config.tuning_min_year, 1, 1)
                seq = 1
                pid = PID(
                    kp=self._config.tuning_pid_kp,
                    ki=self._config.tuning_pid_ki,
                    kd=self._config.tuning_pid_kd,
                    setpoint=self._config.tuning_pid_setpoint,
                    output_limits=(
                        self._config.tuning_pid_limit_min,
                        self._config.tuning_pid_limit_max,
                    ),
                )
                delta_days = self._config.tuning_pid_delta_days
                while start_date > min_date:
                    start_date = end_date - timedelta(days=delta_days)
                    q_param = {
                        "period_choice": "range",
                        "date_from": start_date.strftime("%d.%m.%Y"),
                        "date_to": end_date.strftime("%d.%m.%Y"),
                        "species_choice": "all",
                        "taxonomic_group": taxo["id"],
                    }
                    items_dict = self._api_instance.api_search(
                        q_param, short_version=short_version
                    )
                    # Call backend to store results
                    nb_obs = self._backend.store(
                        self._api_instance.controler,
                        str(id_taxo_group) + "_" + str(seq),
                        items_dict,
                    )
                    log_msg = _(
                        "Iter: {}, {} obs, taxo_group: {}, date: {}, interval: {}"
                    ).format(
                        seq,
                        nb_obs,
                        id_taxo_group,
                        start_date.strftime("%d/%m/%Y"),
                        str(delta_days),
                    )
                    # Call backend to store log
                    self._backend.log(
                        self._config.site,
                        self._api_instance.controler,
                        self._api_instance.transfer_errors,
                        self._api_instance.http_status,
                        log_msg,
                    )
                    logger.info(log_msg)
                    seq += 1
                    end_date = start_date
                    delta_days = int(pid(nb_obs))
        return None

    def _list_taxo_groups(self, id_taxo_group):
        """Return the list of enabled taxo_groups."""
        if id_taxo_group is None:
            # Get all active taxo_groups
            taxo_groups = TaxoGroupsAPI(self._config).api_list()
            taxo_list = []
            for taxo in taxo_groups["data"]:
                if taxo["access_mode"] != "none":
                    logger.debug(
                        _("Starting to download observations from taxo_group %s: %s"),
                        taxo["id"],
                        taxo["name"],
                    )
                    taxo_list.append(taxo["id"])
        else:
            if isinstance(id_taxo_group, list):
                # A list of taxo_group given as parameter
                taxo_list = id_taxo_group
            else:
                # Only 1 taxo_group given as parameter
                taxo_list = [id_taxo_group]

        return taxo_list

    def store(
        self, id_taxo_group=None, by_specie=False, method="search", short_version="1"
    ):
        """Download from VN by API and store json to backend.

        Calls  biolovision_api
        convert to json
        and store using backend.store (database, file...).
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
        short_version : str
            '0' for long JSON and '1' for short_version.
        """
        # Get the list of taxo groups to process
        taxo_list = self._list_taxo_groups(id_taxo_group)

        if method == "search":
            for taxo in taxo_list:
                self._store_search(taxo, short_version=short_version)
        elif method == "list":
            for taxo in taxo_list:
                self._store_list(taxo, by_specie=by_specie, short_version=short_version)
        else:
            raise NotImplementedException

        return None

    def update(self, id_taxo_group=None, since=None, short_version="1"):
        """Download increment from VN by API and store json to file.

        Gets previous update date from database and updates since then.
        Calls  biolovision_api, finds if update or delete.
        If update, get full observation and store to db.
        If delete, delete from db.

        Parameters
        ----------
        id_taxo_group : str or None
            If not None, taxo_group to be downloaded.
        since : str or None
            If None, updates since last download
            Or if provided, updates since that given date.
        short_version : str
            '0' for long JSON and '1' for short_version.
        """
        # GET from API
        logger.debug(
            _("Getting updated observations from controler %s"),
            self._api_instance.controler,
        )

        # Get the list of taxo groups to process
        taxo_list = self._list_taxo_groups(id_taxo_group)

        if since is None:
            get_since = True
        else:
            get_since = False

        for taxo in taxo_list:
            updated = list()
            deleted = list()
            if get_since:
                since = self._backend.increment_get(self._config.site, taxo)
            if since is not None:
                # Valid since date provided or found in database
                self._backend.increment_log(self._config.site, taxo, datetime.now())
                logger.info(
                    _("Getting updates for taxo_group %s since %s"), taxo, since
                )
                items_dict = self._api_instance.api_diff(taxo, since)

                # List by processing type
                for item in items_dict:
                    logger.debug(
                        _("Observation %s was %s"),
                        item["id_sighting"],
                        item["modification_type"],
                    )
                    if item["modification_type"] == "updated":
                        updated.append(item["id_sighting"])
                    elif item["modification_type"] == "deleted":
                        deleted.append(item["id_sighting"])
                    else:
                        logger.error(
                            _("Observation %s has unknown processing %s"),
                            item["id_universal"],
                            item["modification_type"],
                        )
                        raise NotImplementedException
                logger.info(
                    _("Received %d updated and %d deleted items"),
                    len(updated),
                    len(deleted),
                )
            else:
                logger.error(
                    _("No date found for last download, increment not performed")
                )

            # Process updates
            for obs in updated:
                log_msg = _("Updating observation %s").format(obs)
                logger.debug(log_msg)
                items_dict = self._api_instance.api_get(
                    obs, short_version=short_version
                )
                # Call backend to store log
                self._backend.log(
                    self._config.site,
                    self._api_instance.controler,
                    self._api_instance.transfer_errors,
                    self._api_instance.http_status,
                    log_msg,
                )
                # Call backend to store results
                self._backend.store(
                    self._api_instance.controler, str(id_taxo_group) + "_1", items_dict
                )

            # Process deletes
            if len(deleted) > 0:
                self._backend.delete_obs(deleted)

        return None


class Observers(DownloadVn):
    """ Implement store from observers controler.

    Methods
    - store               - Download and store to json

    """

    def __init__(
        self, config, backend, max_retry=None, max_requests=None, max_chunks=None
    ):
        super().__init__(
            config, ObserversAPI(config), backend, max_retry, max_requests, max_chunks
        )
        return None


class Places(DownloadVn):
    """ Implement store from places controler.

    Methods
    - store               - Download and store to json

    """

    def __init__(
        self, config, backend, max_retry=None, max_requests=None, max_chunks=None
    ):
        super().__init__(
            config, PlacesAPI(config), backend, max_retry, max_requests, max_chunks
        )
        return None


class Species(DownloadVn):
    """ Implement store from species controler.

    Methods
    - store               - Download and store to json

    """

    def __init__(
        self, config, backend, max_retry=None, max_requests=None, max_chunks=None
    ):
        super().__init__(
            config, SpeciesAPI(config), backend, max_retry, max_requests, max_chunks
        )
        return None

    def store(self):
        """Store species, iterating over taxo_groups
        """
        taxo_groups = TaxoGroupsAPI(self._config).api_list()
        taxo_list = []
        for taxo in taxo_groups["data"]:
            if taxo["access_mode"] != "none":
                logger.debug(_("Storing species from taxo_group %s"), taxo["id"])
                taxo_list.append({"id_taxo_group": taxo["id"]})
        super().store(iter(taxo_list))

        return None


class TaxoGroup(DownloadVn):
    """ Implement store from taxo_groups controler.

    Methods
    - store               - Download and store to json

    """

    def __init__(
        self, config, backend, max_retry=None, max_requests=None, max_chunks=None
    ):
        super().__init__(
            config, TaxoGroupsAPI(config), backend, max_retry, max_requests, max_chunks
        )
        return None


class TerritorialUnits(DownloadVn):
    """ Implement store from territorial_units controler.

    Methods
    - store               - Download and store to json

    """

    def __init__(
        self, config, backend, max_retry=None, max_requests=None, max_chunks=None
    ):
        super().__init__(
            config,
            TerritorialUnitsAPI(config),
            backend,
            max_retry,
            max_requests,
            max_chunks,
        )
        return None
