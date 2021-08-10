"""Analysis Class for BlackSheep Feature"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import cm
import matplotlib.patches as mpatches
from tabulate import tabulate
from mvg.features.analysis import Analysis


class BlackSheep(Analysis):
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

        # Super
        Analysis.__init__(self, results, t_zone, t_unit)

        # Dataframe conversion
        if "success" not in self.status():
            print("Analysis was not successful")
        else:
            self._results_df = self._bsd_df()
            # List of which assests are what
            self.typicality = pd.DataFrame(
                {"source": results["inputs"]["UUID"], "atypical": False}
            )
            self.typicality = self.typicality.set_index("source")
            aty = [a["source_id"] for a in self.results()["atypical_assets"]]
            self.typicality.loc[aty] = True
            self.typicality = self.typicality.reset_index()
            self.time_column = None

    def _bsd_df(self):
        # Wide
        def aty_df(ass):
            source_id = ass.pop("source_id")
            bsd_df = pd.DataFrame.from_dict(ass)
            bsd_df.columns = [
                "timestamps",
                source_id + "_label",
                source_id + "_atypical",
            ]
            return bsd_df

        wide_df = None
        for ass in self.results()["atypical_assets"]:
            if wide_df is None:
                wide_df = aty_df(ass.copy())
            else:
                wide_df = pd.merge(aty_df(ass.copy()), wide_df, how="outer")

        # Add timestamps
        wide_df = self._add_datetime_df(wide_df, "timestamps")
        return wide_df.sort_values(by="timestamps")

    def summary(self):
        """Print summary on BlackSheep

        Returns
        -------
        Summary tables: atypical assets and stats
        """

        # Header
        super().summary()

        # Table
        print()
        print(
            tabulate(
                self.typicality.reset_index(drop=True, inplace=False),
                headers=["source", "atypical"],
                tablefmt="psql",
            )
        )

        print()
        tbl = self.typicality.groupby(["atypical"]).agg(np.size)
        print(tabulate(tbl, headers=["atypical", "N"], tablefmt="psql"))
        return [self.typicality, tbl]

    # pylint: disable=too-many-locals
    def plot(self, interactive=True, time_format=None):
        """Generate a (not so) basic plot for BlackSheep
        Will show per atypical asset changes to and from
        atypical modes

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

        # Check if run was successful
        self.check_status()

        # For Matrix & xTicks, remove label columns and potentiall datetime
        # store in pdfd df
        pdf = self.to_df()
        pdfd = pdf.loc[:, ~pdf.columns.str.endswith("label")]
        pdfd = pdfd.loc[:, ~pdfd.columns.str.endswith("datetime")]

        # x axis ticks timestamps of changes in atypicality
        # Find changes in atypticality and store rows in
        pdfd.insert(len(pdfd.columns), "hash", 0)
        for row in pdfd.itertuples():
            pdfd.at[row.Index, "hash"] = hash(row[2:])
        ticktimes = pdfd.loc[pdfd["hash"].shift(1) != pdfd["hash"]]

        # Convert EPOCH if t_zone given
        if self._t_zone is not None:
            ticktimes = self._add_datetime_df(ticktimes, "timestamps")

        # select reasonable number of ticks
        # this could be improved to yield equidistant ticks
        if len(ticktimes) > 10:
            ticktimes = ticktimes.iloc[:: int(len(ticktimes) / 10), :]

        # Setup plot
        fig, bsd_plt = plt.subplots(1, 1)

        # Title
        bsd_plt.set_title("Atypical Assets and Modes [" + self.request_id() + "]")

        # y-axis Asset labels
        # extract names from df
        coli = pdfd.columns.to_list()
        assets = [c.replace("_atypical", "") for c in coli if c.endswith("atypical")]
        bsd_plt.set_yticks(np.arange(0, len(assets), 1))
        bsd_plt.set_yticklabels(assets)

        # x axis ticks
        bsd_plt.set_xticks(ticktimes.index)
        if self.time_column is not None:
            bsd_plt.set_xticklabels(
                ticktimes["datetime"].apply(lambda x: x.strftime("%y%m%d-%H%M%S"))
            )
        else:
            bsd_plt.set_xticklabels(ticktimes["timestamps"])
        fig.autofmt_xdate(rotation=45)

        # Color map
        mcm = cm.get_cmap("viridis", 2)

        # Colors for plot and legend
        cmap = {0: mcm(0), 1: mcm(1)}
        labels = {0: "normal", 1: "atypical"}
        patches = [mpatches.Patch(color=cmap[i], label=labels[i]) for i in cmap]
        plt.legend(handles=patches, loc=4, borderaxespad=0.0)

        # The plot (need to remove na)
        # For matrix
        pdfd = pdfd.drop(["timestamps", "hash"], axis=1)
        pdfd = pdfd.fillna(method="ffill")
        pdfd = pdfd.dropna()
        plotmx = np.asmatrix(pdfd).transpose()
        plotmx = plotmx.astype(int)
        bsd_plt.imshow(plotmx, aspect="auto", cmap=mcm)

        # Display plot
        return self._render_plot(interactive)
