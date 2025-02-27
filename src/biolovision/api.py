"""Provide python interface to Biolovision API.

Methods, see each class.

Properties:

- transfer_errors            - Return number of HTTP errors

Exceptions:

- BiolovisionApiException    - General exception
- HTTPError                  - HTTP protocol error
- MaxChunksError             - Too many chunks returned from API calls
- IncorrectParameter         - Incorrect or missing parameter

"""

import json
import logging
import re
import time
from functools import lru_cache
from urllib import parse

import requests
from requests_oauthlib import OAuth1

from . import __version__


class HashableDict(dict):
    """Provide hashable dict type, to enable @lru_cache."""

    def __hash__(self):
        return hash(frozenset(self))


class BiolovisionApiException(Exception):
    """An exception occurred while handling your request."""


class HTTPError(BiolovisionApiException):
    """An HTTP error occurred."""


class MaxChunksError(BiolovisionApiException):
    """Too many chunks returned from API calls."""


class NotImplementedException(BiolovisionApiException):
    """Feature not implemented."""


class IncorrectParameter(BiolovisionApiException):
    """Incorrect or missing parameter."""


class BiolovisionAPI:
    """Top class, not for direct use. Provides internal and template methods."""

    def __init__(
        self,
        controler: str = "",
        user_email: str | None = None,
        user_pw: str | None = None,
        base_url: str | None = None,
        client_key: str | None = None,
        client_secret: str | None = None,
        max_retry: int | None = None,
        max_requests: int | None = None,
        max_chunks: int | None = None,
        unavailable_delay: int | None = None,
        retry_delay: int | None = None,
        timeout: int | None = None,
    ) -> None:
        logger = logging.getLogger(__name__)
        self._logger = logger
        logger.info(_("Initializing API"))
        if controler == "":
            logger.fatal(_("controler must be defined"))
            raise BiolovisionApiException
        else:
            self._ctrl = controler
        if user_email is None:
            logger.fatal(_("user_email must be defined"))
            raise BiolovisionApiException
        else:
            self._user_email = user_email
        if user_pw is None:
            logger.fatal(_("user_pw must be defined"))
            raise BiolovisionApiException
        else:
            self._user_pw = user_pw
        if base_url is None:
            logger.fatal(_("base_url must be defined"))
            raise BiolovisionApiException
        if client_key is None:
            logger.fatal(_("client_key must be defined"))
            raise BiolovisionApiException
        if client_secret is None:
            logger.fatal(_("client_secret must be defined"))
            raise BiolovisionApiException
        if max_retry is None:
            max_retry = 5
        if max_requests is None:
            max_requests = 0
        if max_chunks is None:
            max_chunks = 50
        if unavailable_delay is None:
            unavailable_delay = 600
        if retry_delay is None:
            retry_delay = 5
        self._limits = {
            "max_retry": max_retry,
            "max_requests": max_requests,
            "max_chunks": max_chunks,
            "unavailable_delay": unavailable_delay,
            "retry_delay": retry_delay,
            "timeout": timeout,
        }
        self._transfer_errors = 0
        self._http_status = 0

        # Using OAuth1 auth helper to get access
        self._api_url = base_url + "api/"  # URL of API
        self._oauth = OAuth1(client_key, client_secret=client_secret)

    @property
    def version(self) -> str:
        """Return version."""
        return __version__

    @property
    def transfer_errors(self) -> int:
        """Return the number of HTTP errors during this session."""
        return self._transfer_errors

    @property
    def http_status(self) -> str:
        """Return the latest HTTP status code."""
        return self._http_status

    @property
    def controler(self) -> str:
        """Return the controler name."""
        return self._ctrl

    # ----------------
    # Internal methods
    # ----------------
    @staticmethod
    def _clean_params(params: dict):
        """Remove sensitive data from param dict."""
        c_params = params.copy()
        c_params["user_email"] = "***"
        c_params["user_pw"] = "***"
        return c_params

    def _url_get(self, params, scope, method="GET", body=None, optional_headers=None):
        """Internal function used to request from Biolovision API.

        Prepare the URL header, perform HTTP request and get json content.
        Test HTTP status and returns None if error, else return decoded json content.
        Increments _transfer_errors in case of error.

        Parameters
        ----------
        params : dict of 'parameter name': 'parameter value'
            params is used to build URL GET string.
        scope : str
            scope is the api to be queried, for example 'taxo_groups/'.
        method : str
            HTTP method to use: GET/POST/DELETE/PUT. Default to GET
        body : str
            Optional body for POST or PUT
        optional_headers : dict
            Optional body for request

        Returns
        -------
        json : dict
            dict decoded from json if status OK, else None.

        Raises
        ------
        HTTPError
            HTTP protocol error, returned as argument.
        MaxChunksError
            Loop on chunks exceeded max_chunks limit.

        """
        # Loop on chunks
        nb_chunks = 0
        data_rec = None
        while nb_chunks < self._limits["max_chunks"]:
            # Remove DEBUG logging level to avoid too many details
            level = logging.getLogger().level
            logging.getLogger().setLevel(logging.INFO)

            # Prepare call to API
            payload = parse.urlencode(params, quote_via=parse.quote)
            self._logger.debug(
                _("Params: %s"),
                re.sub(
                    r"user_pw=.*?(&|$)(.*)",
                    r"user_pw=***\1\2",
                    re.sub(r"user_email=.*?(&|$)(.*)", r"user_email=***\1\2", payload),
                ),
            )
            headers = {"Content-Type": "application/json;charset=UTF-8"}
            if optional_headers is not None:
                headers.update(optional_headers)
            protected_url = self._api_url + scope
            if method == "GET":
                resp = requests.get(
                    url=protected_url,
                    auth=self._oauth,
                    params=payload,
                    headers=headers,
                    timeout=self._limits["timeout"],
                )
            elif method == "POST":
                resp = requests.post(
                    url=protected_url,
                    auth=self._oauth,
                    params=payload,
                    headers=headers,
                    data=body,
                    timeout=self._limits["timeout"],
                )
            elif method == "PUT":
                resp = requests.put(
                    url=protected_url,
                    auth=self._oauth,
                    params=payload,
                    headers=headers,
                    data=body,
                    timeout=self._limits["timeout"],
                )
            elif method == "DELETE":
                resp = requests.delete(
                    url=protected_url,
                    auth=self._oauth,
                    params=payload,
                    headers=headers,
                    timeout=self._limits["timeout"],
                )
            else:
                raise NotImplementedException

            self._logger.debug(resp.headers)
            logging.getLogger().setLevel(level)
            self._logger.debug(
                _("%s status code = %s, for URL %s"),
                method,
                resp.status_code,
                protected_url,
            )
            self._http_status = resp.status_code
            if self._http_status >= 300:
                # Request returned an error.
                # Logging and checking if not too many errors to continue
                self._logger.error(
                    _("%s status code: %s, text: %s, for URL %s"),
                    method,
                    resp.status_code,
                    resp.text,
                    protected_url,
                )

                if (self._http_status >= 400) and (self._http_status <= 499):  # pragma: no cover
                    # Unreceverable error
                    self._logger.error(resp)
                    self._logger.critical(
                        _("Unreceverable error %s, raising exception"),
                        self._http_status,
                    )
                    raise HTTPError(resp.status_code)
                self._transfer_errors += 1  # pragma: no cover
                if self._http_status == 503:  # pragma: no cover
                    # Service unavailable: long wait
                    time.sleep(self._limits["unavailable_delay"])
                else:
                    # A transient error: short wait
                    time.sleep(self._limits["retry_delay"])

                if self._transfer_errors > self._limits["max_retry"]:  # pragma: no cover
                    # Too many retries. Raising exception
                    self._logger.critical(_("Too many error %s, raising exception"), self._transfer_errors)
                    raise HTTPError(resp.status_code)
            else:
                # No error from request: processing response if needed
                # Resetting error count after successful transfer
                self._transfer_errors = 0
                if method in ["PUT", "DELETE"]:
                    # No response expected
                    resp_chunk = json.loads("{}")
                else:
                    try:
                        self._logger.debug(_("Response content: %s, text: %s"), resp, resp.text[:1000])
                        # TWEAK: remove extra text outside JSON response
                        if len(resp.text) > 1:
                            rsp = re.findall(r"([\[{].*[}\]])", resp.text)
                            resp_chunk = json.loads(rsp[0]) if len(rsp) > 0 else {}
                        else:
                            resp_chunk = resp.json("{}")
                    except json.decoder.JSONDecodeError:  # pragma: no cover
                        # Error during JSON decoding =>
                        # Logging error and no further processing of empty chunk
                        resp_chunk = json.loads("{}")
                        self._logger.exception(_("Incorrect response content: %s"), resp)
                    except Exception:
                        self._logger.exception(_("Response text causing exception: %s"), resp.text)
                        raise

                # Initialize or append to response dict, depending on content
                if "data" in resp_chunk:
                    observations = False
                    if "sightings" in resp_chunk["data"]:
                        observations = True
                        self._logger.debug(
                            _("Received %d sightings in chunk %d"),
                            len(resp_chunk["data"]["sightings"]),
                            nb_chunks,
                        )
                        if nb_chunks == 0:
                            data_rec = resp_chunk
                        else:
                            if "sightings" in data_rec["data"]:
                                data_rec["data"]["sightings"] += resp_chunk["data"]["sightings"]
                            else:
                                # self._logger.error(_("No 'sightings' in previous data"))
                                # self._logger.error(data_rec)
                                # self._logger.error(resp_chunk)
                                data_rec["data"]["sightings"] = resp_chunk["data"]["sightings"]
                    if "forms" in resp_chunk["data"]:
                        observations = True
                        self._logger.debug(
                            _("Received %d forms in chunk %d"),
                            len(resp_chunk["data"]["forms"]),
                            nb_chunks,
                        )
                        if nb_chunks == 0:
                            data_rec = resp_chunk
                        else:
                            if "forms" in data_rec["data"]:
                                data_rec["data"]["forms"] += resp_chunk["data"]["forms"]
                            else:  # pragma: no cover
                                # self._logger.error(
                                #     _("Trying to add 'forms' to another data stream")
                                # )
                                # self._logger.error(data_rec)
                                # self._logger.error(resp_chunk)
                                data_rec["data"]["forms"] = resp_chunk["data"]["forms"]

                    if not observations:
                        self._logger.debug(
                            _("Received %d data items in chunk %d"),
                            len(resp_chunk),
                            nb_chunks,
                        )
                        if nb_chunks == 0:
                            data_rec = resp_chunk
                        else:
                            data_rec["data"] += resp_chunk["data"]
                else:
                    self._logger.debug(_("Received non-data response: %s"), resp_chunk)
                    if nb_chunks == 0:
                        data_rec = resp_chunk
                    else:
                        data_rec += resp_chunk

                # Is there more data to come?
                if (
                    ("transfer-encoding" in resp.headers)
                    and (resp.headers["transfer-encoding"] == "chunked")
                    and ("pagination_key" in resp.headers)
                ):
                    self._logger.debug(
                        _("Chunked transfer => requesting for more, with key: %s"),
                        resp.headers["pagination_key"],
                    )
                    # Update request parameters to get next chunk
                    params["pagination_key"] = resp.headers["pagination_key"]
                    nb_chunks += 1
                else:
                    self._logger.debug(_("Non-chunked transfer => finished requests"))
                    if "pagination_key" in params:
                        del params["pagination_key"]
                    break

        self._logger.debug(_("Received %d chunks"), nb_chunks)
        if nb_chunks >= self._limits["max_chunks"]:
            raise MaxChunksError

        return data_rec

    def _api_list(self, opt_params=None, optional_headers=None):
        """Query for a list of entities of the given controler.

        Calls /ctrl API.

        Parameters
        ----------
        opt_params : HashableDict (to enable lru_cache)
            optional URL parameters, empty by default.
            See Biolovision API documentation.
        optional_headers : dict
            Optional body for GET request

        Returns
        -------
        json : dict or None
            dict decoded from json if status OK, else None
        """
        # Mandatory parameters.
        params = {
            "user_email": self._user_email,
            "user_pw": self._user_pw,
        }
        if opt_params is not None:
            params.update(opt_params)
        self._logger.debug(
            _("List from: %s, with options:%s, optional_headers:%s"),
            self._ctrl,
            self._clean_params(params),
            optional_headers,
        )
        # GET from API
        entities = self._url_get(params, self._ctrl, optional_headers=optional_headers)["data"]
        self._logger.debug(_("Number of entities = %i"), len(entities))
        return {"data": entities}

    # -----------------------------------------
    #  Generic methods, used by most subclasses
    # -----------------------------------------

    def api_get(self, id_entity, **kwargs):
        """Query for a single entity of the given controler.

        Calls  /ctrl/id API.

        Parameters
        ----------
        id_entity : str
            entity to retrieve.
        **kwargs :
            optional URL parameters, empty by default.
            See Biolovision API documentation.

        Returns
        -------
        json : dict or None
            dict decoded from json if status OK, else None
        """
        # Mandatory parameters.
        params = {
            "user_email": self._user_email,
            "user_pw": self._user_pw,
        }
        for key, value in kwargs.items():
            params[key] = value
        self._logger.debug(
            _("In api_get for controler: %s, entity: %s, with parameters:%s"),
            self._ctrl,
            id_entity,
            self._clean_params(params),
        )
        # GET from API
        return self._url_get(params, self._ctrl + "/" + str(id_entity))

    def api_list(self, opt_params=None, optional_headers=None):
        """Query for a list of entities of the given controler.

        Calls /ctrl API.

        Parameters
        ----------
        opt_params : dict
            optional URL parameters, empty by default.
            See Biolovision API documentation.
        optional_headers : dict
            Optional body for GET request

        Returns
        -------
        json : dict or None
            dict decoded from json if status OK, else None
        """
        h_params = None if opt_params is None else HashableDict(opt_params)
        h_headers = None if optional_headers is None else HashableDict(optional_headers)
        self._logger.debug(
            _("In api_list for controler: %s, header: %s, with parameters:%s"),
            self._ctrl,
            h_headers,
            h_params,
        )
        return self._api_list(opt_params=h_params, optional_headers=h_headers)

    # -------------------------
    # Exception testing methods
    # -------------------------
    def wrong_api(self):
        """Query for a wrong api.

        Calls /error API to raise an exception.

        """
        # Mandatory parameters.
        params = {
            "user_email": self._user_email,
            "user_pw": self._user_pw,
        }
        # GET from API
        return self._url_get(params, "error/")


