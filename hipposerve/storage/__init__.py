"""
The storage access layer for hippo. Assumes that you have an S3-compatible backend,
and uses the MinIO tools.
"""

import datetime
import os

from minio import Minio
from minio.error import S3Error
from pydantic import BaseModel, ConfigDict


def replace_host(url: str, old: str, new: str | None, upgrade: bool) -> str:
    """
    Replaces the host in a URL.
    """

    if new is not None:
        url = url.replace(old, new)

    if upgrade:
        url = url.replace("http://", "https://")

    return url


class Storage(BaseModel):
    url: str
    access_key: str
    secret_key: str
    presign_url: str | None = None
    upgrade_presign_url_to_https: bool = False

    client: Minio | None = None
    expires: datetime.timedelta = datetime.timedelta(days=1)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def model_post_init(self, __context):
        self.client = Minio(
            self.url,
            access_key=self.access_key,
            secret_key=self.secret_key,
            # TODO: Come back and make these secure..?
            secure=False,
            cert_check=False,
        )

    def object_name(self, filename: str, uploader: str, uuid: str) -> str:
        # Filename may contain some kind of path, and this
        # breaks the download side of things, but for some
        # reason this is a valid object name for uploads?
        return f"{uploader}/{uuid}/{os.path.basename(filename)}"

    def bucket(self, name: str):
        if not self.client.bucket_exists(name):
            self.client.make_bucket(name)

        return

    def put(self, name: str, uploader: str, uuid: str, bucket: str) -> str:
        """
        Returns a specific URL for HTTP PUT requests.
        """

        self.bucket(name=bucket)

        base_url = self.client.presigned_put_object(
            bucket_name=bucket,
            object_name=self.object_name(
                filename=name,
                uploader=uploader,
                uuid=uuid,
            ),
            expires=self.expires,
        )

        return replace_host(
            base_url,
            old=self.url,
            new=self.presign_url,
            upgrade=self.upgrade_presign_url_to_https,
        )

    def confirm(self, name: str, uploader: str, uuid: str, bucket: str) -> bool:
        """
        Checks whether an object exists.
        """

        self.bucket(name=bucket)

        try:
            self.client.get_object_tags(
                bucket_name=bucket,
                object_name=self.object_name(
                    filename=name,
                    uploader=uploader,
                    uuid=uuid,
                ),
            )

            return True
        except S3Error:
            return False

    def get(self, name: str, uploader: str, uuid: str, bucket: str) -> str:
        """
        Returns a specific URL for HTTP GET requests.
        """

        self.bucket(name=bucket)

        base_url = self.client.presigned_get_object(
            bucket_name=bucket,
            object_name=self.object_name(
                filename=name,
                uploader=uploader,
                uuid=uuid,
            ),
            expires=self.expires,
        )

        return replace_host(
            base_url,
            old=self.url,
            new=self.presign_url,
            upgrade=self.upgrade_presign_url_to_https,
        )

    def delete(self, name: str, uploader: str, uuid: str, bucket: str) -> str:
        """
        Deletes an object from the bucket.
        """

        self.client.remove_object(
            bucket_name=bucket,
            object_name=self.object_name(
                filename=name,
                uploader=uploader,
                uuid=uuid,
            ),
        )
