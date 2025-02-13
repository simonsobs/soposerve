"""
Service layer for collections.

Note that adding to and removing from collections is provided as part of
the product service.
"""

import asyncio

from beanie import PydanticObjectId
from beanie.operators import Text

from hipposerve.database import Collection, User
from hipposerve.service.product import check_visibility_access


class CollectionNotFound(Exception):
    pass


async def create(
    name: str,
    description: str,
):
    collection = Collection(
        name=name,
        description=description,
    )

    await collection.insert()

    return collection


async def read(id: PydanticObjectId):
    collection = await Collection.find(
        Collection.id == id, fetch_links=True
    ).first_or_none()
    if collection is None:
        raise CollectionNotFound
    return collection


async def read_most_recent(
    fetch_links: bool = False, maximum: int = 16, user: User | None = None
) -> list[Collection]:
    # TODO: Implement updated time for collections.
    collections = await Collection.find(fetch_links=fetch_links).to_list(maximum)
    filtered_collections_with_visibility = await asyncio.gather(
        *(
            check_collection_visibility(collection_item, user)
            for collection_item in collections
        )
    )
    filtered_collections = [
        collection_item
        for collection_item, visibility in filtered_collections_with_visibility
        if visibility
    ]
    return filtered_collections


async def search_by_name(name: str, fetch_links: bool = True) -> list[Collection]:
    """
    Search for Collections by name using the text index.
    """

    results = (
        await Collection.find(Text(name), fetch_links=fetch_links)  # noqa: E712
        .sort([("score", {"$meta": "textScore"})])
        .to_list()
    )
    return results


async def update(
    id: PydanticObjectId,
    description: str | None,
):
    collection = await read(id=id)

    if description is not None:
        await collection.set({Collection.description: description})

    return collection


async def delete(
    id: PydanticObjectId,
):
    collection = await read(id=id)

    await collection.delete()

    return


async def check_collection_visibility(
    collection_item: Collection, user: User | None = None
) -> bool:
    visibility_checks = await asyncio.gather(
        *(
            check_visibility_access(product_item, user)
            for product_item in collection_item.products
        )
    )
    collection_item.products = [
        product_item
        for product_item, visibility in zip(collection_item.products, visibility_checks)
        if visibility
    ]
    return collection_item, any(visibility_checks)
