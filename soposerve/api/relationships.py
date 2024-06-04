"""
API endpoints for relationships between products and collections.
"""

from fastapi import APIRouter, HTTPException, Request, status

from soposerve.api.models.relationships import (
    CreateCollectionRequest,
    ReadCollectionProductResponse,
    ReadCollectionResponse,
)
from soposerve.service import collection, product

relationship_router = APIRouter(prefix="/relationships")

@relationship_router.put("/collection/create/{name}")
async def create_collection(
    name: str,
    model: CreateCollectionRequest,
) -> None:
    # TODO: What to do if collection exists?
    await collection.create(name=name, description=model.description)

@relationship_router.get("/collection/read/{name}")
async def read_collection(
    name: str,
    request: Request,
) -> ReadCollectionResponse:
    """
    Read a collection's details.
    """

    try:
        item = await collection.read(name=name)
    except collection.CollectionNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found."
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
        ]
    )

@relationship_router.put("/collection/add/{collection_name}/{product_name}")
async def add_product_to_collection(
    collection_name: str,
    product_name: str,
) -> None:
    try:
        coll = await collection.read(name=collection_name)
    except collection.CollectionNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found."
        )
    
    try:
        await product.add_collection(name=product_name, collection=coll)
    except product.ProductNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found."
        )
    
@relationship_router.delete("/collection/remove/{collection_name}/{product_name}")
async def remove_product_from_collection(
    collection_name: str,
    product_name: str,
) -> None:
    try:
        coll = await collection.read(name=collection_name)
    except collection.CollectionNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found."
        )
    
    try:
        await product.remove_collection(name=product_name, collection=coll)
    except product.ProductNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found."
        )
    
@relationship_router.delete("/collection/delete/{name}")
async def delete_collection(
    name: str,
) -> None:
    try:
        await collection.delete(name=name)
    except collection.CollectionNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found."
        )


@relationship_router.put("/product/add/child/{name}/{child_name}")
async def add_child_product(
    name: str,
    child_name: str,
) -> None:
    try:
        await product.add_relationship(
            source=name,
            destination=child_name,
            type="child",
        )
    except product.ProductNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found."
        )
    
@relationship_router.delete("/product/remove/child/{name}/{child_name}")
async def remove_child_product(
    name: str,
    child_name: str,
) -> None:
    try:
        await product.remove_relationship(
            source=name,
            destination=child_name,
            type="child",
        )
    except product.ProductNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found."
        )
    
@relationship_router.put("/product/add/related/{name}/{related_name}")
async def add_related_product(
    name: str,
    related_name: str,
) -> None:
    try:
        await product.add_relationship(
            source=name,
            destination=related_name,
            type="related",
        )
    except product.ProductNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found."
        )

@relationship_router.delete("/product/remove/related/{name}/{related_name}")
async def remove_related_product(
    name: str,
    related_name: str,
) -> None:
    try:
        await product.remove_relationship(
            source=name,
            destination=related_name,
            type="related",
        )
    except product.ProductNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found."
        )