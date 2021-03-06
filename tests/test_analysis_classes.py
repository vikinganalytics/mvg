"""
Tests in this file shall test functionlity
not relying on access to vibium-cloud API
"""

import json
import os
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
    pkl_file = feat.save()
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
    assert feat.summary().reset_index().equals(summary_df)


def test_ModeId():

    # read dict
    with open("./tests/test_data/ModeId_results_dict.json") as json_file:
        api_results = json.load(json_file)

    feat = parse_results(api_results, t_zone=None, t_unit=None)
    # Check dataframe conversion
    df_df = pd.read_csv("./tests/test_data/ModeId_df.csv")
    assert df_df.equals(feat.to_df())

    # Summary
    res = feat.summary()
    assert res[0]["portion"][0] == 84
    assert res[0]["counts"][1] == 8
    assert (res[1]["counts"][1] == 8).any()
    assert (res[1]["portion"][0] == 84).any()


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
