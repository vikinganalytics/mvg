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
    session.wait_for_analyses([request])
    status = session.get_analysis_status(request)
    assert status == "successful"
    assert f"{request}::{status}" in LOG_FILE.read_text()

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
    source_id, tabular_dict = tabular_source_with_measurements
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
