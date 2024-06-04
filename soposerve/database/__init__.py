"""
The database access layer for SOPO. Uses MongoDB and Beanie.
"""

from datetime import datetime
from enum import Enum

from beanie import BackLink, Document, Indexed, Link
from pydantic import BaseModel, Field

from soposerve.database.metadata import ALL_METADATA_TYPE


class Privilege(Enum):
    LIST = 0
    DOWNLOAD = 1
    UPLOAD = 2


class ComplianceInformation(BaseModel):
    nersc_username: str | None


class User(Document):
    name: str = Indexed(str, unique=True)
    api_key: str
    privileges: list[Privilege]

    compliance: ComplianceInformation | None


class File(Document):
    name: str = Indexed(str, unique=True)
    uploader: str
    uuid: str
    bucket: str
    size: int
    checksum: str


class Product(Document):
    name: str = Indexed(str, unique=True)
    description: str
    uploaded: datetime
    updated: datetime

    metadata: ALL_METADATA_TYPE = Field(..., descriminator="metdata_type")

    owner: Link[User]

    sources: list[File]

    child_of: list[Link["Product"]] = []
    parent_of: list[BackLink["Product"]] = Field(
        json_schema_extra={"original_field": "child_of"}, default=[]
    )
    related_to: list[Link["Product"]] = []
    collections: list[Link["Collection"]] = []


class Collection(Document):
    name: str = Indexed(str, unique=True)
    description: str
    products: list[BackLink[Product]] = Field(
        json_schema_extra={"original_field": "collections"}
    )


BEANIE_MODELS = [User, File, Product, Collection]
