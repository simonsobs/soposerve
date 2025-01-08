"""
Builds the router and templates.
"""

from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

web_router = APIRouter(prefix="/web")

# potential_routes = ["", "hippo/"]
potential_routes = [""]

for route in potential_routes:
    try:
        templates = Jinja2Templates(
            directory=f"{route}hipposerve/web/templates",
            extensions=["jinja_markdown.MarkdownExtension"],
        )

        static_files = {
            "path": "/web/static",
            "name": "static",
            "app": StaticFiles(
                directory=f"{route}hipposerve/web/static", follow_symlink=True
            ),
        }
    except (FileNotFoundError, RuntimeError):
        continue
