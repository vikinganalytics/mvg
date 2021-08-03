import pandas as pd


# Used by ModeId analysis class
def create_mode_table(label_df, time_unit, show_uncertain):
    """Create mode table of the given label_df dataframe

    Parameters
    ----------
    label_df
        Given label_df dataframe
    time_unit
        time unit for datetime conversion
    show_uncertain
        Boolean uncertain mode table indicator

    Returns
    -------
        Mode table
    """

    mode_table = label_df.copy()  # [["timestamps", "labels", "uncertain"]].copy()
    if show_uncertain:
        mode_table.loc[mode_table["uncertain"], ["labels"]] = -1
    # mode_table = mode_table[["datetime", "timestamps", "labels"]]

    # prepare
    mode_table["nextLabel"] = mode_table["labels"].shift(1)
    mode_table["startRow"] = mode_table.index
    mode_table = mode_table[mode_table["labels"] != mode_table["nextLabel"]]

    # Calculate duration
    mode_table["ts"] = mode_table["timestamps"]
    labels_timestamps = label_df["timestamps"]
    mode_table["endTime"] = mode_table["timestamps"].shift(
        -1, fill_value=labels_timestamps.iloc[-1]
    )
    if time_unit is None:
        mode_table["duration"] = mode_table["endTime"] - mode_table["timestamps"]
    else:
        mode_table["duration"] = pd.to_datetime(
            mode_table["endTime"], unit="s"
        ) - pd.to_datetime(mode_table["timestamps"], unit=time_unit)
    mode_table["nRows"] = (
        mode_table["startRow"].shift(-1, fill_value=len(label_df))
        - mode_table["startRow"]
    )

    # Return table
    if "datetime" in label_df.columns.values:
        mode_table = mode_table[
            ["timestamps", "datetime", "labels", "startRow", "nRows", "duration"]
        ]
    else:
        mode_table = mode_table[
            ["timestamps", "labels", "startRow", "nRows", "duration"]
        ]
    return mode_table
