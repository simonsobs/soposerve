"""
Routes for the product service.
"""

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, Request, status

from soposerve.api.auth import UserDependency, check_user_for_privilege
from soposerve.api.models.product import (
    CreateProductRequest,
    CreateProductResponse,
    ReadFilesResponse,
    ReadProductResponse,
    UpdateProductRequest,
    UpdateProductResponse,
)
from soposerve.database import Privilege, ProductMetadata
from soposerve.service import product, users

product_router = APIRouter(prefix="/product")

DEFAULT_USER_USER_NAME = "default_user"


@product_router.put("/new")
async def create_product(
    request: Request,
    model: CreateProductRequest,
    calling_user: UserDependency,
) -> CreateProductResponse:
    """
    Create a new product, returning the pre-signed URLs for the sources.
    """

    await check_user_for_privilege(calling_user, Privilege.CREATE_PRODUCT)

    if await product.exists(name=model.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Product already exists"
        )

    item, presigned = await product.create(
        name=model.name,
        description=model.description,
        metadata=model.metadata,
        sources=model.sources,
        user=calling_user,
        storage=request.app.storage,
    )

    return CreateProductResponse(id=item.id, upload_urls=presigned)


@product_router.get("/{id}")
async def read_product(
    id: PydanticObjectId,
    request: Request,
    calling_user: UserDependency,
) -> ReadProductResponse:
    """
    Read a single product's metadata.
    """

    await check_user_for_privilege(calling_user, Privilege.READ_PRODUCT)

    try:
        item = (await product.read_by_id(id)).to_metadata()

        response = ReadProductResponse(
            current_present=item.current,
            current=item.version if item.current else None,
            requested=item.version,
            versions={item.version: item},
        )

        return response
    except product.ProductNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )


@product_router.get("/{id}/tree")
async def read_tree(
    id: PydanticObjectId, request: Request, calling_user: UserDependency
) -> ReadProductResponse:
    """
    Read a single product's entire history.
    """

    await check_user_for_privilege(calling_user, Privilege.READ_PRODUCT)

    try:
        requested_item = await product.read_by_id(id)
        current_item = await product.walk_to_current(requested_item)
        history = await product.walk_history(current_item)

        if not current_item.current:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to find the current version of the requested item",
            )

        response = ReadProductResponse(
            current_present=True,
            current=current_item.version,
            requested=requested_item.version,
            versions=history,
        )

        return response
    except product.ProductNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )


@product_router.get("/{id}/files")
async def read_files(
    id: PydanticObjectId, request: Request, calling_user: UserDependency
) -> ReadFilesResponse:
    await check_user_for_privilege(calling_user, Privilege.READ_PRODUCT)

    try:
        item = await product.read_by_id(id=id)
    except product.ProductNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    files = await product.read_files(product=item, storage=request.app.storage)

    return ReadFilesResponse(
        product=item.to_metadata(),
        files=files,
    )


@product_router.post("/{id}/update")
async def update_product(
    id: PydanticObjectId,
    model: UpdateProductRequest,
    request: Request,
    calling_user: UserDependency,
) -> UpdateProductResponse:
    """
    Update a product's details.
    """

    # For now only privileged users can update products, and they can update everyone's.
    await check_user_for_privilege(calling_user, Privilege.UPDATE_PRODUCT)

    try:
        item = await product.read_by_id(id=id)
    except product.ProductNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    if model.owner is not None:
        try:
            user = await users.read(name=model.owner)
        except users.UserNotFound:
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="User not found."
            )
    else:
        user = None

    new_product, upload_urls = await product.update(
        item,
        name=model.name,
        description=model.description,
        metadata=model.metadata,
        owner=user,
        new_sources=model.new_sources,
        replace_sources=model.replace_sources,
        drop_sources=model.drop_sources,
        storage=request.app.storage,
        level=model.level,
    )

    return UpdateProductResponse(
        version=new_product.version,
        id=new_product.id,
        upload_urls=upload_urls,
    )


@product_router.post("/{id}/confirm")
async def confirm_product(
    id: PydanticObjectId, request: Request, calling_user: UserDependency
) -> None:
    """
    Confirm a product's sources.
    """

    await check_user_for_privilege(calling_user, Privilege.CONFIRM_PRODUCT)

    try:
        item = await product.read_by_id(id=id)
        success = await product.confirm(
            product=item,
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


@product_router.delete("/{id}")
async def delete_product(
    id: PydanticObjectId,
    request: Request,
    calling_user: UserDependency,
    data: bool = False,
) -> None:
    """
    Delete a product.
    """

    await check_user_for_privilege(calling_user, Privilege.DELETE_PRODUCT)

    try:
        item = await product.read_by_id(id=id)
    except product.ProductNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
        )

    await product.delete_one(
        item,
        storage=request.app.storage,
        data=data,
    )


@product_router.delete("/{id}/tree")
async def delete_tree(
    id: PydanticObjectId,
    request: Request,
    calling_user: UserDependency,
    data: bool = False,
) -> None:
    """
    Delete a product.
    """

    await check_user_for_privilege(calling_user, Privilege.DELETE_PRODUCT)

    try:
        item = await product.read_by_id(id=id)
    except product.ProductNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
        )

    await product.delete_tree(
        item,
        storage=request.app.storage,
        data=data,
    )


@product_router.get("/search/{text}")
async def search(
    text: str,
    request: Request,
    calling_user: UserDependency,
) -> list[ProductMetadata]:
    """
    Search for a product by name.
    """

    await check_user_for_privilege(calling_user, Privilege.READ_PRODUCT)

    items = await product.search_by_name(name=text)

    return [item.to_metadata() for item in items]
