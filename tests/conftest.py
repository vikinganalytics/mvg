import os
from pathlib import Path

import pytest
import requests
import uuid
import json
import pandas as pd
from mvg import MVG
from mvg.exceptions import MVGAPIError

import argparse
import sys

from tests.helpers import (
    generate_sources_patterns,
    stub_multiaxial_data,
    upload_measurements,
)

VIBIUM_PROD_URL = "https://api.beta.multiviz.com/"


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
version_session = MVG(VIBIUM_PROD_URL, "NO TOKEN")
# VIBIUM_VERSION = str(version_session.tested_api_version)
VIBIUM_VERSION = "prod"



# Pytest initial configuration
def pytest_configure():
    pytest.SOURCE_ID_WAVEFORM = uuid.uuid1().hex
    pytest.REF_DB_PATH = Path.cwd() / "tests" / "test_data" / "mini_charlie"
    pytest.SOURCE_ID_TABULAR = uuid.uuid1().hex
    pytest.VALID_TOKEN = os.environ["TEST_TOKEN"]


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


@pytest.fixture()
def vibium_prod():
    return VIBIUM_PROD_URL


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
        port = docker_services.port_for("vibium-api", 8000)
        url = f"http://{docker_ip}:{port}"
        docker_services.wait_until_responsive(
            timeout=120.0, pause=0.1, check=lambda: is_responsive(url)
        )
        return url

else:

    @pytest.fixture(scope="session")
    # ugly function fetching golbal argument inside context
    def vibium():
        """Ensure that HTTP service is up and responsive."""
        return args.host


@pytest.fixture(scope="session")
def session(vibium) -> MVG:
    url = vibium
    print("Overriding vibium function with url %s", url)
    session = MVG(url, pytest.VALID_TOKEN)
    # To make sure we start from a clean slate
    # we delete our resource in case it exists
    # All information including measurements
    # will be removed
    # TO DO delete all so, currently we only
    # handle resource SOURCE_ID
    source = pytest.SOURCE_ID_WAVEFORM
    try:
        session.get_source(source)
        print(f"Deleting {source}")
        session.delete_source(source)
    except MVGAPIError:
        print(f"Source {source} does not exist")

    return session


@pytest.fixture()
def waveform_source(session):
    try:
        source = pytest.SOURCE_ID_WAVEFORM
        m_file_name = pytest.REF_DB_PATH / "u0001" / "meta.json"
        with open(m_file_name, "r") as json_file:
            meta = json.load(json_file)
        # create_source happy case
        session.create_source(source, channels=["acc"], meta=meta)
        yield source
    finally:
        session.delete_source(source)


@pytest.fixture()
def waveform_source_with_measurements(session, waveform_source):
    # get list of measurements
    src_path = pytest.REF_DB_PATH / "u0001"
    meas = {f.split(".")[0] for f in os.listdir(src_path)}
    meas.remove("meta")
    meas = [int(m) for m in meas]
    meas = list(meas)[0:40]

    # iterate over 40 meas (m is timestamp)
    for ts_m in meas:
        # samples file for one measurement
        ts_meas = str(ts_m) + ".csv"  # filename
        ts_meas = src_path / ts_meas  # path to file
        ts_df = pd.read_csv(
            ts_meas, names=["acc"], float_precision="round_trip"
        )  # read csv into df
        accs = ts_df.iloc[:, 0].tolist()  # convert to list
        print(f"Read {len(accs)} samples")

        # meta information file for one measurement
        ts_meta = str(ts_m) + ".json"  # filename
        ts_meta = src_path / ts_meta  # path
        with open(ts_meta, "r") as json_file:  # read json
            meas_info = json.load(json_file)  # into dict
            print(f"Read meta:{meas_info}")

        # get duration and other meta info
        duration = meas_info["duration"]
        meta_info = meas_info["meta"]

        # add sampling rate
        meta_info["sampling_rate"] = len(accs) / duration

        # create
        session.create_measurement(
            sid=waveform_source,
            duration=duration,
            timestamp=ts_m,
            data={"acc": accs},
            meta=meta_info,
        )

        # create again (ignore error)
        session.create_measurement(
            sid=waveform_source,
            duration=duration,
            timestamp=ts_m,
            data={"acc": accs},
            meta=meta_info,
            exist_ok=True,
        )

    yield waveform_source


def waveform_source_multiaxial_fixture_creator(source_id, pattern):
    @pytest.fixture
    def fixture(session):
        try:
            timestamps, data, _ = stub_multiaxial_data(pattern=pattern)
            session.create_source(
                source_id, meta={"type": "pump"}, channels=list(pattern.keys())
            )
            upload_measurements(session, source_id, data)
            yield source_id, timestamps
        finally:
            session.delete_source(source_id)

    return fixture


"""
Create multiaxial sources with generated measurements based on a pattern
"""
sources_pattern = generate_sources_patterns()
waveform_source_multiaxial_001 = waveform_source_multiaxial_fixture_creator(
    *sources_pattern[0]
)


@pytest.fixture()
def tabular_source(session):
    source_id = pytest.SOURCE_ID_TABULAR
    try:
        tabular_df = pd.read_csv(
            pytest.REF_DB_PATH.parent / "tabular_data.csv", float_precision="round_trip"
        )
        columns = tabular_df.columns.tolist()
        meta = {"extra": "information"}
        session.create_tabular_source(source_id, columns=columns, meta=meta)
        yield source_id, tabular_df.to_dict("list")
    finally:
        session.delete_source(source_id)


@pytest.fixture()
def tabular_source_with_measurements(session, tabular_source):
    source_id, tabular_dict = tabular_source
    session.create_tabular_measurement(source_id, tabular_dict)
    yield tabular_source
