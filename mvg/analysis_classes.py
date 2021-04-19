import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tabulate import tabulate
from mvg import plotting


# Base class for analyses
# pylint: disable=R0902
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

        self.raw_results = results  # TODO
        self.feature = results["feature"]
        self.request_id = results["request_id"]
        self.t_zone = t_zone
        self.t_unit = t_unit
        self.result = results["results"]
        self.status = results["status"]
        self.dframe = None
        self.time_column = "timestamps"

    def _add_datetime(self):
        """
        Convert EPOCH time to datetime with the
        timezone and time unit given in constructor. Will add
        an additional column "datetime" to the dataframe.
        """
        if self.t_zone is not None:
            self.dframe = self.dframe.assign(
                datetime=pd.to_datetime(
                    self.dframe["timestamps"], unit=self.t_unit, utc=True
                )
            )
            self.dframe = self.dframe.assign(
                datetime=(self.dframe["datetime"].dt.tz_convert(self.t_zone))
            )
            self.time_column = "datetime"

    def summary(self):
        """
        Print header for summary function. Called as super() from specific
        analysis class.
        """
        print(f"=== {self.feature} ===")
        print(f"request_id {self.request_id}")
        if self.time_column is not None:
            from_t = self.dframe[self.time_column].min()
            to_t = self.dframe[self.time_column].max()
            if self.time_column == "datetime":
                from_t = from_t.strftime("%Y%m%d-%H:%M.%S")
                to_t = to_t.strftime("%Y%m%d-%H:%M.%S")
            print(f"from {from_t} to {to_t}")

    def plot(self):
        """ Pro forma ancestor function"""
        # NotImplemented
        print(f"Plot function not implemented for {type(self).__name__}")

    def save(self, file_name=None):
        """Serializes the analysis object as pickle file.
        In case of filname is not given, filename will be
        <request_id>.pkl

        Parameters
        ----------
        file_name: str
            filename to save object under.

        Returns
        -------
        Actually used file path.
        """

        if file_name is None:
            file_name = f"{self.request_id}.pkl"
        print(f"Saving {self.feature} object to", file_name)
        filehandler = open(file_name, "wb")
        pickle.dump(self, filehandler)
        filehandler.close()
        return file_name

    def to_df(self):
        """Return a dataframe with the analysis results.
        Format of the dataframe depends on specific analysis

        Returns
        -------
        Dataframe with analysis results
        """
        print("To df")
        return self.dframe.copy()


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

        Analysis.__init__(self, results, t_zone, t_unit)
        self.dframe = pd.DataFrame.from_dict(self.result)
        self._add_datetime()

    def summary(self):
        """Print summary information on RMS."""
        super().summary()
        print()
        print(tabulate(self.dframe.describe(), headers="keys", tablefmt="psql"))

    def plot(self):
        """Generate a basic plot on RMS."""
        print("Plot")
        self.dframe.plot(x=self.time_column, y=["rms", "dc", "utilization"])
        plt.title(f"RMS Summary plot for request {self.request_id}")
        plt.show()


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
        self.result = results["results"]
        self.success = results["status"]
        self.dframe = pd.DataFrame.from_dict(self.result)
        self._add_datetime()

    def summary(self):
        """Print summary on ModeId."""
        # Header
        super().summary()
        # labels
        tbl = self.dframe.groupby(["labels"]).agg(np.size)
        tbl["uncertain"] = tbl["uncertain"] / sum(tbl["uncertain"]) * 100
        tbl = tbl.rename(columns={"timestamps": "portion", "uncertain": "counts"})
        print()
        print("Labels")
        print(tabulate(tbl, headers="keys", tablefmt="psql"))

        # Uncertain
        tbl2 = self.dframe.groupby(
            ["labels", "uncertain"],
        ).agg(np.size)
        tbl2["counts"] = tbl2["timestamps"]
        tbl2 = tbl2.rename(columns={"timestamps": "portion"})
        tbl2["portion"] = tbl2["portion"] / sum(tbl2["portion"]) * 100
        print()
        print("Lables & uncertain labels")
        print(tabulate(tbl2, headers="keys", tablefmt="psql"))

    def plot(self):
        """Generate a basic plot on ModeId."""
        print("Plot")
        plotting.modes_over_time(self.to_df(), self.request_id, timeunit=self.t_unit)
        plt.show()


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

        Analysis.__init__(self, results, t_zone, t_unit)
        self.dframe = pd.DataFrame(
            {"source": results["inputs"]["UUID"], "atypical": False}
        )
        self.dframe = self.dframe.set_index("source")
        self.dframe.loc[self.result["atypical_assets"]] = True
        self.dframe = self.dframe.reset_index()
        self.time_column = None

    def summary(self):
        """Print summary on BlackSheep"""
        super().summary()
        print()
        tbl = self.dframe.groupby(["atypical"]).agg(np.size)
        print(tabulate(tbl, headers=["atypical", "N"], tablefmt="psql"))


def parse_results(results):
    """Parses the result from a get_analysis_results call
    and returns an instance
    of the analysis class.

    Parameters
    ----------
    results: dict
        Dictionary with the server response form a get_analysis_results call.

    Returns
    -------
    Object of the correct analysis type.

    Raises
    ------
    KeyError
        If a either the dictionary is not well formed or no implementation
        for the analysis class exists.
    """

    # Check for well formed input
    try:
        feature = results["feature"]
    except KeyError:
        raise KeyError(
            "Malformed input." "Check if input is result of a get_results call."
        )

    # retrieve instance
    res = None
    for cls in Analysis.__subclasses__():
        if cls.__name__ == feature:
            res = cls(results)

    # raise error if no instance can be instantiated
    if res is None:
        raise KeyError(f"Analysis class for: {feature} not implemented!")

    # return analysis class
    return res
