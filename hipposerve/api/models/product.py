"""
Pydantic models for the product API layer.
"""

from beanie import PydanticObjectId
from pydantic import BaseModel

from hippometa import ALL_METADATA_TYPE
from hipposerve.database import Visibility
from hipposerve.service.product import PostUploadFile, PreUploadFile, ProductMetadata
from hipposerve.service.versioning import VersionRevision


class CreateProductRequest(BaseModel):
    name: str
    description: str
    metadata: ALL_METADATA_TYPE
    sources: list[PreUploadFile]
    visibility: Visibility = Visibility.COLLABORATION


class CreateProductResponse(BaseModel):
    id: PydanticObjectId
    upload_urls: dict[str, str]


class ReadProductResponse(BaseModel):
    current_present: bool
    current: str | None
    requested: str
    versions: dict[str, ProductMetadata]


class ReadFilesResponse(BaseModel):
    product: ProductMetadata
    files: list[PostUploadFile]


class UpdateProductRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    metadata: ALL_METADATA_TYPE | None = None
    owner: str | None = None
    new_sources: list[PreUploadFile] = []
    replace_sources: list[PreUploadFile] = []
    drop_sources: list[str] = []
    level: VersionRevision = VersionRevision.MINOR
    visibility: Visibility = Visibility.COLLABORATION


class UpdateProductResponse(BaseModel):
    version: str
    id: PydanticObjectId
    upload_urls: dict[str, str]
