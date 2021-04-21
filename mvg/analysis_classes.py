""" Utility classes for working with the results from the
analysis requests, like summarizing, plotting and exporting to
a pandas dataFrame.

Basic usage:

>>> result = parse_results(session.get_analysis_results(request_id))  # call API
>>> result.plot() # plot results
>>> result.summary() # print summary table
>>> df = result.to_df() # convert to dataframe
>>> result.save() # save to pickle file

The parse function will detect the kind of request and return an object
of the correct feature class.
"""

import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tabulate import tabulate
from mvg import plotting


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

        self.raw_results = results
        self.t_zone = t_zone
        self.t_unit = t_unit
        self.dframe = None
        self.time_column = None

    def _add_datetime(self):
        """
        Convert EPOCH time to datetime with the
        timezone and time unit given in constructor. Will add
        an additional column "datetime" to the dataframe
        and set time_column to "datetime"
        """

        # Check if there is info for conversion
        if self.t_zone is not None:
            # EPOCH to datetime
            self.dframe = self.dframe.assign(
                datetime=pd.to_datetime(
                    self.dframe["timestamps"], unit=self.t_unit, utc=True
                )
            )
            # Set timezone
            self.dframe = self.dframe.assign(
                datetime=(self.dframe["datetime"].dt.tz_convert(self.t_zone))
            )
            # Mark datetime as availbke
            self.time_column = "datetime"

    # Accessor functions
    def request_id(self):
        """request_id from request

        Returns
        -------
            request_id
        """

        return self.raw_results["request_id"]

    def feature(self):
        """feature from request

        Returns
        -------
            feature
        """

        return self.raw_results["feature"]

    def results(self):
        """results dict as returned from request

        Returns
        -------
            results
        """

        return self.raw_results["results"]

    def status(self):
        """status from request

        Returns
        -------
            status
        """

        return self.raw_results["status"]

    # For avoiding problems when no results are available
    def check_status(self):
        if "success" not in self.status():
            print("   Analysis was not successful")
            raise ValueError(f"Analysis {self.request_id} failed on server side")
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
            from_t = self.dframe[self.time_column].min()
            to_t = self.dframe[self.time_column].max()
            if self.time_column == "datetime":
                from_t = from_t.strftime("%Y%m%d-%H:%M.%S")
                to_t = to_t.strftime("%Y%m%d-%H:%M.%S")
            print(f"from {from_t} to {to_t}")

    # Default method
    def plot(self):
        """ Pro forma ancestor function"""
        self.check_status()
        print(f"Plot function not implemented for {type(self).__name__}")

    # Save self as pickel
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
            file_name = f"{self.request_id()}.pkl"
        print(f"Saving {self.feature()} object to", file_name)
        filehandler = open(file_name, "wb")
        pickle.dump(self, filehandler)
        filehandler.close()
        return file_name

    # Save results to dataframe
    def to_df(self):
        """Return a dataframe with the analysis results.
        Format of the dataframe depends on specific analysis.
        Will raise an exception in case no results are available.

        Returns
        -------
            Dataframe with analysis results.
        """

        self.check_status()
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
        self.dframe = pd.DataFrame.from_dict(self.results())
        self.time_column = "timestamps"
        self._add_datetime()

    def summary(self):
        """Print summary information on RMS.
        Returns
        -------
            Dataframe with summary table.
        """

        super().summary()
        print()
        tab = self.dframe.describe()
        print(tabulate(tab, headers="keys", tablefmt="psql"))
        return tab

    def plot(self):
        """Generate a basic plot on RMS."""

        self.check_status()
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
        self.dframe = pd.DataFrame.from_dict(self.results())
        self.time_column = "timestamps"
        self._add_datetime()

    def summary(self):
        """
        Print summary on ModeId.

        Returns
        -------
            Dataframe with summary table.
        """

        # Header
        super().summary()

        # labels
        tbl = self.dframe.groupby(["labels"]).agg(np.size)
        tbl["uncertain"] = tbl["uncertain"] / sum(tbl["uncertain"]) * 100
        tbl = tbl.rename(columns={"timestamps": "counts", "uncertain": "portion"})
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
        return [tbl, tbl2]

    def plot(self):
        """Generate a basic plot on ModeId."""
        self.check_status()
        plotting.modes_over_time(self.to_df(), self.request_id(), timeunit=self.t_unit)
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

        # Super
        Analysis.__init__(self, results, t_zone, t_unit)

        # Dataframe conversion
        self.dframe = pd.DataFrame(
            {"source": results["inputs"]["UUID"], "atypical": False}
        )
        self.dframe = self.dframe.set_index("source")
        self.dframe.loc[self.results()["atypical_assets"]] = True
        self.dframe = self.dframe.reset_index()
        self.time_column = None

    def summary(self):
        """Print summary on BlackSheep

        Returns
        -------
        data frame with summary table.
        """

        # Header
        super().summary()

        # Table
        print()
        tbl = self.dframe.groupby(["atypical"]).agg(np.size)
        print(tabulate(tbl, headers=["atypical", "N"], tablefmt="psql"))
        return tbl


# Parser/Factory function
def parse_results(results, t_zone=None, t_unit=None):
    """Parses the result from a get_analysis_results call
    and returns an instance
    of the analysis class.

    Parameters
    ----------
    results: dict
        Dictionary with the server response form a get_analysis_results call.

    t_zone: str
        timezone, if None, times will remain in epoch time [Europe/Stockholm].

    t_unit: str
        time unit for conversion from epoch time [ms].


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
            res = cls(results, t_zone, t_unit)

    # raise error if no instance can be instantiated
    if res is None:
        raise KeyError(f"Analysis class for: {feature} not implemented!")

    # return analysis class
    return res
