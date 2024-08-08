"""
Pydantic models for the product API layer.
"""

from pydantic import BaseModel

from sopometa import ALL_METADATA_TYPE
from soposerve.service.product import PostUploadFile, PreUploadFile, ProductMetadata
from soposerve.service.versioning import VersionRevision


class CreateProductRequest(BaseModel):
    name: str
    description: str
    metadata: ALL_METADATA_TYPE
    sources: list[PreUploadFile]


class CreateProductResponse(BaseModel):
    id: str
    upload_urls: dict[str, str]


class ReadProductResponse(BaseModel):
    current_present: bool
    current: str | None
    requested: str
    versions: dict[str, ProductMetadata]

class UpdateProductRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    metadata: ALL_METADATA_TYPE | None
    owner: str | None = None
    new_sources: list[PreUploadFile] = []
    replace_sources: list[PreUploadFile] = []
    drop_sources: list[str] = []
    level: VersionRevision = VersionRevision.MINOR

class UpdateProductResponse(BaseModel):
    version: str
    id: str
    upload_urls: dict[str, str]
