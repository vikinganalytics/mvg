import pandas as pd
from tabulate import tabulate
from mvg import plotting

from mvg.features.analysis import Analysis


class LabelPropagation(Analysis):
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
        super().__init__(results, t_zone=t_zone, t_unit=t_unit)
        self._results_df = pd.DataFrame(self.results())
        self._add_datetime("timestamp")

    def results(self):
        return super().results()["propagated_labels"]

    def summary(self):
        """
        Print summary table with average severity and counts of each label
        """

        super().summary()
        print()

        result_df: pd.DataFrame = self.to_df()
        tbl = result_df.groupby("label").mean().drop("timestamp", axis=1)
        tbl["count"] = result_df.groupby("label").count()["severity"]
        print(tabulate(tbl, headers="keys", tablefmt="psql"))

    def plot(self, interactive=True, time_format=None, filename=None):
        """
        Generate a label plot for the propagated labels

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
            format "{source_1_name}_to_{source_n_name}_{analysis_request_id}.png"
            for multiple sources, and "{source_name}_{analysis_request_id}.png"
            for a single source.

        Returns
        -------
        plot file name : str
          name of plot file (or emtpy string in case of interactive plot)
        """
        self.check_status()
        sources = ", ".join(self.sources())
        plotting.plot_labels_over_time(self.results(), sources, time_format=time_format)

        return self._render_plot(interactive, filename)
