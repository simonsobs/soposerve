"""
Utilities for product search and rendering search results.
"""

import types
from typing import Literal, Union, get_args, get_origin

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from hippometa import ALL_METADATA
from hipposerve.service import collection, product

from .router import templates

router = APIRouter()


def has_list(field_type):
    """
    A simple utility function to test if a type contains a list
    """
    if get_origin(field_type) is list:
        return True
    elif get_origin(field_type) in {types.UnionType, Union}:
        args = get_args(field_type)
        return any(get_origin(arg) is list for arg in args)
    else:
        return False


# Grabs the list argument, but assumes we wouldn't have more than one
# list in a union type
def get_list_arg(field_type):
    args = get_args(field_type)
    if len(args) == 1:
        return args[0].__name__
    else:
        list_arg = [arg for arg in args if get_origin(arg) is list]
        return get_args(list_arg[0])[0].__name__


# Query and render search results from the navigation bar's "search by name" option
@router.get("/search/results", response_class=HTMLResponse)
async def search_results_view(
    request: Request, q: str = None, filter: str = "products"
):
    if filter == "products":
        results = await product.search_by_name(q)
    elif filter == "collections":
        results = await collection.search_by_name(q)
    else:
        results = []

    return templates.TemplateResponse(
        "search_results.html",
        {"request": request, "query": q, "filter": filter, "results": results},
    )


# Query and render search results for the more complex metadata request
@router.get("/searchmetadata/results", response_class=HTMLResponse)
async def searchmetadata_results_view(
    request: Request, q: str = None, filter: str = "products"
):
    query_params = dict(request.query_params)
    # Determine which metadata_class we're searching on so we can get the fields;
    # we will use the fields with the query_params to craft type-specific queries
    metadata_class = next(
        (
            cls
            for cls in ALL_METADATA
            if cls.model_json_schema()["title"] == query_params["metadata_type"]
        )
    )
    metadata_fields = metadata_class.__annotations__

    # Will hold the queries as we craft them below
    metadata_filters = {}

    for key, value in query_params.items():
        if key == "metadata_type":
            continue

        # Literals don't need any regex or case insensitity
        if getattr(metadata_fields[key], "__origin__", None) is Literal:
            metadata_filters[key] = value
        elif has_list(metadata_fields[key]):
            list_type_arg = get_list_arg(metadata_fields[key])
            # Add some number-specific query logic to list[int] and list[float]
            if list_type_arg == "int" or list_type_arg == "float":
                numerical_values = value.split(",")
                min = (
                    numerical_values[0] if numerical_values[0] != "undefined" else None
                )
                max = (
                    numerical_values[1] if numerical_values[1] != "undefined" else None
                )
                if min is not None:
                    metadata_filters[key] = {"$gte": min}
                if max is not None:
                    metadata_filters[key] = metadata_filters.get(key, {})
                    metadata_filters[key]["$lte"] = max
            # Add query logic to list[str] types
            elif list_type_arg == "str":
                metadata_filters[key] = {"$in": [v.strip() for v in value.split(",")]}
            else:
                # Apply a default query as a fallback
                metadata_filters[key] = {"$regex": value, "$options": "i"}
        else:
            # Default queries include regex and case insensitivity
            metadata_filters[key] = {"$regex": value, "$options": "i"}

    results = await product.search_by_metadata(metadata_filters)

    return templates.TemplateResponse(
        "search_results.html",
        {
            "request": request,
            "query": q,
            "filter": filter,
            "results": results,
            "metadata_filters": metadata_filters,
            "metadata_type": query_params["metadata_type"],
        },
    )


@router.get("/searchmetadata", response_class=HTMLResponse)
async def search_metadata_view(request: Request):
    metadata_info = {}

    for metadata_class in ALL_METADATA:
        if metadata_class is None:
            continue

        class_schema = metadata_class.model_json_schema()
        class_name = class_schema["title"]
        class_fields = class_schema["properties"]

        # Separate number fields from other types so we can render the number
        # fields together in the metadata search page
        number_fields = {}
        other_fields = {}

        for field_key, field_data in class_fields.items():
            # additionalProperties means the field is a dictionary with arbitrary keys
            # we can't search on that.
            if field_key == "metadata_type" or "additionalProperties" in field_data:
                continue

            if "anyOf" in field_data:
                # This occurs when we have x | None, extract x and stick it in the field_data
                true_type = [x for x in field_data["anyOf"] if x["type"] != "null"][0]
                field_data = {**field_data, **true_type}
                field_data.pop("anyOf")

            field_type = field_data.get("type", None)

            if "enum" in field_data:
                other_fields[field_key] = {
                    "type": "enum",
                    "title": field_data["title"],
                    "options": field_data["enum"],
                }
            elif field_type == "array":
                other_fields[field_key] = {
                    "type": "array",
                    "list_arg": field_data["items"]["type"],
                    "title": field_data["title"],
                }
            elif field_type == "number":
                number_fields[field_key] = {
                    "type": "number",
                    "title": field_data["title"],
                    "min": field_data.get("min", None),
                    "max": field_data.get("max", None),
                }
            else:
                other_fields[field_key] = {
                    "type": field_type,
                    "title": field_data["title"],
                }

        metadata_info[class_name] = {**number_fields, **other_fields}

    return templates.TemplateResponse(
        "search_metadata.html",
        {"request": request, "metadata": metadata_info},
    )
