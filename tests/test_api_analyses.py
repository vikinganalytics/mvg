# pylint: disable=redefined-outer-name

"""
Tests in this file shall test analyses
relying on access to vibium-cloud API
Tests need to be run in order
-p no:randomly
"""

import os
import subprocess
import time
import socket
from pathlib import Path
import pytest

from mvg import MVG
from mvg.exceptions import MVGAPIError

LOG_FILE = Path("_callback_test_server_log.txt")


def get_ip():
    # based on https://stackoverflow.com/a/28950776/1292374
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


@pytest.fixture
def callback_server():
    with LOG_FILE.open("wt") as f:
        try:
            ip = get_ip()
            port = 9876
            process = subprocess.Popen(
                [
                    "uvicorn",
                    "tests.callback_test_server:app",
                    "--host",
                    ip,
                    "--port",
                    str(port),
                ],
                stderr=f,
                stdout=f,
            )
            time.sleep(5)  # Wait a moment for server to start
            yield f"http://{ip}:{port}"
        finally:
            process.kill()
            f.close()
            os.remove(LOG_FILE)


def test_kpidemo_sources(session: MVG, waveform_source_with_measurements):
    meas = session.list_measurements(waveform_source_with_measurements)
    assert len(meas) > 0


def test_kpidemo_analysis(session, waveform_source_with_measurements):
    request = session.request_analysis(waveform_source_with_measurements, "KPIDemo")
    request_id = request["request_id"]

    session.wait_for_analyses([request_id])
    status = session.get_analysis_status(request_id)
    assert status == "successful"
    results = session.get_analysis_results(request_id)
    assert len(results.keys()) == 7
    assert results["status"] == "successful"
    assert results["feature"] == "KPIDemo"
    kpi_results = results["results"]
    assert len(kpi_results.keys()) == 2
    assert len(kpi_results["acc"].keys()) == 7

    # Delete analysis
    session.delete_analysis(request_id)


@pytest.mark.skip(reason="callback feature")
def test_callback(session, callback_server, waveform_source_with_measurements):
    request = session.request_analysis(
        waveform_source_with_measurements, "KPIDemo", callback_url=callback_server
    )
    request_id = request["request_id"]
    session.wait_for_analyses([request_id])
    status = session.get_analysis_status(request_id)
    assert status == "successful"
    assert f"{request_id}::{status}" in LOG_FILE.read_text()

    # Delete analysis
    session.delete_analysis(request_id)


@pytest.mark.skip(reason="callback feature")
def test_callback_server_failure(
    session, callback_server, waveform_source_with_measurements
):
    request = session.request_analysis(
        waveform_source_with_measurements,
        "KPIDemo",
        callback_url=f"{callback_server}/fail",
    )
    request_id = request["request_id"]
    session.wait_for_analyses([request_id])
    assert "400 Bad Request" in LOG_FILE.read_text()

    # Delete analysis
    session.delete_analysis(request_id)


def test_modeid_analysis_selected_columns(session, tabular_source_with_measurements):
    source_id, tabular_dict, _ = tabular_source_with_measurements
    columns = list(tabular_dict.keys())

    def assert_results(selected_columns):
        parameters = {"n_trials": 1}
        request = session.request_analysis(
            source_id,
            "ModeId",
            selected_columns=selected_columns,
            parameters=parameters,
        )
        request_id = request["request_id"]
        session.wait_for_analyses([request_id])
        results = session.get_analysis_results(request_id)
        assert results["inputs"]["selected_columns"] == (selected_columns or [])

        # Delete analysis
        session.delete_analysis(request_id)

    # Test with defined selected_columns
    assert_results(columns[1:3])

    # Test with defined selected_columns
    assert_results(None)


def test_modeid_analysis_selected_channels(session, waveform_source_multiaxial_001):
    source_id, _ = waveform_source_multiaxial_001
    source_info = session.get_source(source_id)
    channels = source_info["properties"]["channels"]

    def assert_results(selected_channels):
        parameters = {"n_trials": 1}
        request = session.request_analysis(
            source_id,
            "ModeId",
            selected_channels=selected_channels,
            parameters=parameters,
        )
        request_id = request["request_id"]
        session.wait_for_analyses([request_id])
        results = session.get_analysis_results(request_id)
        assert results["inputs"]["selected_channels"] == (selected_channels or [])

        # Delete analysis
        session.delete_analysis(request_id)

    # Test with defined selected_channels
    assert_results(channels[:2])

    # Test with defined selected_channels
    assert_results(None)


def test_delete_analysis(session, waveform_source_multiaxial_001):
    source_id, _ = waveform_source_multiaxial_001
    parameters = {"n_trials": 10}
    request = session.request_analysis(
        sid=source_id, feature="ModeId", parameters=parameters
    )
    request_id = request["request_id"]

    # Deleting a queued analysis
    with pytest.raises(MVGAPIError) as exc:
        session.delete_analysis(request_id)

    session.wait_for_analyses([request_id])
    session.delete_analysis(request_id)

    # Accessing a deleted analysis
    with pytest.raises(MVGAPIError) as exc:
        session.get_analysis_results(request_id)
    assert f"Request with ID {request_id} does not exist" in str(exc)


