"""
Fixtures for the caching client tests.
"""

from pathlib import Path

import pytest

from hippoclient.caching import Cache


@pytest.fixture
def cache(tmp_path):
    cache = Cache(path=Path(tmp_path))

    assert cache.writeable

    yield cache

    for id in cache.complete_id_list:
        cache._remove(id)
