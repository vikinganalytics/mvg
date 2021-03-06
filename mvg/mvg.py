"""
MVG library
-----------
For use of client side development the MVG class shall be used.

The MVGAPI class is intended for development of the library itself.

For more information see README.md.
"""

import re
import json
import time
import logging
import requests
from requests.exceptions import HTTPError, RequestException
import semver

logger = logging.getLogger(__name__)


class MVGAPI:
    """Class for a session providing an API to the vibium server"""

    def __init__(self, endpoint: str, token: str):
        """
        Constructor

        On instantiation of a MVG object the session parameters
        are stored for future calls and the version of the API
        is requested.
        In case token is "NO TOKEN", will insert the harcoded
        valid token from testcases.

        Parameters
        ----------
        endpoint: str
            the server address (URL).

        token: str
            the token used for authentication and authorization.

        Raises
        ------
        HTTPError
            If a connection to the API cannot be established.

        """

        self.endpoint = endpoint
        self.token = token

        self.mvg_version = self.parse_version("v0.5.0")
        self.tested_api_version = self.parse_version("v0.1.1")

        # Errors to ignore
        self.do_not_raise = []

        # Get API version
        try:
            response = self._request("get", "")
        except RequestException as exc:
            logger.exception(exc)
            raise HTTPError("Could not connect to the API.")

        api_vstr = response.json()["message"]["api"]["version"]
        self.api_version = self.parse_version(api_vstr)

    def _request(self, method, path, **kwargs):
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

        **kwargs : Any
            Keyword arguments to pass to requests.request

        Raises
        ------
        HTTPError
            the original HTTPError from raise_for_status

        Returns
        -------
        Response from the API call
        """
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.request(
            method=method,
            url=self.endpoint + path,
            headers=headers,
            **kwargs,
        )

        try:
            response.raise_for_status()
        except HTTPError as exc:
            logger.debug(str(exc))

            # Error ignorer
            ignore = False
            for err_no in self.do_not_raise:
                if re.search(err_no, str(exc)):
                    ignore = True
            if ignore:
                logstr = "Ignoring" + str(exc)
                logger.info(logstr)
            elif response.text:
                logger.debug(str(response.text))
                raise exc

        return response

    @staticmethod
    def parse_version(vstr):
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

    def get_endpoint(self):
        """
        Accessor function.

        Returns
        -------
        endpoint : str
        Endpoint sent to constructor
        """
        return self.endpoint

    def get_token(self):
        """
        Accessor function.

        Returns
        -------
        token : str
        Token  sent to constructor
        """
        return self.token

    def check_version(self):
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
           Showing the api version, the highest vesrion tested against
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
                    f" not supporeted by "
                    f"current MVG version {self.mvg_version}"
                )

        # return version info
        return {
            "api_version": str(self.api_version),
            "mvg_highest_tested_version": str(self.tested_api_version),
            "mvg_version": str(self.mvg_version),
        }

    def say_hello(self):
        """
        Retrievs information about the API.
        This call does not require a valid token.

        Returns
        ------
        message : dict
        Hello message with info on MVG API.
        """
        logger.info("Getting API info for: %s", self.endpoint)

        response = self._request("get", "")

        # return list of IDs
        return response.json()["message"]

    def create_source(self, sid: str, meta: dict):
        """
        Creates a source on the server side.

        Parameters
        ----------
        sid : str
            source Id

        meta : dict
            meta information
        """

        logger.info("endpoint %s", self.endpoint)
        logger.info("creating source with source id=%s", sid)
        logger.info("metadata: %s", meta)

        # Package info to be submitted to db
        source_info = {"source_id": sid, "meta": meta}

        self._request("post", "/sources/", json=source_info)

    def list_sources(self):
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
    def get_source(self, sid: str):
        """Returns the information stored for a source representing
        on the given endpoint.

        Parameters
        ----------
        sid: str
            source Id.

        Returns
        -------
        source_information: (dict)
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

        self._request("put", f"/sources/{sid}", data=json.dumps(meta))

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
        self, sid: str, duration: float, timestamp: int, data: list, meta: dict
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

        data: list
            list of float values.

        meta: dict
            Meta information to attach to data.

        """

        logger.info("endpoint %s", self.endpoint)
        logger.info("creating measurement from source id=%s", sid)
        logger.info("  duration:  %s", duration)
        logger.info("  timestamp: %s", timestamp)
        logger.info("  meta data: %s", meta)

        # Package info for db to be submitted
        meas_struct = {
            "source_id": sid,  # should be source_id
            "timestamp": timestamp,
            "duration": duration,
            "data": data,
            "meta": meta,
        }

        self._request("post", f"/sources/{sid}/measurements", json=meas_struct)

    # in example
    def read_measurements(self, sid: str):
        """Retrieves all measurements for all timestamps for a source.

        Parameters
        ----------
        sid : str
            source Id.

        Returns
        -------
        An array of arrays of single measurements.

        """
        logger.info("endpoint %s", self.endpoint)
        logger.info("retrieving all measurements from source id=%s", sid)

        response = self._request("get", f"/sources/{sid}/measurements")

        # Step 2: read actual measurement data for all timestamps
        timestamps = response.json()
        logger.info("%s measurements in database", len(timestamps))

        all_measurements = []
        for m_time in timestamps:
            all_measurements.append(
                self.read_single_measurement(sid, m_time["timestamp"])
            )

        return all_measurements

    # in example
    def read_single_measurement(self, sid: str, timestamp: int):
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
        array of measurements.
        """

        logger.info("endpoint %s", self.endpoint)
        logger.info("retrieving measurements from source id=%s", sid)
        logger.info("timestamp=%s", timestamp)

        response = self._request("get", f"/sources/{sid}/measurements/{timestamp}")

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
            data=json.dumps(meta),
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
    def supported_features(self):
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
        start_timestamp: int = None,
        end_timestamp: int = None,
    ):
        """Request an analysis on the given endpoint with given parameters.

        Parameters
        ----------
        sid : str
            source Id.

        feature : str
            name of feature to run.

        parameters : dict
            name value pairs of parameters [optional].

        start_timestamp : int
            start of analysis time window [optional].

        end_timestamp : int
            start of analysis time window [optional].

        Returns
        -------
        request_id: analysis identifier

        """
        logger.info("endpoint %s", self.endpoint)
        logger.info("source id=%s", sid)
        logger.info("sending %s analysis request", feature)
        logger.info("parameters %s", parameters)
        logger.info("from %s to %s ", start_timestamp, end_timestamp)

        if parameters is None:
            parameters = dict()

        # Package info for db to be submitted
        analysis_info = {
            "source_id": sid,
            "feature": feature,
            "params": parameters,
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
        }

        response = self._request("post", "/analyses/requests/", json=analysis_info)

        return response.json()

    def request_population_analysis(
        self,
        sids: [str],
        feature: str,
        parameters: dict = None,
        start_timestamp: int = None,
        end_timestamp: int = None,
    ):
        """Request an population analysis on the given endpoint with given parameters.

        Parameters
        ----------
        sids : [str]
            Source ids.

        feature : str
            name of feature to run. This feature must be of population type.

        parameters : dict
            name value pairs of parameters [optional].

        start_timestamp : int
            start of analysis time window [optional].

        end_timestamp : int
            start of analysis time window [optional].

        Returns
        -------
        request_id: analysis identifier

        """
        logger.info("endpoint %s", self.endpoint)
        logger.info("source ids=%s", sids)
        logger.info("sending %s analysis request", feature)
        logger.info("parameters %s", parameters)
        logger.info("from %s to %s ", start_timestamp, end_timestamp)

        if parameters is None:
            parameters = dict()

        # Package info for db to be submitted
        analysis_info = {
            "source_ids": sids,
            "feature": feature,
            "params": parameters,
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
        }

        response = self._request(
            "post", "/analyses/requests/population/", json=analysis_info
        )
        return response.json()

    def list_analyses(self, sid: str, feature: str):
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
        results: list
            a list of analysis IDs.

        """
        logger.info("endpoint %s", self.endpoint)
        logger.info("get list of analyses with source ID=%s", sid)

        response = self._request("get", f"/analyses/source/{sid}/feature/{feature}")

        return response.json()

    def get_analysis_status(self, request_id: str):
        """Return the status of an analysis request with given request_id.

        Parameters
        ----------
        request_id : str
            request_id (analysis identifier)

        Returns
        -------
        status: str
            status of the analysis. It can take any of the following values:
            "queued": The request is cheduled but have not started.
            "ongoing": The request is running
            "failed": The request failed due to internal issue.
            "successful": The request finished successfully.

        """
        logger.info("endpoint %s", self.endpoint)
        logger.info("get analysis status with request_id=%s", request_id)

        response = self._request("get", f"/analyses/requests/{request_id}")

        return response.json()["request_status"]

    def get_analysis_results(self, request_id: str):
        """Retrieves an analysis with given request_id
        The format of the result structure depends on the feature.

        Parameters
        ----------
        request_id : str
            request_id (analysis identifier)

        Returns
        -------
        results: dict
            a dictionary with the results in case available.

        """
        logger.info("endpoint %s", self.endpoint)
        logger.info("get analysis results with request_id=%s", request_id)

        response = self._request("get", f"/analyses/requests/{request_id}/results")

        return response.json()


class MVG(MVGAPI):
    """Class for a session providing an API to the vibium server.
    Note that this class ignores specific http errors
    (per default 409, existing resource). If this is not wanted use
    MVGAPI class instead.
    """

    def __init__(self, endpoint: str, token: str):
        """
        Constructor.
        As compared to super class configures session to ignore
        409 errors (occuring when an existing resource is overwritten.
        More errors can be ignored by setting class
        attribute do_not_raise with a dictionary of http error codes.
        On instantiation of a MVG object the session parameters
        are stored for future calls and the version of the API
        is requested.
        In case token is "NO TOKEN", will insert the harcoded
        valid token from testcases.
        HTTPError is raised if  a connection to the API cannot
        be established.

        Parameters
        ----------
        endpoint: str
            the server address (URL).
        token: str
            the token used for authentication and authorization.
        """
        super().__init__(endpoint=endpoint, token=token)
        self.do_not_raise = ["409"]

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
                    logger.info("Anlysis with ID %s done", request_id)
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
