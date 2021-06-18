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
import numpy as np

VALID_TOKEN = os.environ["TEST_TOKEN"]

# Test data and session setup
REF_DB_PATH = Path.cwd() / "tests" / "test_data" / "mini_charlie"
SOURCE_ID_WAVEFORM = uuid.uuid1().hex  # generate a unique source per testrun
SOURCE_ID_TABULAR = uuid.uuid1().hex

tabular_df = pd.read_csv(REF_DB_PATH.parent / "tabular_data.csv")
tabular_dict = tabular_df.to_dict("list")


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

    try:
        session.get_source(SOURCE_ID_TABULAR)
        print(f"Deleting {SOURCE_ID_TABULAR}")
        session.delete_source(SOURCE_ID_TABULAR)
    except HTTPError:
        print(f"Source {SOURCE_ID_TABULAR} does not exist")

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
    session.create_source(SOURCE_ID_WAVEFORM, meta)
    # list_source happy case
    src = session.get_source(SOURCE_ID_WAVEFORM)
    assert src["source_id"] == SOURCE_ID_WAVEFORM
    assert src["meta"] == meta

    # update source
    meta["updated"] = "YES!"
    session.update_source(SOURCE_ID_WAVEFORM, meta)
    src = session.get_source(SOURCE_ID_WAVEFORM)
    assert src["source_id"] == SOURCE_ID_WAVEFORM
    assert src["meta"] == meta


# API GET    /sources/
def test_list_sources(session):
    sources = session.list_sources()
    print(sources)
    assert False in [SOURCE_ID_WAVEFORM != s["source_id"] for s in sources]


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
            sid=SOURCE_ID_WAVEFORM,
            duration=duration,
            timestamp=ts_m,
            data=accs,
            meta=meta_info,
        )

        # create again (ignore error)
        session.create_measurement(
            sid=SOURCE_ID_WAVEFORM,
            duration=duration,
            timestamp=ts_m,
            data=accs,
            meta=meta_info,
        )

        # read back and check
        m_back = session.read_single_measurement(SOURCE_ID_WAVEFORM, ts_m)
        assert m_back["data"] == accs
        assert m_back["meta"] == meta_info
        assert m_back["duration"] == duration

        # update
        meta_info["updated"] = "YES!"
        session.update_measurement(SOURCE_ID_WAVEFORM, ts_m, meta_info)

        # read back and check
        m_back = session.read_single_measurement(SOURCE_ID_WAVEFORM, ts_m)
        assert m_back["data"] == accs
        assert m_back["meta"] == meta_info
        assert m_back["duration"] == duration

        # delete
        session.delete_measurement(SOURCE_ID_WAVEFORM, ts_m)

    # check if empty
    m_left = session.list_measurements(SOURCE_ID_WAVEFORM)
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
        session.delete_measurement(SOURCE_ID_WAVEFORM, 314152)

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

    session.delete_source(SOURCE_ID_WAVEFORM)
    with pytest.raises(HTTPError) as exc:
        session.get_source(sid=SOURCE_ID_WAVEFORM)

    assert exc.value.response.status_code == 404
    print("Finishing")
    print(session.list_sources())


# API ignore existing
# API POST   /sources/
# API GET    /sources/{source_id}
# API POST   /sources/{source_id} - source exists, ignored
# API POST   /sources/{source_id} - source exists, not ignored
def test_sources_cru_existing(session):
    m_file_name = REF_DB_PATH / "u0001" / "meta.json"
    with open(m_file_name, "r") as json_file:
        meta = json.load(json_file)
    # create_source happy case
    session.create_source(SOURCE_ID_WAVEFORM, meta)
    # list_source happy case
    src = session.get_source(SOURCE_ID_WAVEFORM)
    assert src["source_id"] == SOURCE_ID_WAVEFORM
    assert src["meta"] == meta

    # create_source again (409 ignored)
    session.create_source(SOURCE_ID_WAVEFORM, meta)

    # create_source again (409 not ignored)
    session.do_not_raise = []
    with pytest.raises(HTTPError):
        session.create_source(SOURCE_ID_WAVEFORM, meta)


def test_tabular_sources(session):
    columns = tabular_df.columns.tolist()
    columns.remove("timestamp")
    meta = {"extra": "information"}
    session.create_tabular_source(SOURCE_ID_TABULAR, meta, columns)
    src = session.get_source(SOURCE_ID_TABULAR)
    assert src["source_id"] == SOURCE_ID_TABULAR
    assert src["meta"] == meta
    assert src["properties"]["columns"] == columns


def test_tabular_measurements_float_timestamps(session):
    with pytest.raises(HTTPError) as exc:
        tabular_dict_float = tabular_dict.copy()
        tabular_dict_float["timestamp"] = [ts + 0.1 for ts in tabular_dict["timestamp"]]
        session.create_tabular_measurement(SOURCE_ID_TABULAR, tabular_dict_float)
    assert exc.value.response.status_code == 422


def test_tabular_measurements(session):
    columns = tabular_df.columns.tolist()
    columns.remove("timestamp")
    session.create_tabular_measurement(SOURCE_ID_TABULAR, tabular_dict)

    ts0 = tabular_dict["timestamp"][0]
    meas = session.read_single_measurement(SOURCE_ID_TABULAR, ts0)
    assert meas["meta"] == {}
    assert all(np.array(meas["data"]) == tabular_df.drop("timestamp", axis=1).iloc[0])
    assert meas["columns"] == columns

    session.update_measurement(SOURCE_ID_TABULAR, ts0, {"new": "meta"})
    meas = session.read_single_measurement(SOURCE_ID_TABULAR, ts0)
    assert meas["meta"] == {"new": "meta"}

    session.delete_measurement(SOURCE_ID_TABULAR, ts0)
    with pytest.raises(HTTPError) as exc:
        session.read_single_measurement(SOURCE_ID_TABULAR, ts0)
    assert exc.value.response.status_code == 404


# End of code
