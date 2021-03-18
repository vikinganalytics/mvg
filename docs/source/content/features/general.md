# Using MVG features

MVG provides a set of analytics features for analysis of
vibration data. The documentation in the FEATURES section 
focuses mostly on description of
the features, for detailed information on how to invoke the features
via the API, consult the [API Reference](../api_reference/mvg.html) or
the [Examples](../examples/analysis_visual.html).

## How to use features via MVG

1. All features require data for the sources to be uploaded prior to invocation.

2. Features are invoked via the 
[request_analysis](../api_reference/mvg.html#mvg.mvg.MVG.request_analysis) or the
[request_population_analysis](../api_reference/mvg.html#mvg.mvg.MVG.request_population_analysis) 
methods. The former are features related
to a single source (which is specified via the source id
parameter, while the latter are features which operate on a population
of sources, which are provided in the sids (source ids) parameter; a
list holding the source ids defining the population. Which feature to
run is specified by the `feature` argument.  In case additional parameters are required or supported they are 
documented under the specific feature. On invoking a feature the
analytics engine will queue the analysis and then execute it.

4. After invocation the status of the analysis can be queried via the
[get_analysis_status](../api_reference/mvg.html#mvg.mvg.MVG.get_analysis_status)
method.

5. Once the returned status is "successful", the analysis results can be
   retrieved using the
   [get_analysis_results](../api_reference/mvg.html?highlight=sis_res#mvg.mvg.MVG.get_analysis_results)
   method. 
   
6. The results are returned as a dictionary of the following
structure:

```
{
    'status': "<if call was successful>",
	'results': {<dict with actual results>}
}
```

The format of the actual results in the `results` section is documented under respective feature.
   
## Notes

1. The time until the analytics server has finished will vary
   depending on feature, amount of data to be processed and server
   load. Although normally analyses will complete in less than
   a minute, under extreme conditions that could take as long as 15 minutes.

2. Analyses may fail. Typically these failures are due to the
   algorithm not being able to be run due to the supplied input data 
   (e.g. due to singular  matrices if data is too highly correlated). 

2. If you suspect a bug, please place an issue in our 
   [issue tracking on GitHub](https://github.com/vikinganalytics/mvg/issues).









