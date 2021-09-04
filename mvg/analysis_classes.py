""" Utility classes for working with the results from the
analysis requests, like summarizing, plotting and exporting to
a pandas dataFrame.

Basic usage:

>>> result = parse_results(session.get_analysis_results(request_id))  # call API
>>> result.plot() # plot results
>>> result.summary() # print summary table
>>> df = result.to_df() # convert to dataframe
>>> result.save_pkl() # save to pickle file

The parse function will detect the kind of request and return an object
of the correct feature class.
"""

# Import feature classes
from mvg.features.analysis import Analysis  # Base Class
from mvg.features.rms import RMS
from mvg.features.modeid import ModeId
from mvg.features.blacksheep import BlackSheep
from mvg.features.kpidemo import KPIDemo

# from mvg.features.envelope import Envelope

_ = RMS  # avoid F401 linting error
_ = ModeId  # avoid F401 linting error
_ = BlackSheep  # avoid F401 linting error
_ = KPIDemo  # avoid F401 linting error


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
