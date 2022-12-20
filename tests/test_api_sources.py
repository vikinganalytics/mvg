# pylint: disable=redefined-outer-name

"""
Tests in this file shall test functionlity
relying on access to vibium-cloud API
Tests need to be run in order
-p no:randomly
"""
from datetime import datetime, timedelta
import os
import json
import numpy as np
import pandas as pd
import pytest

from mvg.exceptions import MVGAPIError


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
    source = pytest.SOURCE_ID_WAVEFORM
    m_file_name = pytest.REF_DB_PATH / "u0001" / "meta.json"
    with open(m_file_name, "r") as json_file:
        meta = json.load(json_file)
    # create_source happy case
    session.create_source(source, meta=meta, channels=["acc"])
    # list_source happy case
    src = session.get_source(source)
    assert src["source_id"] == source
    assert src["meta"] == meta

    # update source
    meta["updated"] = "YES!"
    session.update_source(source, meta)
    src = session.get_source(source)
    assert src["source_id"] == source
    assert src["meta"] == meta


# API GET    /sources/
def test_list_sources(session):
    sources = session.list_sources()
    print(sources)
    assert False in [pytest.SOURCE_ID_WAVEFORM != s["source_id"] for s in sources]


# API GET    /sources/{source_id}/measurements
# API POST   /sources/{source_id}/measurements
# API GET    /sources/{source_id}/measurements/{timestamp}
# API PUT    /sources/{source_id}/measurements/{timestamp}
# API DELETE /sources/{source_id}/measurements/{timestamp}
def test_measurements_crud(session):
    source = pytest.SOURCE_ID_WAVEFORM
    # get list of measurements
    src_path = pytest.REF_DB_PATH / "u0001"
    meas = {f.split(".")[0] for f in os.listdir(src_path)}
    meas.remove("meta")
    meas = [int(m) for m in meas]
    meas = list(meas)[0:4]

    # iterate over 4 meas (m is timestamp)
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

        # add sampling rate, not required by vibration API
        meta_info["sampling_rate"] = len(accs) / duration

        # create
        session.create_measurement(
            sid=source,
            duration=duration,
            timestamp=ts_m,
            data={"acc": accs},
            meta=meta_info,
        )

        # create again (ignore error)
        session.create_measurement(
            sid=source,
            duration=duration,
            timestamp=ts_m,
            data={"acc": accs},
            meta=meta_info,
            exist_ok=True,
        )

        # read back and check
        m_back = session.read_single_measurement(source, ts_m)
        assert m_back["data"] == {"acc": accs}
        assert m_back["meta"] == meta_info
        assert m_back["duration"] == duration

        # update
        meta_info["updated"] = "YES!"
        session.update_measurement(source, ts_m, meta_info)

        # read back and check
        m_back = session.read_single_measurement(source, ts_m)
        assert m_back["data"] == {"acc": accs}
        assert m_back["meta"] == meta_info
        assert m_back["duration"] == duration

        # delete
        session.delete_measurement(source, ts_m)

    # check if empty
    m_left = session.list_measurements(source)
    assert len(m_left) == 0


# API POST   /sources/{source_id}/measurements [non-existing source]
def test_failure_create_measurement(session):

    with pytest.raises(MVGAPIError) as exc:
        data = [1, 2, 3]
        session.create_measurement(
            sid="", duration=-3, timestamp=-5, data=data, meta={}
        )
    assert exc.value.response.status_code == 404


# API GET    /sources/{source_id}//measurements/{timestamp} [non-existing meas]
def test_failure_get_measurement(session):

    with pytest.raises(MVGAPIError) as exc:
        session.delete_measurement(pytest.SOURCE_ID_WAVEFORM, 314152)

    assert exc.value.response.status_code == 404


# API GET    /sources/{source_id} [non-existing source]
def test_failure_get_source(session):

    with pytest.raises(MVGAPIError) as exc:
        session.get_source(sid="THE_VOID")

    assert exc.value.response.status_code == 404


# API DELETE /sources/{source_id} [non-existing source]
def test_failure_delete_source(session):

    with pytest.raises(MVGAPIError) as exc:
        session.delete_source(sid="THE_VOID")

    assert exc.value.response.status_code == 404


# API POST   /sources/ [incorrect source name]
def test_failure_create_source(session):
    with pytest.raises(MVGAPIError) as exc:
        session.create_source("unacceptable&name", meta={}, channels=["acc"])
    assert exc.value.response.status_code == 422


# API POST   /sources/
# API DELETE /sources/{source_id}
def test_sources_d(session):

    session.delete_source(pytest.SOURCE_ID_WAVEFORM)
    with pytest.raises(MVGAPIError) as exc:
        session.get_source(sid=pytest.SOURCE_ID_WAVEFORM)

    assert exc.value.response.status_code == 404
    print("Finishing")
    print(session.list_sources())


