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
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import cm
import matplotlib.patches as mpatches
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
        self.inputs = results.get("inputs", "Inputs not available")
        self.time_column = None

    def _add_datetime(self):
        """
        Convert EPOCH time to datetime with the
        timezone and time unit given in constructor. Will add
        an additional column "datetime" to the dataframe
        and set time_column to "datetime"
        Works on class object dframe and sets time column to
        datetime.
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
        if self.t_zone is not None:
            # EPOCH to datetime
            dframe = dframe.assign(
                datetime=pd.to_datetime(dframe[timecolumn], unit=self.t_unit, utc=True)
            )
            # Set timezone
            dframe = dframe.assign(
                datetime=(dframe["datetime"].dt.tz_convert(self.t_zone))
            )
            # Mark datetime as availble
            self.time_column = "datetime"

        return dframe

    # Accessor functions
    def request_id(self):
        """request_id from request

        Returns
        -------
        request_id: str
        """

        return self.raw_results["request_id"]

    def feature(self):
        """feature from request

        Returns
        -------
        feature: str
        """

        return self.raw_results["feature"]

    def request_params(self):
        """inputs to the analysis run

        Returns
        -------
        results: dict
        """

        return self.inputs

    def results(self):
        """results dict as returned from request

        Returns
        -------
        results: dict
        """

        return self.raw_results["results"]

    def status(self):
        """status from request

        Returns
        -------
        status: str
        """

        return self.raw_results["status"]

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
        Actually used file path: str
        """

        if file_name is None:
            file_name = f"{self.request_id()}.pkl"
        print(f"Saving {self.feature()} object to", file_name)
        with open(file_name, "wb") as pkl_file:
            pickle.dump(self, pkl_file)
        return file_name

    # Save results to dataframe
    def to_df(self, file_name=None):
        """Return a dataframe with the analysis results.
        Save as csv if file_name given.
        Format of the dataframe depends on specific analysis.
        Will raise an exception in case no results are available.

        Parameters
        ----------
        file_name: str
            filename to save object under. If not given no file is saved.

        Returns
        -------
        Dataframe with analysis results: dataFrame

        """

        self.check_status()
        if file_name is not None:
            print(f"Saving {self.feature()} data frame results to", file_name)
            self.dframe.copy().to_csv(file_name, index=False)
        return self.dframe

    # Save self as pickel
    def to_json(self, file_name=None, raw=False):
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
            s_dict = self.raw_results
        else:
            s_dict = self.results()

        with open(file_name, "w") as json_file:
            json.dump(s_dict, json_file, indent=4)
        return file_name


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
        summary table: dataFrame
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
        plt.title(f"RMS Summary plot for request {self.request_id()}")
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
        if "success" not in self.status():
            print(f"Analysis {self.request_id} failed on server side")
        else:
            dict_for_df = self.results().copy()
            dict_for_emerging = dict_for_df.pop("mode_info")
            self.emerging_df = pd.DataFrame.from_dict(dict_for_emerging)
            self.dframe = pd.DataFrame.from_dict(dict_for_df)
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

        # Emerging
        print()
        print("Emerging Modes")
        print(tabulate(self.emerging_df, headers="keys", tablefmt="psql"))

        return [tbl, tbl2, self.emerging_df]

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
        if "success" not in self.status():
            print("Analysis was not successful")
        else:
            self.dframe = self._bsd_df()

            # List of which assests are what
            self.typicality = pd.DataFrame(
                {"source": results["inputs"]["UUID"], "atypical": False}
            )
            self.typicality = self.typicality.set_index("source")
            aty = [a["uuid"] for a in self.results()["atypical_assets"]]
            self.typicality.loc[aty] = True
            self.typicality = self.typicality.reset_index()
            self.time_column = None

    def _bsd_df(self):
        # Wide
        def aty_df(ass):
            uuid = ass.pop("uuid")
            bsd_df = pd.DataFrame.from_dict(ass)
            bsd_df.columns = ["timestamps", uuid + "_label", uuid + "_atypical"]
            return bsd_df

        wide_df = None
        for ass in self.results()["atypical_assets"]:
            if wide_df is None:
                wide_df = aty_df(ass.copy())
            else:
                wide_df = pd.merge(aty_df(ass.copy()), wide_df, how="outer")
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

    def plot(self):
        """Generate a (not so) basic plot for BlackSheep
        Will show per atypical asset changes to and from
        atypical modes (experimental)"""

        # Check if run was successful
        self.check_status()

        # For Matrix & xTicks, remove label columns
        # store in pdfd df
        pdf = self.to_df()
        pdfd = pdf.loc[:, ~pdf.columns.str.endswith("label")]

        # x axis ticks timestamps of changes in atypicality
        # Find changes in atypticality and store rows in
        pdfd["hash"] = 0
        for row in pdfd.itertuples():
            pdfd.at[row.Index, "hash"] = hash(row[2:])
        ticktimes = pdfd.loc[pdfd["hash"].shift(1) != pdfd["hash"]]

        # Convert EPOCH if t_zone given
        if self.t_zone is not None:
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
        bsd_plt.set_yticks(np.arange(0, len(assets) + 1, 1))
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
        plt.show()


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
    Object of the correct analysis class: subclass to Analysis

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
