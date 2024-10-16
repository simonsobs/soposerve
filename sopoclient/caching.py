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

import sqlite3
from pathlib import Path

import httpx


class Cache:
    """
    A cache for sources used by the SOPO client.
    """

    path: Path
    database: Path

    connection: sqlite3.Connection

    def __init__(self, path: Path, database_name: str = "cache.db"):
        self.path = path
        self.database = path / database_name

        self.connection = self._initialize_database()

    def _initialize_database(self) -> sqlite3.Connection:
        """
        Initialize the cache database.
        """

        if self.database.exists():
            return sqlite3.connect(self.database)
        else:
            # Create the database
            connection = sqlite3.connect(self.database)

            cursor = connection.cursor()
            cursor.execute(
                "CREATE TABLE sources (id PRIMARY KEY, path, checksum, size, available)"
            )
            connection.commit()

            return connection

    def _add(self, id: str, path: str, checksum: str, size: int):
        """
        Add a source to the cache. Initially marks it as unavailable. This should
        be called _before_ downloading the actual source.
        """

        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO sources (id, path, checksum, size, available) VALUES (?, ?, ?, ?, ?)",
            (id, path, checksum, size, False),
        )
        self.connection.commit()

    def _mark_available(self, id: str):
        """
        Mark a source as available.
        """

        cursor = self.connection.cursor()
        cursor.execute(
            "UPDATE sources SET available = ? WHERE id = ?",
            (True, id),
        )
        self.connection.commit()

    def _mark_unavailable(self, id: str):
        """
        Mark a source as unavailable.
        """

        cursor = self.connection.cursor()
        cursor.execute(
            "UPDATE sources SET available = ? WHERE id = ?",
            (False, id),
        )
        self.connection.commit()

    def _get(self, id: str) -> Path | None:
        """
        Get a source from the cache. Or, if it's not available, return None.
        If it is available we return the absolute path on the system to the file.
        """

        cursor = self.connection.cursor()
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

        cursor = self.connection.cursor()
        cursor.execute(
            "DELETE FROM sources WHERE id = ?",
            (id,),
        )
        self.connection.commit()

    def _fetch(
        self, id: str, path: str, checksum: str, size: int, presigned_url: str
    ) -> Path:
        """
        Fetch a source from the presigned URL we are provided, store it in
        the cache, and return the path to the file.
        """

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

    @property
    def complete_id_list(self) -> list[str]:
        """
        List all the IDs in the cache
        """

        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM sources")

        return [row[0] for row in cursor.fetchall()]