def test_get_analysis_results_modeid_paginated(
    session: MVG, waveform_source_multiaxial_001
):
    source_id, source_info = waveform_source_multiaxial_001
    timestamps = source_info["timestamps"]
    pattern = source_info["pattern"]["acc_x"]

    # ModeId
    parameters = {"n_trials": 1}
    request = session.request_analysis(source_id, "ModeId", parameters=parameters)
    request_id = request["request_id"]
    response = session.get_analysis_results(request_id)
    assert response["results"] == {}
    session.wait_for_analyses([request_id])

    # Request for entire results
    response = session.get_analysis_results(request_id)
    assert timestamps == response["results"]["timestamps"]
    assert pattern == response["results"]["labels"]

    # Request for a subset of results with a limit
    result_size = 100
    response = session.get_analysis_results(request_id, limit=result_size)
    assert timestamps[:result_size] == response["results"]["timestamps"]
    assert pattern[:result_size] == response["results"]["labels"]

    # Request for a subset of results with a limit and an offset
    offset = 10
    result_size = 100
    response = session.get_analysis_results(
        request_id, offset=offset, limit=result_size
    )
    assert timestamps[offset:result_size] == response["results"]["timestamps"]
    assert pattern[offset:result_size] == response["results"]["labels"]

    # Request for a subset of results with an offset
    offset = 10
    response = session.get_analysis_results(request_id, offset=offset)
    assert timestamps[offset:] == response["results"]["timestamps"]
    assert pattern[offset:] == response["results"]["labels"]

    # Delete analysis
    session.delete_analysis(request_id)


def test_get_analysis_results_kpidemo_paginated(
    session: MVG, waveform_source_multiaxial_001
):
    source_id, source_info = waveform_source_multiaxial_001
    timestamps = source_info["timestamps"]

    request = session.request_analysis(source_id, "KPIDemo")
    request_id = request["request_id"]
    response = session.get_analysis_results(request_id)
    assert response["results"] == {}
    session.wait_for_analyses([request_id])

    # Request for entire results
    response = session.get_analysis_results(request_id)
    assert timestamps == response["results"]["timestamps"]

    # Request for a subset of results, but still returns entire results
    result_size = 10
    response = session.get_analysis_results(request_id, limit=result_size)
    assert timestamps == response["results"]["timestamps"]

    # Delete analysis
    session.delete_analysis(request_id)


def test_get_analysis_info(session: MVG, waveform_source_multiaxial_001):
    sid, _ = waveform_source_multiaxial_001
    request = session.request_analysis(sid, "KPIDemo")
    request_id = request["request_id"]

    analysis_info = session.get_analysis_info(request_id)
    assert isinstance(analysis_info, dict)
    assert analysis_info["request_status"] in ["queued", "running"]
    assert analysis_info["request_id"] == request_id

    session.wait_for_analyses([request_id])

    analysis_info = session.get_analysis_info(request_id)
    assert analysis_info["request_status"] == "successful"


def test_get_analysis_results_with_valid_result_type(
    session: MVG, waveform_source_multiaxial_001
):
    source_id, source_info = waveform_source_multiaxial_001
    timestamps = source_info["timestamps"]
    pattern = source_info["pattern"]

    parameters = {"n_trials": 1}
    request = session.request_analysis(source_id, "ModeId", parameters=parameters)
    request_id = request["request_id"]
    result_type = "compressed"
    session.wait_for_analyses([request_id])
    response = session.get_analysis_results(request_id, result_type=result_type)

    results = response["results"]
    num_timestamps_in_modes = [6, 14, 5]  # from the pattern
    assert response["status"] == "successful"
    assert results["count"] == num_timestamps_in_modes
    for channel in pattern.keys():
        assert all(label in pattern[channel] for label in results["label"])
    assert all(ts in timestamps for ts in results["start_timestamp"])
    assert all(ts in timestamps for ts in results["end_timestamp"])


def test_get_analysis_results_with_noncompliant_result_type(
    session: MVG, waveform_source_with_measurements
):
    source_id = waveform_source_with_measurements

    feature = "KPIDemo"
    request = session.request_analysis(source_id, feature)
    request_id = request["request_id"]
    result_type = "compressed"
    session.wait_for_analyses([request_id])

    with pytest.raises(MVGAPIError) as exc:
        session.get_analysis_results(request_id, result_type=result_type)
    assert f"Feature {feature} supports only result types in" in str(exc)


def test_get_analysis_results_with_invalid_result_type(
    session: MVG, waveform_source_with_measurements
):
    source_id = waveform_source_with_measurements

    request = session.request_analysis(source_id, "KPIDemo")
    request_id = request["request_id"]
    result_type = "someresultype"
    session.wait_for_analyses([request_id])

    with pytest.raises(MVGAPIError) as exc:
        session.get_analysis_results(request_id, result_type=result_type)
    assert f"Feature result type '{result_type}' does not exist." in str(exc)
