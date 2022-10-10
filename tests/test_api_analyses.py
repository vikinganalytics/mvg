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
    kpi = session.request_analysis(waveform_source_with_measurements, "KPIDemo")
    session.wait_for_analyses([kpi["request_id"]])
    status = session.get_analysis_status(kpi["request_id"])
    assert status == "successful"
    results = session.get_analysis_results(kpi["request_id"])
    assert len(results.keys()) == 7
    assert results["status"] == "successful"
    assert results["feature"] == "KPIDemo"
    kpi_results = results["results"]
    assert len(kpi_results.keys()) == 2
    assert len(kpi_results["acc"].keys()) == 7


@pytest.mark.skip(reason="callback feature")
def test_callback(session, callback_server, waveform_source_with_measurements):
    req = session.request_analysis(
        waveform_source_with_measurements, "KPIDemo", callback_url=callback_server
    )
    req_id = req["request_id"]
    session.wait_for_analyses([req_id])
    status = session.get_analysis_status(req_id)
    assert status == "successful"
    assert f"{req_id}::{status}" in LOG_FILE.read_text()


@pytest.mark.skip(reason="callback feature")
def test_callback_server_failure(
    session, callback_server, waveform_source_with_measurements
):
    req = session.request_analysis(
        waveform_source_with_measurements,
        "KPIDemo",
        callback_url=f"{callback_server}/fail",
    )
    session.wait_for_analyses([req["request_id"]])
    assert "400 Bad Request" in LOG_FILE.read_text()


def test_modeid_analysis_selected_columns(session, tabular_source_with_measurements):
    source_id, tabular_dict = tabular_source_with_measurements
    columns = list(tabular_dict.keys())

    def assert_results(selected_columns):
        req = session.request_analysis(
            source_id, "ModeId", selected_columns=selected_columns
        )
        session.wait_for_analyses([req["request_id"]])
        results = session.get_analysis_results(req["request_id"])
        assert results["inputs"]["selected_columns"] == (selected_columns or [])

    # Test with defined selected_columns
    assert_results(columns[1:3])

    # Test with defined selected_columns
    assert_results(None)


def test_modeid_analysis_selected_channels(session, waveform_source_multiaxial_001):
    source_id, _ = waveform_source_multiaxial_001
    source_info = session.get_source(source_id)
    channels = source_info["properties"]["channels"]

    def assert_results(selected_channels):
        req = session.request_analysis(
            source_id, "ModeId", selected_channels=selected_channels
        )
        session.wait_for_analyses([req["request_id"]])
        results = session.get_analysis_results(req["request_id"])
        assert results["inputs"]["selected_channels"] == (selected_channels or [])

    # Test with defined selected_channels
    assert_results(channels[:2])

    # Test with defined selected_channels
    assert_results(None)
