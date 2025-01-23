"""Methods to download from VisioNature and store to file.


Methods

- download_taxo_groups      - Download and store taxo groups

Properties

-

"""

import logging
from collections import deque
from collections.abc import Callable
from datetime import datetime, timedelta
from itertools import chain
from sys import getsizeof
from time import perf_counter_ns

from biolovision.api import (
    EntitiesAPI,
    FamiliesAPI,
    FieldsAPI,
    HTTPError,
    LocalAdminUnitsAPI,
    ObservationsAPI,
    ObserversAPI,
    PlacesAPI,
    SpeciesAPI,
    TaxoGroupsAPI,
    TerritorialUnitsAPI,
    ValidationsAPI,
)
from export_vn.regulator import PID
from export_vn.store_postgresql import ReadPostgresql

from . import __version__

logger = logging.getLogger(__name__)


def total_size(o, handlers=None):
    """Returns the approximate memory footprint an object and all of its contents.

    Automatically finds the contents of the following builtin containers and
    their subclasses:  tuple, list, deque, dict, set and frozenset.
    To search other containers, add handlers to iterate over their contents:

        handlers = {SomeContainerClass: iter,
                    OtherContainerClass: OtherContainerClass.get_elements}

    """
    all_handlers = {
        tuple: iter,
        list: iter,
        deque: iter,
        dict: lambda d: chain.from_iterable(d.items()),
        set: iter,
        frozenset: iter,
    }
    if handlers is not None:
        all_handlers.update(handlers)  # user handlers take precedence
    seen = set()  # track which object id's have already been seen
    default_size = getsizeof(0)  # estimate sizeof object without __sizeof__

    def sizeof(o):
        if id(o) in seen:  # do not double count the same object
            return 0
        seen.add(id(o))
        s = getsizeof(o, default_size)

        for typ, handler in all_handlers.items():
            if isinstance(o, typ):
                s += sum(map(sizeof, handler(o)))
                break
        return s

    return sizeof(o)


class DownloadVnException(Exception):
    """An exception occurred while handling download or store."""


class NotImplementedException(DownloadVnException):
    """Feature not implemented."""


class DownloadVn:
    """Top class, not for direct use.
    Provides internal and template methods."""

    def __init__(
        self,
        site: str,
        api_instance: Callable[..., None],
        backend: Callable[..., None],
    ) -> None:
        self._site = site
        self._api_instance = api_instance
        self._backend = backend

    @property
    def version(self):
        """Return version."""
        return __version__

    @property
    def transfer_errors(self):
        """Return the number of HTTP errors during this session."""
        return self._api_instance.transfer_errors

    @property
    def name(self):
        """Return the controler name."""
        return self._api_instance.controler

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
        try:
            for opt_params in opt_params_iter:
                i += 1
                log_msg = _("Iteration {}, opt_params = {}").format(i, opt_params)
                logger.debug(log_msg)
                timing = perf_counter_ns()
                items_dict = self._api_instance.api_list(opt_params=opt_params)
                timing = (perf_counter_ns() - timing) / 1000
                # Call backend to store generic log
                self._backend.log(
                    self._site,
                    self._api_instance.controler,
                    self._api_instance.transfer_errors,
                    self._api_instance.http_status,
                    log_msg,
                    total_size(items_dict),
                    timing,
                )
                # Call backend to store results
                self._backend.store(self._api_instance.controler, str(i), items_dict)
        except HTTPError:
            self._backend.log(
                self._site,
                self._api_instance.controler,
                self._api_instance.transfer_errors,
                self._api_instance.http_status,
                _("HTTP error during download"),
            )

        return None


class Entities(DownloadVn):
    """Implement store from entities controler.

    Methods
    - store               - Download and store to json

    """

    def __init__(
        self,
        site: str,
        user_email: str,
        user_pw: str,
        base_url: str,
        client_key: str,
        client_secret: str,
        backend: Callable[..., None],
        max_retry: int = 5,
        max_requests: int = 0,
        max_chunks: int = 100,
        unavailable_delay: int = 600,
        retry_delay: int = 5,
    ) -> None:
        super().__init__(
            site,
            EntitiesAPI(
                user_email=user_email,
                user_pw=user_pw,
                base_url=base_url,
                client_key=client_key,
                client_secret=client_secret,
                max_retry=max_retry,
                max_requests=max_requests,
                max_chunks=max_chunks,
                unavailable_delay=unavailable_delay,
                retry_delay=retry_delay,
            ),
            backend,
        )


