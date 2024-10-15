"""
Service layer for collections.

Note that adding to and removing from collections is provided as part of
the product service.
"""

from beanie.operators import Text

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


async def read_most_recent(
    fetch_links: bool = False, maximum: int = 16
) -> list[Collection]:
    # TODO: Implement updated time for collections.
    return await Collection.find(fetch_links=fetch_links).to_list(maximum)


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
