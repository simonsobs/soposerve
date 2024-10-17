"""
Web frontend for SOPO. This consumes the service layer.

NOTE: Code coverage is an explicit NON-goal for the web
      frontend, and as such it is excluded from our
      coverage metrics.
"""

from beanie import PydanticObjectId
from fastapi import APIRouter, Request

# Consider: jinja2-fragments for integration with HTMX.
from fastapi.templating import Jinja2Templates

from soposerve.service import collection, product

# TODO: Static file moutning.

web_router = APIRouter(prefix="/web")
templates = Jinja2Templates(
    directory="soposerve/web/templates", extensions=["jinja_markdown.MarkdownExtension"]
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
