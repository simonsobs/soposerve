"""
Authentication code for the API, which uses api key based
authentication.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from soposerve.service import users

api_key_header = APIKeyHeader(name="X-API-Key")


async def get_user(api_key_header: str = Security(api_key_header)) -> users.User:
    try:
        return await users.user_from_api_key(api_key_header)
    except users.UserNotFound:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )


UserDependency = Annotated[users.User, Depends(get_user)]


async def check_user_for_privilege(
    user: users.User, privilege: users.Privilege
) -> None:
    if privilege not in user.privileges:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient privileges",
        )
