"""
Tests for just the product service.
"""

import pytest

from soposerve.service import product, users


@pytest.mark.asyncio(scope="session")
async def test_get_existing_file(created_full_product, database):
    selected_product = await product.read(
        name=created_full_product.name
    )

    assert selected_product.name == created_full_product.name
    assert selected_product.description == created_full_product.description


@pytest.mark.asyncio(scope="session")
async def test_get_missing_file(database):
    with pytest.raises(product.ProductNotFound):
        await product.read(name="Missing Product")


@pytest.mark.asyncio(scope="session")
async def test_add_to_collection(created_collection, created_full_product, database):
    await product.add_collection(
        name=created_full_product.name,
        collection=created_collection,
    )

    selected_product = await product.read(
        name=created_full_product.name
    )

    assert created_collection.name in [c.name for c in selected_product.collections]

    await product.remove_collection(
        name=created_full_product.name,
        collection=created_collection,
    )

    selected_product = await product.read(
        name=created_full_product.name
    )

    assert created_collection.name not in [c.name for c in selected_product.collections]


@pytest.mark.asyncio(scope="session")
async def test_update(created_full_product, database):
    new_user = await users.create(
        name="new_user",
        privileges=[users.Privilege.LIST]
    )

    updated_product = await product.update(
        name=created_full_product.name,
        description="New description",
        owner=new_user,
    )

    assert updated_product.name == created_full_product.name
    assert updated_product.description == "New description"
    assert updated_product.owner.name == new_user.name

    updated_product = await product.update(
        name=created_full_product.name,
        owner=created_full_product.owner,
        description=created_full_product.description,
    )

    assert updated_product.name == created_full_product.name
    assert updated_product.description == created_full_product.description
    assert updated_product.owner.name == created_full_product.owner.name

    await users.delete(new_user.name)