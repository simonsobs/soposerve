"""
Tests the cache functionality.
"""

from pathlib import Path


def test_add_file_to_cache(cache):
    """
    Test adding a file to the cache.
    """
    keys = dict(
        id="123456789012345678901234",
        path="test.txt",
        checksum="12345678901234567890123456789012",
        size=123,
    )

    cache._add(**keys)

    cache._mark_available(keys["id"])

    assert str(cache._get(keys["id"])) == str(cache.path / Path(keys["path"]))

    cache._mark_unavailable(keys["id"])

    cache._remove(keys["id"])


def test_add_real_file_to_cache(cache):
    """
    Test adding a real file to the cache
    """

    path = cache.get(
        id="abcdefghijk",
        path="my/path/to/file.png",
        checksum="not-a-real-checksum",
        size=1234,
        # 2022 wikimedia picture of the year!
        presigned_url="https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Phalacrocorax_carbo%2C_Egretta_garzetta_and_Mareca_strepera_in_Taudha_Lake.jpg/640px-Phalacrocorax_carbo%2C_Egretta_garzetta_and_Mareca_strepera_in_Taudha_Lake.jpg",
    )

    assert path.exists()

    assert str(path) == str(cache.path / Path("my/path/to/file.png"))

    # Now get it back again
    path = cache.get(
        id="abcdefghijk",
        path="my/path/to/file.png",
        checksum="not-a-real-checksum",
        size=1234,
        # Not a real presigned url! It will never be tried if the file is in the cache
        presigned_url="https://example.com/this-will-never-be-reached",
    )
