from json.decoder import JSONDecodeError
from requests import HTTPError, Response


class MVGError(Exception):
    """Base class for MVG Exceptions"""


class MVGConnectionError(MVGError):
    """Raised on failure to connect to API"""


class MVGAPIError(MVGError):
    """Raised then there has been an error with a request"""

    def __init__(self, response: Response):
        self.response = response
        self.msg = self._get_error_message()
        super().__init__(
            f"{self.response.status_code} - {self.response.reason}: {self.msg}"
        )

    def _get_error_message(self):
        default_error_msg = "No error detail"
        try:
            response_body = self.response.json()
            return response_body.get("detail", default_error_msg)
        except (JSONDecodeError, AttributeError):
            return default_error_msg


def raise_for_status(response: Response):
    try:
        response.raise_for_status()
    except HTTPError:
        raise MVGAPIError(response)