class EntitiesAPI(BiolovisionAPI):
    """Implement api calls to entities controler.

    Methods:

    - api_get                - Return a single entity from the controler

    - api_list               - Return a list of entity from the controler

    """

    def __init__(
        self,
        user_email: str | None = None,
        user_pw: str | None = None,
        base_url: str | None = None,
        client_key: str | None = None,
        client_secret: str | None = None,
        max_retry: int | None = None,
        max_requests: int | None = None,
        max_chunks: int | None = None,
        unavailable_delay: int | None = None,
        retry_delay: int | None = None,
    ) -> None:
        super().__init__(
            controler="entities",
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
        )
        return None


class FamiliesAPI(BiolovisionAPI):
    """Implement api calls to families controler.

    Methods:

    - api_get                - Return a single entity from the controler

    - api_list               - Return a list of entity from the controler

    """

    def __init__(
        self,
        user_email: str | None = None,
        user_pw: str | None = None,
        base_url: str | None = None,
        client_key: str | None = None,
        client_secret: str | None = None,
        max_retry: int | None = None,
        max_requests: int | None = None,
        max_chunks: int | None = None,
        unavailable_delay: int | None = None,
        retry_delay: int | None = None,
    ) -> None:
        super().__init__(
            controler="families",
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
        )
        return None


