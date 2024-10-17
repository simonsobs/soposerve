"""
The caching layer for sources used by the SOPO client.

A cache is:

a) A directory on your filesystem
b) A set of files in that directory
c) A SQLite database that stores metadata about the files
   that are being cached.

Because marshalling is so simple here we do not use
SQLAlchemy or any other ORM. We just use the built-in
Python sqlite3 module.
"""

import os
import sqlite3
from pathlib import Path

import httpx
from pydantic import BaseModel


class CacheNotWriteableError(Exception):
    """
    Raised when the cache is not writeable.
    """

    def __init__(self):
        super().__init__("The cache is not writeable.")


class Cache(BaseModel):
    """
    A cache for sources used by the SOPO client. All sources are labelled by their
    unique ID, given by the main mongodb database.

    The general execution flow when using a (set of) cache(s) is:

    1. Check if the file is in the cache with ``available``. If it is, you will be
       immediately given the on-disk path to the file. If not, we will raise a
       FileNotFoundError.
    2. Check the other caches if it is not available.
    3. Attain a pre-signed URL for your source.
    4. Fetch the source from the pre-signed URL with your preferred cache with ``get``.
       This will return you an on-disk path to the downloaded source within your cache
       area. You can check which caches are writeable with ``writeable``.

    So for a list of caches, you would do something like:

    .. code-block::python

        MY_FILE_ID = "123456789012345678901234"
        path: Path | None = None

        for cache in caches:
            try:
                path = cache.available(MY_FILE_ID)
                break
            except FileNotFoundError:
                continue

        if path is None:
            for cache in filter(lambda c: c.writeable, caches):
                try:
                    path = cache.get(
                        id=MY_FILE_ID,
                        path="path/to/file",
                        checksum="checksum",
                        size=1234,
                        presigned_url="https://example.com/presigned-url",
                    )
                    break
                except {SOME EXCEPTION}:
                    continue

        if path is None:
            raise FileNotFoundError
    """

    path: Path
    database_name: str = "cache.db"

    _database: Path
    _connection: sqlite3.Connection

    def model_post_init(__context):
        __context._database = __context.object.path / __context.object.database_name
        __context.object._connection = __context.object._initialize_database()

    def _initialize_database(self) -> sqlite3.Connection:
        """
        Initialize the cache database.
        """

        if self._database.exists():
            return sqlite3.connect(self._database)
        else:
            # Create the database
            connection = sqlite3.connect(self._database)

            cursor = connection.cursor()
            cursor.execute(
                "CREATE TABLE sources (id PRIMARY KEY, path, checksum, size, available)"
            )
            connection.commit()

            return connection

    @property
    def writeable(self) -> bool:
        """
        Check if the cache is writeable.
        """

        return os.access(self._database, os.W_OK)

    def _add(self, id: str, path: str, checksum: str, size: int):
        """
        Add a source to the cache. Initially marks it as unavailable. This should
        be called _before_ downloading the actual source.
        """

        cursor = self._connection.cursor()
        cursor.execute(
            "INSERT INTO sources (id, path, checksum, size, available) VALUES (?, ?, ?, ?, ?)",
            (id, path, checksum, size, False),
        )
        self._connection.commit()

    def _mark_available(self, id: str):
        """
        Mark a source as available.
        """

        cursor = self._connection.cursor()
        cursor.execute(
            "UPDATE sources SET available = ? WHERE id = ?",
            (True, id),
        )
        self._connection.commit()

    def _mark_unavailable(self, id: str):
        """
        Mark a source as unavailable.
        """

        cursor = self._connection.cursor()
        cursor.execute(
            "UPDATE sources SET available = ? WHERE id = ?",
            (False, id),
        )
        self._connection.commit()

    def _get(self, id: str) -> Path | None:
        """
        Get a source from the cache. Or, if it's not available, return None.
        If it is available we return the absolute path on the system to the file.
        """

        cursor = self._connection.cursor()
        cursor.execute(
            "SELECT path FROM sources WHERE id = ? AND available = ?",
            (id, True),
        )

        result = cursor.fetchone()

        if result is None:
            return None
        else:
            return self.path / Path(result[0])

    def _remove(self, id: str):
        """
        Remove a source from the cache.
        """

        # Get it first, if it's there then we need to delete it.
        path = self._get(id)

        if path is not None:
            path.unlink()

        cursor = self._connection.cursor()
        cursor.execute(
            "DELETE FROM sources WHERE id = ?",
            (id,),
        )
        self._connection.commit()

    def _fetch(
        self, id: str, path: str, checksum: str, size: int, presigned_url: str
    ) -> Path:
        """
        Fetch a source from the presigned URL we are provided, store it in
        the cache, and return the path to the file.

        Parameters
        ----------
        id : str
            The ID of the source
        path : str
            The path to the source
        checksum : str
            The checksum of the source
        size : int
            The size of the source
        presigned_url : str
            The presigned URL to fetch the source from

        Returns
        -------
        Path
            The path to the source in the cache

        Raises
        ------
        CacheNotWriteableError
            If the cache is not writeable
        """

        if not self.writeable:
            raise CacheNotWriteableError

        self._add(id=id, path=path, checksum=checksum, size=size)

        # Download the file
        destination_path = self.path / Path(path)
        destination_path.parent.mkdir(parents=True, exist_ok=True)

        with httpx.stream("GET", presigned_url) as response:
            with open(destination_path, "wb") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)

        self._mark_available(id)

        return destination_path

    def get(
        self, id: str, path: str, checksum: str, size: int, presigned_url: str
    ) -> Path:
        """
        Get a source from the cache. If it's not available, fetch it from the
        presigned URL and store it in the cache.

        Parameters
        ----------
        id : str
            The ID of the source
        path : str
            The path to the source
        checksum : str
            The checksum of the source
        size : int
            The size of the source
        presigned_url : str
            The presigned URL to fetch the source from, if it not in the cache.
        """

        cached = self._get(id)

        if cached is not None:
            return cached
        else:
            return self._fetch(
                id=id,
                path=path,
                checksum=checksum,
                size=size,
                presigned_url=presigned_url,
            )

    def available(self, id: str) -> Path:
        """
        Check if a source is available in the cache with id ``id``.
        If it is, we return the Path. If not, we raise a FileNotFoundError.

        Parameters
        ----------
        id : str
            The ID of the source

        Returns
        -------
        Path
            The path to the source in the cache

        Raises
        ------
        FileNotFoundError
            If the source is not available in the cache
        """

        path = self._get(id)

        if path is None:
            raise FileNotFoundError

        return path

    @property
    def complete_id_list(self) -> list[str]:
        """
        List all the IDs in the cache
        """

        cursor = self._connection.cursor()
        cursor.execute("SELECT id FROM sources")

        return [row[0] for row in cursor.fetchall()]
