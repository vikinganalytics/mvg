# pylint: disable=redefined-outer-name

"""
Tests in this file shall test functionlity
relying on access to vibium-cloud API
Tests need to be run in order
-p no:randomly
"""
import json
import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from mvg.exceptions import MVGAPIError
from mvg.mvg import MVG
from mvg.utils.response_processing import get_paginated_items
from tests.helpers import (
    generate_random_source_id,
    make_channel_names,
    simulate_spectrum_data,
)


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


def test_get_source_spectrum_source(session: MVG):
    source_id = generate_random_source_id()
    channels = make_channel_names(n_channels=1)
    
    m_file_name = pytest.REF_DB_PATH / "u0001" / "meta.json"
    with open(m_file_name, "r") as json_file:
        meta = json.load(json_file)
    meta["extra"] = "pump"

    try:
        session.create_spectrum_source(source_id, channels=channels, meta=meta)
        source = session.get_source(source_id)

        # Check received source data
        assert source["source_id"] == source_id
        assert source["meta"] == meta

        props = source["properties"]
        assert props["data_class"] == "spectrum"
        assert props["channels"] == channels
    finally:
        session.delete_source(source_id)

    # Check that the source has been removed
    with pytest.raises(MVGAPIError) as exc:
        session.get_source(source_id)
    assert exc.value.response.status_code == 404
    assert f"Source ID: {source_id} does not exist!" in str(exc.value)


def test_create_spectrum_source_existing(
    session: MVG, spectrum_source_with_zero_measurements
):
    source_id, source_info = spectrum_source_with_zero_measurements

    # create existing source (409 not ignored)
    with pytest.raises(MVGAPIError) as exc:
        session.create_spectrum_source(
            sid=source_id, channels=source_info["channels"], meta=source_info["meta"]
        )
    assert exc.value.response.status_code == 409


def test_create_spectrum_source_ignore_409(
    session: MVG, spectrum_source_with_zero_measurements
):
    source_id, source_info = spectrum_source_with_zero_measurements
    # create existing source (409 ignored)
    session.create_spectrum_source(
        sid=source_id,
        channels=source_info["channels"],
        meta=source_info["meta"],
        exist_ok=True,
    )


def test_create_spectrum_measurement_new_measurement(
    session: MVG, spectrum_source_with_zero_measurements
):
    source_id, source_info = spectrum_source_with_zero_measurements

    _, measurements = simulate_spectrum_data(
        pattern=[0], channels=source_info["channels"]
    )
    for measurement in measurements:
        session.create_spectrum_measurement(sid=source_id, **measurement)

    # Check received source data
    list_measurements = session.list_measurements(source_id)
    assert len(list_measurements) == 1

    assert list_measurements[0]["timestamp"] == measurement["timestamp"]
    assert list_measurements[0]["freq_range"] == measurement["freq_range"]
    assert list_measurements[0]["meta"] == measurement["meta"]


def test_create_spectrum_measurement_existing(
    session: MVG, spectrum_source_with_measurements
):
    source_id, source_info = spectrum_source_with_measurements
    data = source_info["measurements"][0]

    # create existing measurement (409 not ignored)
    with pytest.raises(MVGAPIError) as exc:
        session.create_spectrum_measurement(sid=source_id, **data)
    assert exc.value.response.status_code == 409


def test_create_spectrum_measurement_ignore_409(
    session: MVG, spectrum_source_with_measurements
):
    source_id, source_info = spectrum_source_with_measurements
    data = source_info["measurements"][0]

    # create existing measurement (409 ignored)
    session.create_spectrum_measurement(sid=source_id, exist_ok=True, **data)


def test_tabular_sources(session, tabular_source):
    source_id, tabular_dict, meta = tabular_source
    columns = list(tabular_dict.keys())

    # create source again (409 not ignored)
    with pytest.raises(MVGAPIError) as exc:
        session.create_tabular_source(source_id, columns, meta)
    assert exc.value.response.status_code == 409

    # create source again (409 ignored)
    session.create_tabular_source(source_id, columns, meta, exist_ok=True)

    columns.remove("timestamp")
    src = session.get_source(source_id)
    assert src["source_id"] == source_id
    assert src["meta"] == meta
    assert src["properties"]["columns"] == columns


