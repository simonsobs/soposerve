"""
Individual (fully synchronous) storage tests.
"""

import io

import pytest
import requests


@pytest.fixture(scope="session")
def simple_uploaded_file(storage):
    # Ingest the file into the storage service.
    file_info = {
        "name": "test_file.txt",
        "uploader": "test_uploader",
        "uuid": "1234-1234-1234",
        "bucket": "testbucket",
    }

    put = storage.put(**file_info)

    # Put is a pre-signed URL. We've gotta HTTP upload it.
    with io.BytesIO() as f:
        f.write(b"\x00" * 1234)
        f.seek(0)
        requests.put(put, data=f)

    yield file_info

    # Remove it! Request a deletion.
    storage.delete(**file_info)


def test_simple_uploaded_file(simple_uploaded_file, storage):
    get = storage.get(**simple_uploaded_file)

    # Try to download it.
    response = requests.get(get)
    assert response.status_code == 200

    # Check the contents.
    assert response.content == b"\x00" * 1234


def test_existing_object(simple_uploaded_file, storage):
    assert storage.confirm(**simple_uploaded_file)


def test_non_existing_object(storage):
    assert not storage.confirm(
        name="non_existing_file.txt",
        uploader="test_uploader",
        uuid="1234-1234-1234",
        bucket="testbucket",
    )
