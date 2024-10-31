"""
Facilities for creating and updating users.
"""

import secrets

from beanie import PydanticObjectId
from passlib.context import CryptContext

from hipposerve.database import Privilege, User

# TODO: Settings
API_KEY_BYTES = 128


def API_KEY():
    return secrets.token_urlsafe(API_KEY_BYTES)


# TODO: Centralised exceptions?
class UserNotFound(Exception):
    pass


class AuthenticationError(Exception):
    pass


async def create(
    name: str, password: str, privileges: list[Privilege], context: CryptContext
) -> User:
    hashed_password = context.hash(password)

    user = User(
        name=name,
        hashed_password=hashed_password,
        api_key=API_KEY(),
        privileges=privileges,
        # TODO: Compliance
        compliance=None,
    )

    await user.create()

    return user


async def read(name: str) -> User:
    result = await User.find(User.name == name).first_or_none()

    if result is None:
        raise UserNotFound

    return result


async def read_by_id(id: PydanticObjectId) -> User:
    result = await User.get(id)

    if result is None:
        raise UserNotFound

    return result


async def update(
    name: str,
    context: CryptContext,
    password: str | None,
    privileges: list[Privilege] | None,
    refresh_key: bool = False,
) -> User:
    user = await read(name=name)

    if privileges is not None:
        await user.set({User.privileges: privileges})

    if refresh_key:
        await user.set({User.api_key: API_KEY()})

    if password is not None:
        hashed_password = context.hash(password)
        await user.set({User.hashed_password: hashed_password})

    return user


async def delete(name: str):
    user = await read(name=name)
    await user.delete()

    return


### --- Security --- ###


async def user_from_api_key(api_key: str) -> User:
    result = await User.find(User.api_key == api_key).first_or_none()

    if result is None:
        raise UserNotFound

    return result


async def read_with_password_verification(
    name: str, password: str, context: CryptContext
) -> User:
    user = await read(name=name)

    if context.verify(password, user.hashed_password):
        return user
    else:
        raise UserNotFound
