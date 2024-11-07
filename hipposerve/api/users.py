"""
Routes for user management.

TODO: Authentication.
"""

from fastapi import APIRouter, HTTPException, status
from loguru import logger

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

    logger.info("Request to create user: {} from {}", name, calling_user.name)

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
            privileges=request.privileges,
            hasher=SETTINGS.hasher,
        )

    logger.info("User {} created for {}", user.name, calling_user.name)

    return CreateUserResponse(api_key=user.api_key)


@users_router.get("/{name}")
async def read_user(name: str, calling_user: UserDependency) -> ReadUserResponse:
    """
    Read a user's details, but not their API key.
    """

    logger.info("Request to read user: {} from {}", name, calling_user.name)

    if name != calling_user.name:
        await check_user_for_privilege(calling_user, users.Privilege.READ_USER)

    user = await users.read(name=name)

    logger.info("User {} read by {}", name, calling_user.name)

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

    logger.info("Request to update user: {} from {}", name, calling_user.name)

    await check_user_for_privilege(calling_user, users.Privilege.UPDATE_USER)

    user = await users.update(
        name=name,
        privileges=request.privileges,
        refresh_key=request.refresh_key,
        password=request.password,
        hasher=SETTINGS.hasher,
    )

    logger.info(
        "User {} updated by {} with new API key"
        if request.refresh_key
        else "User {} updated by {}",
        name,
        calling_user.name,
    )

    return UpdateUserResponse(api_key=user.api_key if request.refresh_key else None)


@users_router.delete("/{name}")
async def delete_user(name: str, calling_user: UserDependency) -> None:
    """
    Delete a user.
    """

    logger.info("Request to delete user: {} from {}", name, calling_user.name)

    await check_user_for_privilege(calling_user, users.Privilege.DELETE_USER)

    await users.delete(name=name)

    logger.info("User {} deleted by {}", name, calling_user.name)

    return
