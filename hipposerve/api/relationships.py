"""
API endpoints for relationships between products and collections.
"""

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, Request, status
from loguru import logger

from hipposerve.api.auth import UserDependency, check_user_for_privilege
from hipposerve.api.models.relationships import (
    CreateCollectionRequest,
    ReadCollectionProductResponse,
    ReadCollectionResponse,
)
from hipposerve.database import Privilege
from hipposerve.service import collection, product

relationship_router = APIRouter(prefix="/relationships")


@relationship_router.put("/collection/{name}")
async def create_collection(
    name: str,
    model: CreateCollectionRequest,
    calling_user: UserDependency,
) -> PydanticObjectId:
    """
    Create a new collection with {name}.
    """

    logger.info(f"Request to create collection: {name} from {calling_user.name}")

    await check_user_for_privilege(calling_user, Privilege.CREATE_COLLECTION)

    # TODO: What to do if collection exists?
    # TODO: Collections should have a 'manager' who can change their properties.
    coll = await collection.create(name=name, description=model.description)

    logger.info(f"Collection {coll.id} ({name}) created for {calling_user.name}")

    return coll.id


@relationship_router.get("/collection/{id}")
async def read_collection(
    id: PydanticObjectId,
    request: Request,
    calling_user: UserDependency,
) -> ReadCollectionResponse:
    """
    Read a collection's details.
    """

    logger.info(f"Request to read collection: {id} from {calling_user.name}")

    await check_user_for_privilege(calling_user, Privilege.READ_COLLECTION)

    try:
        item = await collection.read(id=id)
    except collection.CollectionNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found."
        )

    return ReadCollectionResponse(
        id=item.id,
        name=item.name,
        description=item.description,
        products=[
            ReadCollectionProductResponse(
                id=x.id,
                name=x.name,
                version=x.version,
                description=x.description,
                owner=x.owner.name,
                uploaded=x.uploaded,
                metadata=x.metadata,
            )
            for x in item.products
        ],
    )


@relationship_router.get("/collection/search/{name}")
async def search_collection(
    name: str,
    request: Request,
    calling_user: UserDependency,
) -> list[ReadCollectionResponse]:
    """
    Search for collections by name. Products are not returned; these should be
    fetched separately through the read_collection endpoint.
    """

    logger.info(f"Request to search for collection: {name} from {calling_user.name}")

    await check_user_for_privilege(calling_user, Privilege.READ_COLLECTION)

    results = await collection.search_by_name(name=name)

    logger.info(f"Found {len(results)} collections for {name} from {calling_user.name}")

    return [
        ReadCollectionResponse(
            id=item.id,
            name=item.name,
            description=item.description,
            products=None,
        )
        for item in results
    ]


@relationship_router.put("/collection/{collection_id}/{product_id}")
async def add_product_to_collection(
    collection_id: PydanticObjectId,
    product_id: PydanticObjectId,
    calling_user: UserDependency,
) -> None:
    """
    Add a product to a collection.
    """

    logger.info(
        f"Request to add product {product_id} to collection {collection_id} "
        f"from {calling_user.name}"
    )

    await check_user_for_privilege(calling_user, Privilege.UPDATE_COLLECTION)

    try:
        coll = await collection.read(id=collection_id)
    except collection.CollectionNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found."
        )

    try:
        item = await product.read_by_id(id=product_id)
        await product.add_collection(product=item, collection=coll)
        logger.info(f"Successfully added {item.name} to collection {coll.name}")
    except product.ProductNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
        )


@relationship_router.delete("/collection/{collection_id}/{product_id}")
async def remove_product_from_collection(
    collection_id: PydanticObjectId,
    product_id: PydanticObjectId,
    calling_user: UserDependency,
) -> None:
    """
    Remove a product from a collection.
    """

    logger.info(
        f"Request to remove product {product_id} from collection {collection_id} "
        f"from {calling_user.name}"
    )

    await check_user_for_privilege(calling_user, Privilege.UPDATE_COLLECTION)

    try:
        coll = await collection.read(id=collection_id)
    except collection.CollectionNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found."
        )

    try:
        item = await product.read_by_id(id=product_id)
        await product.remove_collection(product=item, collection=coll)
        logger.info(f"Successfully removed {item.name} from collection {coll.name}")
    except product.ProductNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
        )


@relationship_router.delete("/collection/{id}")
async def delete_collection(
    id: PydanticObjectId,
    calling_user: UserDependency,
) -> None:
    """
    Delete a collection.
    """

    logger.info(f"Request to delete collection: {id} from {calling_user.name}")

    await check_user_for_privilege(calling_user, Privilege.DELETE_COLLECTION)

    try:
        await collection.delete(id=id)
        logger.info(f"Successfully deleted collection {id} from {calling_user.name}")
    except collection.CollectionNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found."
        )


@relationship_router.put("/product/{parent_id}/child_of/{child_id}")
async def add_child_product(
    parent_id: PydanticObjectId,
    child_id: PydanticObjectId,
    calling_user: UserDependency,
) -> None:
    """
    Add a child product to a parent product.
    """

    logger.info(
        f"Request to add product {child_id} as child of {parent_id} "
        f"from {calling_user.name}"
    )

    await check_user_for_privilege(calling_user, Privilege.CREATE_RELATIONSHIP)

    try:
        source = await product.read_by_id(id=parent_id)
        destination = await product.read_by_id(id=child_id)
        await product.add_relationship(
            source=source,
            destination=destination,
            type="child",
        )
        logger.info(f"Successfully added {destination.name} as child of {source.name}")
    except product.ProductNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
        )


@relationship_router.delete("/product/{parent_id}/child_of/{child_id}")
async def remove_child_product(
    parent_id: PydanticObjectId,
    child_id: PydanticObjectId,
    calling_user: UserDependency,
) -> None:
    """
    Remove a parent-child relationship between two products.
    """

    logger.info(
        f"Request to remove product {child_id} as child of {parent_id} "
        f"from {calling_user.name}"
    )

    await check_user_for_privilege(calling_user, Privilege.DELETE_RELATIONSHIP)

    try:
        source = await product.read_by_id(id=parent_id)
        destination = await product.read_by_id(id=child_id)
        await product.remove_relationship(
            source=source,
            destination=destination,
            type="child",
        )
        logger.info(
            f"Successfully removed {destination.name} as child of {source.name}"
        )
    except product.ProductNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
        )
