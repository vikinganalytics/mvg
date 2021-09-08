# pylint: disable=redefined-outer-name

"""
Tests in this file shall test analyses
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
SOURCE_ID_WAVEFORM = uuid.uuid1().hex  # generate a unique source per testrun


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

    m_file_name = REF_DB_PATH / "u0001" / "meta.json"
    with open(m_file_name, "r") as json_file:
        meta = json.load(json_file)
    # create_source happy case
    session.create_source(SOURCE_ID_WAVEFORM, meta)


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


@pytest.fixture()
def waveform_source_with_measurements(session, waveform_source):
    # get list of measurements
    src_path = REF_DB_PATH / "u0001"
    meas = {f.split(".")[0] for f in os.listdir(src_path)}
    meas.remove("meta")
    meas = [int(m) for m in meas]
    meas = list(meas)[0:40]

    # iterate over 40 meas (m is timestamp)
    for ts_m in meas:
        # samples file for one measurement
        ts_meas = str(ts_m) + ".csv"  # filename
        ts_meas = REF_DB_PATH / "u0001" / ts_meas  # path to file
        ts_df = pd.read_csv(
            ts_meas, names=["acc"], float_precision="round_trip"
        )  # read csv into df
        accs = ts_df.iloc[:, 0].tolist()  # convert to list
        print(f"Read {len(accs)} samples")

        # meta information file for one measurement
        ts_meta = str(ts_m) + ".json"  # filename
        ts_meta = REF_DB_PATH / "u0001" / ts_meta  # path
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
            sid=SOURCE_ID_WAVEFORM,
            duration=duration,
            timestamp=ts_m,
            data=accs,
            meta=meta_info,
        )

    yield waveform_source


def test_kpidemo_analysis(session, waveform_source):
    kpi = session.request_analysis(waveform_source, "KPIDemo")
    print(kpi)
    assert kpi["request_id"]
    session.wait_for_analyses(kpi["request_id"])
    status = session.get_analysis_status(kpi["request_id"])
    assert status == "successful"
    results = session.get_analysis_results(kpi["request_id"])
    assert len(results.keys()) == 7
    assert results["status"] == "successful"
    assert results["feature"] == "KPIDemo"
    kpi_results = results["results"]
    assert len(kpi_results.keys()) == 8
