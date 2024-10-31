"""
Web frontend for hippo. This consumes the service layer.

NOTE: Code coverage is an explicit NON-goal for the web
      frontend, and as such it is excluded from our
      coverage metrics.
"""

from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, status

# Consider: jinja2-fragments for integration with HTMX.
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates

from hipposerve.service import collection, product
from hipposerve.service import users as user_service
from hipposerve.settings import SETTINGS
import httpx

from .auth import LoggedInUser, create_access_token

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


# --- Authentication ---

@web_router.get("/github")
async def login_with_github_for_access_token(
    request: Request,
    code: str,
) -> RedirectResponse:
    if not SETTINGS.web_allow_github_login:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="GitHub login is not enabled.",
        )
    
    # See if we can exchange the code for a token.

    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not authenticate with GitHub.",
    )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": SETTINGS.web_github_client_id,
                "client_secret": SETTINGS.web_github_client_secret,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )

    if response.status_code != 200:
        raise unauthorized
    
    access_token = response.json().get("access_token")

    if access_token is None:
        raise unauthorized
    
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        response = await client.get(
            "https://api.github.com/user",
            headers=headers
        )

        if response.status_code != 200:
            raise unauthorized

        user_info = response.json()

        if SETTINGS.web_github_required_organisation_membership is not None:
            response = await client.get(
                user_info["organizations_url"],
                headers=headers
            )

            if response.status_code != 200:
                raise unauthorized

            orgs = response.json()

            if not any(
                org["login"] == SETTINGS.web_github_required_organisation_membership
                for org in orgs
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not a member of the required organisation.",
                )
            
    # At this point we are authenticated and have the user information.
    # Try to match this against a user in the database.
    try:
        user = await user_service.read(name=user_info["login"])
    except user_service.UserNotFound:
        # Need to create one!
        user = await user_service.create(
            name=user_info["login"],
            # TODO: MAKE PASSWORDS OPTIONAL
            password="GitHub",
            privileges=list(user_service.Privilege),
            context=SETTINGS.crypt_context,
        )

    access_token = create_access_token(
        user=user, expires_delta=SETTINGS.web_jwt_expires
    )

    new_response = RedirectResponse(
        url=request.url.path.replace("/github", "/user"), status_code=302
    )

    new_response.set_cookie(key="access_token", value=access_token, httponly=True)
    return new_response
        

@web_router.post("/token")
async def login_for_access_token(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> RedirectResponse:
    try:
        user = await user_service.read_with_password_verification(
            name=form_data.username,
            password=form_data.password,
            context=SETTINGS.crypt_context,
        )
    except user_service.UserNotFound:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        user=user, expires_delta=SETTINGS.web_jwt_expires
    )

    new_response = RedirectResponse(
        url=request.url.path.replace("/token", "/user"), status_code=302
    )
    new_response.set_cookie(key="access_token", value=access_token, httponly=True)
    return new_response


@web_router.get("/logout")
async def logout(request: Request) -> RedirectResponse:
    new_response = RedirectResponse(
        url=request.url.path.replace("/logout", ""), status_code=302
    )
    new_response.delete_cookie(key="access_token")
    return new_response


@web_router.get("/user")
async def read_user(request: Request, user: LoggedInUser):
    return templates.TemplateResponse("user.html", {"request": request, "user": user})


@web_router.get("/login")
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "github_client_id": SETTINGS.web_github_client_id})
