import numpy as np
import pickle
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from mvg import plotting

# Base class for 
class Analysis:

    # Init class with results
    def __init__(self, results, t_zone="Europe/Stockholm", t_unit="ms"):
        self.feature = None
        self.request_id = "0ABC"
        self.t_zone = t_zone
        self.t_unit = t_unit
        self.dframe = None

    # Summarizes result
    def summary(self):
        # NotImplemented
        pass

    # convert to dataFrame
    def to_df(self):
        # NotImplemented
        pass

    # Plots result
    def plot(self):
        # NotImplemented
        pass

    def save(self, file_name=None):
        if file_name is None:
            file_name = f"{self.request_id}.pkl"
        print("Saving RMS object to", file_name)
        filehandler = open(file_name, "wb")
        pickle.dump(self, filehandler)
        filehandler.close()

    def _fix_ts(self):
        if self.t_zone is not None:
            self.dframe = self.dframe.assign(
                timestamps=pd.to_datetime(
                    self.dframe["timestamps"],
                    unit=self.t_unit
                )
            )


class RMS(Analysis):

    def __init__(self, results, t_zone="Europe/Stockholm", t_unit="ms"):
        Analysis.__init__(self, results, t_zone, t_unit)
        self.result = results['result']
        self.success = results['success']
        self.dframe = pd.DataFrame.from_dict(self.result)
        self._fix_ts()


    def summary(self):
        print(f"Summary for {self.request_id}")
        from_t = self.dframe["timestamps"].min()
        to_t = self.dframe["timestamps"].max()
        print(f"Time period from {from_t} to {to_t}")
        print(self.dframe.describe())

    def plot(self):
        print("Plot")
        self.dframe.plot(x="timestamps", y=["rms", "dc", "utilization"])
        plt.title(f"RMS Summary plot for request {self.request_id}")
        plt.show()

    def to_df(self):
        print("To df")
        return self.dframe


class ModeId(Analysis):

    def __init__(self, results, t_zone="Europe/Stockholm", t_unit="ms"):
        Analysis.__init__(self, results, t_zone, t_unit)
        self.result = results['results']
        self.success = results['status']
        self.dframe = pd.DataFrame.from_dict(self.result)
        self._fix_ts()

    def summary(self):
        print(f"Summary for {self.request_id}")
        from_t = self.dframe["timestamps"].min()
        to_t = self.dframe["timestamps"].max()
        print(f"Time period from {from_t} to {to_t}")
        # labels
        tbl = self.dframe.groupby(['labels']).agg(np.size)
        tbl['uncertain'] = tbl['uncertain']/sum(tbl['uncertain'])*100
        tbl = tbl.rename(columns={"timestamps": "portion", "uncertain": "counts"})
        print()
        print("Labels")
        print(tbl)
        tbl2 = self.dframe.groupby(['labels','uncertain'],).agg(np.size)
        tbl2["counts"] = tbl2["timestamps"]
        tbl2 = tbl2.rename(columns={"timestamps": "portion"})
        tbl2['portion'] = tbl2['portion']/sum(tbl2['portion'])*100
        print()
        print("Lables & uncertain labels")
        print(tbl2)


    def plot(self):
        print("Plot")
        df_plt = self.dframe
        df_plt["uncertain"] = pd.Categorical(self.dframe.uncertain).codes
        #self.dframe.plot(x="timestamps", y=["labels", "uncertain"])
        # self.dframe["uncert"] = 
        sns.scatterplot(x=df_plt["timestamps"],
                        y=df_plt["labels"],
                        hue=df_plt["uncertain"])

        plt.title(f"ModeId Summary plot for request {self.request_id}")
        plt.xticks(rotation=30, horizontalalignment='right')
        plt.show()

    def s_plot(self):
        print("Plot")
        breakpoint()
        img = plotting.modes_over_time(self.dframe,
                                       self.request_id)
        print("Plotting")
        
    def to_df(self):
        print("To df")
        return self.dframe

