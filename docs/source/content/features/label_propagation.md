# Label Propagation

.. image:: ../img/label-propagation_sales.png

## What does Label Propagation do?

The label propagation feature spreads existing ground truth labels to unlabelled measurements.

## Use case for the algorithm

Provide with labels to all individual measurements without 
an expert having to manually provide with a label to every single measurement.


## How does Label Propagation work?

Label propagation uses a semi-supervised algorithm for the spreading of the labels.
It uses the results from the ModeId, such as mode assigment and mode probability of each individual measurement, 
along with the ground truth labels provided by the expert.
Therefore, the provided labels will be propagated to all measurements.
Ideally, the expert should had provided at least one label per each mode segment.
However, the more labels had been provided the better is the performance of the algorithm.
The end result is a label attached to each individual measurement.

### Illustrative Example

The figure below shows the results of a ModeId analysis where a total of three operational modes has been identified.
This is followed by a plot showing the initial labeled measurements, which correspond to three measurements per mode.
Finally, it shows how all the labels had been propagated to all the measurements after using the LabelPropagation feature.

.. image:: ../img/BLABLABLA_plot.png

## Using the algorithm via mvg

For code example see the ["Labeling and Label Propagation"](../examples/7-labeling.ipynb) example.

1. Identify the request_id of a successful ModeId analysis.

2. Request an analysis for the source and pass the request_id as a analysis parameter.

3. Readd the results (see below).

## Analysis Parameters

The LabelPropagation feature requires to know the source id (`sid`) of the asset to analyze and the `request_id` of a successful "ModeId" analysis.

By default, LabelPropagation will not require any additional, algorithmic input parameters,
given that the optimal parameters had been thoroughly tested and are used as the default settings.

If, however, these parameters want to be modified, these are the parameters that can updated.

```
"propagation_params":
{
	'n_neighbours': 7,
	'clamping_factor': 0.2
}
```


## Structure of the Results

BLIBLIBLI
```
{ 
	'atypical_assets': ['source 2', 'source 3']
}
```

## Notes

1. XXXXXXXXXXXXXXXXX.

2. YYYYYYYYYYYYYYYYY.
   