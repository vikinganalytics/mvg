import logging
from requests import Session
from requests.adapters import HTTPAdapter, Retry
from mvg.exceptions import raise_for_status

logger = logging.getLogger(__name__)


class RequestRetry(Retry):
    """
    Retry with logging
    """

    def __init__(
        self,
        total=3,
        status_forcelist=frozenset([500, 502, 503, 504]),
        raise_on_status=False,
        backoff_factor=0.5,
        remove_headers_on_redirect=frozenset(),
        **kwargs,
    ):
        if kwargs.get("history"):
            request = kwargs.get("history")[-1]
            logger.warning(
                f"Retring request {request[1]} with status code {request[3]}"
            )

        super().__init__(
            total=total,
            status_forcelist=status_forcelist,
            raise_on_status=raise_on_status,
            backoff_factor=backoff_factor,
            remove_headers_on_redirect=remove_headers_on_redirect,
            **kwargs,
        )


class HTTPClient:
    def __init__(
        self,
        endpoint,
        token,
        mvg_version=None,
        retries=None,
        timeout=120,
    ):
        self.endpoint = endpoint
        self.token = token
        self.timeout = timeout
        self.mvg_version = mvg_version

        self.retries = retries
        if not self.retries:
            self.retries = RequestRetry()

    def request(self, method, path, headers=None, do_not_raise=None, **kwargs):
        response = None
        with Session() as session:
            session.mount("http://", HTTPAdapter(max_retries=self.retries))
            session.mount("https://", HTTPAdapter(max_retries=self.retries))

            _headers = {
                "Authorization": f"Bearer {self.token}",
                "User-Agent": f"mvg/{self.mvg_version}",
            }
            if headers:
                _headers.update(headers)

            response = session.request(
                method=method,
                url=self.endpoint + path,
                headers=_headers,
                timeout=self.timeout,
                **kwargs,
            )

            if do_not_raise is None:
                do_not_raise = []

            if response.status_code in do_not_raise:
                logger.warning(
                    f"Ignoring error {response.status_code} - {response.text}"
                )
            else:
                raise_for_status(response)

        return response
