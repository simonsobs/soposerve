"""
Pydantic models for the product API layer.
"""

from pydantic import BaseModel

from sopometa import ALL_METADATA_TYPE
from soposerve.service.product import PostUploadFile, PreUploadFile


class CreateProductRequest(BaseModel):
    description: str
    metadata: ALL_METADATA_TYPE
    sources: list[PreUploadFile]


class CreateProductResponse(BaseModel):
    upload_urls: dict[str, str]


class ReadProductResponse(BaseModel):
    name: str
    description: str
    sources: list[PostUploadFile]
    owner: str
    parent_of: list[str]
    child_of: list[str]
    related_to: list[str]
    collections: list[str]


class UpdateProductRequest(BaseModel):
    description: str | None = None
    owner: str | None = None
