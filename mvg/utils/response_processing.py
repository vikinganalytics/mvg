"""
This module contains helper functions for manipulating the response from endpoints.
"""

from enum import Enum
from typing import Callable, Dict

from pydantic import conlist

FrequencyRange = conlist(float, min_items=2, max_items=2)


def clamp(value, minimum, maximum):
    """
    Clamps a value within a specified range.

    Parameters
    ----------
    value : float|int
        The value to be clamped.
    minimum : float|int
        The minimum value of the range.
    maximum : float|int
        The maximum value of the range.

    Returns
    -------
    float or int: The clamped value,
    which is guaranteed to be within the range [minimum, maximum].

    Example
    -------
        >>> clamp(10, 0, 5)
        5
        >>> clamp(3, 0, 5)
        3
        >>> clamp(-1, 0, 5)
        0
    """

    return max(minimum, min(value, maximum))


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
    response = request("get", url, params=params)
    response = response.json()
    items = response["items"]
    total_items_num = response["total"]
    request_limit = response["limit"]

    offset = params.get("offset", response["offset"])
    limit = params.get("limit", total_items_num)

    # The items count we expect to receive given the pagination params
    expected_num = clamp(limit, 0, total_items_num - offset)

    # The items count we didn't receive due to request max items limit
    missing_num = expected_num - len(items)

    # How many additional requests to fetch the data
    num_reqs = (missing_num - 1) // request_limit + 1

    for _ in range(0, num_reqs):
        if "limit" in params:
            params["limit"] -= request_limit
        offset += request_limit
        params["offset"] = offset
        response = request("get", url, params=params)
        items += response.json()["items"]

    return {"items": items, "total": total_items_num, "limit": request_limit}


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
