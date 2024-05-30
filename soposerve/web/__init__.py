"""
Web frontend for SOPO. This consumes the service layer.

NOTE: Code coverage is an explicit NON-goal for the web
      frontend, and as such it is excluded from our
      coverage metrics.
"""

from fastapi import APIRouter, Request

# Consider: jinja2-fragments for integration with HTMX.
from fastapi.templating import Jinja2Templates

from soposerve.service import product

# TODO: Static file moutning.

web_router = APIRouter(prefix="/web")
templates = Jinja2Templates(directory="soposerve/web/templates")


@web_router.get("/")
async def index(request: Request):
    products = await product.read_most_recent(fetch_links=True, maximum=16)

    return templates.TemplateResponse(
        "index.html", {"request": request, "products": products}
    )
