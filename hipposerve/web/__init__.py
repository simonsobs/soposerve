"""
Web frontend for hippo. This consumes the service layer.

NOTE: Code coverage is an explicit NON-goal for the web
      frontend, and as such it is excluded from our
      coverage metrics.
"""

from typing import Annotated, Literal, get_args, get_origin

import httpx
from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, status

# Consider: jinja2-fragments for integration with HTMX.
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from hippometa import ALL_METADATA
from hipposerve.service import collection, product
from hipposerve.service import users as user_service
from hipposerve.settings import SETTINGS

from .auth import PotentialLoggedInUser, create_access_token

# TODO: Static file moutning.

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


@web_router.get("/")
async def index(request: Request, user: PotentialLoggedInUser):
    products = await product.read_most_recent(fetch_links=True, maximum=16)
    collections = await collection.read_most_recent(fetch_links=True, maximum=16)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "products": products,
            "collections": collections,
            "user": user,
        },
    )


@web_router.get("/products/{id}")
async def product_view(request: Request, id: str, user: PotentialLoggedInUser):
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
            "user": user,
        },
    )


@web_router.get("/collections/{id}")
async def collection_view(
    request: Request, id: PydanticObjectId, user: PotentialLoggedInUser
):
    collection_instance = await collection.read(id)

    return templates.TemplateResponse(
        "collection.html",
        {"request": request, "collection": collection_instance, "user": user},
    )


@web_router.get("/search/results", response_class=HTMLResponse)
async def search_results_view(
    request: Request,
    user: PotentialLoggedInUser,
    q: str = None,
    filter: str = "products",
):
    if filter == "products":
        results = await product.search_by_name(q)
    elif filter == "collections":
        results = await collection.search_by_name(q)
    else:
        results = []

    return templates.TemplateResponse(
        "search_results.html",
        {
            "request": request,
            "query": q,
            "filter": filter,
            "results": results,
            "user": user,
        },
    )


@web_router.get("/searchmetadata/results", response_class=HTMLResponse)
async def searchmetadata_results_view(
    request: Request,
    user: PotentialLoggedInUser,
    q: str = None,
    filter: str = "products",
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
            "user": user,
        },
    )


@web_router.get("/searchmetadata", response_class=HTMLResponse)
async def search_metadata_view(request: Request, user: PotentialLoggedInUser):
    metadata_info = {}

    for metadata_class in ALL_METADATA:
        if metadata_class is not None:
            class_name = metadata_class.__name__
            fields = metadata_class.__annotations__

            # Separate number fields from other types so we can render the number
            # fields together in the metadata search page
            number_fields = {}
            other_fields = {}

            for field_key, field_type in fields.items():
                if get_origin(field_type) is not dict:
                    if getattr(field_type, "__origin__", None) is Literal:
                        literal_values = field_type.__args__
                        other_fields[field_key] = " | ".join(literal_values)
                    elif get_origin(field_type) is list:
                        list_type = get_args(field_type)[0]
                        list_type_str = f"list[{list_type.__name__}]"

                        if list_type_str in ["list[int]", "list[float]"]:
                            number_fields[field_key] = list_type_str
                        else:
                            other_fields[field_key] = list_type_str
                    else:
                        other_fields[field_key] = field_type

            metadata_info[class_name] = {**number_fields, **other_fields}

    return templates.TemplateResponse(
        "search_metadata.html",
        {"request": request, "metadata": metadata_info, "user": user},
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
        response = await client.get("https://api.github.com/user", headers=headers)

        if response.status_code != 200:
            raise unauthorized

        user_info = response.json()

        if SETTINGS.web_github_required_organisation_membership is not None:
            response = await client.get(user_info["organizations_url"], headers=headers)

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
            email=user_info["email"],
            avatar_url=user_info["avatar_url"],
            gh_profile_url=user_info["html_url"],
            privileges=list(user_service.Privilege),
            hasher=SETTINGS.hasher,
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
    if not SETTINGS.web_only_allow_github_login:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="GitHub login is the only login method enabled",
        )

    try:
        user = await user_service.read_with_password_verification(
            name=form_data.username,
            password=form_data.password,
            hasher=SETTINGS.hasher,
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


@web_router.get("/user/apikey")
async def read_apikey(request: Request, user: PotentialLoggedInUser):
    if user is None:
        new_response = RedirectResponse(
            url=request.url.path.replace("/user/apikey", "/login"), status_code=302
        )
        return new_response
    updated_user = await user_service.update(
        name=user.name,
        hasher=SETTINGS.hasher,
        password=None,
        privileges=user.privileges,
        compliance=None,
        refresh_key=True,
    )
    return templates.TemplateResponse(
        "apikey.html", {"request": request, "user": updated_user}
    )


@web_router.post("/user/update")
async def update_compliance(request: Request, user: PotentialLoggedInUser):
    if user is None:
        new_response = RedirectResponse(
            url=request.url.path.replace("/user/update", "/login"), status_code=302
        )
        return new_response
    form_data = await request.form()
    compliance_info = form_data.get("nersc_user_name")
    await user_service.update(
        name=user.name,
        hasher=SETTINGS.hasher,
        password=None,
        privileges=user.privileges,
        compliance=compliance_info,
        refresh_key=False,
    )
    new_response = RedirectResponse(
        url=request.url.path.replace("/user/update", "/user"), status_code=302
    )
    return new_response


@web_router.get("/user")
async def read_user(request: Request, user: PotentialLoggedInUser):
    if user is None:
        new_response = RedirectResponse(
            url=request.url.path.replace("/user", "/login"), status_code=302
        )
        return new_response
    return templates.TemplateResponse("user.html", {"request": request, "user": user})


@web_router.get("/login")
async def login(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "github_client_id": SETTINGS.web_github_client_id,
            "only_allow_github_login": SETTINGS.web_only_allow_github_login,
            "allow_github_login": SETTINGS.web_allow_github_login,
        },
    )
