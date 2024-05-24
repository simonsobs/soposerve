import pytest
from testcontainers.minio import MinioContainer

from soposerve.storage import Storage


@pytest.fixture(scope="session")
def storage_container():
    with MinioContainer() as container:
        yield container.get_config()

@pytest.fixture(scope="session")
def storage(storage_container):
    yield Storage(
        url=storage_container["endpoint"],
        access_key=storage_container["access_key"],
        secret_key=storage_container["secret_key"]
    )
