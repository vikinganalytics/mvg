"""Analysis Class for KPIDemo Feature"""
import pandas as pd
import matplotlib.pyplot as plt
from tabulate import tabulate
from mvg.features.analysis import Analysis


def unfold_result_to_df(result: dict) -> pd.DataFrame:
    unfolded_result = {}
    unfolded_result["timestamps"] = result.pop("timestamps")

    for channel, kpis in result.items():
        for kpi, kpi_values in kpis.items():
            unfolded_result[f"{kpi}_{channel}"] = kpi_values

    return pd.DataFrame.from_dict(unfolded_result)


class KPIDemo(Analysis):
    """Analysis class for KPIDemo feature."""

    def __init__(self, results, t_zone=None, t_unit=None):
        """Constructor

        Parameters
        ----------
        results: dict
            Dictionary with the server response form a get_analysis_results call.

        t_zone: str
            timezone, if None, times will remain in epoch time [UTC].

        t_unit: str
            time unit for conversion from epoch time [ms].
        """

        super().__init__(results, t_zone, t_unit)
        self._results_df = unfold_result_to_df(self.results())
        self._add_datetime()

    def summary(self):
        """Print summary information on RMS.

        Returns
        -------
        summary table: dataFrame
        """

        super().summary()
        print()
        tab = self.to_df().describe()
        print(tabulate(tab, headers="keys", tablefmt="psql"))
        return tab

    def plot(
        self, kpi=None, interactive=True, time_format=None, filename=None
    ):  # pylint: disable=arguments-differ
        """
        Generate a basic plot on KPIs.

        Parameters
        ----------
        kpi: str
            sting that describes the KPI to be displayed.
            Default kpi is RMS

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
        result_df = self.to_df()

        # Select the default column as the one after timestamps which is first
        kpi = kpi if kpi is not None else result_df.columns[1]

        self.check_status()
        result_df.plot(x=self.time_column, y=kpi)
        plt.title(f"{kpi} Summary plot for request {self.request_id()}")
        return self._render_plot(interactive, filename)
