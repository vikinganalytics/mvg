import numpy as np
from itertools import cycle

from mvg.mvg import MVG


def upload_measurements(session: MVG, sid: str, data: list):
    """Upload measurements for a source"""
    timestamps = list(data.keys())
    for ts in timestamps:
        ts_data = data[ts]
        session.create_measurement(
            sid, ts_data["meta"]["duration"], ts, ts_data["data"], ts_data["meta"]
        )


def stub_multiaxial_data(samp_freq=3000, duration=3.0, pattern={}):
    """Create measurements based on cosine signals (with added noise) for a multiaxial source.

    Parameters
    ----------
    samp_freq
        Sampling frequency of the signal
    duration
        Duration of each measurement
    pattern
        Dictionary of axis with each axis pointing to a list of patterns. Length of every pattern must be equal.

    Returns
    -------
    timestamps
        List of timestamps, one for each measurement
    data
        Dictionary of timestamps, with each timestamp pointing to a dictionary containing measurements for each axis and metadata
    duration
        Duration of the measurements

    Examples
    --------
    >>> pattern = {'acc_x': [0] * 1 + [1] * 1, 'acc_x': [0] * 2, 'acc_z': [1] * 2}
    >>> timestamps, data, duration = stub_multiaxial_data()
    >>> print(data)
    {0: {"data": {"acc_x": [...], "acc_y": [...], "acc_z": [...]}, "meta": {}}, 3600000: {"data": {"acc_x": [...], "acc_y": [...], "acc_z": [...]}, "meta": {}}}
    """

    # Collect list of axis and number of measurements from pattern
    axes = list(pattern.keys())
    assert len(axes) > 0 and len(axes) <= 3
    n_meas = len(list(pattern.values())[0])
    assert all(len(p) == n_meas for p in pattern.values())

    timestamps = [k * 3600 * 1000 for k in range(n_meas)]
    n_samples = int(samp_freq * duration)
    T = np.linspace(0.0, duration, n_samples + 1)
    f_peak = 300.0
    np.random.seed(0)

    # Find unique modes from the pattern
    unique_modes = set()
    for value_list in list(pattern.values()):
        unique_modes.update(value_list)

    # Define signal for each unique mode
    signals = []
    for k in unique_modes:
        signals.append(np.cos(2 * np.pi * (f_peak + (k * 200)) * T))

    # Generate data dict
    # Iterate through a zip of (timestamp, list of axis, list of pattern for the timestamp)
    data = {}
    pattern_by_meas = zip(*pattern.values())
    for timestamp, axes_list, ptn_list in zip(
        timestamps, cycle([axes]), pattern_by_meas
    ):
        data[timestamp] = {
            "data": {
                axis: list(signals[ptn] + np.random.normal(0, 0.05, len(T)))
                for (axis, ptn) in zip(axes_list, ptn_list)
            },
            "meta": {
                "duration": duration,
                "sampling_rate": samp_freq,
            },
        }

    return timestamps, data, duration

def generate_sources_patterns():
    """Generate a list of multiaxial sources with axis-based patterns"""
    sources_patterns = [
        (
            "multiaxial_source_001",
            {
                "acc_x": [0] * 6 + [1] * 14 + [0] * 5,
                "acc_y": [0] * 6 + [1] * 14 + [0] * 5,
                "acc_z": [0] * 6 + [1] * 14 + [0] * 5,
            },
        )
    ]
    return sources_patterns
