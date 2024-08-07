"""
Routes for the product service.
"""

from fastapi import APIRouter, HTTPException, Request, status

from soposerve.api.auth import UserDependency, check_user_for_privilege
from soposerve.api.models.product import (
    CreateProductRequest,
    CreateProductResponse,
    ReadProductResponse,
    UpdateProductRequest,
)
from soposerve.database import Privilege
from soposerve.service import product, users

product_router = APIRouter(prefix="/product")

DEFAULT_USER_USER_NAME = "default_user"


@product_router.put("/{name}")
async def create_product(
    name: str,
    request: Request,
    model: CreateProductRequest,
    calling_user: UserDependency,
) -> CreateProductResponse:
    """
    Create a new product, returning the pre-signed URLs for the sources.
    """

    await check_user_for_privilege(calling_user, Privilege.CREATE_PRODUCT)

    try:
        # TODO: This is an insane way to handle this.
        item = await product.read(name=name)

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Product already exists."
        )
    except product.ProductNotFound:
        item, presigned = await product.create(
            name=name,
            description=model.description,
            metadata=model.metadata,
            sources=model.sources,
            version=model.version,
            # TODO: Authentication
            user=calling_user,
            storage=request.app.storage,
        )

    return CreateProductResponse(upload_urls=presigned)


@product_router.get("/{name}")
async def read_product(
    name: str,
    request: Request,
    calling_user: UserDependency,
) -> ReadProductResponse:
    """
    Read a product's details (only latest version)
    """

    await check_user_for_privilege(calling_user, Privilege.READ_PRODUCT)

    try:
        item = await product.read(name=name)
        item_version = item.versions[item.current_version]
    except product.ProductNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
        )

    sources = await product.presign_read(
        product=item, storage=request.app.storage, version=item.current_version
    )

    return ReadProductResponse(
        name=item.name,
        version=item.current_version,
        description=item_version.description,
        sources=sources,
        owner=item.owner.name,
        related_to=[x.name for x in item.related_to],
        child_of=[x.name for x in item.child_of],
        parent_of=[x.name for x in item.parent_of],
        collections=[x.name for x in item.collections],
    )


@product_router.post("/{name}/update")
async def update_product(
    name: str, model: UpdateProductRequest, calling_user: UserDependency
) -> None:
    """
    Update a product's details.
    """

    # For now only privileged users can update products, and they can update everyone's.
    await check_user_for_privilege(calling_user, Privilege.UPDATE_PRODUCT)

    # TODO: Authentication
    if model.owner is not None:
        try:
            user = await users.read(name=model.owner)
        # Uncoverable until we have variable users. TODO: Authentication
        except users.UserNotFound:  # pragma: no cover
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="User not found."
            )
    else:
        user = None

    await product.update(
        name=name,
        version=model.version,
        description=model.description,
        owner=user,
    )


@product_router.post("/{name}/confirm")
async def confirm_product(
    name: str, request: Request, calling_user: UserDependency
) -> None:
    """
    Confirm a product's sources.
    """

    await check_user_for_privilege(calling_user, Privilege.CONFIRM_PRODUCT)

    try:
        success = await product.confirm(
            name=name,
            storage=request.app.storage,
        )
    except product.ProductNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
        )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail="Not all sources were present.",
        )


@product_router.delete("/{name}")
async def delete_product(
    name: str,
    request: Request,
    calling_user: UserDependency,
    data: bool = False,
) -> None:
    """
    Delete a product.
    """

    await check_user_for_privilege(calling_user, Privilege.DELETE_PRODUCT)

    await product.delete(name=name, storage=request.app.storage, data=data)
