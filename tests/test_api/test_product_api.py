"""
Tests the product API endpoints.
"""

import pytest_asyncio
import requests
from fastapi.testclient import TestClient

from soposerve.api.models.product import (
    CreateProductResponse,
    PreUploadFile,
    ReadProductResponse,
)


@pytest_asyncio.fixture(scope="function")
def test_api_product(test_api_client: TestClient, test_api_user: str):
    TEST_PRODUCT_NAME = "test_product"
    TEST_PRODUCT_DESCRIPTION = "test_description"
    TEST_PRODUCT_SOURCES = [
        PreUploadFile(name="test_file", size=100, checksum="test_checksum").model_dump()
    ]

    response = test_api_client.put(
        f"/product/{TEST_PRODUCT_NAME}",
        json={
            "description": TEST_PRODUCT_DESCRIPTION,
            "metadata": {"metadata_type": "simple"},
            "sources": TEST_PRODUCT_SOURCES,
        },
    )

    assert response.status_code == 200
    validated = CreateProductResponse.model_validate(response.json())

    # Now we have to actually upload the files.
    for source in TEST_PRODUCT_SOURCES:
        response = requests.put(
            validated.upload_urls[source["name"]], data=b"test_data"
        )

        assert response.status_code == 200

    # And check...
    response = test_api_client.post(f"/product/{TEST_PRODUCT_NAME}/confirm")

    assert response.status_code == 200

    yield TEST_PRODUCT_NAME

    response = test_api_client.delete(
        f"/product/{TEST_PRODUCT_NAME}", params={"data": True}
    )
    assert response.status_code == 200


def test_upload_product_again(test_api_client: TestClient, test_api_product: str):
    response = test_api_client.put(
        f"/product/{test_api_product}",
        json={
            "description": "test_description",
            "metadata": {"metadata_type": "simple"},
            "sources": [
                PreUploadFile(
                    name="test_file", size=100, checksum="test_checksum"
                ).model_dump()
            ],
            "version": "1.0.0",
        },
    )

    assert response.status_code == 409


def test_read_product(
    test_api_client: TestClient,
    test_api_product: str,
    test_api_user: str,
):
    response = test_api_client.get(f"/product/{test_api_product}")

    assert response.status_code == 200
    validated = ReadProductResponse.model_validate(response.json())

    assert validated.name == test_api_product

    # Use the pre-signed url to check that the file data is b"test_data", as expected.
    # TODO: Right now we actually don't furnish a pre-signed URL! We need to add that, maybe to the API?
    for source in validated.sources:
        response = requests.get(source.url)

        assert response.status_code == 200
        assert response.content == b"test_data"


def test_read_product_not_found(
    test_api_client: TestClient,
):
    response = test_api_client.get("/product/not_a_real_product")

    assert response.status_code == 404


def test_update_product(test_api_client: TestClient, test_api_product: str):
    response = test_api_client.post(
        f"/product/{test_api_product}/update",
        json={
            "description": "new_description",
            "metadata": {"metadata_type": "simple"},
            "owner": "default_user",
            "version": "1.1.0",
        },
    )

    assert response.status_code == 200

    response = test_api_client.get(f"/product/{test_api_product}")
    validated = ReadProductResponse.model_validate(response.json())

    assert validated.description == "new_description"
    assert validated.owner == "default_user"


def test_update_product_invalid_owner(
    test_api_client: TestClient, test_api_product: str
):
    response = test_api_client.post(
        f"/product/{test_api_product}/update",
        json={
            "description": "new_description",
            "owner": "not_exist_user",
            "version": "1.1.0",
        },
    )

    assert response.status_code == 406


def test_update_product_no_owner_change(
    test_api_client: TestClient, test_api_product: str
):
    response = test_api_client.post(
        f"/product/{test_api_product}/update",
        json={"description": "New description, again!", "version": "2.0.0"},
    )

    assert response.status_code == 200

    response = test_api_client.get(f"/product/{test_api_product}")
    validated = ReadProductResponse.model_validate(response.json())

    assert validated.description == "New description, again!"


def test_confirm_product(test_api_client: TestClient, test_api_product: str):
    response = test_api_client.post(f"/product/{test_api_product}/confirm")

    assert response.status_code == 200
    assert response.json() is None

    response = test_api_client.post(f"/product/not_{test_api_product}/confirm")
    assert response.status_code == 404


def test_confirm_product_product_not_existing(test_api_client):
    TEST_PRODUCT_NAME = "product_we_never_uploaded"
    response = test_api_client.put(
        f"/product/{TEST_PRODUCT_NAME}",
        json={
            "description": "A test product that was never uploaded.",
            "metadata": None,
            "sources": [
                PreUploadFile(
                    name="test_file", size=100, checksum="test_checksum"
                ).model_dump()
            ],
        },
    )

    assert response.status_code == 200
    _ = CreateProductResponse.model_validate(response.json())

    # And check...
    response = test_api_client.post(f"/product/{TEST_PRODUCT_NAME}/confirm")

    assert response.status_code == 424
