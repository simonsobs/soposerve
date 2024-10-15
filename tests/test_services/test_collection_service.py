"""
Tests for the collection service.
"""

import pytest

from soposerve.service import collection


@pytest.mark.asyncio(scope="session")
async def test_update(created_collection):
    updated = await collection.update(
        name=created_collection.name,
        description="New description",
    )

    assert updated.name == created_collection.name
    assert updated.description == "New description"


@pytest.mark.asyncio(scope="session")
async def test_search(created_collection):
    read = (await collection.search_by_name(name=created_collection.name))[0]

    assert read.name == created_collection.name


@pytest.mark.asyncio(scope="session")
async def test_update_missing():
    with pytest.raises(collection.CollectionNotFound):
        await collection.update(
            name="Missing Collection",
            description="New description",
        )
