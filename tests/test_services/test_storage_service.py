import io

import pytest
import requests

from soposerve.service import storage as storage_service


@pytest.mark.asyncio(scope="session")
async def test_create_storage_item(storage, created_user, database):
    file, put = await storage_service.create(
        name="test_file.txt",
        description=None,
        uploader=created_user.name,
        size=1234,
        checksum="FakeChecksum",
        storage=storage,
    )

    await file.save()

    FILE_CONTENT = b"Hello, World!"

    # Upload the file
    with io.BytesIO(FILE_CONTENT) as f:
        requests.put(put, f)

    # Check we got it by downloading through the service.
    get = await storage_service.read(
        file=file,
        storage=storage,
    )

    # Download the file
    response = requests.get(get)

    assert response.content == FILE_CONTENT

    # Kill it with fire
    await storage_service.delete(
        file=file,
        storage=storage,
    )