class FieldsAPI(BiolovisionAPI):
    """Implement api calls to fields controler.

    Methods:

    - api_get                - Return a single entity from the controler

    - api_list               - Return a list of entity from the controler

    """

    def __init__(
        self,
        user_email: str | None = None,
        user_pw: str | None = None,
        base_url: str | None = None,
        client_key: str | None = None,
        client_secret: str | None = None,
        max_retry: int | None = None,
        max_requests: int | None = None,
        max_chunks: int | None = None,
        unavailable_delay: int | None = None,
        retry_delay: int | None = None,
    ) -> None:
        super().__init__(
            controler="fields",
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
        )
        return None


class LocalAdminUnitsAPI(BiolovisionAPI):
    """Implement api calls to local_admin_units controler.

    Methods:

    - api_get                - Return a single entity from the controler

    - api_list               - Return a list of entity from the controler

    """

    def __init__(
        self,
        user_email: str | None = None,
        user_pw: str | None = None,
        base_url: str | None = None,
        client_key: str | None = None,
        client_secret: str | None = None,
        max_retry: int | None = None,
        max_requests: int | None = None,
        max_chunks: int | None = None,
        unavailable_delay: int | None = None,
        retry_delay: int | None = None,
    ) -> None:
        super().__init__(
            controler="local_admin_units",
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
        )


