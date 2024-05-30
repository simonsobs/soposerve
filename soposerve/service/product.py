"""
Service for products.
"""

import datetime

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

class PostUploadFile(BaseModel):
    name: str
    size: int
    checksum: str
    url: str

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
        updated=datetime.datetime.now(datetime.timezone.utc),
        owner=user,
        sources=pre_upload_sources,
        # TODO: Consider allowing collections pre-upload,
        # but for now they must be added _after_.
        collections=[],
    )

    await product.create()

    return product, presigned

async def confirm(
    name: str,
    storage: Storage
) -> bool:
    product = await read(name)

    for file in product.sources:
        if not await storage_service.confirm(file=file, storage=storage):
            return False
        
    return True


async def read(name: str) -> Product:
    potential = await Product.find(
        Product.name == name, fetch_links=True, nesting_depth=2
    ).first_or_none()

    if potential is None:
        raise ProductNotFound
    
    return potential


async def presign_read(product: Product, storage: Storage) -> list[PostUploadFile]:
    """
    Given a product, generates pre-signed URLs for all of its sources.
    """
    files = [
        PostUploadFile(
            name=source.name,
            size=source.size,
            checksum=source.checksum,
            url=storage.get(
                name=source.name,
                uploader=source.uploader,
                uuid=source.uuid,
                bucket=source.bucket
            )
         ) for source in product.sources
    ]

    return files


async def read_most_recent(fetch_links: bool = False, maximum: int = 16) -> list[Product]:
    return await Product.find(
        fetch_links=fetch_links
    ).sort(-Product.updated).to_list(maximum)


async def update(
    name: str,
    description: str | None,
    owner: User | None,
) -> Product:
    product = await read(name=name)

    if description is not None:
        await product.set(
            {Product.description: description, Product.updated: datetime.datetime.now(datetime.timezone.utc)})

    if owner is not None:
        await product.set({Product.owner: owner, Product.updated: datetime.datetime.now(datetime.timezone.utc)})

    return product


async def add_collection(name: str, collection: Collection) -> Product:
    product = await read(name=name)

    product.collections = product.collections + [collection]

    await product.save()

    return product


async def remove_collection(name: str, collection: Collection) -> Product:
    product = await read(name=name)

    product.collections = [c for c in product.collections if c.name != collection.name]

    await product.save()

    return product


async def delete(name: str, storage: Storage, data: bool = False):
    product = await read(name=name)

    if data:
        for file in product.sources:
            await storage_service.delete(file=file, storage=storage)

    await product.delete()

    return
