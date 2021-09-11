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
# Test data setup
REF_DB_PATH = Path.cwd() / "tests" / "test_data" / "mini_charlie"


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
            sid=waveform_source,
            duration=duration,
            timestamp=ts_m,
            data=accs,
            meta=meta_info,
        )

        # create again (ignore error)
        session.create_measurement(
            sid=waveform_source,
            duration=duration,
            timestamp=ts_m,
            data=accs,
            meta=meta_info,
            exist_ok=True,
        )

    yield waveform_source


def test_kpidemo_analysis(session, waveform_source_with_measurements):
    kpi = session.request_analysis(waveform_source_with_measurements, "KPIDemo")
    session.wait_for_analyses([kpi["request_id"]])
    status = session.get_analysis_status(kpi["request_id"])
    assert status == "successful"
    results = session.get_analysis_results(kpi["request_id"])
    assert len(results.keys()) == 7
    assert results["status"] == "successful"
    assert results["feature"] == "KPIDemo"
    kpi_results = results["results"]
    assert len(kpi_results.keys()) == 8
