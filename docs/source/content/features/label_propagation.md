# Label Propagation

.. image:: ../img/label-propagation_sales.png

## What does Label Propagation do?

The label propagation feature spreads existing ground truth labels to unlabelled measurements.

## Use case for the algorithm

Associate labels to all individual measurements without 
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

.. image:: ../img/labelpropagation_plots.png

## Using the algorithm via mvg

For code example see the ["Labeling and Label Propagation"](../examples/7-labeling.ipynb) example.

1. Identify the `request_id` of a successful ModeId analysis.

2. Request an analysis for the source and pass the `request_id` as an analysis parameter.

3. Read the results (see below).

## Analysis Parameters

The LabelPropagation feature requires to know the source id (`sid`) of the asset to analyze and the `request_id` of a successful "ModeId" analysis.

By default, LabelPropagation will not require any additional, algorithmic input parameters,
given that the optimal parameters had been thoroughly tested and are used as the default settings.


## Structure of the Results

The results returned by the analysis call will be a dictionary called `propagated_labels`, 
which contains a list equal to the number of measurements in the source.
Each item on this list is a dictionary with five elements, the keys of these elements are: *label*, *severity*, *notes*, *label_timestamp*, and *timestamp*.
This final item refers to the timestamp of the measurement.


```
{ 
    'propagated_labels': [... list of measurement results ...],
}
```

## Notes

1. The label identification string is unique for each label and is case and spelling sensitive, i.e. `"failure"` and `"Failure"` are not interpreted as the same label. 
   
2. The propagated severity level is used to indicate whether the label was added by the user or propagated by the algorithm. A value of -1 means that the label was propagated by the algorithm.
   
3. The notes exist for the end user to add extra information to a certain label and is not used by MVG in any way.


   