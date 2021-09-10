import os
from pathlib import Path

import pytest
import requests
from mvg import MVG
import uuid
import json

import argparse
import sys
from requests import HTTPError

# This version of conftest.py adds some really ugly code to
# run the tests as integration tests by running like
# > pytest -s  tests --host http://127.0.0.1:8000
# As it is impossible to call a fixture outside a test
# and I did not find a way to disable docker compose
# the command line argument --host is consumed by argparse
# before being passed to pytest
# see https://izziswift.com/how-to-pass-arguments-in-pytest-by-command-line/


# Stuff for --host
# needed, otherwise --host will fail pytest
def pytest_addoption(parser):
    parser.addoption("--host")


# consume --host via argparse
parser = argparse.ArgumentParser(description="run test on --host")
parser.add_argument(
    "--host", help="host to run tests on (default: %(default)s)", default=""
)
args, notknownargs = parser.parse_known_args()
sys.argv[1:] = notknownargs


# Retrieve API version to test against
version_session = MVG("https://api.beta.multiviz.com", "NO TOKEN")
VIBIUM_VERSION = "v" + str(version_session.tested_api_version)

VALID_TOKEN = os.environ["TEST_TOKEN"]

# Test data and session setup
REF_DB_PATH = Path.cwd() / "tests" / "test_data" / "mini_charlie"
SOURCE_ID_WAVEFORM = uuid.uuid1().hex  # generate a unique source per testrun


def is_responsive(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return True
    except requests.exceptions.ConnectionError:
        return False


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    os.environ["VIBIUM_VERSION"] = VIBIUM_VERSION
    return pytestconfig.rootdir / "tests" / "docker-compose.yml"


# ugly vibium fixture configuration
# Here we need to switch between vibium fixture
# for docker-run (--host not set)
# or for run towards a running server
# e.g. --host http://127.0.0.1:8000
# the token shall be stored in an environemnt variable
# TEST_TOKEN
if args.host == "":

    @pytest.fixture(scope="session")
    def vibium(docker_ip, docker_services):
        """Ensure that HTTP service is up and responsive."""
        # `port_for` takes a container port and returns the corresponding host port
        port = docker_services.port_for("vibium", 8000)
        url = "http://{}:{}".format(docker_ip, port)
        docker_services.wait_until_responsive(
            timeout=30.0, pause=0.1, check=lambda: is_responsive(url)
        )
        return url


else:

    @pytest.fixture(scope="session")
    # ugly function fetching golbal argument inside context
    def vibium():
        """Ensure that HTTP service is up and responsive."""
        return args.host


@pytest.fixture(scope="session")
def session(vibium):

    url = vibium
    print("Overriding vibium function with url %s", url)
    session = MVG(url, VALID_TOKEN)
    # To make sure we start from a clean slate
    # we delete our resource in case it exists
    # All information including measurements
    # will be removed
    # TO DO delete all so, currently we only
    # handle resource SOURCE_ID
    try:
        session.get_source(SOURCE_ID_WAVEFORM)
        print(f"Deleting {SOURCE_ID_WAVEFORM}")
        session.delete_source(SOURCE_ID_WAVEFORM)
    except HTTPError:
        print(f"Source {SOURCE_ID_WAVEFORM} does not exist")

    return session


@pytest.fixture()
def waveform_source(session):
    try:
        m_file_name = REF_DB_PATH / "u0001" / "meta.json"
        with open(m_file_name, "r") as json_file:
            meta = json.load(json_file)
        # create_source happy case
        session.create_source(SOURCE_ID_WAVEFORM, meta)
        yield SOURCE_ID_WAVEFORM
    finally:
        session.delete_source(SOURCE_ID_WAVEFORM)
