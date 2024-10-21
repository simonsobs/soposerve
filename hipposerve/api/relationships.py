"""
API endpoints for relationships between products and collections.
"""

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, Request, status

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
) -> str:
    await check_user_for_privilege(calling_user, Privilege.CREATE_COLLECTION)

    # TODO: What to do if collection exists?
    # TODO: Collections should have a 'manager' who can change their properties.
    coll = await collection.create(name=name, description=model.description)

    return str(coll.id)


@relationship_router.get("/collection/{id}")
async def read_collection(
    id: PydanticObjectId,
    request: Request,
    calling_user: UserDependency,
) -> ReadCollectionResponse:
    """
    Read a collection's details.
    """

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

    await check_user_for_privilege(calling_user, Privilege.READ_COLLECTION)

    results = await collection.search_by_name(name=name)

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
    except product.ProductNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
        )


@relationship_router.delete("/collection/{id}")
async def delete_collection(
    id: PydanticObjectId,
    calling_user: UserDependency,
) -> None:
    await check_user_for_privilege(calling_user, Privilege.DELETE_COLLECTION)

    try:
        await collection.delete(id=id)
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
    await check_user_for_privilege(calling_user, Privilege.CREATE_RELATIONSHIP)

    try:
        source = await product.read_by_id(id=parent_id)
        destination = await product.read_by_id(id=child_id)
        await product.add_relationship(
            source=source,
            destination=destination,
            type="child",
        )
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
    await check_user_for_privilege(calling_user, Privilege.DELETE_RELATIONSHIP)

    try:
        source = await product.read_by_id(id=parent_id)
        destination = await product.read_by_id(id=child_id)
        await product.remove_relationship(
            source=source,
            destination=destination,
            type="child",
        )
    except product.ProductNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
        )
