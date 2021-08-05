# Envelope

.. image:: ../img/envelope.png

## What does Envelope do?

It calculates and displays the FFT of the raw signal as well as the
Enveloped (demodulated signal). The Envelope feature allows for basic 
analysis of the frequency domain view of waveform measurement data. 

## Use cases for the algorithm

* Finding peaks in the frequency domain representation of vibration signals.

* Using Envelope analysis e.g. demodulate the raw frequency signal for
  finding failures with low frequency signatures, e.g. outer race failures.


## How does the Enveloping feature work?

### FFT
For each single waveform measurement the FFT is calculated from the
time domain samples according to standard procedures: Before
calculation the DC component is removed.

### Enveloping
Prior to the FFT calculation, the time domain signal is demodulated,
with the aim to remove the system's eigen frequency and just show the
modulating frequencies. Technically demodulation is achieved by means
of a succession of low-pass filtering, high-pass filtering and a final
low pass filtering, alternatively Hilbert transformation.


## Using the algorithm via mvg

1. Upload vibration time series data to a source.

2. Request an Envelope analysis for the source.

3. Use the Analysis Classes to obtain plots, summaries and a proper
   representation of the results.

## Analysis Parameters

### Mandatory Arguments

- sid: source_id
- feature = "Envelope"


### Optional Arguments

#### Timestamps

- start_timestamp

- end_timestamp

By default Envelope will do the calculation for all timestamps
available in the database. The results returned will be the average
spectrum and the standard deviation per frequency bin for FFT and
envelope.

To select a subset specify start_timestamp and end_timestamp. For
analyzing just a single timestamp use that specific value for
start_timestamp and end_timestamp.

#### Algorithm Parameters

A number of optional arguments can be passed to adapt the analysis, if
no values are given default values are used (values in square
brackets).

- max_samples: the maximum number of time domain samples to use for
  FFT and enveloping [16384]. If data has less samples, the analysis
  will only use available samples.
  
- env_lo: lower cutoff frequency for the enveloping [undisclosed
  default value]
  
- env_hi: higher cutoff frequency for the enveloping [undisclosed
  default value]

- env_order: filter order for enveloping [4]

- env_squared: whether to use squared envelope [False]

- env_squared: whether to use Hilbert transform rather than low-pass filter [True]


## Produced results

All standard functions of the analysis classes are supported, most
notably:

- plot(): will plot raw FFT, envelope and zoomed envelope. If more
  than one timestamp is given amplitudes + 1 SD will also be plotted
  (see above).

- to_df(): will give amplitudes (and SDEV) for raw FFT and enveloped FFT.


## References

The implementation follows:

Wade A. Smith and Robert B. Randall (2005), Rolling element bearing
diagnostics using the Case Western Reserve University data: A
benchmark study, Mechanical Systems and Signal Processing.





