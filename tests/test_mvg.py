"""
Tests in this file shall test functionlity
not relying on access to vibium-cloud API
"""

from requests import HTTPError
import pytest
from mvg import MVG


def test_create_session_without_server():
    """We should get an HTTPError because we cannot connect to localhost:8000"""
    with pytest.raises(HTTPError):
        MVG("localhost:8000", "NO TOKEN")
