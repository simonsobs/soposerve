"""
Web frontend for SOPO. This consumes the service layer.

NOTE: Code coverage is an explicit NON-goal for the web
      frontend, and as such it is excluded from our
      coverage metrics.
"""

from fastapi import APIRouter, Request

# Consider: jinja2-fragments for integration with HTMX.
from fastapi.templating import Jinja2Templates

from soposerve.service import collection, product

# TODO: Static file moutning.

web_router = APIRouter(prefix="/web")
templates = Jinja2Templates(directory="soposerve/web/templates")


@web_router.get("/")
async def index(request: Request):
    products = await product.read_most_recent(fetch_links=True, maximum=16)
    collections = await collection.read_most_recent(fetch_links=True, maximum=16)

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "products": products, "collections": collections},
    )


@web_router.get("/products/{name}")
async def product_view(request: Request, name: str):
    product_instance = await product.read(name)
    sources = await product.presign_read(product_instance, storage=request.app.storage)

    return templates.TemplateResponse(
        "product.html",
        {"request": request, "product": product_instance, "sources": sources},
    )


@web_router.get("/collections/{name}")
async def collection_view(request: Request, name: str):
    collection_instance = await collection.read(name)

    return templates.TemplateResponse(
        "collection.html", {"request": request, "collection": collection_instance}
    )