class ObservationsAPI(BiolovisionAPI):
    """Implement api calls to observations controler.

    Methods:

    - api_get         - Return a single observations from the controler

    - api_list        - Return a list of observations from the controler

    - api_diff        - Deprecated: Return all changes in observations since a given date

    - api_search      - Search for observations based on parameter value

    - api_create      - Create a single observation

    - api_update      - Update an existing observation

    - api_delete      - Delete an observation

    - api_delete_list - Delete a list/form

    """

    def __init__(
        self,
        user_email: str | None = None,
        user_pw: str | None = None,
        base_url: str | None = None,
        client_key: str | None = None,
        client_secret: str | None = None,
        max_retry: int | None = None,
        max_requests: int | None = None,
        max_chunks: int | None = None,
        unavailable_delay: int | None = None,
        retry_delay: int | None = None,
    ) -> None:
        super().__init__(
            controler="observations",
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
        )
        return None

    def api_list(self, id_taxo_group, **kwargs):
        """Query for list of observations by taxo_group from the controler.

        Calls  /observations API.

        Parameters
        ----------
        id_taxo_group : integer
            taxo_group to query for observations
        **kwargs :
            optional URL parameters, empty by default.
            See Biolovision API documentation.

        Returns
        -------
        json : dict or None
            dict decoded from json if status OK, else None
        """
        opt_params = {}
        opt_params["id_taxo_group"] = str(id_taxo_group)
        for key, value in kwargs.items():
            opt_params[key] = value
        self._logger.debug(_("In api_list, with parameters %s"), opt_params)
        return super().api_list(opt_params)

    def api_diff(self, id_taxo_group, delta_time, modification_type="all"):
        """Query for a list of updates or deletions since a given date.

        Calls /observations/diff to get list of created/updated or deleted
        observations since a given date (max 10 weeks backward).

        Parameters
        ----------
        id_taxo_group : str
            taxo group from which to query diff.
        delta_time : str
            Start of time interval to query.
        modification_type : str
            Type of diff queried : can be only_modified, only_deleted or
            all (default).

        Returns
        -------
        json : dict or None
            dict decoded from json if status OK, else None
        """
        # Mandatory parameters.
        params = {
            "user_email": self._user_email,
            "user_pw": self._user_pw,
        }
        # Specific parameters.
        params["id_taxo_group"] = str(id_taxo_group)
        params["modification_type"] = modification_type
        params["date"] = delta_time
        # GET from API
        return super()._url_get(params, "observations/diff/")

    def api_search(self, q_params, **kwargs):
        """Search for observations, based on parameter conditions.

        Calls /observations/search to get observations
        same parameters than in online version can be used

        Parameters
        ----------
        q_params : dict
            Query parameters, same as online version.
        **kwargs :
            optional URL parameters, empty by default.
            See Biolovision API documentation.

        Returns
        -------
        json : dict or None
            dict decoded from json if status OK, else None
        """
        # Mandatory parameters.
        params = {
            "user_email": self._user_email,
            "user_pw": self._user_pw,
        }
        for key, value in kwargs.items():
            params[key] = value
        # Specific parameters.
        if q_params is not None:
            body = json.dumps(q_params)
        else:
            raise IncorrectParameter
        self._logger.debug(
            _("Search from %s, with option %s and body %s"),
            self._ctrl,
            self._clean_params(params),
            body,
        )
        # GET from API
        return super()._url_get(params, "observations/search/", "POST", body)

    def api_create(self, data: dict) -> None:
        """Create an observation.

        Calls POST on /observations to create a new observation.

        Parameters
        ----------
        data: json
            Body containing observation in JSON format
        """
        # Mandatory parameters.
        params = {
            "user_email": self._user_email,
            "user_pw": self._user_pw,
        }
        self._logger.debug(_("Create observation, with data %s"), data)
        # POST to API
        resp = super()._url_get(params, "observations/", "POST", body=json.dumps(data))
        if self._http_status == 201:
            # Successful creation
            return resp
        else:
            raise super().HTTPError(self._http_status)

    def api_update(self, obs_id: str, data: dict) -> None:
        """Update an observation.

        Calls PUT on /observations/%id% to update the observation.

        Parameters
        ----------
        obs_id: str
            Id of observation to update
        data: json
            Body containing observation in JSON format
        """
        # Mandatory parameters.
        params = {
            "user_email": self._user_email,
            "user_pw": self._user_pw,
        }
        self._logger.debug(_("Update observation %s, with data %s"), obs_id, data)
        # PUT to API
        return super()._url_get(params, "observations/" + obs_id, "PUT", body=json.dumps(data))

    def api_delete(self, obs_id: str) -> None:
        """Deleta an observation.

        Calls DELETE on /observations/%id% to delete the observation.

        Parameters
        ----------
        obs_id: str
            Id of observation to delete
        """
        # Mandatory parameters.
        params = {
            "user_email": self._user_email,
            "user_pw": self._user_pw,
        }
        self._logger.debug(_("Delete observation %s"), obs_id)
        # DELETE to API
        return super()._url_get(params, "observations/" + obs_id, "DELETE")

    def api_delete_list(self, data: dict | None = None) -> None:
        """Deleta a list/form.

        Calls POST on /observations/delete_list/%id% to delete the observation.

        Parameters
        ----------
        data: Dict
            id_form or id_form_universal to delete
        """
        # Mandatory parameters.
        params = {
            "user_email": self._user_email,
            "user_pw": self._user_pw,
        }
        self._logger.debug(_("Delete list/form %s"), json.dumps(data))
        # POST to API
        if data is not None:
            res = super()._url_get(params, "observations/delete_list", "POST", body=json.dumps(data))
        else:
            self._logger.warning(_("No parameter passed: call ignored"))
            res = None
        return res


