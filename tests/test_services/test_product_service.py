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
async def test_presign_read(created_full_product, storage):
    sources = await product.presign_read(created_full_product, storage)

    for source in sources:
        assert source.url is not None

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

    before_update_time = updated_product.updated

    updated_product = await product.update(
        name=created_full_product.name,
        owner=created_full_product.owner,
        description=created_full_product.description,
    )

    assert updated_product.name == created_full_product.name
    assert updated_product.description == created_full_product.description
    assert updated_product.owner.name == created_full_product.owner.name
    assert updated_product.updated > before_update_time

    await users.delete(new_user.name)

@pytest.mark.asyncio(scope="session")
async def test_read_most_recent_products(database, created_user, storage):
    # Insert a bunch of products.
    for i in range(20):
        await product.create(
            name=f"product_{i}",
            description=f"description_{i}",
            sources=[],
            user=created_user,
            storage=storage,
        )

    products = await product.read_most_recent(
        fetch_links=False, maximum=8
    )
    
    assert len(products) == 8

    # Clean up.
    for i in range(20):
        await product.delete(name=f"product_{i}", data=True, storage=storage)
