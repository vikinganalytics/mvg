# pylint: disable=redefined-outer-name

"""
Tests in this file shall test analyses
relying on access to vibium-cloud API
Tests need to be run in order
-p no:randomly
"""
from pathlib import Path

import pytest
from mvg import MVG

# Test data setup
REF_DB_PATH = Path.cwd() / "tests" / "test_data" / "mini_charlie"


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
