import os

import pytest_asyncio
from fastapi.testclient import TestClient

from soposerve.api.models.users import CreateUserResponse
from soposerve.database import Privilege

### -- Service Mock Fixtures -- ###


@pytest_asyncio.fixture(scope="session")
def test_api_server(database_container, storage_container):
    settings = {
        "mongo_uri": database_container["url"],
        "minio_url": storage_container["endpoint"],
        "minio_access": storage_container["access_key"],
        "minio_secret": storage_container["secret_key"],
        "title": "Test API",
        "description": "Test API Description",
        "debug": "yes",
        "add_cors": "yes",
    }
    os.environ.update(settings)

    from soposerve.api.app import app

    yield app


@pytest_asyncio.fixture(scope="session")
def test_api_client(test_api_server):
    with TestClient(test_api_server) as client:
        yield client


### -- User Fixtures -- ###


@pytest_asyncio.fixture(scope="module")
def test_api_user(test_api_client: TestClient):
    TEST_USER_NAME = "default_user"
    TEST_USER_PRIVALEGES = [Privilege.DOWNLOAD.value, Privilege.LIST.value]

    response = test_api_client.put(
        f"/users/{TEST_USER_NAME}", json={"privileges": TEST_USER_PRIVALEGES}
    )

    assert response.status_code == 200
    _ = CreateUserResponse.model_validate(response.json())

    yield TEST_USER_NAME

    response = test_api_client.delete(f"/users/{TEST_USER_NAME}")
    assert response.status_code == 200
