"""
This module contains helper functions for manipulating the response from endpoints.
"""

from pydantic import conlist

from enum import Enum
from typing import Dict, Callable

FrequencyRange = conlist(float, min_items=2, max_items=2)

class SortOrder(Enum):
    ASC = "asc"
    DESC = "desc"


def get_paginated_items(request: Callable, url: str, params: Dict) -> Dict:
    """
    Retrieves items and total as a dictionary from a paginated endpoint.
    If offset and limit params are not specified, all items will be returned.

    Parameters
    ----------
    request : Callable
        The request function to be used to make the GET request.
    url : str
        The paginated endpoint URL.
    params : Dict
        The query parameters for the GET request, including optional:
        offset: int
            index of the first timestamp in the database [optional].
        limit: int
            maximum number of timestamps to be returned [optional].

    Returns
    -------
    A dictionary containing the following keys:

        - "items": list of int, representing timestamps.
        - "total": int, representing total number of items.
    """
    if "limit" in params or "offset" in params:
        response = request("get", url, params=params)
        response = response.json()
        all_items = response["items"]
        num_items = response["total"]
    else:
        # List all by default if pagination is not requested
        response = request("get", url, params=params)
        resp_first = response.json()
        all_items = resp_first["items"]
        num_items = resp_first["total"]
        limit = resp_first["limit"]
        num_reqs = (num_items - 1) // limit
        for idx in range(1, num_reqs + 1):
            offset = idx * limit
            params["offset"] = offset
            response = request("get", url, params=params)
            all_items += response.json()["items"]
    return {"items": all_items, "total": num_items}


def get_paginated_analysis_results(request: Callable, url: str, params: Dict) -> Dict:
    """
    Iteratively construct the results of an analysis making use of the
    pagination parameters provided in the params dictionary

    Parameters
    ----------
    request : Callable
        the request object
    url : str
        the URL to retrieve the analysis results
    params : Dict
        parameters dict for the request object

    Returns
    -------
    Dict
        Analysis results
    """
    response = request("get", url, params=params).json()

    if "limit" not in params and "offset" not in params:
        # User has not requested a subset of results
        results = response["results"]

        # Pagination Model fields
        paginator_model_fields = ["total", "limit", "offset"]

        # Does the analysis results include pagination?
        # We remove this check when the backend has enabled pagination for
        # the results of all analysis
        is_paginated = all(f in results for f in paginator_model_fields)
        if is_paginated:
            # Fields with paginated data
            # We might have to later re-enable this to not make this
            # automatically paginate list-based values.
            # paginated_fields = ["timestamps", "labels", "uncertain",
            # "mode_probability"]

            num_items = results["total"]
            limit = results["limit"]
            num_reqs = (num_items - 1) // limit
            for idx in range(1, num_reqs + 1):
                offset = idx * limit
                params["offset"] = offset
                _results = request("get", url, params=params).json()["results"]
                for key in _results:
                    if isinstance(_results[key], list):
                        results[key] += _results[key]

        # Construct the response to return
        response["results"] = results

    return response
