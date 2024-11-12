"""
Routes for user management.

TODO: Authentication.
"""

from fastapi import APIRouter, HTTPException, status

from hipposerve.api.auth import UserDependency, check_user_for_privilege
from hipposerve.api.models.users import (
    CreateUserRequest,
    CreateUserResponse,
    ReadUserResponse,
    UpdateUserRequest,
    UpdateUserResponse,
)
from hipposerve.service import users
from hipposerve.settings import SETTINGS

users_router = APIRouter(prefix="/users")


@users_router.put("/{name}")
async def create_user(
    name: str,
    request: CreateUserRequest,
    calling_user: UserDependency,
    # TODO: Compliance
) -> CreateUserResponse:
    """
    Create a new user.
    """

    await check_user_for_privilege(calling_user, users.Privilege.CREATE_USER)

    try:
        user = await users.read(name=name)

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists."
        )
    except users.UserNotFound:
        user = await users.create(
            name=name,
            password=request.password,
            email=None,
            avatar_url=None,
            gh_profile_url=None,
            privileges=request.privileges,
            hasher=SETTINGS.hasher,
        )

    return CreateUserResponse(api_key=user.api_key)


@users_router.get("/{name}")
async def read_user(name: str, calling_user: UserDependency) -> ReadUserResponse:
    """
    Read a user's details, but not their API key.
    """

    if name != calling_user.name:
        await check_user_for_privilege(calling_user, users.Privilege.READ_USER)

    user = await users.read(name=name)

    return ReadUserResponse(
        name=user.name,
        privileges=user.privileges,
    )


@users_router.post("/{name}/update")
async def update_user(
    name: str, request: UpdateUserRequest, calling_user: UserDependency
) -> UpdateUserResponse:
    """
    Update a user's details. At present, only admins can update users.
    """

    await check_user_for_privilege(calling_user, users.Privilege.UPDATE_USER)

    user = await users.update(
        name=name,
        privileges=request.privileges,
        refresh_key=request.refresh_key,
        password=request.password,
        hasher=SETTINGS.hasher,
    )

    return UpdateUserResponse(api_key=user.api_key if request.refresh_key else None)


@users_router.delete("/{name}")
async def delete_user(name: str, calling_user: UserDependency) -> None:
    """
    Delete a user.
    """

    await check_user_for_privilege(calling_user, users.Privilege.DELETE_USER)

    await users.delete(name=name)

    return
