# KPI Demo

.. image:: ../img/rms_sales.png

## What does KPIDemo do?

The KPIDemo feature calculates a set of Key Performance Indicators (KPIs) of vibration measurements. The calculated KPIs are

- RMS - Estimate of vibration amplitude
- Peak - Maximum acceleration value
- Peak to peak - Difference between maximum and minimum acceleration value
- Variance - Variance of the vibration
- Crest factor - Ratio of the peak value of the waveform to its RMS value
- Utilization - Boolean value if vibration RMS is above a given utilization threshold, default to 0.1
- DC component - Estimated value for the DC bias of the signal

## Use cases for the feature

- Determining trends in the vibration level over time. An increasing
  trend may indicate a developing failure.

- Comparing similar assets in terms of their RMS (or other KPI) value.

- High level visualization of vibration measurements.

## How the KPIs work

Each KPI attempts to summarize some behaviour of the vibration measurement into a single number. Below are the formulas for each of the KPIs where $x \in \mathbb{R}^n$ is the vibration measurement vector.

### RMS

The most common KPI is the Root Mean Square (RMS) of the measurement.

.. math:: \sqrt{ \frac{1}{n} \left( x_1^2 + x_2^2 + \dots + x_n^2 \right) }

The plot below shows a series of acceleration samples and the
calculated RMS.

.. image:: ../img/rms_plot.png

### Peak

The peak is the maximum value from a measurement.

.. math:: Peak = \max(x)

### Peak to peak

The peak to peak is the difference between the maximum and the minimum value in the measurement.

.. math:: \max(x) - \min(x)

### Variance

The statistical variance of the measurement values.

.. math:: \frac{1}{n}\sum_{i=1}^{n}(x_i - \mu)^2

Where $n$ is the number of samples in the measurement and $\mu$ is the average measurement value.

### Crest factor

.. math:: \max(||x||) / \text{RMS}(x)

### Utilization

.. math:: \theta(\text{RMS(x)} - t)

Where $t$ is the utilization threshold and $\theta$ is the heaviside step function.

### DC component

The DC bias of the signal is estimated as the mean value of the signal.

.. math:: \frac{1}{n} \sum_{i=1}^{n}a_{i} = \frac {a_{1} + a_{2} + \dots + a_{n}}{n}

## Using the algorithm via mvg

1. Upload vibration time series data to a source.

2. Request a KPIDemo analysis for the source.

3. Read the results(see below).

## Analysis Parameters

The KPIDemo feature requires no parameters apart from sourceId (sid).

## Structure of the Results

The result returned by the analysis call will be a dictionary
containing eight lists:
```
{
    'timestamps': [... list of timestamps ...],
    'rms': {"channel": [... list of floats ...]},
    'peak': {"channel": [... list of floats ...]},
    'peak2peak': {"channel": [... list of floats ...]},
    'variance': {"channel": [... list of floats ...]},
    'crest_factor': {"channel": [... list of floats ...]},
    'utilization': {"channel": [... list of ints ...]},
	'dc_component': {"channel": [... list of floats ...]},
}
```

## Notes

1. The feature is agnostic to the scale of the measurements, but the
   scale for all measurements needs to be consistent.

2. The measurements are trimmed of DC offset.

3. Neither of the KPIs are selective of frequency bands.
