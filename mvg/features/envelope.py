"""Analysis Class for Envelope Feature"""
import pandas as pd
import matplotlib.pyplot as plt
from tabulate import tabulate
from mvg.features.analysis import Analysis


class Envelope(Analysis):
    """ Analysis class for Envelope feature."""

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
        self._results_df = pd.DataFrame.from_dict(
            {
                "freq": self.results()["fft_freq"],
                "raw_amp": self.results()["fft_amp"],
                "raw_sd": self.results()["fft_amp_sd"],
                "env_amp": self.results()["env_amp"],
                "env_sd": self.results()["env_amp_sd"],
            }
        )
        self.time_column = "timestamps"
        self._pdt = pd.DataFrame.from_dict({"timestamps": self.results()["timestamps"]})

        # Add wallclock time if timezone is given
        if self._t_zone is not None:
            self._pdt = self._add_datetime_df(self._pdt, "timestamps")
            self.time_column = "datetime"

    def summary(self):
        """Print summary information on Envelope.

        Returns
        -------
        summary table: dataFrame
        """
        tcs = self.time_column
        self.time_column = None
        super().summary()
        self.time_column = tcs

        # print time info if applicable
        from_t = self._pdt[self.time_column].min()
        to_t = self._pdt[self.time_column].max()
        if self.time_column == "datetime":
            from_t = from_t.strftime("%Y%m%d-%H:%M.%S")
            to_t = to_t.strftime("%Y%m%d-%H:%M.%S")

        print(f"from {from_t} to {to_t}, total {len(self._pdt)} timestamps")
        print()
        tab = self.to_df().describe()
        print(tabulate(tab, headers="keys", tablefmt="psql"))
        return tab

    def plot(self, interactive=True, time_format=None):
        """Generate a basic plot of FFT and Envelope.

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
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, sharex=False)
        fsmin = f"[fs min: {self.results()['fsample_min']} Hz]"
        ax1.set_title(f"FFT of raw data for {self.sources()[0]} {fsmin}")
        ax1.set_xlabel("Frequency [Hz]")
        ax1.set_ylabel("Magnitude")
        ax1.plot(
            self.to_df().freq,
            self.to_df().raw_amp + self.to_df().raw_sd,
            c="gray",
            label="Std dev",
        )
        ax1.plot(
            self.to_df().freq,
            self.to_df().raw_amp,
            c="mediumvioletred",
            label="Amplitude",
        )
        ax1.legend()

        env_df = self.to_df()
        ax2.set_title("FFT of envelope")
        ax2.set_xlabel("Frequency [Hz]")
        ax2.set_ylabel("Magnitude")
        ax2.plot(env_df.freq, env_df.env_amp + env_df.env_sd, c="gray", label="Std dev")
        ax2.plot(env_df.freq, env_df.env_amp, c="blue", label="Amplitude")
        ax2.legend()

        env_df = self.to_df()
        env_df = env_df[env_df["freq"] < 1000]
        env_params = f"[lo: {self.inputs()['params']['env_lo']} "
        env_params = env_params + f"hi: {self.inputs()['params']['env_hi']} "
        env_params = env_params + "Hz]"

        ax3.set_title("FFT of envelope ")
        ax3.set_xlabel("Frequency [Hz]")
        ax3.set_ylabel("Magnitude")
        ax3.plot(env_df.freq, env_df.env_amp + env_df.env_sd, c="gray", label="Std dev")
        ax3.plot(env_df.freq, env_df.env_amp, c="blue", label="Amplitude")
        ax3.legend()

        # Control overall layout
        fig.tight_layout()
        return self._render_plot(interactive)
