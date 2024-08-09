"""
API endpoints for relationships between products and collections.
"""

from fastapi import APIRouter, HTTPException, Request, status

from soposerve.api.auth import UserDependency, check_user_for_privilege
from soposerve.api.models.relationships import (
    CreateCollectionRequest,
    ReadCollectionProductResponse,
    ReadCollectionResponse,
)
from soposerve.database import Privilege
from soposerve.service import collection, product

relationship_router = APIRouter(prefix="/relationships")


@relationship_router.put("/collection/{name}")
async def create_collection(
    name: str,
    model: CreateCollectionRequest,
    calling_user: UserDependency,
) -> None:
    await check_user_for_privilege(calling_user, Privilege.CREATE_COLLECTION)

    # TODO: What to do if collection exists?
    # TODO: Collections should have a 'manager' who can change their properties.
    await collection.create(name=name, description=model.description)


@relationship_router.get("/collection/{name}")
async def read_collection(
    name: str,
    request: Request,
    calling_user: UserDependency,
) -> ReadCollectionResponse:
    """
    Read a collection's details.
    """

    await check_user_for_privilege(calling_user, Privilege.READ_COLLECTION)

    try:
        item = await collection.read(name=name)
    except collection.CollectionNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found."
        )

    return ReadCollectionResponse(
        name=item.name,
        description=item.description,
        products=[
            ReadCollectionProductResponse(
                name=x.name,
                description=x.description,
                owner=x.owner.name,
            )
            for x in item.products
        ],
    )


@relationship_router.put("/collection/{collection_name}/{product_name}")
async def add_product_to_collection(
    collection_name: str,
    product_name: str,
    calling_user: UserDependency,
) -> None:
    await check_user_for_privilege(calling_user, Privilege.UPDATE_COLLECTION)

    try:
        coll = await collection.read(name=collection_name)
    except collection.CollectionNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found."
        )

    try:
        item = await product.read_by_name(name=product_name, version=None)
        await product.add_collection(product=item, collection=coll)
    except product.ProductNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
        )


@relationship_router.delete("/collection/{collection_name}/{product_name}")
async def remove_product_from_collection(
    collection_name: str,
    product_name: str,
    calling_user: UserDependency,
) -> None:
    await check_user_for_privilege(calling_user, Privilege.UPDATE_COLLECTION)

    try:
        coll = await collection.read(name=collection_name)
    except collection.CollectionNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found."
        )

    try:
        item = await product.read_by_name(name=product_name, version=None)
        await product.remove_collection(product=item, collection=coll)
    except product.ProductNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
        )


@relationship_router.delete("/collection/{name}")
async def delete_collection(
    name: str,
    calling_user: UserDependency,
) -> None:
    await check_user_for_privilege(calling_user, Privilege.DELETE_COLLECTION)

    try:
        await collection.delete(name=name)
    except collection.CollectionNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found."
        )


@relationship_router.put("/product/{name}/child_of/{child_name}")
async def add_child_product(
    name: str,
    child_name: str,
    calling_user: UserDependency,
) -> None:
    await check_user_for_privilege(calling_user, Privilege.CREATE_RELATIONSHIP)

    try:
        source = await product.read_by_name(name=name, version=None)
        destination = await product.read_by_name(name=child_name, version=None)
        await product.add_relationship(
            source=source,
            destination=destination,
            type="child",
        )
    except product.ProductNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
        )


@relationship_router.delete("/product/{name}/child_of/{child_name}")
async def remove_child_product(
    name: str,
    child_name: str,
    calling_user: UserDependency,
) -> None:
    await check_user_for_privilege(calling_user, Privilege.DELETE_RELATIONSHIP)

    try:
        source = await product.read_by_name(name=name, version=None)
        destination = await product.read_by_name(name=child_name, version=None)
        await product.remove_relationship(
            source=source,
            destination=destination,
            type="child",
        )
    except product.ProductNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
        )
