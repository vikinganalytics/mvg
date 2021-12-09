"""Analysis Class for ModeId Feature"""
import numpy as np
import pandas as pd
from tabulate import tabulate
from mvg import plotting
from mvg.features.analysis import Analysis


class ModeId(Analysis):
    def __init__(self, results, t_zone=None, t_unit=None):
        """Constructor

        Parameters
        ----------
        results: dict
            Dictionary with the server response from a get_analysis_results call.

        t_zone: str
            timezone, if None, times will remain in epoch time [UTC].

        t_unit: str
            time unit for conversion from epoch time [ms].
        """

        Analysis.__init__(self, results, t_zone, t_unit)
        if "success" not in self.status():
            print(f"Analysis {self.request_id} failed on server side")
        else:
            dict_for_df = self.results().copy()
            dict_for_emerging = dict_for_df.pop("mode_info")
            dict_for_mode_proba = dict_for_df.pop("mode_probabilities", {})
            self.emerging_df = pd.DataFrame.from_dict(dict_for_emerging)
            self.probabilities = pd.DataFrame.from_dict(dict_for_mode_proba)
            self._results_df = pd.DataFrame.from_dict(dict_for_df)
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
        print("Labels & uncertain labels")
        print(tabulate(tbl2, headers="keys", tablefmt="psql"))

        # Emerging
        print()
        print("Emerging Modes")
        print(tabulate(self.emerging_df, headers="keys", tablefmt="psql"))

        return [tbl, tbl2, self.emerging_df]

    def plot(self, interactive=True, time_format=None, filename=None):
        """
        Generate a basic plot on ModeId.

        Parameters
        ----------
        interactive : bool
            True: show plot, False: save plot

        time_format: str, optional
            strftime format specifier for tick_x_labels. If not given
            only dates are shown. To show dates and time use %y%m%d-%H:%M:%S

        filename: str, optional
            filename for the plot. If interactive is True, filename will be
            ignored. If interactive is False, default filename will be of the
            format "{source_name}_{analysis_request_id}.png".

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

        return self._render_plot(interactive, filename)

    def plot_probabilities(
        self, selected_modes=None, interactive=True, time_format=None, filename=None
    ):
        """
        Generate a basic plot on mode probabilites over time.

        Parameters
        ----------
        interactive : bool
            True: show plot, False: save plot

        selected_modes : List[int]
            Plot the mode probabilities for a list of modes.
            By default, the probability of all modes will be plotted.

        time_format: str, optional
            strftime format specifier for x-axis tick labels.
            If not given, dates will be shown in locale format.
            To show dates and time use %y%m%d-%H:%M:%S.

        filename: str, optional
            filename for the plot. If interactive is True, filename will be
            ignored. If interactive is False, default filename will be of the
            format "{source_name}_{analysis_request_id}.png".

        Returns
        -------
        plot file name : str
          name of plot file (or emtpy string in case of interactive plot)
        """

        self.check_status()
        # Append timestamps column taken from results
        data = self.probabilities.assign(timestamps=self._results_df.timestamps.values)
        data.set_index("timestamps", inplace=True)
        # Replace 0 values with NAN
        data.replace(to_replace=0, value=np.NAN, inplace=True, method="pad")

        # Dataframe should only contain data for the requested modes
        if selected_modes:
            modes_list = [f"mode {n}" for n in selected_modes]
            data = data[modes_list]

        plotting.modes_probabilities_over_time(
            data=data,
            title=f"Probability of modes over time for {self.request_id()}",
            timeunit=self._t_unit,
            time_format=time_format,
        )

        return self._render_plot(interactive, filename)

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
        mode_table["prevLabel"] = mode_table["labels"].shift(-1)
        mode_table["startRow"] = mode_table.index
        mode_table["endRow"] = mode_table.index

        mt_next = mode_table[mode_table["labels"] != mode_table["nextLabel"]].copy()
        mt_next = mt_next.rename(columns={"timestamps": "start", "datetime": "wcStart"})
        mt_next = mt_next.drop(
            ["mode_probability", "nextLabel", "prevLabel", "endRow"], axis=1
        )

        mt_prev = mode_table[mode_table["labels"] != mode_table["prevLabel"]].copy()
        mt_prev = mt_prev.rename(columns={"timestamps": "end", "datetime": "wcEnd"})
        mt_prev = mt_prev.drop(
            [
                "mode_probability",
                "nextLabel",
                "prevLabel",
                "startRow",
                "labels",
                "uncertain",
            ],
            axis=1,
        )

        # merge
        mt_both = pd.concat([mt_next, mt_prev.set_index(mt_next.index)], axis=1)

        # Durations
        mt_both["duration"] = mt_both["end"] - mt_both["start"]
        if self._t_unit is not None:
            mt_both["wcDuration"] = pd.to_datetime(
                mt_both["end"], unit=self._t_unit
            ) - pd.to_datetime(mt_both["start"], unit=self._t_unit)

        # Number of Rows
        mt_both["nRows"] = mt_both["endRow"] - mt_both["startRow"]

        common_fields = [
            "labels",
            "start",
            "end",
            "duration",
            "startRow",
            "endRow",
            "nRows",
        ]
        wallclock_fields = ["wcStart", "wcEnd", "wcDuration"]

        # Return table
        if "datetime" in label_df.columns.values:
            mt_both = mt_both[common_fields + wallclock_fields]
        else:
            mt_both = mt_both[common_fields]

        return mt_both
