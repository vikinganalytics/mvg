"""
Tests in this file shall test functionlity
not relying on access to vibium-cloud API
"""

import json
import os
import tempfile
import pandas as pd
import pytest
from mvg import analysis_classes
from mvg.analysis_classes import parse_results


def test_RMS():
    # read dict
    with open("./tests/test_data/RMS_results_dict.json") as json_file:
        api_results = json.load(json_file)

    # get object
    feat = parse_results(api_results, t_zone=None, t_unit=None)

    # Check dataframe conversion - columns
    assert set(feat.to_df().columns.values) == set(api_results["results"].keys())

    # Check dataframe conversion - length
    assert len(feat.to_df()["timestamps"]) == len(api_results["results"]["timestamps"])

    # Test datetime conversion
    feat = analysis_classes.RMS(api_results, t_zone="Europe/Stockholm", t_unit="s")
    assert str(feat.to_df()["datetime"][0]) == "2019-10-04 13:01:00+02:00"

    # test save as pickle file
    pkl_file = feat.save_pkl()
    assert pkl_file == "2f6dc5ae055f9e82f6f5311c23250f07.pkl"

    assert os.path.exists(pkl_file)
    os.remove(pkl_file)  # Cleanup

    # Summary
    assert set(feat.summary().index) == {
        "mean",
        "min",
        "std",
        "count",
        "50%",
        "75%",
        "25%",
        "max",
    }

    # Plot (not tested at all)
    plt_file = feat.plot(False)
    assert plt_file is not None
    assert os.path.exists(plt_file)
    os.remove(plt_file)  # Cleanup

    # Accessor functions (tested only in RMS)
    ts_sum = 78615280200
    assert sum(feat.raw_results()["results"]["timestamps"]) == ts_sum
    assert feat.request_id() == "2f6dc5ae055f9e82f6f5311c23250f07"
    assert feat.feature() == "RMS"
    assert sum(feat.inputs()["timestamps"]) == ts_sum
    assert sum(feat.results()["timestamps"]) == ts_sum
    assert feat.status() == "successful"
    assert feat.sources() == ["u0001"]


def test_KPIDemo():
    # read dict
    with open("./tests/test_data/KPIDemo_results_dict.json") as json_file:
        api_results = json.load(json_file)

    # get object
    feat = parse_results(api_results, t_zone=None, t_unit=None)

    # Check dataframe conversion - columns
    assert set(feat.to_df().columns.values) == set(api_results["results"].keys())

    # Check dataframe conversion - length
    assert len(feat.to_df()["timestamps"]) == len(api_results["results"]["timestamps"])

    # Test datetime conversion
    feat = analysis_classes.KPIDemo(api_results, t_zone="Europe/Stockholm", t_unit="s")
    assert str(feat.to_df()["datetime"][0]) == "2019-10-04 13:01:00+02:00"

    # test save as pickle file
    pkl_file = feat.save_pkl()
    assert pkl_file == "45f202227d51402eb7e71efd58370415.pkl"

    assert os.path.exists(pkl_file)
    os.remove(pkl_file)  # Cleanup

    # Summary
    assert set(feat.summary().index) == {
        "mean",
        "min",
        "std",
        "count",
        "50%",
        "75%",
        "25%",
        "max",
    }

    # Plot (not tested at all)
    plt_file = feat.plot("rms", False)
    assert plt_file is not None
    assert os.path.exists(plt_file)
    os.remove(plt_file)  # Cleanup

    # Accessor functions (tested only in KPIDemo)
    ts_sum = 73900313220
    assert sum(feat.raw_results()["results"]["timestamps"]) == ts_sum
    assert feat.request_id() == "45f202227d51402eb7e71efd58370415"
    assert feat.feature() == "KPIDemo"
    assert sum(feat.inputs()["timestamps"]) == ts_sum
    assert sum(feat.results()["timestamps"]) == ts_sum
    assert feat.status() == "successful"
    assert feat.sources() == ["u0001"]


def test_BlackSheep():
    # read dict
    with open("./tests/test_data/BlackSheep_results_dict.json") as json_file:
        api_results = json.load(json_file)

    # get object
    feat = parse_results(api_results, t_zone=None, t_unit=None)

    # Check dataframe conversion
    df_df = pd.read_csv("./tests/test_data/BlackSheep_df.csv")
    assert df_df.equals(feat.to_df())

    # Summary
    summary_df = pd.read_csv("./tests/test_data/BlackSheep_summary.csv")
    feat_summary_df = feat.summary()[0]
    assert feat_summary_df.equals(summary_df)


def test_ModeId():

    # read dict
    with open("./tests/test_data/ModeId_results_dict.json") as json_file:
        api_results = json.load(json_file)

    feat = parse_results(api_results, t_zone=None, t_unit=None)
    # Check dataframe conversion
    df_df = pd.read_csv("./tests/test_data/ModeId_df.csv")
    pd.testing.assert_frame_equal(feat.to_df(), df_df, check_less_precise=True)

    # Summary
    res = feat.summary()
    assert res[0]["portion"][0] == 84
    assert res[0]["counts"][1] == 8
    assert (res[1]["counts"][1] == 8).any()
    assert (res[1]["portion"][0] == 84).any()

    # Mode table (only EPOCH times)
    mt_df = feat.mode_table().reset_index(drop=True)
    mt_correct_df = pd.read_csv("./tests/test_data/mode_table_nowc.csv")
    assert mt_correct_df.equals(mt_df.reset_index(drop=True))

    # Mode table (+wallclock times)
    feat = parse_results(api_results, t_zone="Europe/Stockholm", t_unit="s")
    mt_df = feat.mode_table().reset_index(drop=True)
    mt_correct_df = pd.read_pickle("./tests/test_data/mode_table_wc.pkl")
    mt_correct_df = mt_correct_df.reset_index(drop=True)
    assert mt_correct_df.equals(mt_df.reset_index(drop=True))


def test_none_existing_feature():
    # read dict
    with open("./tests/test_data/Nonexisting_feature.json") as json_file:
        api_results = json.load(json_file)

    # try to get non implemented object
    with pytest.raises(KeyError):
        assert parse_results(api_results, t_zone=None, t_unit=None)


def test_failed_run():
    # read dict
    with open("./tests/test_data/BlackSheep_failed.json") as json_file:
        api_results = json.load(json_file)

    # try to get non implemented object
    feat = parse_results(api_results, t_zone=None, t_unit=None)
    with pytest.raises(ValueError):
        assert feat.summary()

    with pytest.raises(ValueError):
        assert feat.plot()

    with pytest.raises(ValueError):
        assert feat.to_df()
