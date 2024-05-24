"""
The storage access layer for SOPO. Assumes that you have an S3-compatible backend,
and uses the MinIO tools.
"""

import datetime

from minio import Minio
from pydantic import BaseModel, ConfigDict


class Storage(BaseModel):
    url: str
    access_key: str
    secret_key: str

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
    
    def object_name(
        self, filename: str, uploader: str, uuid: str
    ) -> str:
        return f"{uploader}/{uuid}/{filename}"
    
    def bucket(
        self, name: str
    ):
        if not self.client.bucket_exists(name):
            self.client.make_bucket(name)

        return

    def put(self, name: str, uploader: str, uuid: str, bucket: str) -> str:
        """
        Returns a specific URL for HTTP PUT requests.
        """

        self.bucket(name=bucket)

        return self.client.presigned_put_object(
            bucket_name=bucket,
            object_name=self.object_name(
                filename=name,
                uploader=uploader,
                uuid=uuid,
            ),
            expires=self.expires
        )

    def get(self, name: str, uploader: str, uuid: str, bucket: str) -> str:
        """
        Returns a specific URL for HTTP GET requests.
        """

        self.bucket(name=bucket)

        return self.client.presigned_get_object(
            bucket_name=bucket,
            object_name=self.object_name(
                filename=name,
                uploader=uploader,
                uuid=uuid,
            ),
            expires=self.expires
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
            )
        )
