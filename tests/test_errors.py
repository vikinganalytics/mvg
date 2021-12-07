"""
Tests in this file shall test functionlity
not relying on access to vibium-cloud API
"""

import pytest
import requests
from mvg.exceptions import MVGAPIError, raise_for_status


class MockResponse:
    def __init__(self, status_code, reason, json_body):
        self.status_code = status_code
        self.reason = reason
        self.json_body = json_body

    def json(self):
        return self.json_body

    def raise_for_status(self):
        if 400 <= self.status_code < 600:
            raise requests.HTTPError()


def test_raise_for_status_not_raises():
    response = MockResponse(200, "OK", {})
    raise_for_status(response)


def test_raise_for_status_raises():
    response = MockResponse(400, "Bad Request", {})
    with pytest.raises(MVGAPIError):
        raise_for_status(response)


def test_mvg_api_error_with_detail():
    response = MockResponse(400, "Bad Request", {"detail": "Client Error"})
    exc = MVGAPIError(response)
    assert str(exc) == "400 - Bad Request: Client Error"


def test_mvg_api_error_without_detail():
    response = MockResponse(400, "Bad Request", {})
    exc = MVGAPIError(response)
    assert str(exc) == "400 - Bad Request: No error detail"


def test_mvg_api_error_not_dict_response():
    response = MockResponse(400, "Bad Request", ["list", "data"])
    exc = MVGAPIError(response)
    assert str(exc) == "400 - Bad Request: No error detail"
