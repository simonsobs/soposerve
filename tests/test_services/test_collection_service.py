"""
Tests for the collection service.
"""

import pytest
from beanie import PydanticObjectId

from hipposerve.service import collection


@pytest.mark.asyncio(loop_scope="session")
async def test_update(created_collection):
    updated = await collection.update(
        id=created_collection.id,
        description="New description",
    )

    assert updated.name == created_collection.name
    assert updated.description == "New description"


@pytest.mark.asyncio(loop_scope="session")
async def test_search(created_collection, created_user):
    read = (
        await collection.search_by_name(name=created_collection.name, user=created_user)
    )[0]

    assert read.name == created_collection.name


@pytest.mark.asyncio(loop_scope="session")
async def test_update_missing():
    with pytest.raises(collection.CollectionNotFound):
        await collection.update(
            id=PydanticObjectId("7" * 24),
            description="New description",
        )
