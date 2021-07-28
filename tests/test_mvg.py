"""
Tests in this file shall test functionlity
not relying on access to vibium-cloud API
"""

import pytest
import requests
from mvg import MVG


def test_create_session_without_server():
    """We should get an HTTPError because we cannot connect to localhost:8000"""
    with pytest.raises(requests.ConnectionError):
        MVG("localhost:8000", "NO TOKEN")
