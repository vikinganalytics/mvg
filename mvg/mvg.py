# pylint: disable=too-many-lines

"""
MVG library
-----------
For use of client side development the MVG class shall be used.

The MVGAPI class is intended for development of the library itself.

For more information see README.md.
"""

import logging
import re
import time
from typing import Dict, List, Optional

import pandas as pd
import requests
import semver
from requests.exceptions import RequestException

from mvg.exceptions import MVGConnectionError
from mvg.http_client import HTTPClient
from mvg.utils.response_processing import (
    FrequencyRange,
    SortOrder,
    get_paginated_analysis_results,
    get_paginated_items,
)

logger = logging.getLogger(__name__)


class MVGAPI:
    """Class for a session providing an API to the vibium server"""

    def __init__(self, endpoint: str, token: str):
        """
        Constructor

        On instantiation of a MVG object the session parameters
        are stored for future calls and the version of the API
        is requested.
        In case token is "NO TOKEN", will insert the hardcoded
        valid token from testcases.

        Parameters
        ----------
        endpoint: str
            the server address (URL).

        token: str
            the token used for authentication and authorization.

        Raises
        ------
        MVGConnectionError
            If a connection to the API cannot be established.

        """

        self.endpoint = endpoint
        self.token = token

        self.mvg_version = self.parse_version("v0.14.9")
        self.tested_api_version = self.parse_version("v0.9.3")

        # Get API version
        try:
            response = self._request("get", "")
        except RequestException:
            raise MVGConnectionError("Could not connect to the API.")

        api_root = response.json()["message"]
        api_vstr = api_root["api"]["version"]
        self.api_version = self.parse_version(api_vstr)
        self.api_content = api_root["content"]

    def _request(
        self, method, path, do_not_raise=None, retries=None, **kwargs
    ) -> requests.Response:
        """Helper function for removing duplicate code on API requests.
        Makes requests on self.endpoint with authorization header and
        validates the response by status code. Writes DEBUG logs on
        failed requests.

        Parameters
        ----------
        method : str
            REST method to use for the request

        path : str
            Path to the url to call relative the self.endpoint

        do_not_raise : list
            List of error status codes to ignore. Defaults to [] if None

        retries: RequestRetry
            A RequestRetry object that defines the configuration for retry requests

        **kwargs : Any
            Keyword arguments to pass to requests.request

        Returns
        -------
        Response from the API call
        """
        client = HTTPClient(self.endpoint, self.token, retries)
        response = client.request(
            method=method, path=path, do_not_raise=do_not_raise, **kwargs
        )
        return response

    @staticmethod
    def parse_version(vstr) -> semver.VersionInfo:
        """
        Parses the version string into an array

        Parameters
        ---------
        vstr : str
            Version string of form v3.2.1

        Returns
        ------
        version : VersionInfo
        """
        vstr = re.sub("^v", "", vstr)
        return semver.VersionInfo.parse(vstr)

    def get_endpoint(self) -> str:
        """
        Accessor function.

        Returns
        -------
        endpoint : str
        Endpoint sent to constructor
        """
        return self.endpoint

    def get_token(self) -> str:
        """
        Accessor function.

        Returns
        -------
        token : str
        Token  sent to constructor
        """
        return self.token

    def check_version(self) -> dict:
        """
        Checks if the version of MVG is compatible with
        the API version called on the server side.
        This call does not require a valid token.
        Where: API version is the version on the server side,
        highest tested version is the highest API version the MVG
        has been tested against, and the MVG version is the
        version of the MVG library.

        Raises
        ------
        UserWarning
            In case it would be advisable to upgrade MVG.
        ValueError
            In case MVG is incompatible with the API.

        Returns
        ------
        message : dict
           Showing the api version, the highest version tested against
           and the version of the MVG library.
        """
        logger.info("Checking versions for:%s", self.endpoint)
        logger.info("mvg version: %s", self.mvg_version)
        logger.info("Highest tested API version: %s", self.tested_api_version)

        # Using developer API
        if self.api_version == semver.VersionInfo(0, 0, 0, "dev0"):
            logger.warning(
                f"Using developer API: {self.api_version}. You must "
                "confirm compatibility yourself."
            )
        else:
            # Check compatibility
            # If major versions of tested and api differ
            # it is considered as an incompatibility
            if self.api_version.major != self.tested_api_version.major:
                raise ValueError(
                    f"API version {self.api_version} is incompatible with "
                    f"current MVG version {self.mvg_version}"
                )

            # If minor version of API is lower than mvg tested version
            # This is an error as that should never happen
            if self.api_version.replace(
                prerelease=None, build=None
            ) < self.tested_api_version.replace(prerelease=None, build=None):
                raise ValueError(
                    f"API version {self.api_version} is lower "
                    "than version MVG is tested against: "
                    f"{self.tested_api_version}. "
                    f"Current MVG version is {self.mvg_version}"
                )

            # If minor version of API is higher than mvg tested version
            # API may have additional features not accesible via MVG
            if self.api_version.minor > self.tested_api_version.minor:
                raise UserWarning(
                    f"API version {self.api_version} may contain features"
                    f" not supported by "
                    f"current MVG version {self.mvg_version}"
                )

        # return version info
        return {
            "api_version": str(self.api_version),
            "mvg_highest_tested_version": str(self.tested_api_version),
            "mvg_version": str(self.mvg_version),
        }

    def say_hello(self) -> dict:
        """
        Retrieves information about the API.
        This call does not require a valid token.

        Returns
        ------
        message : dict
        Hello message with info on MVG API.
        """
        logger.info("Getting API info for: %s", self.endpoint)

        response = self._request("get", "")

        # return list of IDs
        return response.json()["message"]["api"]

    def create_source(
        self,
        sid: str,
        channels: List[str],
        meta: dict = None,
        exist_ok: bool = False,
    ):
        """
        Creates a source on the server side.

        Parameters
        ----------
        sid : str
            Source ID

        channels : List[str]
            Channels of waveform Data. For instance axial, vertical and horizontal
            measurements for the source.
            Cannot be updated after creating source.

        meta : dict
            Meta information of source [optional].

        exist_ok : bool
            Set to true to prevent exceptions for 409 Conflict errors
            caused by trying to create an existing source. Defaults to False.
        """

        logger.info("endpoint %s", self.endpoint)
        logger.info("creating source with source id=%s", sid)
        logger.info("metadata: %s", meta)
        logger.info("channels: %s", channels)

        if meta is None:
            meta = {}

        do_not_raise = []
        if exist_ok:
            do_not_raise.append(requests.codes["conflict"])  # 409

        # Package info to be submitted to db
        source_info = {"source_id": sid, "meta": meta, "channels": channels}
        self._request("post", "/sources/", do_not_raise, json=source_info)

    def create_spectrum_source(
        self,
        sid: str,
        channels: List[str],
        meta: dict = None,
        exist_ok: bool = False,
    ):
        """
        Creates a spectrum source on the server side.

        Parameters
        ----------
        sid : str
            Source ID

        channels : List[str]
            Channels of spectrum Data. For instance axial, vertical and horizontal.
            Channel names must be unique.
            Cannot be updated after creating source.

        meta : dict
            Meta information of source [optional].

        exist_ok : bool
            Set to true to prevent exceptions for 409 Conflict errors
            caused by trying to create an existing source. Defaults to False.
        """

        logger.info("endpoint %s", self.endpoint)
        logger.info("creating spectrum source with source id=%s", sid)
        logger.info("metadata: %s", meta)
        logger.info("channels: %s", channels)

        if meta is None:
            meta = {}

        do_not_raise = []
        if exist_ok:
            do_not_raise.append(requests.codes["conflict"])  # 409

        source_info = {"source_id": sid, "meta": meta, "channels": channels}
        self._request("post", "/sources/spectrum", do_not_raise, json=source_info)

    def create_tabular_source(
        self,
        sid: str,
        columns: List[str],
        meta: dict = None,
        exist_ok: bool = False,
    ):
        """
        Creates a tabular source on the server side.

        Parameters
        ----------
        sid : str
            Source ID

        columns : List[str]
            Data variables. Currently supports numerical data.
            Cannot be updated after creating source.

        meta : dict
            Meta information of source [optional].

        exist_ok : bool
            Set to true to prevent exceptions for 409 Conflict errors
            caused by trying to create an existing source. Defaults to False.
        """

        logger.info("endpoint %s", self.endpoint)
        logger.info("creating tabular source with source id=%s", sid)
        logger.info("metadata: %s", meta)
        logger.info("columns: %s", columns)

        if meta is None:
            meta = {}

        do_not_raise = []
        if exist_ok:
            do_not_raise.append(requests.codes["conflict"])  # 409

        # Package info to be submitted to db
        source_info = {"source_id": sid, "meta": meta, "columns": columns}
        self._request("post", "/sources/tabular", do_not_raise, json=source_info)

    def list_sources(self) -> list:
        """Lists all sources (sensors) on the server side

        Returns
        -------
        list of all source id:s known to the server

        """

        logger.info("endpoint %s", self.endpoint)
        logger.info("listing sources")

        response = self._request("get", "/sources/")

        # return list of IDs
        return response.json()

    # In example
    def get_source(self, sid: str) -> dict:
        """Returns the information stored for a source representing
        on the given endpoint.

        Parameters
        ----------
        sid: str
            source Id.

        Returns
        -------
        dict
            Information stored about the source.
        """

        logger.info("endpoint %s", self.endpoint)
        logger.info("retrieving source with source id=%s", sid)

        response = self._request("get", f"/sources/{sid}")

        # return list of IDs
        return response.json()

    # In example
    def update_source(self, sid: str, meta: dict):
        """
        Replaces source meta information on the server side.

        Parameters
        ----------
        sid: str
            source Id.

        meta: dict
            meta information to replace old meta information.
        """

        logger.info("endpoint %s", self.endpoint)
        logger.info("updating source with source id=%s", sid)
        logger.info("metadata: %s", meta)

        self._request("put", f"/sources/{sid}", json=meta)

    # In example
    def delete_source(self, sid: str):
        """Deletes a source on the given endpoint.

        Parameters
        ----------
        sid: str
            source Id.
        """

        logger.info("endpoint %s", self.endpoint)
        logger.info("deleting source with source id=%s", sid)

        self._request("delete", f"/sources/{sid}")

    ####################################
    # Measurements
    # in example
    def create_measurement(
        self,
        sid: str,
        duration: float,
        timestamp: int,
        data: Dict[str, List[float]],
        meta: dict = None,
        exist_ok: bool = False,
    ):
        """Stores a measurement on the server side.

        Although it is up to the client side to handle the
        scaling of data it is recommended that the values
        represent the acceleration in g.
        The timestamp shall represent the time when the measurement was
        recorded.

        Parameters
        ----------
        sid: str
            source Id.

        duration: float
            duration of the measurement in seconds.

        timestamp: int
            in milliseconds since EPOCH.

        data: Dict[str, List[float]]
            Data on the format {channel: values}. Each value is a timeseries
            of measurements.
            This format can be generated by pandas.DataFrame.to_dict("list")

        meta: dict
            Meta information to attach to data.

        exist_ok: bool
            Set to true to prevent exceptions for 409 Conflict errors
            caused by trying to create an existing measurement. Defaults to False
        """

        logger.info("endpoint %s", self.endpoint)
        logger.info("creating measurement for source id=%s", sid)
        logger.info("  duration:  %s", duration)
        logger.info("  timestamp: %s", timestamp)
        logger.info("  meta data: %s", meta)

        if meta is None:
            meta = {}

        do_not_raise = []
        if exist_ok:
            do_not_raise.append(requests.codes["conflict"])  # 409

        # Package info for db to be submitted
        meas_struct = [
            {
                "timestamp": timestamp,
                "duration": duration,
                "data": data,
                "meta": meta,
            }
        ]

        self._request(
            "post", f"/sources/{sid}/measurements", do_not_raise, json=meas_struct
        )

    def create_spectrum_measurement(
        self,
        sid: str,
        freq_range: FrequencyRange,
        timestamp: int,
        data: Dict[str, List[float]],
        meta: dict = None,
        exist_ok: bool = False,
    ):
        """Stores a measurement on the server side.

        Although it is up to the client side to handle the
        scaling of data it is recommended that the values
        represent the acceleration in g.
        The timestamp shall represent the time when the measurement was
        recorded.

        Parameters
        ----------
        sid: str
            source Id.

        freq_range: FrequencyRange
            lowest and highest frequency available in the spectrum as a list [MIN, MAX].

        timestamp: int
            in milliseconds since EPOCH.

        data: Dict[str, List[float]]
            Data on the format {channel: values}.
            This format can be generated by pandas.DataFrame.to_dict("list").

        meta: dict
            Meta information to attach to data [optional].

        exist_ok: bool
            Set to true to prevent exceptions for 409 Conflict errors
            caused by trying to create an existing measurement. Defaults to False.
        """

        logger.info("endpoint %s", self.endpoint)
        logger.info("creating spectrum measurement for source id=%s", sid)
        logger.info("  freq_range: %s", freq_range)
        logger.info("  timestamp: %s", timestamp)
        logger.info("  meta data: %s", meta)

        if meta is None:
            meta = {}

        do_not_raise = []
        if exist_ok:
            do_not_raise.append(requests.codes["conflict"])  # 409

        meas_struct = [
            {
                "timestamp": timestamp,
                "freq_range": freq_range,
                "data": data,
                "meta": meta,
            }
        ]

        self._request(
            "post",
            f"/sources/{sid}/measurements/spectrum",
            do_not_raise,
            json=meas_struct,
        )

    def create_tabular_measurement(
        self,
        sid: str,
        data: Dict[str, List[float]],
        meta: Dict[float, dict] = None,
        exist_ok: bool = False,
    ):
        """Stores a measurement on the server side.

        Although it is up to the client side to handle the
        scaling of data it is recommended that the values
        represent the acceleration in g.
        The timestamp shall represent the time when the measurement was
        recorded.

        Parameters
        ----------
        sid: str
            source Id.

        data: Dict[str, List[float]]
            Tabular data on the format {column: values}. 'timestamp' column is required.
            This format can be generated by pandas.DataFrame.to_dict("list")

        meta: dict
            Meta information to attach to data. Should have the format
            {timestamp: meta_dict}. Timestamps must match data timestamps

        exist_ok: bool
            Set to true to prevent exceptions for 409 Conflict errors
            caused by trying to create an existing measurement. Defaults to False
        """

        logger.info("endpoint %s", self.endpoint)
        logger.info("creating tabular measurement for source id=%s", sid)

        do_not_raise = []
        if exist_ok:
            do_not_raise.append(requests.codes["conflict"])  # 409

        body = {"data": data}
        if meta is not None:
            body["meta"] = meta

        self._request(
            "post",
            f"/sources/{sid}/measurements/tabular",
            do_not_raise,
            json=body,
        )

    def list_timestamps(
        self,
        sid: str,
        offset: int = None,
        limit: int = None,
        order: SortOrder = SortOrder.ASC.value,
    ) -> Dict:
        """
        Retrieves timestamps for a source.
        If offset and limit params are not specified, all timestamps will be returned.

        Parameters
        ----------
        sid : str
            source ID.
        offset: int
            index of the first timestamp in the database [optional].
        limit: int
            maximum number of timestamps to be returned [optional].
        order : SortOrder
            Sort order, either "asc" or "desc". Defaults to "asc".

        Returns
        -------
        A dictionary containing the following keys:

            - "offset": int, representing starting point of returned items.
            - "limit: int, representing max items to return."
            - "items": list of int, representing timestamps.
            - "total": int, representing total number of items.
        """
        logger.info("endpoint %s", self.endpoint)
        logger.info("retrieving timestamps from source id=%s", sid)
        url = f"/sources/{sid}/timestamps"
        params = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if order is not None:
            params["order"] = order
        paginated_items = get_paginated_items(self._request, url, params)

        logger.info("%s timestamps in database", paginated_items["total"])
        logger.info("Returned %s timestamps", len(paginated_items["items"]))

        return {
            "offset": offset or 0,
            "limit": limit or paginated_items["total"],
            "items": paginated_items["items"],
            "total": paginated_items["total"],
        }

    # in example
    def list_measurements(
        self, sid: str, offset: int = None, limit: int = None
    ) -> list:
        """Retrieves measurements (all timestamps and metadata) for a source.

        Parameters
        ----------
        sid : str
            source ID.
        offset: int
            index of the first measurement in the database
        limit: int
            maximum number of measurements to be returned

        Returns
        -------
        An array of arrays of single measurements.

        """
        logger.info("endpoint %s", self.endpoint)
        logger.info("retrieving all measurements from source id=%s", sid)
        url = f"/sources/{sid}/measurements"
        params = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        paginated_items = get_paginated_items(self._request, url, params)

        logger.info("%s measurements in database", paginated_items["total"])
        logger.info("Returned %s measurements", len(paginated_items["items"]))

        return paginated_items["items"]

    # in example
    def read_single_measurement(self, sid: str, timestamp: int) -> dict:
        """
        Retrieves all measurements for one single timestamps from source Id.

        The format of the returned measurement is
        an array with the first value being the time stamp and the
        subsequent values being the data (samples).

        Parameters
        ----------
        sid : str
            source Id.

        timestamp : int
            in milliseconds since EPOCH.

        Returns
        -------
        dict containing measurement data, meta information and duration or
        columns, depending on source data class
        """

        logger.info("endpoint %s", self.endpoint)
        logger.info("retrieving measurements from source id=%s", sid)
        logger.info("timestamp=%s", timestamp)

        response = self._request("get", f"/sources/{sid}/measurements/{timestamp}")

        return response.json()

    # pylint: disable=too-many-locals
    def list_tabular_measurements(
        self,
        sid: str,
        start_timestamp: int = None,
        end_timestamp: int = None,
        offset: int = None,
        limit: int = None,
    ) -> dict:
        """Retrieves tabular measurements (including metadata) for a source.

        Parameters
        ----------
        sid : str
            source Id.

        start_timestamp : int
            Measurements starting from a timestamp [optional].

        end_timestamp : int
            Measurements ending at a timestamp [optional].

        offset: int
            index of the first measurement in the database
        limit: int
            maximum number of measurements to be returned

        Returns
        -------
        An dict having a list of all timestamps, a list of all measurements grouped by
        column names, and metadata corresponding to a measurement.
        """
        logger.info("endpoint %s", self.endpoint)
        logger.info("retrieving all measurements from source id=%s", sid)

        url = f"/sources/{sid}/measurements/tabular"
        params = {}

        if start_timestamp is not None:
            params["start_timestamp"] = start_timestamp
        if end_timestamp is not None:
            params["end_timestamp"] = end_timestamp
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        response = self._request(
            "get",
            url,
            params=params,
        )

        resp_first = response.json()
        all_measurements = resp_first["items"]
        total_num = resp_first.get("total", None)
        request_limit = resp_first.get("limit", None)

        has_missing_items = False
        if total_num and request_limit:
            offset = offset or 0
            limit = min(limit or total_num, total_num - offset)
            has_missing_items = request_limit < limit

        if not params or has_missing_items:
            # List all by default if pagination is not requested or
            # start/end timestamps are not specified
            num_reqs = (total_num - 1) // request_limit
            for _ in range(1, num_reqs + 1):
                if "limit" in params:
                    params["limit"] -= request_limit
                offset += request_limit
                params["offset"] = offset
                response = self._request("get", url, params=params)
                for key, items in response.json()["items"].items():
                    all_measurements[key] += items

        return all_measurements

    def list_tabular_downsampled_measurements(
        self,
        sid: str,
        threshold: Optional[int] = None,
        start_timestamp: Optional[int] = None,
        end_timestamp: Optional[int] = None,
    ) -> dict:
        """Retrieves downsampled tabular measurements for a source.

        Parameters
        ----------
        sid : str
            source Id.

        threshold: int
            Max number of points to display per dataset.
            Value of 0 means no downsampling will be applied [optional].

        start_timestamp : int
            Measurements starting from a timestamp [optional].

        end_timestamp : int
            Measurements ending at a timestamp [optional].

        Returns
        -------
        A dictionary of KPIs in the format:
        {kpi1: { x: timestamps, y: values }, kpi2: { ... }}
        """
        logger.info("endpoint %s", self.endpoint)
        logger.info("retrieving all measurements from source id=%s", sid)

        params = {}

        if threshold is not None:
            params["threshold"] = threshold
        if start_timestamp is not None:
            params["start_timestamp"] = start_timestamp
        if end_timestamp is not None:
            params["end_timestamp"] = end_timestamp

        response = self._request(
            "get", f"/sources/{sid}/measurements/tabular/downsample", params=params
        )

        return response.json()

    # in example
    def update_measurement(self, sid: str, timestamp: int, meta: dict):
        """Replaces meta information along measurement.
        It is not possible to update the actual measurement
        data.

        Parameters
        ----------
        sid: str
            source Id.

        timestamp: int
            in milliseconds since EPOCH. Identifies measurement.

        meta: dict
            Meta information to attach to data.
        """

        logger.info("endpoint %s", self.endpoint)
        logger.info("deleting measurement for source id=%s", sid)
        logger.info("  timestamp: %s", timestamp)

        self._request(
            "put",
            f"/sources/{sid}/measurements/{timestamp}",
            json={"meta": meta},
        )

    # In example
    def delete_measurement(self, sid: str, timestamp: int):
        """Deletes a measurement.

        Parameters
        ----------
        sid: str
            source Id. Identifies source.

        timestamp: int
            in milliseconds since EPOCH. Identifies measurement.

        """

        logger.info("endpoint %s", self.endpoint)
        logger.info("deleting measurement for source id=%s", sid)
        logger.info("  timestamp: %s", timestamp)

        self._request("delete", f"/sources/{sid}/measurements/{timestamp}")

    # Analysis
    def supported_features(self) -> list:
        """Return all supported features.
        Presence of a feature is indicated by string with the
        feature name set to true.
        That string shall be used to specify
        that feature in an analysis request.
        This call does not require a valid token.

        Returns
        -------
        A list of supported features (strings).

        """
        logger.info("endpoint %s", self.endpoint)
        logger.info("retrieving supported features")

        response = self._request("get", "/analyses/")

        return response.json()

    def request_analysis(
        self,
        sid: str,
        feature: str,
        parameters: dict = None,
        selected_channels: List[str] = None,
        selected_columns: List[str] = None,
        start_timestamp: int = None,
        end_timestamp: int = None,
        callback_url: str = None,
        force: bool = False,
    ) -> dict:
        """Request an analysis on the given endpoint with given parameters.

        Parameters
        ----------
        sid : str
            Source Id.

        feature : str
            Name of feature to run.

        parameters : dict
            Name value pairs of parameters [optional].

        selected_channels : List[str]
            Subset of Waveform Data channels for analysis.
            This cannot be used in conjunction with selected_columns [optional].

        selected_columns : List[str]
            Subset of Tabular Data columns for analysis.
            This cannot be used in conjunction with selected_channels [optional].

        start_timestamp : int
            Start of analysis time window [optional].

        end_timestamp : int
            Start of analysis time window [optional].

        callback_url : str
            Base URL to receive a notification when the analysis job ends.
            A POST request will be made to {callback_url}/analyses with payload
            that includes the request_id and request_status of the job [optional].

        force: bool
            Set to False to reuse the analysis results if it already exists, otherwise
            re-run the analysis. Defaults to False.

        Returns
        -------
        dict
            Containing request_id and request_status corresponding to
            analysis identifier and analysis status.

        """
        logger.info("endpoint %s", self.endpoint)
        logger.info("source id=%s", sid)
        logger.info("sending %s analysis request", feature)
        logger.info("parameters %s", parameters)
        logger.info(
            "from start timestamp as %s to end timestamp as %s ",
            start_timestamp,
            end_timestamp,
        )

        if parameters is None:
            parameters = {}

        # Update parameters with certain method parameters
        if selected_channels:
            parameters["selected_channels"] = selected_channels
        if selected_columns:
            parameters["selected_columns"] = selected_columns

        # Package info for db to be submitted
        analysis_info = {
            "source_id": sid,
            "feature": feature,
            "params": parameters,
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
            "force": force,
        }

        params = None
        if callback_url:
            params = {"callback_url": callback_url}
        response = self._request(
            "post", "/analyses/requests/", json=analysis_info, params=params
        )

        return response.json()

    def request_population_analysis(
        self,
        sids: List[str],
        feature: str,
        parameters: dict = None,
        start_timestamp: int = None,
        end_timestamp: int = None,
        callback_url: str = None,
        force: bool = False,
    ) -> dict:
        """Request a population analysis on the given endpoint with given parameters.

        Parameters
        ----------
        sids : List[str]
            Source ids.

        feature : str
            Name of feature to run. This feature must be of population type.

        parameters : dict
            Name value pairs of parameters [optional].

        start_timestamp : int
            Start of analysis time window [optional].

        end_timestamp : int
            Start of analysis time window [optional].

        callback_url : str
            Base URL to receive a notification when the analysis job ends.
            A POST request will be made to {callback_url}/analyses with payload
            that includes the request_id and request_status of the job [optional].

        force: bool
            Set to True to force a re-run on any existing analysis, otherwise existing
            analysis results will be reused. Defaults to False.

        Returns
        -------
        dict
            Containing request_id and request_status corresponding to
            analysis identifier and analysis status.

        """
        logger.info("endpoint %s", self.endpoint)
        logger.info("source ids=%s", sids)
        logger.info("sending %s analysis request", feature)
        logger.info("parameters %s", parameters)
        logger.info(
            "from start timestamp as %s to end timestamp as %s ",
            start_timestamp,
            end_timestamp,
        )

        if parameters is None:
            parameters = {}

        # Package info for db to be submitted
        analysis_info = {
            "source_ids": sids,
            "feature": feature,
            "params": parameters,
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
            "force": force,
        }

        params = None
        if callback_url:
            params = {"callback_url": callback_url}
        response = self._request(
            "post", "/analyses/requests/population/", json=analysis_info, params=params
        )

        return response.json()

    def list_analyses(self, sid: str, feature: str) -> list:
        """Retrieves list of analysis IDs associated with a source
        and a feature.

        Parameters
        ----------
        sid : str
            source Id.

        feature : str
            name of the feature.

        Returns
        -------
        list
            a list of analysis IDs.

        """
        logger.info("endpoint %s", self.endpoint)
        logger.info("get list of analyses with source ID=%s", sid)

        response = self._request("get", f"/analyses/source/{sid}/feature/{feature}")

        return response.json()

    def get_analysis_status(self, request_id: str) -> str:
        """Return the status of an analysis request with given request_id.

        Parameters
        ----------
        request_id : str
            request_id (analysis identifier)

        Returns
        -------
        str
            status of the analysis. It can take any of the following values:
            "queued": The request is scheduled but have not started.
            "ongoing": The request is running
            "failed": The request failed due to internal issue.
            "successful": The request finished successfully.

        """
        logger.info("endpoint %s", self.endpoint)
        logger.info("get analysis status with request_id=%s", request_id)

        response = self._request("get", f"/analyses/requests/{request_id}")

        return response.json()["request_status"]

    def get_analysis_info(self, request_id: str) -> dict:
        """Retrieves info of an analysis request.

        The info of an analysis request includes the current status and the
        status history of the analysis where the status history is a list of
        statuses logged for the analysis. The info also contains an overview
        of the measurements used by the analysis.

        Parameters
        ----------
        request_id : str
            request_id (analysis identifier)

        Returns
        -------
        dict
            a dictionary with the analysis info.

        """
        logger.info("endpoint %s", self.endpoint)
        logger.info("get analysis info with request_id=%s", request_id)

        response = self._request("get", f"/analyses/requests/{request_id}")

        return response.json()

    def get_analysis_results(
        self,
        request_id: str,
        offset: int = None,
        limit: int = None,
        result_type: str = None,
    ) -> dict:
        """Retrieves an analysis with given request_id
        The format of the result structure depends on the feature.

        Parameters
        ----------
        request_id : str
            request_id (analysis identifier)
        offset: int
            zero-based index of an item in one of the dictionaries
            in the data for "results" key [optional].
        limit: int
            maximum number of items to be returned from each
            dictionary in the data for "results" key [optional].
        result_type: str
            The type of results to return. By default, the type is
            'full' implying the complete analysis results will be
            returned. The allowed types varies between features [optional].

        Returns
        -------
        dict
            a dictionary with the results in case available.

        """
        logger.info("endpoint %s", self.endpoint)
        logger.info("get analysis results with request_id=%s", request_id)

        url = f"/analyses/requests/{request_id}/results"
        params = {}
        if offset is not None:
            params["offset"] = offset
        if limit is not None:
            params["limit"] = limit
        if result_type is not None:
            params["result_type"] = result_type

        response = get_paginated_analysis_results(self._request, url, params)
        return response

    def delete_analysis(self, request_id: str):
        """Deletes an analysis.

        Parameters
        ----------
        request_id : str
            request_id (analysis identifier)

        """

        logger.info("endpoint %s", self.endpoint)
        logger.info("deleting analysis with request_id=%s", request_id)

        self._request("delete", f"/analyses/requests/{request_id}")

    # Labels
    def create_label(
        self,
        sid: str,
        timestamp: int,
        label: str,
        severity: int,
        notes: Optional[str] = "",
        exist_ok: bool = False,
    ):
        """Create a label for a measurement

        Parameters
        ----------
        sid : str
            Id of the source for the measurement
        timestamp : int
            Timestamp of the measurement to label
        label : str
            A string label to attach to the measurement
        severity : int
            Severity of the label as a positive integer
        notes : Optional[str], optional
            Optional notes for the label, by default ""
        exist_ok : bool
            Set to true to prevent exceptions for 409 Conflict errors
            caused by trying to create an existing label. Defaults to False
        """
        logger.info("endpoint %s", self.endpoint)
        logger.info(f"Creating label for {sid} - {timestamp}")

        label_data = {"label": label, "severity": severity, "notes": notes}

        do_not_raise = []
        if exist_ok:
            do_not_raise.append(requests.codes["conflict"])  # 409

        self._request(
            "post", f"/sources/{sid}/labels/{timestamp}", do_not_raise, json=label_data
        )

    def get_label(self, sid: str, timestamp: int) -> dict:
        """Get a single label from a measurement

        Parameters
        ----------
        sid : str
            Id of the source for the measurement
        timestamp : int
            Timestamp of the measurement

        Returns
        -------
        dict
            label information
        """

        logger.info("endpoint %s", self.endpoint)
        logger.info("Getting label")

        response = self._request("get", f"/sources/{sid}/labels/{timestamp}")
        return response.json()

    def list_labels(
        self, source_id: str, include_unlabeled: bool = False
    ) -> List[dict]:
        """Get a list of all the labels for a source

        Parameters
        ----------
        source_id : str
            Source ID of the source to get the labels from
        include_unlabeled : bool
            Only returns the labeled times if True, by default False

        Returns
        -------
        List[dict]
            Label information for the different timestamps
        """
        logger.info("endpoint %s", self.endpoint)
        logger.info("Getting labels")

        response = self._request("get", f"/sources/{source_id}/labels")
        labels = response.json()

        if not include_unlabeled:
            return labels

        # Include the missing labels
        measurements = self.list_measurements(source_id)
        measurements_ts = pd.DataFrame(measurements)[["timestamp"]]
        return (
            pd.DataFrame(labels)
            .merge(measurements_ts, on=["timestamp"], how="outer", sort=True)
            .to_dict("list")
        )

    def update_label(
        self,
        sid: str,
        timestamp: int,
        label: str,
        severity: int,
        notes: Optional[str] = "",
    ):
        """Update a label for a measurement

        Parameters
        ----------
        sid : str
            Id of the source for the measurement
        timestamp : int
            Timestamp of the measurement
        label : str
            The new label to attach to the measurement
        severity : int
            The new severity of the label as a positive integer
        notes : Optional[str], optional
            New optional notes for the label, by default ""
        """
        logger.info("endpoint %s", self.endpoint)
        logger.info(f"Updating label of {sid} - {timestamp}")

        label_data = {"label": label, "severity": severity, "notes": notes}

        self._request("put", f"/sources/{sid}/labels/{timestamp}", json=label_data)

    def delete_label(self, sid: str, timestamp: int):
        """Delete all label information from a measurement

        Parameters
        ----------
        sid : str
            Id of the source for the measurement
        timestamp : int
            Timestamp of the measurement
        """
        logger.info("endpoint %s", self.endpoint)
        logger.info(f"Deleting label for {sid} - {timestamp}")

        self._request("delete", f"/sources/{sid}/labels/{timestamp}")


class MVG(MVGAPI):
    """Class for a session providing an API to the vibium server.
    Contains additional functionality over API methods"""

    def wait_for_analyses(self, request_id_list: list, timeout=None):
        """Wait for the analyses specified by list of request_ids to finish.

        Parameters
        ----------
        request_id_list : list
            list of request_ids (analysis identifier)
        timeout: float [Optional]
            amount of time (in seconds) to wait for the analyses to finish
        """

        start = time.time()
        min_wait = 1.5
        jobs = set(request_id_list)
        while len(jobs) > 0:
            done_jobs = set()
            for request_id in jobs:
                status = self.get_analysis_status(request_id)
                if status in ("successful", "failed"):
                    logger.info("Analysis with ID %s done", request_id)
                    done_jobs.add(request_id)
            jobs = jobs - done_jobs

            if len(jobs) > 0:
                if timeout is None:
                    time.sleep(min_wait)
                else:
                    elapsed = time.time() - start
                    if elapsed > timeout:
                        logger.info("wait_for_analyses timed out")
                        break
                    time.sleep(min(min_wait, timeout - elapsed))