class Families(DownloadVn):
    """Implement store from families controler.

    Methods
    - store               - Download and store to json

    """

    def __init__(
        self,
        site: str,
        user_email: str,
        user_pw: str,
        base_url: str,
        client_key: str,
        client_secret: str,
        backend: Callable[..., None],
        max_retry: int = 5,
        max_requests: int = 0,
        max_chunks: int = 100,
        unavailable_delay: int = 600,
        retry_delay: int = 5,
    ) -> None:
        super().__init__(
            site,
            FamiliesAPI(
                user_email=user_email,
                user_pw=user_pw,
                base_url=base_url,
                client_key=client_key,
                client_secret=client_secret,
                max_retry=max_retry,
                max_requests=max_requests,
                max_chunks=max_chunks,
                unavailable_delay=unavailable_delay,
                retry_delay=retry_delay,
            ),
            backend,
        )


class Fields(DownloadVn):
    """Implement store from fields controler.

    Methods
    - store               - Download and store to json

    """

    def __init__(
        self,
        site: str,
        user_email: str,
        user_pw: str,
        base_url: str,
        client_key: str,
        client_secret: str,
        backend: Callable[..., None],
        max_retry: int = 5,
        max_requests: int = 0,
        max_chunks: int = 100,
        unavailable_delay: int = 600,
        retry_delay: int = 5,
    ) -> None:
        super().__init__(
            site,
            FieldsAPI(
                user_email=user_email,
                user_pw=user_pw,
                base_url=base_url,
                client_key=client_key,
                client_secret=client_secret,
                max_retry=max_retry,
                max_requests=max_requests,
                max_chunks=max_chunks,
                unavailable_delay=unavailable_delay,
                retry_delay=retry_delay,
            ),
            backend,
        )

    def store(self, opt_params_iter=None):
        """Download from VN by API and store json to file.

        Calls  biolovision_api, convert to json and call backend to store.
        Specific for fields :
        1) list field groups
        2) for each field, get details

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
        try:
            for opt_params in opt_params_iter:
                i += 1
                log_msg = _("Iteration {}, opt_params = {}").format(i, opt_params)
                logger.debug(log_msg)
                timing = perf_counter_ns()
                items_dict = self._api_instance.api_list(opt_params=opt_params)
                timing = (perf_counter_ns() - timing) / 1000
                # Call backend to store generic log
                self._backend.log(
                    self._site,
                    self._api_instance.controler,
                    self._api_instance.transfer_errors,
                    self._api_instance.http_status,
                    log_msg,
                    total_size(items_dict),
                    timing,
                )
                # Call backend to store groups of fields
                self._backend.store("field_groups", str(i), items_dict)

                # Loop on field groups to get details
                for field in items_dict["data"]:
                    field_id = field["id"]
                    field_details = self._api_instance.api_get(field_id)
                    for detail in field_details["data"]:
                        detail["group"] = field_id
                    logger.debug(_("Details for field group %s = %s"), field_id, field_details)
                    # Call backend to store groups of fields
                    self._backend.store("field_details", str(i), field_details)
        except HTTPError:
            self._backend.log(
                self._site,
                self._api_instance.controler,
                self._api_instance.transfer_errors,
                self._api_instance.http_status,
                _("HTTP error during download"),
            )

        return None


class LocalAdminUnits(DownloadVn):
    """Implement store from local_admin_units controler.

    Methods
    - store               - Download and store to json

    """

    def __init__(
        self,
        site: str,
        user_email: str,
        user_pw: str,
        base_url: str,
        client_key: str,
        client_secret: str,
        backend: Callable[..., None],
        max_retry: int = 5,
        max_requests: int = 0,
        max_chunks: int = 100,
        unavailable_delay: int = 600,
        retry_delay: int = 5,
    ) -> None:
        super().__init__(
            site,
            LocalAdminUnitsAPI(
                user_email=user_email,
                user_pw=user_pw,
                base_url=base_url,
                client_key=client_key,
                client_secret=client_secret,
                max_retry=max_retry,
                max_requests=max_requests,
                max_chunks=max_chunks,
                unavailable_delay=unavailable_delay,
                retry_delay=retry_delay,
            ),
            backend,
        )

    def store(
        self,
        territorial_unit_ids=None,
    ):
        """Download from VN by API and store json to backend.

        Overloads base method to add territorial_unit filter

        Parameters
        ----------
        territorial_unit_ids : list
            List of territorial_units to include in storage.
        """
        if territorial_unit_ids is not None and len(territorial_unit_ids) > 0:
            for id_canton in territorial_unit_ids:
                logger.debug(
                    _("Getting local_admin_units from id_canton %s, using API list"),
                    id_canton,
                )
                q_param = {"id_canton": id_canton}
                super().store([q_param])
        else:
            logger.debug(_("Getting all local_admin_units, using API list"))
            super().store()


class Observations(DownloadVn):
    """Implement store from observations controler.

    Methods
    - store               - Download (by date interval) and store to json
    - update              - Download (by date interval) and store to json

    """

    def __init__(
        self,
        site: str,
        user_email: str,
        user_pw: str,
        base_url: str,
        client_key: str,
        client_secret: str,
        db_enabled: bool,
        db_user: str,
        db_pw: str,
        db_host: str,
        db_port: str,
        db_name: str,
        db_schema_import: str,
        db_schema_vn: str,
        db_group: str,
        db_out_proj: str,
        backend: Callable[..., None],
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        type_date: str = "sighting",
        max_list_length: int = 100,
        max_retry: int = 5,
        max_requests: int = 0,
        max_chunks: int = 100,
        unavailable_delay: int = 600,
        retry_delay: int = 5,
        pid_kp: float = 0.0,
        pid_ki: float = 0.003,
        pid_kd: float = 0.0,
        pid_setpoint: int = 10000,
        pid_limit_min: int = 5,
        pid_limit_max: int = 2000,
        pid_delta_days: int = 15,
    ) -> None:
        self._site = site
        self._user_email = user_email
        self._user_pw = user_pw
        self._base_url = base_url
        self._client_key = client_key
        self._client_secret = client_secret
        self._db_enabled = db_enabled
        self._db_user = db_user
        self._db_pw = db_pw
        self._db_host = db_host
        self._db_port = db_port
        self._db_name = db_name
        self._db_schema_import = db_schema_import
        self._db_schema_vn = db_schema_vn
        self._db_group = db_group
        self._db_out_proj = db_out_proj
        self._start_date = start_date
        self._end_date = end_date
        self._type_date = type_date
        self._backend = backend
        self._max_list_length = max_list_length
        self._max_retry = max_retry
        self._max_requests = max_requests
        self._max_chunks = max_chunks
        self._unavailable_delay = unavailable_delay
        self._retry_delay = retry_delay
        self._pid_kp = pid_kp
        self._pid_ki = pid_ki
        self._pid_kd = pid_kd
        self._pid_setpoint = pid_setpoint
        self._pid_limit_min = pid_limit_min
        self._pid_limit_max = pid_limit_max
        self._pid_delta_days = pid_delta_days

        self._t_units = None

        super().__init__(
            site,
            ObservationsAPI(
                user_email=user_email,
                user_pw=user_pw,
                base_url=base_url,
                client_key=client_key,
                client_secret=client_secret,
                max_retry=max_retry,
                max_requests=max_requests,
                max_chunks=max_chunks,
                unavailable_delay=unavailable_delay,
                retry_delay=retry_delay,
            ),
            backend,
        )

    def _store_list(self, id_taxo_group, by_specie, short_version="1"):
        """Download from VN by API list and store json to file.

        Calls biolovision_api to get observations, convert to json and store.
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
        # Download territorial_units if needed
        if self._t_units is None:
            if self._db_enabled:
                # Try to read from local database
                self._t_units = ReadPostgresql(
                    self._site,
                    self._db_enabled,
                    self._db_user,
                    self._db_pw,
                    self._db_host,
                    self._db_port,
                    self._db_name,
                    self._db_schema_import,
                    self._db_schema_vn,
                    self._db_group,
                    self._db_out_proj,
                ).read("territorial_units")
            if (self._t_units is None) or (len(self._t_units) == 0):
                # No territorial_units available, read from API
                self._t_units = [
                    TerritorialUnitsAPI(
                        user_email=self._user_email,
                        user_pw=self._user_pw,
                        base_url=self._base_url,
                        client_key=self._client_key,
                        client_secret=self._client_secret,
                        max_retry=self._max_retry,
                        max_requests=self._max_requests,
                        max_chunks=self._max_chunks,
                        unavailable_delay=self._unavailable_delay,
                        retry_delay=self._retry_delay,
                    ).api_list()["data"]
                ]

        # GET from API
        logger.debug(
            _("Getting observations from controler %s, using API list"),
            self._api_instance.controler,
        )
        if id_taxo_group is None:
            taxo_groups = TaxoGroupsAPI(
                user_email=self._user_email,
                user_pw=self._user_pw,
                base_url=self._base_url,
                client_key=self._client_key,
                client_secret=self._client_secret,
                max_retry=self._max_retry,
                max_requests=self._max_requests,
                max_chunks=self._max_chunks,
                unavailable_delay=self._unavailable_delay,
                retry_delay=self._retry_delay,
            ).api_list()["data"]
        else:
            taxo_groups = [{"id": id_taxo_group, "access_mode": "full"}]
        try:
            for taxo in taxo_groups:
                if taxo["access_mode"] != "none":
                    id_taxo_group = taxo["id"]
                    self._backend.increment_log(self._site, id_taxo_group, datetime.now())
                    logger.info(
                        _("Getting observations from taxo_group %s, in _store_list"),
                        id_taxo_group,
                    )
                    if by_specie:
                        species = SpeciesAPI(
                            user_email=self._user_email,
                            user_pw=self._user_pw,
                            base_url=self._base_url,
                            client_key=self._client_key,
                            client_secret=self._client_secret,
                            max_retry=self._max_retry,
                            max_requests=self._max_requests,
                            max_chunks=self._max_chunks,
                            unavailable_delay=self._unavailable_delay,
                            retry_delay=self._retry_delay,
                        ).api_list({"id_taxo_group": str(id_taxo_group)})["data"]
                        for specie in species:
                            if specie["is_used"] == "1":
                                logger.info(
                                    _("Getting observations from taxo_group %s, specie %s"),
                                    id_taxo_group,
                                    specie["id"],
                                )
                                timing = perf_counter_ns()
                                items_dict = self._api_instance.api_list(
                                    id_taxo_group,
                                    id_species=specie["id"],
                                    short_version=short_version,
                                )
                                timing = (perf_counter_ns() - timing) / 1000
                                # Call backend to store list by taxo_group, species log
                                self._backend.log(
                                    self._site,
                                    self._api_instance.controler,
                                    self._api_instance.transfer_errors,
                                    self._api_instance.http_status,
                                    (
                                        _("observations from taxo_group %s, species %s"),
                                        id_taxo_group,
                                        specie["id"],
                                    ),
                                    total_size(items_dict),
                                    timing,
                                )
                                # Call backend to store results
                                self._backend.store(
                                    self._api_instance.controler,
                                    str(id_taxo_group) + "_" + specie["id"],
                                    items_dict,
                                )
                    else:
                        timing = perf_counter_ns()
                        items_dict = self._api_instance.api_list(id_taxo_group, short_version=short_version)
                        timing = (perf_counter_ns() - timing) / 1000
                        # Call backend to store list by taxo_group log
                        self._backend.log(
                            self._site,
                            self._api_instance.controler,
                            self._api_instance.transfer_errors,
                            self._api_instance.http_status,
                            (_("observations from taxo_group %s"), id_taxo_group),
                            total_size(items_dict),
                            timing,
                        )
                        # Call backend to store results
                        self._backend.store(
                            self._api_instance.controler,
                            str(id_taxo_group) + "_1",
                            items_dict,
                        )
        except HTTPError:
            self._backend.log(
                self._site,
                self._api_instance.controler,
                self._api_instance.transfer_errors,
                self._api_instance.http_status,
                _("HTTP error during download"),
            )

        return None

    def _store_search(self, id_taxo_group, territorial_unit_ids=None, short_version="1"):
        """Download from VN by API search and store json to file.

        Calls biolovision_api to get observations, convert to json and store.
        If id_taxo_group is defined, downloads only this taxo_group
        Else if id_taxo_group is None, downloads all database
        Moves back in date range, starting from now
        Date range is adapted to regulate flow

        Parameters
        ----------
        id_taxo_group : str or None
            If not None, taxo_group to be downloaded.
        territorial_unit_ids : list
            List of territorial_units to include in storage.
        short_version : str
            '0' for long JSON and '1' for short_version.
        """
        # Download territorial_units if needed
        if self._t_units is None:
            if self._db_enabled:
                # Try to read from local database
                self._t_units = ReadPostgresql(
                    self._site,
                    self._db_enabled,
                    self._db_user,
                    self._db_pw,
                    self._db_host,
                    self._db_port,
                    self._db_name,
                    self._db_schema_import,
                    self._db_schema_vn,
                    self._db_group,
                    self._db_out_proj,
                ).read("territorial_units")
            if (self._t_units is None) or (len(self._t_units) == 0):
                # No territorial_units available, read from API
                self._t_units = [
                    [tu]
                    for tu in TerritorialUnitsAPI(
                        user_email=self._user_email,
                        user_pw=self._user_pw,
                        base_url=self._base_url,
                        client_key=self._client_key,
                        client_secret=self._client_secret,
                        max_retry=self._max_retry,
                        max_requests=self._max_requests,
                        max_chunks=self._max_chunks,
                        unavailable_delay=self._unavailable_delay,
                        retry_delay=self._retry_delay,
                    ).api_list()["data"]
                ]

        # GET from API
        logger.debug(
            _("Getting observations from controler %s, using API search"),
            self._api_instance.controler,
        )
        if id_taxo_group is None:
            taxo_groups = TaxoGroupsAPI(
                user_email=self._user_email,
                user_pw=self._user_pw,
                base_url=self._base_url,
                client_key=self._client_key,
                client_secret=self._client_secret,
                max_retry=self._max_retry,
                max_requests=self._max_requests,
                max_chunks=self._max_chunks,
                unavailable_delay=self._unavailable_delay,
                retry_delay=self._retry_delay,
            ).api_list()["data"]
        else:
            taxo_groups = [{"id": id_taxo_group, "access_mode": "full"}]
        try:
            for taxo in taxo_groups:
                if taxo["access_mode"] != "none":
                    id_taxo_group = taxo["id"]
                    logger.debug(
                        _("Getting observations from taxo_group %s"),
                        id_taxo_group,
                    )

                    # Record end of download interval
                    end_date = datetime.now() if self._end_date is None else self._end_date
                    since = self._backend.increment_get(self._site, id_taxo_group)
                    if since is None:
                        since = end_date
                    self._backend.increment_log(self._site, id_taxo_group, since)

                    # When to start download interval
                    start_date = end_date
                    min_date = datetime(1900, 1, 1) if self._start_date is None else self._start_date
                    seq = 1
                    pid = PID(
                        kp=self._pid_kp,
                        ki=self._pid_ki,
                        kd=self._pid_kd,
                        setpoint=self._pid_setpoint,
                        output_limits=(
                            self._pid_limit_min,
                            self._pid_limit_max,
                        ),
                    )
                    delta_days = self._pid_delta_days
                    while start_date > min_date:
                        nb_obs = 0
                        start_date = end_date - timedelta(days=delta_days)
                        q_param = {
                            "period_choice": "range",
                            "date_from": start_date.strftime("%d.%m.%Y"),
                            "date_to": end_date.strftime("%d.%m.%Y"),
                            "species_choice": "all",
                            "taxonomic_group": taxo["id"],
                        }
                        if self._type_date is not None:
                            if self._type_date == "entry":
                                q_param["entry_date"] = "1"
                            else:
                                q_param["entry_date"] = "0"
                        if territorial_unit_ids is None or len(territorial_unit_ids) == 0:
                            t_us = self._t_units
                        else:
                            t_us = [u for u in self._t_units if u[0]["short_name"] in territorial_unit_ids]
                        for t_u in t_us:
                            logger.debug(
                                _("Getting observations from territorial_unit %s, using API search"),
                                t_u[0]["name"],
                            )
                            q_param["location_choice"] = "territorial_unit"
                            q_param["territorial_unit_ids"] = [t_u[0]["id_country"] + t_u[0]["short_name"]]

                            timing = perf_counter_ns()
                            items_dict = self._api_instance.api_search(q_param, short_version=short_version)
                            timing = (perf_counter_ns() - timing) / 1000

                            # Call backend to store results
                            nb_o = self._backend.store(
                                self._api_instance.controler,
                                str(id_taxo_group)
                                + "_"
                                + t_u[0]["id_country"]
                                + t_u[0]["short_name"]
                                + "_"
                                + str(seq),
                                items_dict,
                            )
                            # Throttle on max size downloaded during each interval
                            nb_obs = max(nb_o, nb_obs)
                            log_msg = _(
                                "{} => Iter: {}, {} obs, taxo_group: {}, territorial_unit: {}, date: {}, interval: {}"
                            ).format(
                                self._site,
                                seq,
                                nb_o,
                                id_taxo_group,
                                t_u[0]["id_country"] + t_u[0]["short_name"],
                                start_date.strftime("%d/%m/%Y"),
                                str(delta_days),
                            )
                            # Call backend to store log
                            self._backend.log(
                                self._site,
                                self._api_instance.controler,
                                self._api_instance.transfer_errors,
                                self._api_instance.http_status,
                                log_msg,
                                total_size(items_dict),
                                timing,
                            )
                            logger.info(log_msg)
                        seq += 1
                        end_date = start_date
                        delta_days = int(pid(nb_obs))
        except HTTPError:
            self._backend.log(
                self._site,
                self._api_instance.controler,
                self._api_instance.transfer_errors,
                self._api_instance.http_status,
                _("HTTP error during download"),
            )

        return None

    def _list_taxo_groups(self, id_taxo_group, taxo_groups_ex=None):
        """Return the list of enabled taxo_groups."""
        if id_taxo_group is None:
            # Get all active taxo_groups
            taxo_groups = TaxoGroupsAPI(
                user_email=self._user_email,
                user_pw=self._user_pw,
                base_url=self._base_url,
                client_key=self._client_key,
                client_secret=self._client_secret,
                max_retry=self._max_retry,
                max_requests=self._max_requests,
                max_chunks=self._max_chunks,
                unavailable_delay=self._unavailable_delay,
                retry_delay=self._retry_delay,
            ).api_list()
            taxo_list = []
            for taxo in taxo_groups["data"]:
                if (taxo["name_constant"] not in taxo_groups_ex) and (taxo["access_mode"] != "none"):
                    logger.debug(
                        _("Starting to download observations from taxo_group %s: %s"),
                        taxo["id"],
                        taxo["name"],
                    )
                    taxo_list.append(taxo["id"])
        else:
            # Select list of taxo_group or only 1 taxo_group given as parameter
            taxo_list = id_taxo_group if isinstance(id_taxo_group, list) else [id_taxo_group]

        return taxo_list

    def store(
        self,
        id_taxo_group=None,
        by_specie=False,
        method="search",
        taxo_groups_ex=None,
        territorial_unit_ids=None,
        short_version="1",
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
            API used to download, only 'search'.
        taxo_groups_ex : list
            List of taxo_groups to exclude from storage.
        territorial_unit_ids : list
            List of territorial_units to include in storage.
        short_version : str
            '0' for long JSON and '1' for short_version.
        """
        # Get the list of taxo groups to process
        taxo_list = self._list_taxo_groups(id_taxo_group, taxo_groups_ex)
        logger.info(
            _("%s => Downloading taxo_groups: %s, territorial_units: %s"),
            self._site,
            taxo_list,
            territorial_unit_ids,
        )

        if method == "search":
            for taxo in taxo_list:
                self._store_search(taxo, territorial_unit_ids, short_version=short_version)
        elif method == "list":
            logger.warning(_("Download using list method is deprecated. Please use search method only"))
            for taxo in taxo_list:
                self._store_list(taxo, by_specie=by_specie, short_version=short_version)
        else:
            raise NotImplementedException

        return None

    def update(self, id_taxo_group=None, since=None, taxo_groups_ex=None, short_version="1"):
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
        taxo_groups_ex : list
            List of taxo_groups to exclude from storage.
        short_version : str
            '0' for long JSON and '1' for short_version.
        """
        # GET from API
        logger.debug(
            _("Getting updated observations from controler %s"),
            self._api_instance.controler,
        )

        # Get the list of taxo groups to process
        taxo_list = self._list_taxo_groups(id_taxo_group, taxo_groups_ex)
        logger.info(_("Downloaded taxo_groups: %s"), taxo_list)

        for taxo in taxo_list:
            updated = []
            deleted = []
            if since is None:
                since = self._backend.increment_get(self._site, taxo)
            if since is not None:
                # Valid since date provided or found in database
                self._backend.increment_log(self._site, taxo, datetime.now())
                logger.info(_("Getting updates for taxo_group %s since %s"), taxo, since)
                items_dict = self._api_instance.api_diff(taxo, since, modification_type="all")

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
                logger.error(_("No date found for last download, increment not performed"))

            # Process updates
            try:
                if len(updated) > 0:
                    logger.debug(_("Creating or updating %d observations"), len(updated))
                    # Update backend store, in chunks
                    for i in range((len(updated) + self._max_list_length - 1) // self._max_list_length):
                        s_list = ",".join(updated[i * self._max_list_length : (i + 1) * self._max_list_length])
                        logger.debug(_("Updating slice %s"), s_list)
                        timing = perf_counter_ns()
                        items_dict = self._api_instance.api_list(
                            taxo,
                            id_sightings_list=s_list,
                            short_version=short_version,
                        )
                        timing = (perf_counter_ns() - timing) / 1000

                        # Call backend to store results
                        self._backend.store(
                            self._api_instance.controler,
                            str(id_taxo_group) + "_upd_" + str(i),
                            items_dict,
                        )

                        # Call backend to store log
                        self._backend.log(
                            self._site,
                            self._api_instance.controler,
                            self._api_instance.transfer_errors,
                            self._api_instance.http_status,
                            _("Creating or updating %d observations") % (s_list.count(",") + 1),
                            total_size(items_dict),
                            timing,
                        )
            except HTTPError:
                self._backend.log(
                    self._site,
                    self._api_instance.controler,
                    self._api_instance.transfer_errors,
                    self._api_instance.http_status,
                    _("HTTP error during download"),
                )

            # Process deletes
            if len(deleted) > 0:
                self._backend.delete_obs(deleted)

        return None


class Observers(DownloadVn):
    """Implement store from observers controler.

    Methods
    - store               - Download and store to json

    """

    def __init__(
        self,
        site: str,
        user_email: str,
        user_pw: str,
        base_url: str,
        client_key: str,
        client_secret: str,
        backend: Callable[..., None],
        max_retry: int = 5,
        max_requests: int = 0,
        max_chunks: int = 100,
        unavailable_delay: int = 600,
        retry_delay: int = 5,
    ) -> None:
        super().__init__(
            site,
            ObserversAPI(
                user_email=user_email,
                user_pw=user_pw,
                base_url=base_url,
                client_key=client_key,
                client_secret=client_secret,
                max_retry=max_retry,
                max_requests=max_requests,
                max_chunks=max_chunks,
                unavailable_delay=unavailable_delay,
                retry_delay=retry_delay,
            ),
            backend,
        )


class Places(DownloadVn):
    """Implement store from places controler.

    Methods
    - store               - Download and store to json
    - update              - Retrieve list of updates, then and update or delete places

    """

    def __init__(
        self,
        site: str,
        user_email: str,
        user_pw: str,
        base_url: str,
        client_key: str,
        client_secret: str,
        backend: Callable[..., None],
        db_enabled: bool = False,
        max_retry: int = 5,
        max_requests: int = 0,
        max_chunks: int = 100,
        unavailable_delay: int = 600,
        retry_delay: int = 5,
    ) -> None:
        self._user_email = user_email
        self._user_pw = user_pw
        self._base_url = base_url
        self._client_key = client_key
        self._client_secret = client_secret
        self._max_retry = max_retry
        self._max_requests = max_requests
        self._max_chunks = max_chunks
        self._unavailable_delay = unavailable_delay
        self._retry_delay = retry_delay
        self._db_enabled = db_enabled
        self._place_id = -1  # Integer index, to comply with taxo_groups, for increment log
        self._l_a_units = None
        super().__init__(
            site,
            PlacesAPI(
                user_email=user_email,
                user_pw=user_pw,
                base_url=base_url,
                client_key=client_key,
                client_secret=client_secret,
                max_retry=max_retry,
                max_requests=max_requests,
                max_chunks=max_chunks,
                unavailable_delay=unavailable_delay,
                retry_delay=retry_delay,
            ),
            backend,
        )

    def store(
        self,
        territorial_unit_ids=None,
    ):
        """Download from VN by API and store json to backend.

        Overloads base method to add territorial_unit filter

        Parameters
        ----------
        territorial_unit_ids : list
            List of territorial_units to include in storage.
        """
        logger.info(_("Getting local_admin_units, before getting places"))
        # Get local_admin_units if needed
        if self._l_a_units is None:
            if self._db_enabled:
                # Try to read from local database
                self._l_a_units = ReadPostgresql(
                    self._site,
                    self._db_enabled,
                    self._db_user,
                    self._db_pw,
                    self._db_host,
                    self._db_port,
                    self._db_name,
                    self._db_schema_import,
                    self._db_schema_vn,
                    self._db_group,
                    self._db_out_proj,
                ).read("local_admin_units")
            if (self._l_a_units is None) or (len(self._l_a_units) == 0):
                # No local_admin_units available, read from API
                self._l_a_units = [
                    LocalAdminUnitsAPI(
                        user_email=self._user_email,
                        user_pw=self._user_pw,
                        base_url=self._base_url,
                        client_key=self._client_key,
                        client_secret=self._client_secret,
                        max_retry=self._max_retry,
                        max_requests=self._max_requests,
                        max_chunks=self._max_chunks,
                        unavailable_delay=self._unavailable_delay,
                        retry_delay=self._retry_delay,
                    ).api_list()["data"]
                ]

        self._backend.increment_log(self._site, self._place_id, datetime.now())
        if territorial_unit_ids is not None and len(territorial_unit_ids) > 0:
            # Get local_admin_units
            for id_canton in territorial_unit_ids:
                # Loop on local_admin_units of the territorial_unit
                for l_a_u in self._l_a_units[0]:
                    if l_a_u["id_canton"] == id_canton:
                        logger.info(
                            _("Getting places from id_canton %s, id_commune %s, using API list"),
                            id_canton,
                            l_a_u["id"],
                        )
                        q_param = {"id_commune": l_a_u["id"], "get_hidden": "1"}
                        super().store([q_param])
        else:
            for l_a_u in self._l_a_units:
                logger.info(
                    _("Getting places from id_commune %s, using API list"),
                    l_a_u[0]["id"],
                )
                q_param = {"id_commune": l_a_u[0]["id"], "get_hidden": "1"}
                super().store([q_param])

    def update(self, territorial_unit_ids=None, since=None):
        """Download increment from VN by API and store json to file.

        Gets previous update date from database and updates since then.
        Calls  biolovision_api, finds if update or delete.
        If update, get full place and store to db.
        If delete, delete from db.

        Parameters
        ----------
        territorial_unit_ids : str or None
            If not None, territorial_unit to be downloaded.
        since : str or None
            If None, updates since last download
            Or if provided, updates since that given date.

        """
        updated = []
        deleted = []
        if since is None:
            since = self._backend.increment_get(self._site, self._place_id)
        if since is not None:
            # Valid since date provided or found in database
            self._backend.increment_log(self._site, self._place_id, datetime.now())
            logger.info(_("Getting updates for places since %s"), since)
            items_dict = self._api_instance.api_diff(since, modification_type="all")

            # List by processing type
            for item in items_dict:
                logger.debug(
                    _("Place %s was %s"),
                    item["id_place"],
                    item["modification_type"],
                )
                if item["modification_type"] == "updated":
                    updated.append(item["id_place"])
                elif item["modification_type"] == "deleted":
                    deleted.append(item["id_place"])
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
            logger.error(_("No date found for last download, increment not performed"))

        # Process updates
        if len(updated) > 0:
            logger.debug(_("Creating or updating %d places"), len(updated))
            # Update backend store, in chunks
            for i in range(len(updated)):
                logger.debug(_("Updating place %s"), updated[i])
                timing = perf_counter_ns()
                items_dict = self._api_instance.api_get(updated[i])
                timing = (perf_counter_ns() - timing) / 1000

                # Call backend to store results
                self._backend.store(
                    self._api_instance.controler,
                    "upd_" + str(i),
                    items_dict,
                )

                # Call backend to store log
                self._backend.log(
                    self._site,
                    self._api_instance.controler,
                    self._api_instance.transfer_errors,
                    self._api_instance.http_status,
                    _("Creating or updating 1 place"),
                    total_size(items_dict),
                    timing,
                )

        # Process deletes
        if len(deleted) > 0:
            self._backend.delete_place(deleted)


class Species(DownloadVn):
    """Implement store from species controler.

    Methods
    - store               - Download and store to json

    """

    def __init__(
        self,
        site: str,
        user_email: str,
        user_pw: str,
        base_url: str,
        client_key: str,
        client_secret: str,
        backend: Callable[..., None],
        max_retry: int = 5,
        max_requests: int = 0,
        max_chunks: int = 100,
        unavailable_delay: int = 600,
        retry_delay: int = 5,
    ) -> None:
        self._user_email = user_email
        self._user_pw = user_pw
        self._base_url = base_url
        self._client_key = client_key
        self._client_secret = client_secret
        self._max_retry = max_retry
        self._max_requests = max_requests
        self._max_chunks = max_chunks
        self._unavailable_delay = unavailable_delay
        self._retry_delay = retry_delay

        super().__init__(
            site,
            SpeciesAPI(
                user_email=user_email,
                user_pw=user_pw,
                base_url=base_url,
                client_key=client_key,
                client_secret=client_secret,
                max_retry=max_retry,
                max_requests=max_requests,
                max_chunks=max_chunks,
                unavailable_delay=unavailable_delay,
                retry_delay=retry_delay,
            ),
            backend,
        )

    def store(self):
        """Store species, iterating over taxo_groups"""
        taxo_groups = TaxoGroupsAPI(
            user_email=self._user_email,
            user_pw=self._user_pw,
            base_url=self._base_url,
            client_key=self._client_key,
            client_secret=self._client_secret,
            max_retry=self._max_retry,
            max_requests=self._max_requests,
            max_chunks=self._max_chunks,
            unavailable_delay=self._unavailable_delay,
            retry_delay=self._retry_delay,
        ).api_list()
        taxo_list = []
        for taxo in taxo_groups["data"]:
            if taxo["access_mode"] != "none":
                logger.debug(_("Storing species from taxo_group %s"), taxo["id"])
                taxo_list.append({"id_taxo_group": taxo["id"]})
        super().store(iter(taxo_list))

        return None


class TaxoGroup(DownloadVn):
    """Implement store from taxo_groups controler.

    Methods
    - store               - Download and store to json

    """

    def __init__(
        self,
        site: str,
        user_email: str,
        user_pw: str,
        base_url: str,
        client_key: str,
        client_secret: str,
        backend: Callable[..., None],
        max_retry: int = 5,
        max_requests: int = 0,
        max_chunks: int = 100,
        unavailable_delay: int = 600,
        retry_delay: int = 5,
    ) -> None:
        super().__init__(
            site,
            TaxoGroupsAPI(
                user_email=user_email,
                user_pw=user_pw,
                base_url=base_url,
                client_key=client_key,
                client_secret=client_secret,
                max_retry=max_retry,
                max_requests=max_requests,
                max_chunks=max_chunks,
                unavailable_delay=unavailable_delay,
                retry_delay=retry_delay,
            ),
            backend,
        )


class TerritorialUnits(DownloadVn):
    """Implement store from territorial_units controler.

    Methods
    - store               - Download and store to json

    """

    def __init__(
        self,
        site: str,
        user_email: str,
        user_pw: str,
        base_url: str,
        client_key: str,
        client_secret: str,
        backend: Callable[..., None],
        max_retry: int = 5,
        max_requests: int = 0,
        max_chunks: int = 100,
        unavailable_delay: int = 600,
        retry_delay: int = 5,
    ) -> None:
        super().__init__(
            site,
            TerritorialUnitsAPI(
                user_email=user_email,
                user_pw=user_pw,
                base_url=base_url,
                client_key=client_key,
                client_secret=client_secret,
                max_retry=max_retry,
                max_requests=max_requests,
                max_chunks=max_chunks,
                unavailable_delay=unavailable_delay,
                retry_delay=retry_delay,
            ),
            backend,
        )


class Validations(DownloadVn):
    """Implement store from validations controler.

    Methods
    - store               - Download and store to json

    """

    def __init__(
        self,
        site: str,
        user_email: str,
        user_pw: str,
        base_url: str,
        client_key: str,
        client_secret: str,
        backend: Callable[..., None],
        max_retry: int = 5,
        max_requests: int = 0,
        max_chunks: int = 100,
        unavailable_delay: int = 600,
        retry_delay: int = 5,
    ) -> None:
        super().__init__(
            site,
            ValidationsAPI(
                user_email=user_email,
                user_pw=user_pw,
                base_url=base_url,
                client_key=client_key,
                client_secret=client_secret,
                max_retry=max_retry,
                max_requests=max_requests,
                max_chunks=max_chunks,
                unavailable_delay=unavailable_delay,
                retry_delay=retry_delay,
            ),
            backend,
        )
