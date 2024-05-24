"""
Facilities for creating and updating users.
"""
import secrets

from soposerve.database import Privilege, User

# TODO: Settings
API_KEY_BYTES = 256
def API_KEY(): return secrets.token_urlsafe(API_KEY_BYTES)


# TODO: Centralised exceptions?
class UserNotFound(Exception):
    pass

async def create(name: str, privileges: list[Privilege]) -> User:
    user = User(
        name=name,
        api_key=API_KEY(),
        privileges=privileges,
        # TODO: Compliance
        compliance=None
    )

    await user.create()

    return user


async def read(name: str) -> User:
    result = await User.find(User.name == name).first_or_none()

    if result is None:
        raise UserNotFound

    return result


async def update(name: str, privileges: list[Privilege] | None, refresh_key: bool = False) -> User:
    user = await read(name=name)

    if privileges is not None:
        await user.set({User.privileges: privileges})

    if refresh_key:
        await user.set({User.api_key: API_KEY()})

    return user


async def delete(name: str):
    user = await read(name=name)
    await user.delete()

    return



