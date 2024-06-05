"""
Tests for the relationship API endpoints, creating, adding to, and deleting collections,
parent/child relationships, and side-by-side relationships.
"""

import pytest_asyncio
from fastapi.testclient import TestClient


@pytest_asyncio.fixture(scope="function")
def test_api_products_for_use(test_api_client: TestClient, test_api_user: str):
    # Creates four separate metadata-only products for testing
    # the collections API with. Also creates a collection to use
    # and destroys it after the test.
    collection_name = "Test Collection"
    response = test_api_client.put(
        f"/relationships/collection/{collection_name}",
        json={"description": "test_description"},
    )

    product_names = [f"Product {x}" for x in range(4)]

    for name in product_names:
        response = test_api_client.put(
            f"/product/{name}",
            json={
                "description": "test_description",
                "metadata": {"metadata_type": "simple"},
                "sources": [],
            },
        )
        assert response.status_code == 200

        response = test_api_client.put(
            f"/relationships/collection/{collection_name}/{name}",
        )
        assert response.status_code == 200

    yield collection_name, product_names

    for name in product_names:
        response = test_api_client.delete(f"/product/{name}", params={"data": True})
        assert response.status_code == 200

    response = test_api_client.delete(f"/relationships/collection/{collection_name}")
    assert response.status_code == 200


def test_read_collection(
    test_api_client: TestClient, test_api_products_for_use: tuple[str, list[str]]
):
    collection_name, product_names = test_api_products_for_use

    response = test_api_client.get(f"/relationships/collection/{collection_name}")
    assert response.status_code == 200

    assert response.json()["name"] == collection_name
    assert response.json()["description"] == "test_description"
    assert len(response.json()["products"]) == 4

    for product in response.json()["products"]:
        assert product["name"] in product_names
        assert product["description"] == "test_description"
        assert product["owner"] == "default_user"


def test_create_child_relationship(test_api_client, test_api_products_for_use):
    collection_name, product_names = test_api_products_for_use

    response = test_api_client.put(
        f"/relationships/product/{product_names[0]}/child_of/{product_names[1]}"
    )
    assert response.status_code == 200

    response = test_api_client.get(f"/product/{product_names[0]}")
    assert response.status_code == 200
    assert product_names[1] in response.json()["child_of"]

    response = test_api_client.get(f"/product/{product_names[1]}")
    assert response.status_code == 200
    assert product_names[0] in response.json()["parent_of"]


def test_sideways_relationship(test_api_client, test_api_products_for_use):
    collection_name, product_names = test_api_products_for_use

    response = test_api_client.put(
        f"/relationships/product/{product_names[0]}/related_to/{product_names[2]}"
    )
    assert response.status_code == 200

    response = test_api_client.get(f"/product/{product_names[0]}")
    assert response.status_code == 200
    assert product_names[2] in response.json()["related_to"]

    # Remove it again
    response = test_api_client.delete(
        f"/relationships/product/{product_names[0]}/related_to/{product_names[2]}"
    )


def test_read_non_existent_collection(test_api_client):
    response = test_api_client.get("/relationships/collection/Nonexistent")
    assert response.status_code == 404
    assert response.json()["detail"] == "Collection not found."


def test_add_to_non_existent_collection(test_api_client):
    response = test_api_client.put(
        "/relationships/collection/Nonexistent/doesnt_matter"
    )
    assert response.status_code == 404

    # Also test removal
    response = test_api_client.delete(
        "/relationships/collection/Nonexistent/doesnt_matter"
    )
    assert response.status_code == 404


def test_add_non_existent_product_to_existing_collection(
    test_api_client, test_api_products_for_use
):
    response = test_api_client.put(
        f"/relationships/collection/{test_api_products_for_use[0]}/non_existent"
    )
    assert response.status_code == 404

    # Also test removal
    response = test_api_client.delete(
        f"/relationships/collection/{test_api_products_for_use[0]}/non_existent"
    )
    assert response.status_code == 404


def test_delete_non_existent_collection(test_api_client):
    response = test_api_client.delete("/relationships/collection/Nonexistent")
    assert response.status_code == 404
    assert response.json()["detail"] == "Collection not found."


def test_add_child_product_to_non_existent_parent(test_api_client):
    response = test_api_client.put(
        "/relationships/product/Nonexistent/child_of/doesnt_matter"
    )
    assert response.status_code == 404


def test_remove_child_product_from_non_existent_parent(test_api_client):
    response = test_api_client.delete(
        "/relationships/product/Nonexistent/child_of/doesnt_matter"
    )
    assert response.status_code == 404


def test_add_related_product_to_non_existent_product(test_api_client):
    response = test_api_client.put(
        "/relationships/product/Nonexistent/related_to/doesnt_matter"
    )
    assert response.status_code == 404


def test_remove_related_product_from_non_existent_product(test_api_client):
    response = test_api_client.delete(
        "/relationships/product/Nonexistent/related_to/doesnt_matter"
    )
    assert response.status_code == 404