def test_tabular_measurements_float_timestamps(session, tabular_source):
    with pytest.raises(MVGAPIError) as exc:
        source_id, tabular_dict, _ = tabular_source
        tabular_dict_float = tabular_dict.copy()
        tabular_dict_float["timestamp"] = [ts + 0.1 for ts in tabular_dict["timestamp"]]
        session.create_tabular_measurement(source_id, tabular_dict_float)
    assert exc.value.response.status_code == 422


def test_tabular_measurements(session, tabular_source):
    source_id, tabular_dict, _ = tabular_source
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
    source_id, tabular_dict, _ = tabular_source
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
    assert all(tabular_dict[column][1:] == response[column] for column in columns)

    # Retrieve entire data (0..n)
    response = session.list_tabular_measurements(
        source_id, start_timestamp=ts_0, end_timestamp=ts_n
    )
    assert all(tabular_dict[column] == response[column] for column in columns)

    # Retrieve one page (0..MAX_PAGE_LIMIT)
    response = session.list_tabular_measurements(source_id)
    assert all(tabular_dict[column] == response[column] for column in columns)

    # Retrieve data that is beyond the range of the dataset timestamps
    response = session.list_tabular_measurements(source_id, ts_n + 1, ts_n + 2)
    assert all(response[column] == [] for column in columns)

    # Call API with negative timestamp
    with pytest.raises(MVGAPIError) as exc:
        session.list_tabular_measurements(source_id, -1)
    assert exc.value.response.status_code == 422

    # Call API with negative timestamp
    with pytest.raises(MVGAPIError) as exc:
        session.list_tabular_measurements(source_id, None, -1)
    assert exc.value.response.status_code == 422


