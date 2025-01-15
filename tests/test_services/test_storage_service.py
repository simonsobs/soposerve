import io

import pytest
import requests

from hipposerve.service import storage as storage_service


@pytest.mark.asyncio(loop_scope="session")
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
        requests.put(put[0], f)

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


@pytest.mark.asyncio(loop_scope="session")
async def test_create_storage_item_large(storage, created_user, database):
    file, put = await storage_service.create(
        name="test_file.txt",
        description=None,
        uploader=created_user.name,
        size=92 * 1024 * 1024,
        checksum="FakeChecksum",
        storage=storage,
    )

    await file.save()

    FILE_CONTENT = b""

    for mbyte in range(92):
        FILE_CONTENT += b"1" * 1024 * 1024

    # Upload the file - you must use multipart uploads here now.
    headers = []
    sizes = []
    with io.BytesIO(FILE_CONTENT) as f:
        for part, url in enumerate(put):
            segment = f.read(50 * 1024 * 1024)
            sizes.append(len(segment))
            headers.append(
                requests.put(url, segment).headers,
            )

    # Run the confirmation step
    await storage_service.finalize(
        file=file,
        storage=storage,
        response_headers=headers,
        sizes=sizes,
    )

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