class ObserversAPI(BiolovisionAPI):
    """Implement api calls to observers controler.

    Methods:

    - api_get                - Return a single entity from the controler

    - api_list               - Return a list of entity from the controler

    """

    def __init__(
        self,
        user_email: str | None = None,
        user_pw: str | None = None,
        base_url: str | None = None,
        client_key: str | None = None,
        client_secret: str | None = None,
        max_retry: int | None = None,
        max_requests: int | None = None,
        max_chunks: int | None = None,
        unavailable_delay: int | None = None,
        retry_delay: int | None = None,
    ) -> None:
        super().__init__(
            controler="observers",
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
        )
        return None


class PlacesAPI(BiolovisionAPI):
    """Implement api calls to places controler.

    Methods:

    - api_get                - Return a single place from the controler

    - api_list               - Return a list of places from the controler

    - api_diff               - Search for change in places

    """

    def __init__(
        self,
        user_email: str | None = None,
        user_pw: str | None = None,
        base_url: str | None = None,
        client_key: str | None = None,
        client_secret: str | None = None,
        max_retry: int | None = None,
        max_requests: int | None = None,
        max_chunks: int | None = None,
        unavailable_delay: int | None = None,
        retry_delay: int | None = None,
    ) -> None:
        super().__init__(
            controler="places",
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
        )
        return None

    def api_diff(self, delta_time, modification_type="all"):
        """Query for a list of updates or deletions since a given date.

        Calls /places/diff to get list of created/updated or deleted
        places since a given date (max 10 weeks backward).

        Parameters
        ----------
        delta_time : str
            Start of time interval to query.
        modification_type : str
            Type of diff queried : can be only_modified, only_deleted or
            all (default).

        Returns
        -------
        json : dict or None
            dict decoded from json if status OK, else None
        """
        # Mandatory parameters.
        params = {
            "user_email": self._user_email,
            "user_pw": self._user_pw,
        }
        # Specific parameters.
        params["modification_type"] = modification_type
        params["date"] = delta_time
        # GET from API
        return super()._url_get(params, "places/diff/")


