from mvg.exceptions import MVGAPIError
from mvg.http_client import HTTPClient, RequestRetry

from pytest_localserver import http
import pytest


@pytest.fixture
def httpserver(request):
    server = http.ContentServer()
    server.start()
    request.addfinalizer(server.stop)
    yield server


def test_retry_default(httpserver):
    client = HTTPClient(endpoint=httpserver.url, token="")
    retries = client.retries.total
    status_forcelist = client.retries.status_forcelist
    status_code = status_forcelist[0]

    # Ask the server to return content with the provided status code
    httpserver.serve_content({}, code=status_code)
    with pytest.raises(MVGAPIError) as excinfo:
        client.request("get", "")

    assert excinfo.value.response.status_code == status_code
    assert len(httpserver.requests) == retries + 1


def test_retry_custom(httpserver):
    # Define retry for status code 402
    status_code = 402
    retries_obj = RequestRetry(
        total=3,
        status_forcelist=[status_code],
        raise_on_status=False,
        backoff_factor=0.5,
        remove_headers_on_redirect=[],
    )
    client = HTTPClient(endpoint=httpserver.url, token="", retries=retries_obj)
    retries = client.retries.total

    httpserver.serve_content({}, code=status_code)
    with pytest.raises(MVGAPIError) as exc:
        client.request("get", "")

    assert exc.value.response.status_code == status_code
    assert len(httpserver.requests) == retries + 1


def test_ignore_409(httpserver):
    # Define retry for status code 402
    client = HTTPClient(endpoint=httpserver.url, token="")
    status_code = 409

    httpserver.serve_content({}, code=status_code)
    client.request("get", "", do_not_raise=[status_code])
    assert len(httpserver.requests) == 1


def test_do_not_ignore_409(httpserver):
    # Define retry for status code 402
    client = HTTPClient(endpoint=httpserver.url, token="")
    status_code = 409

    httpserver.serve_content({}, code=status_code)
    with pytest.raises(MVGAPIError) as exc:
        client.request("get", "", do_not_raise=[])
    assert len(httpserver.requests) == 1


def test_no_retry(httpserver):
    client = HTTPClient(endpoint=httpserver.url, token="")
    # Successful request is assumed to be never retried
    status_code = 200

    httpserver.serve_content({}, code=status_code)
    client.request("get", "")
    assert len(httpserver.requests) == 1
