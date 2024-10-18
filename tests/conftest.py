import pytest
import pytest_asyncio
from testcontainers.minio import MinioContainer
from testcontainers.mongodb import MongoDbContainer

from hipposerve.storage import Storage

### -- Database Fixtures -- ###


@pytest_asyncio.fixture(scope="session")
def database_container():
    kwargs = {
        "username": "root",
        "password": "password",
        "port": 27017,
        "dbname": "hippo_test",
    }

    with MongoDbContainer(**kwargs) as container:
        kwargs["url"] = container.get_connection_url()
        yield kwargs


### -- MinIO storage service fixtures -- ###


@pytest.fixture(scope="session")
def storage_container():
    with MinioContainer() as container:
        yield container.get_config()


@pytest.fixture(scope="session")
def storage(storage_container):
    yield Storage(
        url=storage_container["endpoint"],
        access_key=storage_container["access_key"],
        secret_key=storage_container["secret_key"],
    )
