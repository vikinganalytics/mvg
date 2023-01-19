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
    Dict
        A dictionary containing the items and total number of items.
    """
    if "limit" in params or "offset" in params:
        response = request("get", url, params=params)
        response = response.json()
        all_items = response["items"]
        num_items = response["total"]
    else:
        # List all by default if pagination is not requested
        response = request("get", url)
        resp_first = response.json()
        all_items = resp_first["items"]
        num_items = resp_first["total"]
        limit = resp_first["limit"]
        num_reqs = (num_items - 1) // limit
        for idx in range(1, num_reqs + 1):
            offset = idx * limit
            response = request("get", url, params={"offset": offset})
            all_items += response.json()["items"]
    return {"items": all_items, "total": num_items}
