# pylint: disable=redefined-outer-name

"""
Tests in this file shall test functionlity
relying on access to vibium-cloud API
Tests need to be run in order
-p no:randomly
"""
from pathlib import Path

import os
import json
import uuid
import pandas as pd
from requests import HTTPError
import pytest
from mvg import MVG

VALID_TOKEN = os.environ["TEST_TOKEN"]

# Test data and session setup
REF_DB_PATH = Path.cwd() / "tests" / "test_data" / "mini_charlie"
SOURCE_ID = uuid.uuid1().hex  # generate a unique source per testrun


# To override vibium with a locally running version
# @pytest.fixture(scope="session")
# def vibium():
#     url = "https://api.beta.multiviz.com"
#     # url = "http://127.0.0.1:8000"
#     return url


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
        session.get_source(SOURCE_ID)
        print(f"Deleting {SOURCE_ID}")
        session.delete_source(SOURCE_ID)
    except HTTPError:
        print(f"Source {SOURCE_ID} does not exist")

    return session


# Just to check if API is live
def test_say_hello(session):
    hello = session.say_hello()
    print(hello)
    assert hello is not None


# DB should be empty
# TODO check just for u0001 not in list


# API Successful transactions
# API POST   /sources/
# API GET    /sources/{source_id}
# API PUT    /sources/{source_id}
def test_sources_cru(session):
    m_file_name = REF_DB_PATH / "u0001" / "meta.json"
    with open(m_file_name, "r") as json_file:
        meta = json.load(json_file)
    # create_source happy case
    session.create_source(SOURCE_ID, meta)
    # list_source happy case
    src = session.get_source(SOURCE_ID)
    assert src["source_id"] == SOURCE_ID
    assert src["meta"] == meta

    # update source
    meta["updated"] = "YES!"
    session.update_source(SOURCE_ID, meta)
    src = session.get_source(SOURCE_ID)
    assert src["source_id"] == SOURCE_ID
    assert src["meta"] == meta


# API GET    /sources/
def test_list_sources(session):
    sources = session.list_sources()
    print(sources)
    assert False in [SOURCE_ID != s["source_id"] for s in sources]


# API GET    /sources/{source_id}/measurements
# API POST   /sources/{source_id}/measurements
# API GET    /sources/{source_id}/measurements/{timestamp}
# API PUT    /sources/{source_id}/measurements/{timestamp}
# API DELETE /sources/{source_id}/measurements/{timestamp}
def test_measurements_crud(session):

    # get list of measurements
    src_path = REF_DB_PATH / "u0001"
    meas = {f.split(".")[0] for f in os.listdir(src_path)}
    meas.remove("meta")
    meas = [int(m) for m in meas]
    meas = list(meas)[0:4]

    # iterate over 4 meas (m is timestamp)
    for ts_m in meas:

        # samples file for one measurement
        ts_meas = str(ts_m) + ".csv"  # filename
        ts_meas = REF_DB_PATH / "u0001" / ts_meas  # path to file
        ts_df = pd.read_csv(ts_meas, names=["acc"])  # read csv into df
        accs = ts_df.iloc[:, 0].tolist()  # convert to list
        print(f"Read {len(accs)} samples")

        # meta information file for one measurement
        ts_meta = str(ts_m) + ".json"  # filename
        ts_meta = REF_DB_PATH / "u0001" / ts_meta  # path
        with open(ts_meta, "r") as json_file:  # read json
            meas_info = json.load(json_file)  # into dict
            print("Read meta:{meas_info}")

        # get duration and other meta info
        duration = meas_info["duration"]
        meta_info = meas_info["meta"]

        # add sampling rate, not required by vibration API
        meta_info["sampling_rate"] = len(accs) / duration

        # create
        session.create_measurement(
            sid=SOURCE_ID, duration=duration, timestamp=ts_m, data=accs, meta=meta_info
        )

        # read back and check
        m_back = session.read_single_measurement(SOURCE_ID, ts_m)
        assert m_back["data"] == accs
        assert m_back["meta"] == meta_info
        assert m_back["timestamp"] == ts_m
        assert m_back["duration"] == duration

        # update
        meta_info["updated"] = "YES!"
        session.update_measurement(SOURCE_ID, ts_m, meta_info)

        # read back and check
        m_back = session.read_single_measurement(SOURCE_ID, ts_m)
        assert m_back["data"] == accs
        assert m_back["meta"] == meta_info
        assert m_back["timestamp"] == ts_m
        assert m_back["duration"] == duration

        # delete
        session.delete_measurement(SOURCE_ID, ts_m)

    # check if empty
    m_left = session.read_measurements(SOURCE_ID)
    assert len(m_left) == 0


# API POST   /sources/{source_id}/measurements [non-existing source]
def test_failure_create_measurement(session):

    with pytest.raises(HTTPError) as exc:
        data = [1, 2, 3]
        session.create_measurement(
            sid="", duration=-3, timestamp=-5, data=data, meta={}
        )
    assert exc.value.response.status_code == 404


# API GET    /sources/{source_id}//measurements/{timestamp} [non-existing meas]
def test_failure_get_measurement(session):

    with pytest.raises(HTTPError) as exc:
        session.delete_measurement(SOURCE_ID, 314152)

    assert exc.value.response.status_code == 404


# API GET    /sources/{source_id} [non-existing source]
def test_failure_get_source(session):

    with pytest.raises(HTTPError) as exc:
        session.get_source(sid="THE_VOID")

    assert exc.value.response.status_code == 404


# API DELETE /sources/{source_id} [non-existing source]
def test_failure_delete_source(session):

    with pytest.raises(HTTPError) as exc:
        session.delete_source(sid="THE_VOID")

    assert exc.value.response.status_code == 404


# API POST   /sources/ [incorrect source name]
def test_failure_create_source(session):
    with pytest.raises(HTTPError) as exc:
        session.create_source("unacceptable&name", {})
    assert exc.value.response.status_code == 422


# API POST   /sources/
# API DELETE /sources/{source_id}
def test_sources_d(session):

    session.delete_source(SOURCE_ID)
    with pytest.raises(HTTPError) as exc:
        session.get_source(sid=SOURCE_ID)

    assert exc.value.response.status_code == 404
    print("Finishing")
    print(session.list_sources())
