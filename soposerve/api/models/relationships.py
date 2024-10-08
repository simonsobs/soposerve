"""
Models for relationships and collections.
"""

from pydantic import BaseModel
import datetime


class CreateCollectionRequest(BaseModel):
    """
    Request model for creating a collection.
    """

    description: str


class ReadCollectionProductResponse(BaseModel):
    """
    Response model for reading a product in a collection.
    """

    name: str
    description: str
    owner: str
    uploaded: datetime.datetime


class ReadCollectionResponse(BaseModel):
    """
    Response model for reading a collection.
    """

    name: str
    description: str
    products: list[ReadCollectionProductResponse]
