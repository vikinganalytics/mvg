"""Analysis Classes Base Class"""
import pickle
import json
import pandas as pd
import matplotlib.pyplot as plt


# Base class for analyses
class Analysis:
    """Root class for analysis system classes."""

    # Init class with results
    def __init__(self, results, t_zone="Europe/Stockholm", t_unit="ms"):
        """
        Constructor
        Called as super() from specific analysis class. Stores the results
        form the request, preforms basic (result independent parsing) and
        sets timezone/time unit.

        Parameters
        ----------
        results: dict
            analysis results
        t_zone: t_zone
            timezone, if None, times will remain in epoch time [Europe/Stockholm].

        t_unit: t_unit
            time unit for conversion from epoch time [ms].
        """

        # raw_results as returned from server
        self._raw_results = results

        # timezone and unit set in constructor
        self._t_zone = t_zone
        self._t_unit = t_unit

        # Dataframe representation
        self._results_df = None

        self._inputs = results.get("inputs", "Inputs not available")

        self.time_column = None

    def _render_plot(self, interactive, filename=""):
        """Render plot to screen (interactive) or file.

        Parameters
        ---------
        interactive: bool
            Wheter to display plot on screen (True) or to store to file (False).
        filename: str
            Filename for the plot

        Returns
        -------
        plot file name: str
          name of plot file (or emtpy string in case of interactive plot)
        """
        if interactive:
            plot_file = ""
            plt.show()
        else:
            if filename == "" or filename is None:
                if len(self.sources()) > 1:
                    srcstr = self.sources()[0] + "_to_" + self.sources()[-1] + "_"
                else:
                    srcstr = self.sources()[0] + "_"
                plot_file = srcstr + self.request_id() + ".png"
            else:
                plot_file = filename

            plt.savefig(plot_file, dpi=600, bbox_inches="tight")
            print(f"saved plot to {plot_file}")

        return plot_file

    def _add_datetime(self):
        """
        Convert EPOCH time to datetime with the
        timezone and time unit given in constructor. Will add
        an additional column "datetime" to the dataframe
        and set time_column to "datetime"
        Works on class object dframe and sets time column to
        datetime.
        """

        self._results_df = self._add_datetime_df(self._results_df, "timestamps")

    def _add_datetime_df(self, dframe, timecolumn):
        """
        Convert EPOCH time to datetime with the
        timezone and time unit given in constructor. Will add
        an additional column "datetime" to the dataframe
        Operates on given df and given time column

        Parameters
        ----------
        dframe: DataFrame
            DataFrame to operate on
        timecolumn: str
            columns containing time

        Returns
        -------
        DataFrame with added datetime colums
        """

        # Check if there is info for conversion
        if self._t_zone is not None:

            # EPOCH to datetime considering time zone
            dt_col = pd.to_datetime(
                dframe[timecolumn], unit=self._t_unit, utc=True
            ).dt.tz_convert(self._t_zone)

            dframe["datetime"] = dt_col

            # Mark timecolumn as available
            self.time_column = "datetime"

        return dframe

    # Accessor functions
    def raw_results(self):
        """Raw results as returned by server
        Returns
        -------
        raw_results: dict
        """

        return self._raw_results

    def request_id(self):
        """request_id from request

        Returns
        -------
        request_id: str
        """

        return self._raw_results["request_id"]

    def feature(self):
        """feature from request

        Returns
        -------
        feature: str
        """

        return self._raw_results["feature"]

    def results(self):
        """results dict as returned from request

        Returns
        -------
        results: dict
        """

        return self._raw_results["results"]

    def status(self):
        """status from request

        Returns
        -------
        status: str
        """

        return self._raw_results["status"]

    def inputs(self):
        """inputs to the request algortihm

        Returns
        -------
        inputs: dict
        """

        return self._inputs

    def sources(self):
        """sources to the request algortihm

        Returns
        -------
        sources: list
        """

        sources = self.inputs()["UUID"]
        if not isinstance(self.inputs()["UUID"], list):
            sources = [self.inputs()["UUID"]]

        return sources

    # For avoiding problems when no results are available
    def check_status(self):
        if "success" not in self.status():
            err_str = f"Analysis {self.request_id} failed on server side"
            print(err_str)
            raise ValueError(err_str)
        return self.status()

    # Prints header for summary functions
    def summary(self):
        """
        Print header for summary function. Called as super() from specific
        analysis class. Will raise an exception in case request was not
        successful
        """

        # Anounce
        print(f"=== {self.feature()} ===")
        print(f"request_id {self.request_id()}")
        # Check success
        self.check_status()
        # print time info if applicable
        if self.time_column is not None:
            from_t = self._results_df[self.time_column].min()
            to_t = self._results_df[self.time_column].max()
            if self.time_column == "datetime":
                from_t = from_t.strftime("%Y%m%d-%H:%M.%S")
                to_t = to_t.strftime("%Y%m%d-%H:%M.%S")
            print(f"from {from_t} to {to_t}")

    # Default method
    def plot(
        self, interactive=True, time_format=None
    ):  # pylint: disable=unused-argument
        """Pro forma ancestor function.

        Parameters
        ----------
        interactive : bool
            True: show plot, False: save plot

        time_format: str, optional
            strftime format specifier for tick_x_lables. If not given
            only dates are shown. To show dates and time use %y%m%d-%H:%M:%S

        Returns
        -------
        plot file name: str
          name of plot file (or emtpy string in case of interactive plot)
        """

        self.check_status()
        print(f"Plot function not implemented for {type(self).__name__}")
        return ""

    # Save self as pickel
    def save_pkl(self, file_name=None):
        """Serializes the analysis object as pickle file.
        In case of filname is not given, filename will be
        <request_id>.pkl

        Parameters
        ----------
        file_name: str
            filename to save object under.

        Returns
        -------
        Actually used file path: str
        """

        if file_name is None:
            file_name = f"{self.request_id()}.pkl"
        print(f"Saving {self.feature()} object to", file_name)
        with open(file_name, "wb") as pkl_file:
            pickle.dump(self, pkl_file)
        return file_name

    # Return results as dataframe
    def to_df(self):
        """Return a dataframe with the analysis results.
        Returns
        -------
        Dataframe with analysis results: dataFrame

        """

        self.check_status()
        return self._results_df

    # Save results to dataframe
    def save_df(self, file_name=None):
        """Save a dataframe with the analysis results.
        In case of filname is not given, filename will be
        <request_id>.csv
        Format of the dataframe depends on specific analysis.
        Will raise an exception in case no results are available.

        Parameters
        ----------
        file_name: str
            filename to save dataframe under.

        Returns
        -------
        Actually used file path: str

        """

        self.check_status()

        if file_name is None:
            file_name = f"{self.request_id()}.csv"

        print(f"Saving {self.feature()} data frame results to", file_name)
        self._results_df.copy().to_csv(file_name, index=False)

        return file_name

    # Save self as pickel
    def save_json(self, file_name=None, raw=False):
        """Saves the request result from the API JSON
        In case of filname is not given, filename will be
        <request_id>.json

        Parameters
        ----------
        file_name: str
            filename to save object under.
        raw: boolean
            return only alogrithm results [false, default]
            return full request response [true]

        Returns
        -------
        Actually used file path: str
        """

        if file_name is None:
            file_name = f"{self.request_id()}.json"
        print(f"Saving {self.feature()} API results to", file_name)

        if raw:
            s_dict = self._raw_results
        else:
            s_dict = self.results()

        with open(file_name, "w") as json_file:
            json.dump(s_dict, json_file, indent=4)
        return file_name