class SpeciesAPI(BiolovisionAPI):
    """Implement api calls to species controler.

    Methods:

    - api_get                - Return a single specie from the controler

    - api_list               - Return a list of species from the controler

    """

    def __init__(
        self,
        user_email: str | None = None,
        user_pw: str | None = None,
        base_url: str | None = None,
        client_key: str | None = None,
        client_secret: str | None = None,
        max_retry: int | None = None,
        max_requests: int | None = None,
        max_chunks: int | None = None,
        unavailable_delay: int | None = None,
        retry_delay: int | None = None,
    ) -> None:
        super().__init__(
            controler="species",
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
        )
        return None


class TaxoGroupsAPI(BiolovisionAPI):
    """Implement api calls to taxo_groups controler.

    Methods:

    - api_get                - Return a single taxo group from the controler

    - api_list               - Return a list of taxo groups from the controler

    """

    def __init__(
        self,
        user_email: str | None = None,
        user_pw: str | None = None,
        base_url: str | None = None,
        client_key: str | None = None,
        client_secret: str | None = None,
        max_retry: int | None = None,
        max_requests: int | None = None,
        max_chunks: int | None = None,
        unavailable_delay: int | None = None,
        retry_delay: int | None = None,
    ) -> None:
        super().__init__(
            controler="taxo_groups",
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
        )
        return None

    @lru_cache(maxsize=32)
    def api_list(self, opt_params=None):
        """Return list of taxo groups, from cache or site."""
        return super().api_list()


