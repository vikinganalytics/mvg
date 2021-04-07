import os

import pytest
import requests
from mvg import MVG

# Retrieve API version to test against
session = MVG("NO ENDPOINT", "NO TOKEN")
VIBIUM_VERSION = "v" + str(session.tested_api_version)


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
