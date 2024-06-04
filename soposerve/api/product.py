"""
Routes for the product service.
"""

from fastapi import APIRouter, HTTPException, Request, status

from soposerve.api.models.product import (
    CreateProductRequest,
    CreateProductResponse,
    ReadProductResponse,
    UpdateProductRequest,
)
from soposerve.service import product, users

product_router = APIRouter(prefix="/product")

DEFAULT_USER_USER_NAME = "default_user"

@product_router.put("/create/{name}")
async def create_product(
    name: str,
    request: Request,
    model: CreateProductRequest,
) -> CreateProductResponse:
    """
    Create a new product, returning the pre-signed URLs for the sources.
    """

    # TODO: Authentication
    try:
        user = await users.read(name=DEFAULT_USER_USER_NAME)
    # Uncoverable until we have variable users. TODO: Authentication
    except users.UserNotFound: # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Default user not found."
        )

    try:
        item = await product.read(name=name)

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product already exists."
        )
    except product.ProductNotFound:
        item, presigned = await product.create(
            name=name,
            description=model.description,
            metadata=model.metadata,
            sources=model.sources,
            # TODO: Authentication
            user=user,
            storage=request.app.storage,
        )

    return CreateProductResponse(
        upload_urls=presigned
    )


@product_router.get("/read/{name}")
async def read_product(
    name: str,
    request: Request,
) -> ReadProductResponse:
    """
    Read a product's details.
    """

    try:
        item = await product.read(name=name)
    except product.ProductNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found."
        )

    sources = await product.presign_read(product=item, storage=request.app.storage)

    return ReadProductResponse(
        name=item.name,
        description=item.description,
        sources=sources,
        owner=item.owner.name,
        collections=item.collections,
    )


@product_router.post("/update/{name}")
async def update_product(
    name: str,
    model: UpdateProductRequest
) -> None:
    """
    Update a product's details.
    """

    # TODO: Authentication
    if model.owner is not None:
        try:
            user = await users.read(name=model.owner)
        # Uncoverable until we have variable users. TODO: Authentication
        except users.UserNotFound: # pragma: no cover
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="User not found."
            )
    else:
        user = None
    
    await product.update(
        name=name,
        description=model.description,
        owner=user,
    )


@product_router.post("/confirm/{name}")
async def confirm_product(
    name: str,
    request: Request
) -> None:
    """
    Confirm a product's sources.
    """

    try:
        success = await product.confirm(
            name=name,
            storage=request.app.storage,
        )
    except product.ProductNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found."
        )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail="Not all sources were present."
        )
    

@product_router.delete("/delete/{name}")
async def delete_product(
    name: str,
    request: Request ,
    data: bool = False,
) -> None:
    """
    Delete a product.
    """

    await product.delete(name=name, storage=request.app.storage, data=data)
