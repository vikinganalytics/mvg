"""Analysis Class for ModeId Feature"""
import numpy as np
import pandas as pd
from tabulate import tabulate
from mvg import plotting
from mvg.features.analysis import Analysis


class ModeId(Analysis):
    def __init__(self, results, t_zone="Europe/Stockholm", t_unit="ms"):
        """Constructor

        Parameters
        ----------
        results: dict
            Dictionary with the server response form a get_analysis_results call.

        t_zone: str
            timezone, if None, times will remain in epoch time [Europe/Stockholm].

        t_unit: str
            time unit for conversion from epoch time [ms].
        """

        Analysis.__init__(self, results, t_zone, t_unit)
        if "success" not in self.status():
            print(f"Analysis {self.request_id} failed on server side")
        else:
            dict_for_df = self.results().copy()
            dict_for_emerging = dict_for_df.pop("mode_info")
            self.emerging_df = pd.DataFrame.from_dict(dict_for_emerging)
            self._results_df = pd.DataFrame.from_dict(dict_for_df)
            self.time_column = "timestamps"
            self._add_datetime()
            self.emerging_df = self._add_datetime_df(self.emerging_df, "emerging_time")

    def summary(self):
        """
        Print summary on ModeId.

        Returns
        -------
        Summary table: dataFrame
        """

        # Header
        super().summary()

        # labels
        tbl = self._results_df.groupby(["labels"]).agg(np.size)
        tbl["uncertain"] = tbl["uncertain"] / sum(tbl["uncertain"]) * 100
        tbl = tbl.rename(columns={"timestamps": "counts", "uncertain": "portion"})
        print()
        print("Labels")
        print(tabulate(tbl, headers="keys", tablefmt="psql"))

        # Uncertain
        tbl2 = self._results_df.groupby(
            ["labels", "uncertain"],
        ).agg(np.size)
        tbl2["counts"] = tbl2["timestamps"]
        tbl2 = tbl2.rename(columns={"timestamps": "portion"})
        tbl2["portion"] = tbl2["portion"] / sum(tbl2["portion"]) * 100
        print()
        print("Lables & uncertain labels")
        print(tabulate(tbl2, headers="keys", tablefmt="psql"))

        # Emerging
        print()
        print("Emerging Modes")
        print(tabulate(self.emerging_df, headers="keys", tablefmt="psql"))

        return [tbl, tbl2, self.emerging_df]

    def plot(self, interactive=True, time_format=None):
        """
        Generate a basic plot on ModeId.

        Parameters
        ----------
        interactive : bool
            True: show plot, False: save plot

        time_format: str, optional
            strftime format specifier for tick_x_lables. If not given
            only dates are shown. To show dates and time use %y%m%d-%H:%M:%S

        Returns
        -------
        plot file name : str
          name of plot file (or emtpy string in case of interactive plot)
        """

        self.check_status()
        plotting.modes_over_time(
            data=self.to_df(),
            request_id=self.request_id(),
            timeunit=self._t_unit,
            time_format=time_format,
        )

        return self._render_plot(interactive)

    def mode_table(self, show_uncertain=False):
        """
        Show mode table which gives start time for each consecutive period of
        equal labels, including number of rows and time difference.
        Will also show datetimes if timezone is given when instatiating
        class.

        Parameters
        ----------
        show_uncertain: bool
            wheter to consider uncertain labels in the table (False)

        Returns
        -------
        mode_table: df
            Dataframe showing times when modes change.
        """
        label_df = self.to_df()
        mode_table = self.to_df()
        if show_uncertain:
            mode_table.loc[mode_table["uncertain"], ["labels"]] = -1

        # prepare
        mode_table["nextLabel"] = mode_table["labels"].shift(1)
        mode_table["startRow"] = mode_table.index
        mode_table = mode_table[mode_table["labels"] != mode_table["nextLabel"]].copy()

        # End Times
        mode_table["ts"] = mode_table["timestamps"]

        labels_timestamps = label_df["timestamps"]
        mode_table["end"] = mode_table["timestamps"].shift(
            -1, fill_value=labels_timestamps.iloc[-1]
        )
        if "datetime" in label_df.columns.values:
            mode_table["endWc"] = mode_table["datetime"].shift(-1, fill_value=None)
            mode_table["startWc"] = mode_table["datetime"]

        # Durations
        mode_table["duration"] = mode_table["end"] - mode_table["timestamps"]
        if self._t_unit is not None:
            mode_table["durationWc"] = pd.to_datetime(
                mode_table["end"], unit="s"
            ) - pd.to_datetime(mode_table["timestamps"], unit=self._t_unit)

        # Number of Rows
        mode_table["nRows"] = (
            mode_table["startRow"].shift(-1, fill_value=len(label_df))
            - mode_table["startRow"]
        )

        # rename in a safe way
        mode_table["start"] = mode_table["timestamps"]

        common_fields = ["start", "end", "labels", "startRow", "nRows"]
        wallclock_fields = ["durationWc", "startWc", "endWc"]

        # Return table
        if "datetime" in label_df.columns.values:
            mode_table = mode_table[common_fields + wallclock_fields]
        else:
            mode_table = mode_table[common_fields]

        return mode_table