class TerritorialUnitsAPI(BiolovisionAPI):
    """Implement api calls to territorial_units controler.

    Methods:

    - api_get                - Return a single territorial unit from the controler

    - api_list               - Return a list of territorial units from the controler

    """

    def __init__(
        self,
        user_email: str | None = None,
        user_pw: str | None = None,
        base_url: str | None = None,
        client_key: str | None = None,
        client_secret: str | None = None,
        max_retry: int | None = None,
        max_requests: int | None = None,
        max_chunks: int | None = None,
        unavailable_delay: int | None = None,
        retry_delay: int | None = None,
    ) -> None:
        super().__init__(
            controler="territorial_units",
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
        )
        return None

    @lru_cache(maxsize=32)
    def api_list(self, opt_params=None):
        """Return list of taxo groups, from cache or site."""
        return super().api_list()


class ValidationsAPI(BiolovisionAPI):
    """Implement api calls to validations controler.

    Methods:

    - api_get                - Return a single validation from the controler

    - api_list               - Return the list of validations from the controler

    """

    def __init__(
        self,
        user_email: str | None = None,
        user_pw: str | None = None,
        base_url: str | None = None,
        client_key: str | None = None,
        client_secret: str | None = None,
        max_retry: int | None = None,
        max_requests: int | None = None,
        max_chunks: int | None = None,
        unavailable_delay: int | None = None,
        retry_delay: int | None = None,
    ) -> None:
        super().__init__(
            controler="validations",
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
        )
        return None
