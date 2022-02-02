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

BLABLABLA

.. image:: ../img/BLABLABLA_plot.png

## Using the algorithm via mvg

1. AAAAAAAAAAAAA.

2. BBBBBBBBBBBBBBBB.

3. CCCCCCCCCCCCCCC.

## Analysis Parameters

BLEBLEBLE


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
   