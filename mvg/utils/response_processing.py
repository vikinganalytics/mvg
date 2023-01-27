"""
This module contains helper functions for manipulating the response from endpoints.
"""

from enum import Enum
from typing import Dict, Union, Callable


class SortOrder(Enum):
    ASC = "asc"
    DESC = "desc"


def get_paginated_items(
    request: Callable, url: str, params: Dict[str, Union[int, SortOrder]]
) -> Dict:
    """
    Retrieves items and total as a dictionary from a paginated endpoint.
    If offset and limit params are not specified, all items will be returned.

    Parameters
    ----------
    request : Callable
        The request function to be used to make the GET request.
    url : str
        The paginated endpoint URL.
    params : Dict[str, Union[int, SortOrder]]
        The query parameters for the GET request.

    Returns
    -------
    A dictionary containing the following keys:

        - "offset": int, representing starting point of returned items.
        - "limit: int, representing max items to return."
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
