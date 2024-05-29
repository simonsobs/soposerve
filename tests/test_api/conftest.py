import os

import pytest_asyncio
from fastapi.testclient import TestClient


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