# API ignore existing
# API POST   /sources/
# API GET    /sources/{source_id}
# API POST   /sources/{source_id} - source exists, ignored
# API POST   /sources/{source_id} - source exists, not ignored
def test_sources_cru_existing(session):
    source = pytest.SOURCE_ID_WAVEFORM
    m_file_name = pytest.REF_DB_PATH / "u0001" / "meta.json"
    with open(m_file_name, "r") as json_file:
        meta = json.load(json_file)
    # create_source happy case
    session.create_source(source, meta=meta, channels=["acc"])
    # list_source happy case
    src = session.get_source(source)
    assert src["source_id"] == source
    assert src["meta"] == meta

    # create_source again (409 ignored)
    session.create_source(source, meta=meta, channels=["acc"], exist_ok=True)

    # create_source again (409 not ignored)
    with pytest.raises(MVGAPIError):
        session.create_source(source, meta=meta, channels=["acc"])


def test_tabular_sources(session, tabular_source):
    source_id, tabular_dict = tabular_source
    columns = list(tabular_dict.keys())
    meta = {"extra": "information"}

    # create source again (409 ignored)
    session.create_tabular_source(source_id, columns, meta, exist_ok=True)

    # create source again (409 not ignored)
    with pytest.raises(MVGAPIError) as exc:
        session.create_tabular_source(source_id, columns, meta)
    assert exc.value.response.status_code == 409

    columns.remove("timestamp")
    src = session.get_source(source_id)
    assert src["source_id"] == source_id
    assert src["meta"] == meta
    assert src["properties"]["columns"] == columns


def test_tabular_measurements_float_timestamps(session, tabular_source):
    with pytest.raises(MVGAPIError) as exc:
        source_id, tabular_dict = tabular_source
        tabular_dict_float = tabular_dict.copy()
        tabular_dict_float["timestamp"] = [ts + 0.1 for ts in tabular_dict["timestamp"]]
        session.create_tabular_measurement(source_id, tabular_dict_float)
    assert exc.value.response.status_code == 422


def test_tabular_measurements(session, tabular_source):
    source_id, tabular_dict = tabular_source
    columns = list(tabular_dict.keys())
    columns.remove("timestamp")
    tabular_df = pd.DataFrame(tabular_dict)

    # Create tabular measurement
    session.create_tabular_measurement(source_id, tabular_dict)

    # create measurements again (409 ignored)
    session.create_tabular_measurement(source_id, tabular_dict, exist_ok=True)

    # create measurements again (409 not ignored)
    with pytest.raises(MVGAPIError) as exc:
        session.create_tabular_measurement(source_id, tabular_dict)
    assert exc.value.response.status_code == 409

    # Validate read single measruement
    ts0 = tabular_dict["timestamp"][0]
    meas = session.read_single_measurement(source_id, ts0)
    assert meas["meta"] == {}
    assert all(np.array(meas["data"]) == tabular_df.drop("timestamp", axis=1).iloc[0])
    assert meas["columns"] == columns

    # Validate update measurement
    session.update_measurement(source_id, ts0, {"new": "meta"})
    meas = session.read_single_measurement(source_id, ts0)
    assert meas["meta"] == {"new": "meta"}

    # Validate delete measurement
    session.delete_measurement(source_id, ts0)
    with pytest.raises(MVGAPIError) as exc:
        session.read_single_measurement(source_id, ts0)
    assert exc.value.response.status_code == 404


def test_list_tabular_measurements(session, tabular_source):
    source_id, tabular_dict = tabular_source
    columns = list(tabular_dict.keys())

    ts_0 = tabular_dict["timestamp"][0]
    ts_1 = tabular_dict["timestamp"][1]
    ts_n = tabular_dict["timestamp"][-1]

    # Metadata for two timestamps
    meta = {
        f"{ts_0}": {"new": "meta for {ts_0}"},
        f"{ts_1}": {"new": "meta for {ts_1}"},
    }

    # Create all measurements
    session.create_tabular_measurement(source_id, tabular_dict, meta)

    # Retrieve data for a segment (1..n)
    response = session.list_tabular_measurements(source_id, ts_1, ts_n)
    assert all(
        tabular_dict[column][1:] == response["data"][column] for column in columns
    )
    assert len(response["meta"].keys()) == 1
    assert response["meta"][f"{ts_1}"] == meta[f"{ts_1}"]

    # Retrieve entire data (0..n)
    response = session.list_tabular_measurements(source_id, None, None)
    assert all(tabular_dict[column] == response["data"][column] for column in columns)
    assert len(response["meta"].keys()) == 2
    assert response["meta"][f"{ts_0}"] == meta[f"{ts_0}"]
    assert response["meta"][f"{ts_1}"] == meta[f"{ts_1}"]

    # Retrieve data that is beyond the range of the dataset timestamps
    with pytest.raises(MVGAPIError) as exc:
        session.list_tabular_measurements(source_id, ts_n + 1, ts_n + 2)
    assert exc.value.response.status_code == 404

    # Call API with negative timestamp
    with pytest.raises(MVGAPIError) as exc:
        session.list_tabular_measurements(source_id, -1)
    assert exc.value.response.status_code == 422

    # Call API with negative timestamp
    with pytest.raises(MVGAPIError) as exc:
        session.list_tabular_measurements(source_id, None, -1)
    assert exc.value.response.status_code == 422


