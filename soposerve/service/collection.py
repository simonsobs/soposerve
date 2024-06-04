"""
Service layer for collections.

Note that adding to and removing from collections is provided as part of
the product service.
"""

from soposerve.database import Collection


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


async def read(
    name: str,
):
    collection = await Collection.find(
        Collection.name == name, fetch_links=True
    ).first_or_none()

    if collection is None:
        raise CollectionNotFound

    return collection


async def update(
    name: str,
    description: str | None,
):
    collection = await read(name=name)

    if description is not None:
        await collection.set({Collection.description: description})

    return collection


async def delete(
    name: str,
):
    collection = await read(name=name)

    await collection.delete()

    return