def test_list_tabular_downsampled_measurements(
    session, tabular_source_with_measurements
):
    source_id, tabular_dict, _ = tabular_source_with_measurements

    # Unsuccessful call to API using a negative threshold
    with pytest.raises(MVGAPIError) as exc:
        session.list_tabular_downsampled_measurements(source_id, -1)
    assert exc.value.response.status_code == 422

    # Successful call to API requesting downsampled data
    threshold = 2
    response_threshold = session.list_tabular_downsampled_measurements(
        source_id, threshold
    )
    assert len(response_threshold["data"]) > 0
    assert all(
        # Ensure number of timestamps and values equals threshold value
        len(value["timestamps"]) == threshold and len(value["values"]) == threshold
        for value in list(response_threshold["data"].values())
    )

    # Successful call to API requesting a specific time range
    timestamps = sorted(tabular_dict["timestamp"])
    start_timestamp = timestamps[len(timestamps) // 5]
    end_timestamp = timestamps[len(timestamps) - len(timestamps) // 5]
    response_time_range = session.list_tabular_downsampled_measurements(
        source_id,
        threshold=0,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
    )
    assert len(response_time_range["data"]) > 0
    assert all(
        # Ensure response timestamps are within given timestamp range
        all(
            timestamp in range(start_timestamp, end_timestamp + 1)
            for timestamp in kpi["timestamps"]
        )
        for kpi in response_time_range["data"].values()
    )


def test_create_label(session, tabular_source_with_measurements):
    source_id, tabular_dict, _ = tabular_source_with_measurements
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
    dtdiff1 = datetime.now().astimezone() - datetime.strptime(
        label1_timestamp, "%Y-%m-%d %H:%M:%S%z"
    )
    assert label1_response == label1
    assert dtdiff1 < timedelta(minutes=1)

    label2_timestamp = label2_response.pop("label_timestamp")
    dtdiff2 = datetime.now().astimezone() - datetime.strptime(
        label2_timestamp, "%Y-%m-%d %H:%M:%S%z"
    )
    assert label2_response == label2
    assert dtdiff2 < timedelta(minutes=1)


def test_update_label(session, tabular_source_with_measurements):
    source_id, tabular_dict, _ = tabular_source_with_measurements
    timestamps = tabular_dict["timestamp"]
    label_pre = {"label": "failure", "severity": 100, "notes": "This is really bad!"}
    session.create_label(source_id, timestamps[0], **label_pre)

    label_post = {"label": "normal", "severity": 0, "notes": "It wasn't so bad"}
    session.update_label(source_id, timestamps[0], **label_post)

    label_response = session.get_label(source_id, timestamps[0])

    label_timestamp = label_response.pop("label_timestamp")
    dtdiff = datetime.now().astimezone() - datetime.strptime(
        label_timestamp, "%Y-%m-%d %H:%M:%S%z"
    )
    assert label_response == label_post
    assert dtdiff < timedelta(minutes=1)


def test_delete_label(session, tabular_source_with_measurements):
    source_id, tabular_dict, _ = tabular_source_with_measurements
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
    source_id, tabular_dict, _ = tabular_source_with_measurements
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


def test_pagination(session, tabular_source_with_measurements):
    sid, tabular_dict, _ = tabular_source_with_measurements
    timestamps = tabular_dict["timestamp"]
    num_meas = len(timestamps)

    # default offset and limit
    response = session.list_measurements(sid)
    assert len(response) == num_meas

    response = session.list_tabular_measurements(sid)
    assert len(response["timestamp"]) == num_meas

    response = session.list_timestamps(sid)
    assert len(response["items"]) == num_meas

    # non-default offset
    offset = num_meas // 3
    response = session.list_measurements(sid, offset=offset)
    assert len(response) == num_meas - offset

    response = session.list_tabular_measurements(sid, offset=offset)
    assert len(response["timestamp"]) == num_meas - offset

    response = session.list_timestamps(sid, offset=offset)
    assert response["total"] == num_meas
    assert len(response["items"]) == num_meas - offset

    # non-default limit
    limit = num_meas // 10
    response = session.list_measurements(sid, limit=limit)
    assert len(response) == limit

    response = session.list_tabular_measurements(sid, limit=limit)
    assert len(response["timestamp"]) == limit

    response = session.list_timestamps(sid, limit=limit)
    assert response["total"] == num_meas
    assert len(response["items"]) == limit

    # test order=asc
    response = session.list_timestamps(sid, order="asc")
    assert response["items"] == sorted(response["items"])

    # test order=desc
    response = session.list_timestamps(sid, order="desc")
    assert response["items"] == sorted(response["items"], reverse=True)


def test_pagination_limits(session, tabular_source_with_measurements):
    # API sets the limits for pagination which MVG is not aware of. The source
    # fixtures defined in MVG might have measurements less than the pagination
    # limits. This test enhances the fixtures beyond the pagination limits to
    # run tests

    sid, tabular_dict, _ = tabular_source_with_measurements
    end_timestamp = tabular_dict["timestamp"][-1]
    num_meas = len(tabular_dict["timestamp"])

    # Find the default pagination limits of the API
    url = f"/sources/{sid}/measurements"
    paginated_items = get_paginated_items(session._request, url, {})
    measurements_limit = paginated_items["limit"]

    # Prepare measurements upto "x" times the limit
    n_times = 2 * measurements_limit
    new_timestamps = [end_timestamp + i for i in range(1, n_times + 1)]
    data = {
        col: n_times * [values[-1]]
        for col, values in tabular_dict.items()
        if col != "timestamp"
    }
    data["timestamp"] = new_timestamps

    # Add measurements
    session.create_tabular_measurement(sid, data)
    for column in tabular_dict:
        tabular_dict[column].extend(data[column])

    # Number of new + existing measurements
    num_new_meas = len(tabular_dict["timestamp"])
    # Assert we have the expected number of measurements
    assert num_new_meas == num_meas + n_times

    # Default offset and limit
    response = session.list_measurements(sid)
    assert len(response) == num_new_meas

    # Non-default limit
    limit = num_new_meas // 2
    response = session.list_measurements(sid, limit=limit)
    assert len(response) == limit
