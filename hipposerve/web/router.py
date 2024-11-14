"""
Builds the router and templates.
"""

from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

web_router = APIRouter(prefix="/web")

templates = Jinja2Templates(
    directory="hipposerve/web/templates",
    extensions=["jinja_markdown.MarkdownExtension"],
)

static_files = {
    "path": "/web/static",
    "name": "static",
    "app": StaticFiles(directory="hipposerve/web/static"),
}
