# pylint: disable=redefined-outer-name
# pylint: disable=W0212
"""
Tests in this file shall test general API functionality
"""

import os
import pytest
import semver
from requests import HTTPError
import requests
from mvg import MVG

VALID_TOKEN = os.environ["TEST_TOKEN"]


# API        /
def test_say_hello(vibium):
    session = MVG(vibium, "NO TOKEN")
    hello = session.say_hello()
    print(hello)
    assert session.say_hello() is not None


# API        /
# Test version handling
def test_check_version(vibium):

    # Get current API version for testing
    session = MVG(vibium, "NO TOKEN")

    # Check OK run
    session.tested_api_version = session.api_version
    assert session.check_version()["api_version"] == session.api_version

    # Check Incompatible Major version. Note: This test does not work locally
    session.tested_api_version = semver.VersionInfo(major=100)
    with pytest.raises(ValueError):
        session.check_version()

    # Check to high highest tested version
    session.tested_api_version = session.api_version.bump_minor()
    with pytest.raises(ValueError):
        session.check_version()

    # Check API minor version higher
    session.api_version = session.tested_api_version.bump_minor()
    with pytest.raises(UserWarning):
        session.check_version()

    # Check version with pre-release
    session.tested_api_version = session.api_version.bump_prerelease()
    session.check_version()


# Test for features
# TODO decide on feature content per release
# API GET    /analyses
def test_supported_features(vibium):
    session = MVG(vibium, VALID_TOKEN)
    resp = session.supported_features()
    print(resp)
    assert resp["ModeId"]


# API GET    /analyses [unauthorized]
def test_failure_authorization(vibium):
    unauth_session = MVG(vibium, "NO TOKEN")

    with pytest.raises(HTTPError) as exc:
        unauth_session.supported_features()

    assert exc.value.response.status_code == 401


def test_create_session_invalid_url():
    with pytest.raises(requests.ConnectionError):
        MVG("invalidurl", "NO TOKEN")
