"""
Tests the functions in the user service.
"""

import pytest

from soposerve.service import users


@pytest.mark.asyncio(scope="session")
async def test_read_user(created_user):
    this_user = await users.read(name=created_user.name)
    assert this_user.name == created_user.name

    this_user = await users.read_by_id(id=created_user.id)
    assert this_user.name == created_user.name


@pytest.mark.asyncio(scope="session")
async def test_update_user(created_user):
    this_user = await users.update(
        name=created_user.name,
        privileges=[users.Privilege.DOWNLOAD_PRODUCT],
        refresh_key=True,
    )

    assert this_user.name == created_user.name
    assert this_user.privileges == [users.Privilege.DOWNLOAD_PRODUCT]

    this_user = await users.update(
        name=created_user.name,
        privileges=[users.Privilege.LIST_PRODUCT],
        refresh_key=False,
    )

    assert this_user.name == created_user.name
    assert this_user.privileges == [users.Privilege.LIST_PRODUCT]


@pytest.mark.asyncio(scope="session")
async def test_read_user_not_found():
    with pytest.raises(users.UserNotFound):
        await users.read(name="non_existent_user")

    with pytest.raises(users.UserNotFound):
        await users.read_by_id(id="7" * 24)

    with pytest.raises(users.UserNotFound):
        await users.user_from_api_key(api_key="hahahahaha")
