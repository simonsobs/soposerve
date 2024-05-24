"""
Service for products.
"""

from pydantic import BaseModel

from soposerve.database import Collection, Product, User
from soposerve.service import storage as storage_service
from soposerve.storage import Storage


class ProductNotFound(Exception):
    pass


class PreUploadFile(BaseModel):
    name: str
    size: int
    checksum: str


async def create(
    name: str,
    description: str,
    sources: list[PreUploadFile],
    user: User,
    storage: Storage,
) -> tuple[Product, list[dict[str, str]]]:
    presigned = {}
    pre_upload_sources = []

    for source in sources:
        pre_upload_source, presigned_url = await storage_service.create(
            name=source.name,
            uploader=user.name,
            size=source.size,
            checksum=source.checksum,
            storage=storage,
        )

        presigned[source.name] = presigned_url
        pre_upload_sources.append(pre_upload_source)

    product = Product(
        name=name,
        description=description,
        owner=user,
        sources=pre_upload_sources,
        # TODO: Consider allowing collections pre-upload,
        # but for now they must be added _after_.
        collections=[],
    )

    await product.create()

    return product, presigned


async def read(name: str) -> Product:
    potential = await Product.find(
        Product.name == name, fetch_links=True, nesting_depth=2
    ).first_or_none()

    if potential is None:
        raise ProductNotFound

    return potential


async def update(
    name: str,
    description: str | None,
    owner: User | None,
) -> Product:
    product = await read(name=name)

    if description is not None:
        await product.set({Product.description: description})

    if owner is not None:
        await product.set({Product.owner: owner})

    return product


async def add_collection(name: str, collection: Collection) -> Product:
    product = await read(name=name)

    await product.set({Product.collections: product.collections + [collection]})

    return product


async def remove_collection(name: str, collection: Collection) -> Product:
    product = await read(name=name)

    await product.set(
        {Product.collections: [c for c in product.collections if c != collection]}
    )

    return product


async def delete(name: str, storage: Storage, data: bool = False):
    product = await read(name=name)

    if data:
        for file in product.sources:
            await storage_service.delete(file=file, storage=storage)

    await product.delete()

    return
