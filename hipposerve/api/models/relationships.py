"""
Models for relationships and collections.
"""

import datetime

from beanie import PydanticObjectId
from pydantic import BaseModel

from hippometa import ALL_METADATA_TYPE


class CreateCollectionRequest(BaseModel):
    """
    Request model for creating a collection.
    """

    description: str


class ReadCollectionProductResponse(BaseModel):
    """
    Response model for reading a product in a collection.
    """

    id: PydanticObjectId
    name: str
    description: str
    owner: str
    version: str
    uploaded: datetime.datetime
    metadata: ALL_METADATA_TYPE


class ReadCollectionResponse(BaseModel):
    """
    Response model for reading a collection.
    """

    id: PydanticObjectId
    name: str
    description: str
    products: list[ReadCollectionProductResponse] | None
