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
from mvg.features.label_propagation import LabelPropagation

TZ = "Europe/Stockholm"


def test_KPIDemo():
    # read dict
    with open("./tests/test_data/KPIDemo_results_dict.json") as json_file:
        api_results = json.load(json_file)

    # get object
    feat = parse_results(api_results, t_zone=TZ, t_unit=None)

    cols = feat.to_df().columns.tolist()
    cols_without_datetime = cols.copy()  # Datetime is not part of the original data
    cols_without_datetime.remove("datetime")

    # Check dataframe conversion - columns
    assert "peak2peak_acc" in set(cols_without_datetime)

    # Check dataframe conversion - length
    assert len(feat.to_df()["timestamps"]) == len(api_results["results"]["timestamps"])

    # Test datetime conversion
    feat = analysis_classes.KPIDemo(api_results, t_zone=TZ, t_unit="s")
    assert str(feat.to_df()["datetime"][0]) == "2019-10-04 13:01:00+02:00"

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
    plt_file = feat.plot("rms_acc", False)
    assert plt_file is not None
    assert os.path.exists(plt_file)
    os.remove(plt_file)  # Cleanup

    # Accessor functions (tested only in KPIDemo)
    ts_sum = 78615280200
    assert sum(feat.raw_results()["results"]["timestamps"]) == ts_sum
    assert feat.request_id() == "75fc046d1b6ca741cf442552f506f95b"
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
    feat = parse_results(api_results, t_zone=TZ, t_unit=None)

    # Check dataframe conversion
    df_df = pd.read_csv("./tests/test_data/BlackSheep_df.csv")
    assert df_df.equals(feat.to_df().drop("datetime", axis=1))

    # Summary
    summary_df = pd.read_csv("./tests/test_data/BlackSheep_summary.csv")
    feat_summary_df = feat.summary()[0]
    assert feat_summary_df.equals(summary_df)


def test_ModeId():

    # read dict
    with open("./tests/test_data/ModeId_results_dict.json") as json_file:
        api_results = json.load(json_file)

    feat = parse_results(api_results, t_zone=TZ, t_unit=None)
    # Check dataframe conversion
    df_df = pd.read_csv("./tests/test_data/ModeId_df.csv")
    pd.testing.assert_frame_equal(
        feat.to_df().drop("datetime", axis=1), df_df, atol=1e-5, rtol=0
    )

    # Summary
    res = feat.summary()
    assert res[0]["portion"][0] == 84
    assert res[0]["counts"][1] == 8
    assert (res[1]["counts"][1] == 8).any()
    assert (res[1]["portion"][0] == 84).any()

    # Mode table (+wallclock times)
    feat = parse_results(api_results, t_zone=TZ, t_unit="s")
    mt_df = feat.mode_table().reset_index(drop=True)
    mt_correct_df = pd.read_pickle("./tests/test_data/mode_table_wc.pkl")
    mt_correct_df = mt_correct_df.reset_index(drop=True)
    assert mt_correct_df.equals(mt_df.reset_index(drop=True))


def test_labelprop():

    with open("./tests/test_data/label_prop_results.json") as json_file:
        api_results = json.load(json_file)

    labelprop: LabelPropagation = parse_results(api_results, t_zone=TZ)

    # Accessor functions
    assert labelprop.feature() == "LabelPropagation"
    assert labelprop.sources() == [api_results["inputs"]["UUID"]]
    assert labelprop.request_id() == "208e5dfafaee0687d73dce036a42fd04"
    assert labelprop.inputs() == api_results["inputs"]
    assert labelprop.status() == api_results["status"]
    assert labelprop.raw_results() == api_results
    assert labelprop.results() == api_results["results"]["propagated_labels"]

    # Plot (not tested at all)
    plt_file = labelprop.plot(False)
    assert plt_file is not None
    assert os.path.exists(plt_file)
    os.remove(plt_file)  # Cleanup


def test_none_existing_feature():
    # read dict
    with open("./tests/test_data/Nonexisting_feature.json") as json_file:
        api_results = json.load(json_file)

    # try to get non implemented object
    with pytest.raises(KeyError):
        assert parse_results(api_results, t_zone=TZ, t_unit=None)


def test_failed_run():
    # read dict
    with open("./tests/test_data/BlackSheep_failed.json") as json_file:
        api_results = json.load(json_file)

    # try to get non implemented object
    feat = parse_results(api_results, t_zone=TZ, t_unit=None)
    with pytest.raises(ValueError):
        assert feat.summary()

    with pytest.raises(ValueError):
        assert feat.plot()

    with pytest.raises(ValueError):
        assert feat.to_df()


if __name__ == "__main__":
    test_ModeId()
