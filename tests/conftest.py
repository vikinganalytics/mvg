import os

import pytest
import requests
from mvg import MVG


import argparse
import sys

# This version of conftest.py adds some really ugly code to
# run the tests as integration tests by running like
# >pytest -s  tests --host http://127.0.0.1:8000
# As it is impossible to call a fixture outside a test
# and I did not find a way to disable docker compose
# the command line argument --host is consumed by argparse
# before being passed to pytest
# see https://izziswift.com/how-to-pass-arguments-in-pytest-by-command-line/

# needed, otherwise --host will fail pytest
def pytest_addoption(parser):
    parser.addoption("--host")


# ugly parser code
parser = argparse.ArgumentParser(description="run test on --host")
parser.add_argument(
    "--host", help="host to run tests on (default: %(default)s)", default=""
)
args, notknownargs = parser.parse_known_args()
sys.argv[1:] = notknownargs


# Retrieve API version to test against
version_session = MVG("https://api.beta.multiviz.com", "NO TOKEN")
VIBIUM_VERSION = "v" + str(version_session.tested_api_version)


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
if args.host == "":

    @pytest.fixture(scope="session")
    def vibium(docker_ip, docker_services, target_url):
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
