"""
Routes for user management.

TODO: Authentication.
"""

from fastapi import APIRouter, HTTPException, status

from soposerve.api.models.users import (
    CreateUserRequest,
    CreateUserResponse,
    ReadUserResponse,
    UpdateUserRequest,
    UpdateUserResponse,
)
from soposerve.service import users

users_router = APIRouter(prefix="/users")


@users_router.put("/create/{name}")
async def create_user(
    name: str,
    request: CreateUserRequest,
    # TODO: Compliance
) -> CreateUserResponse:
    """
    Create a new user.
    """

    try:
        user = await users.read(name=name)

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists."
        )
    except users.UserNotFound:
        user = await users.create(
            name=name,
            privileges=request.privileges,
        )

    return CreateUserResponse(api_key=user.api_key)


@users_router.get("/read/{name}")
async def read_user(name: str) -> ReadUserResponse:
    """
    Read a user's details, but not their API key.
    """

    user = await users.read(name=name)

    return ReadUserResponse(
        name=user.name,
        privileges=user.privileges,
    )


@users_router.post("/update/{name}")
async def update_user(name: str, request: UpdateUserRequest) -> UpdateUserResponse:
    """
    Update a user's details.
    """

    user = await users.update(
        name=name,
        privileges=request.privileges,
        refresh_key=request.refresh_key,
    )

    return UpdateUserResponse(api_key=user.api_key if request.refresh_key else None)


@users_router.delete("/delete/{name}")
async def delete_user(name: str) -> None:
    """
    Delete a user.
    """

    await users.delete(name=name)

    return
