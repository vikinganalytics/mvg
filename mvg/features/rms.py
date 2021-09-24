"""Analysis Class for RMS Feature"""
import copy
import pandas as pd
import matplotlib.pyplot as plt
from tabulate import tabulate
from mvg.features.analysis import Analysis


class RMS(Analysis):
    """ Analysis class for RMS feature."""

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

        rsl = copy.deepcopy(results)
        # Handle multi-channel waveform data.
        channels = [k for k in rsl["results"] if k != "timestamps"]
        if len(channels) == 1:
            rsl["results"].update(rsl["results"].pop(channels[0]))
        else:
            # Prefix the KPIs with channel name
            for chan in channels:
                rch = rsl["results"].pop(chan)
                rsl["results"].update(
                    {chan + "_" + kpi: val for kpi, val in rch.items()}
                )

        Analysis.__init__(self, rsl, t_zone, t_unit)

        self._results_df = pd.DataFrame.from_dict(self.results())
        self.time_column = "timestamps"
        self._add_datetime()

    def summary(self):
        """Print summary information on RMS.

        Returns
        -------
        summary table: dataFrame
        """

        super().summary()
        print()
        tab = self._results_df.describe()
        print(tabulate(tab, headers="keys", tablefmt="psql"))
        return tab

    def plot(self, interactive=True, time_format=None):
        """
        Generate a basic plot on RMS.

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
        self._results_df.plot(x=self.time_column, y=["rms", "dc", "utilization"])
        plt.title(f"RMS Summary plot for request {self.request_id()}")
        return self._render_plot(interactive)
