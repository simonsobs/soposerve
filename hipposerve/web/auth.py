"""
Authentication layer for the Web UI. Provides two core dependencies:

- `LoggedInUser` - a dependency that requires a user to be logged in. If the user is not logged in, a 401 Unauthorized response is returned.
- `PotentialLoggedInUser` - a dependency that returns a user if they are logged in, or `None` if they are not.
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from beanie import PydanticObjectId
from fastapi import Depends, HTTPException, Request, status
from fastapi.openapi.models import OAuthFlows
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from pydantic import BaseModel

from hipposerve.service import users as users_service
from hipposerve.settings import SETTINGS


class OAuth2PasswordBearerWithCookie(OAuth2):
    """
    A custom OAuth2 scheme (extremely similar to the built-in FastAPI
    ``OAuth2PasswordBearer`` scheme) that reads the token from a cookie
    instead of the `Authorization` header. The key method here is ``__call__``,
    which reads the token from the cookie, given a request object, and returns
    the token as a string.

    For more complete documentation see the FastAPI documentation on OAuth2
    authentication schemes: ``https://fastapi.tiangolo.com/reference/security/``.

    Parameters
    ----------
    tokenUrl : str
        The URL to obtain the OAuth2 token. This would be the path operation that has
        ``OAuth2PasswordRequestForm`` as a dependency.
    scheme_name : str, optional
        The name of the scheme for OpenAPI docs. Defaults to `None`.
    scopes : dict, optional
        The OAuth2 scopes that would be required by the path operations
        that use this dependency.
    auto_error : bool, optional
        By default, if no HTTP Authorization header is provided, required for
        OAuth2 authentication, it will automatically cancel the request and
        send the client an error.

        If auto_error is set to False, when the HTTP Authorization cookie
        is not available, instead of erroring out, the dependency result
        will be None.

        This is provided for compatibility with other OAuth2 schemes, however
        in hippo we use two separate dependencies for this purpose.

    Notes
    -----
    This should, in theory, enable the 'docs' Web UI to store the token in a cookie
    and work as expected. However, the current implementation does not fully satisfy
    this as I believe the password form is expecting to use a header. A potential
    way around this would be to set both, but that could lead to inconsistencies.

    """

    def __init__(
        self,
        tokenUrl: str,
        scheme_name: str = None,
        scopes: dict = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlows(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> str | None:
        authorization: str = request.cookies.get("access_token")

        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None

        return param


oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="/web/token")


class WebTokenData(BaseModel):
    username: str | None = None
    user_id: PydanticObjectId | None = None
    origin: str | None = None

    def encode(self):
        return f"{self.username}:::{self.user_id}:::{self.origin}"

    @classmethod
    def decode(cls, token: str):
        username, user_id, origin = token.split(":::")
        return cls(username=username, user_id=PydanticObjectId(user_id), origin=origin)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], request: Request
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, SETTINGS.web_jwt_secret, algorithms=[SETTINGS.web_jwt_algorithm]
        )
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception
        token_data = WebTokenData.decode(sub)
        print(token_data)
    except jwt.PyJWTError:
        raise credentials_exception
    except ValueError:
        # Unable to split
        raise credentials_exception

    if SETTINGS.web_jwt_check_origin:
        # Don't use the Origin header as it's often not set (e.g. it is never set
        # on GET requests as the browser already checked that). Let's just use the
        # Sec-Fetch-Site header instead.
        potential_origin = request.headers.get("Sec-Fetch-Site")
        if potential_origin == "cross-origin":
            raise credentials_exception

    try:
        user = await users_service.read_by_id(id=token_data.user_id)
    except users_service.UserNotFound:
        raise credentials_exception

    return user


async def get_potential_current_user(request: Request):
    try:
        token = await oauth2_scheme(request=request)
        if token:
            return await get_current_user(token)
    except HTTPException:
        return None

    return None


def create_access_token(
    user: users_service.User, expires_delta: timedelta, origin: str
):
    to_encode = {
        "exp": datetime.now(timezone.utc) + expires_delta,
        "sub": WebTokenData(
            username=user.name, user_id=user.id, origin=origin
        ).encode(),
    }
    encoded_jwt = jwt.encode(
        to_encode, SETTINGS.web_jwt_secret, algorithm=SETTINGS.web_jwt_algorithm
    )
    print(to_encode)
    return f"Bearer {encoded_jwt}"


LoggedInUser = Annotated[users_service.User, Depends(get_current_user)]
PotentialLoggedInUser = Annotated[
    users_service.User | None, Depends(get_potential_current_user)
]
