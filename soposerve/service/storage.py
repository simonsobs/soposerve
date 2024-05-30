"""
Service drivers for interacting with the storage layer.
"""

import os
import uuid

from asyncer import asyncify

from soposerve.database import File
from soposerve.storage import Storage


# TODO: Settings
def UUID():
    return str(uuid.uuid4())


GLOBAL_BUCKET_NAME = "global"


async def create(
    name: str,
    uploader: str,
    size: int,
    checksum: str,
    storage: Storage,
) -> tuple[File, str]:
    file = File(
        # Strip any paths that were passed to us through
        # the layers, just in case.
        name=os.path.basename(name),
        uploader=uploader,
        uuid=UUID(),
        bucket=GLOBAL_BUCKET_NAME,
        size=size,
        checksum=checksum,
    )

    put = await asyncify(storage.put)(
        name=file.name, uploader=file.uploader, uuid=file.uuid, bucket=file.bucket
    )

    return file, put

async def confirm(
    file: File,
    storage: Storage
) -> bool:
    return await asyncify(storage.confirm)(
        name=file.name, uploader=file.uploader, uuid=file.uuid, bucket=file.bucket
    )

async def read(
    file: File,
    storage: Storage,
) -> str:
    return await asyncify(storage.get)(
        name=file.name, uploader=file.uploader, uuid=file.uuid, bucket=file.bucket
    )


async def delete(
    file: File,
    storage: Storage,
):
    await asyncify(storage.delete)(
        name=file.name, uploader=file.uploader, uuid=file.uuid, bucket=file.bucket
    )
    return