def test_list_tabular_downsampled_measurements(session, tabular_source):
    source_id, tabular_dict = tabular_source

    # Create all measurements
    session.create_tabular_measurement(source_id, tabular_dict)

    # Unsuccessfull call to API using a negative threshold
    with pytest.raises(MVGAPIError) as exc:
        session.list_tabular_downsampled_measurements(source_id, -1)
    assert exc.value.response.status_code == 422

    # Successfull call to API requesting downsampled data
    threshold = 2
    response = session.list_tabular_downsampled_measurements(source_id, threshold)
    assert len(response["data"]) > 0
    assert all(
        len(value["x"]) == threshold and len(value["y"]) == threshold
        for value in list(response["data"].values())
    )


def test_create_label(session, tabular_source_with_measurements):
    source_id, tabular_dict = tabular_source_with_measurements
    timestamps = tabular_dict["timestamp"]
    label1 = {"label": "normal", "severity": 0, "notes": ""}
    label2 = {"label": "failure", "severity": 100, "notes": "This is really bad!"}

    session.create_label(source_id, timestamps[0], **label1)
    session.create_label(source_id, timestamps[1], **label2)

    label1_response = session.get_label(source_id, timestamps[0])
    label2_response = session.get_label(source_id, timestamps[1])

    labels = session.list_labels(source_id)

    # Remove label creation timestamps
    labels.pop("label_timestamp")
    assert labels == {
        "timestamp": timestamps[0:2],
        "label": [label1["label"], label2["label"]],
        "severity": [label1["severity"], label2["severity"]],
        "notes": [label1["notes"], label2["notes"]],
    }

    label1_timestamp = label1_response.pop("label_timestamp")
    dtdiff1 = datetime.utcnow() - datetime.strptime(
        label1_timestamp, "%Y-%m-%d %H:%M:%S"
    )
    assert label1_response == label1
    assert dtdiff1 < timedelta(minutes=1)

    label2_timestamp = label2_response.pop("label_timestamp")
    dtdiff2 = datetime.utcnow() - datetime.strptime(
        label2_timestamp, "%Y-%m-%d %H:%M:%S"
    )
    assert label2_response == label2
    assert dtdiff2 < timedelta(minutes=1)


def test_update_label(session, tabular_source_with_measurements):
    source_id, tabular_dict = tabular_source_with_measurements
    timestamps = tabular_dict["timestamp"]
    label_pre = {"label": "failure", "severity": 100, "notes": "This is really bad!"}
    session.create_label(source_id, timestamps[0], **label_pre)

    label_post = {"label": "normal", "severity": 0, "notes": "It wasn't so bad"}
    session.update_label(source_id, timestamps[0], **label_post)

    label_response = session.get_label(source_id, timestamps[0])

    label_timestamp = label_response.pop("label_timestamp")
    dtdiff = datetime.utcnow() - datetime.strptime(label_timestamp, "%Y-%m-%d %H:%M:%S")
    assert label_response == label_post
    assert dtdiff < timedelta(minutes=1)


def test_delete_label(session, tabular_source_with_measurements):
    source_id, tabular_dict = tabular_source_with_measurements
    timestamps = tabular_dict["timestamp"]
    session.create_label(
        source_id,
        timestamps[0],
        "failure",
        100,
        "This is really bad!",
    )

    session.delete_label(source_id, timestamps[0])
    with pytest.raises(MVGAPIError) as exc:
        session.get_label(source_id, timestamps[0])
        assert exc.value.response.status_code == 404


def test_list_labels(session, tabular_source_with_measurements):
    source_id, tabular_dict = tabular_source_with_measurements
    timestamps = tabular_dict["timestamp"]
    for k in [0, -1]:
        session.create_label(
            source_id,
            timestamps[k],
            "failure",
            100,
            "This is really bad!",
        )

    list_short = session.list_labels(source_id, include_unlabeled=False)
    list_short.pop("label_timestamp")
    assert list_short == {
        "timestamp": [43854, 44080],
        "label": ["failure", "failure"],
        "severity": [100, 100],
        "notes": ["This is really bad!", "This is really bad!"],
    }

    list_long = session.list_labels(source_id, include_unlabeled=True)
    assert list_long["timestamp"] == tabular_dict["timestamp"]
    assert list_long["label"][0] == "failure"
    assert list_long["label"][-1] == "failure"
    assert np.all(np.isnan(np.array(list_long["label"][1:-2])))


# End of code
