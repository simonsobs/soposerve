"""
Tests for just the product service.
"""

import io

import pytest
import pytest_asyncio
import requests

from soposerve.service import product


@pytest_asyncio.fixture(scope="session")
async def created_full_product(database, storage, created_user):
    PRODUCT_NAME = "My Favourite Product"
    PRODUCT_DESCRIPTION = "The best product ever."
    FILE_CONTENTS = b"0x0" * 1024
    SOURCES = [
        product.PreUploadFile(
            name=f"test_{x}.txt",
            size=1024,
            checksum="eh_whatever"
        ) for x in range(4)
    ]

    data, file_puts = await product.create(
        name=PRODUCT_NAME,
        description=PRODUCT_DESCRIPTION,
        sources=SOURCES,
        user=created_user,
        storage=storage
    )

    with io.BytesIO(FILE_CONTENTS) as f:
        for put in file_puts.values():
            requests.put(put, f)

    yield data

    await product.delete(
        name=data.name,
        storage=storage,
        data=True
    )

@pytest.mark.asyncio(scope="session")
async def test_get_existing_file(created_full_product, database):
    selected_product = await product.read(
        name=created_full_product.name
    )

    assert selected_product.name == created_full_product.name
    assert selected_product.description == created_full_product.description


@pytest.mark.asyncio(scope="session")
async def test_get_missing_file(database):
    with pytest.raises(product.ProductNotFound):
        await product.read(name="Missing Product")
