"""
Web frontend for hippo. This consumes the service layer.

NOTE: Code coverage is an explicit NON-goal for the web
      frontend, and as such it is excluded from our
      coverage metrics.
"""

from typing import Literal, get_origin

from beanie import PydanticObjectId
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

# Consider: jinja2-fragments for integration with HTMX.
from fastapi.templating import Jinja2Templates

from hippometa import ALL_METADATA
from hipposerve.service import collection, product

# TODO: Static file moutning.

web_router = APIRouter(prefix="/web")
templates = Jinja2Templates(
    directory="hipposerve/web/templates",
    extensions=["jinja_markdown.MarkdownExtension"],
)


@web_router.get("/")
async def index(request: Request):
    products = await product.read_most_recent(fetch_links=True, maximum=16)
    collections = await collection.read_most_recent(fetch_links=True, maximum=16)

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "products": products, "collections": collections},
    )


@web_router.get("/products/{id}")
async def product_view(request: Request, id: str):
    product_instance = await product.read_by_id(id)
    sources = await product.read_files(product_instance, storage=request.app.storage)
    # Grab the history!
    latest_version = await product.walk_to_current(product_instance)
    version_history = await product.walk_history(latest_version)

    return templates.TemplateResponse(
        "product.html",
        {
            "request": request,
            "product": product_instance,
            "sources": sources,
            "versions": version_history,
        },
    )


@web_router.get("/collections/{id}")
async def collection_view(request: Request, id: PydanticObjectId):
    collection_instance = await collection.read(id)

    return templates.TemplateResponse(
        "collection.html", {"request": request, "collection": collection_instance}
    )


@web_router.get("/search/results", response_class=HTMLResponse)
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


@web_router.get("/searchmetadata/results", response_class=HTMLResponse)
async def searchmetadata_results_view(
    request: Request, q: str = None, filter: str = "products"
):
    query_params = dict(request.query_params)
    metadata_filters = {
        key: value
        for key, value in query_params.items()
        if value and key != "metadata_type"
    }
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


@web_router.get("/searchmetadata", response_class=HTMLResponse)
async def search_metadata_view(request: Request):
    metadata_info = {}

    for metadata_class in ALL_METADATA:
        if metadata_class is not None:
            class_name = metadata_class.__name__
            fields = metadata_class.__annotations__
            temp_fields = {}
            for field_key, field_type in fields.items():
                if get_origin(field_type) is not dict:
                    if getattr(field_type, "__origin__", None) is Literal:
                        literal_values = field_type.__args__
                        temp_fields[field_key] = " | ".join(literal_values)
                    else:
                        temp_fields[field_key] = field_type
            metadata_info[class_name] = temp_fields

    return templates.TemplateResponse(
        "search_metadata.html",
        {"request": request, "metadata": metadata_info},
    )
