"""
The database access layer for SOPO. Uses MongoDB and Beanie.
"""

from enum import Enum

from beanie import BackLink, Document, Link
from pydantic import BaseModel, Field


class Privilege(Enum):
    LIST = 0
    DOWNLOAD = 1
    UPLOAD = 2

class ComplianceInformation(BaseModel):
    nersc_username: str | None

class User(Document):
    name: str
    api_key: str
    privileges: list[Privilege]

    compliance: ComplianceInformation | None

class File(Document):
    name: str
    uploader: Link[User]
    uuid: str
    bucket: str
    size: int
    checksum: str

class Product(Document):
    name: str
    description: str
    owner: Link[User]
    sources: list[File]
    collections: list[Link["Collection"]]

class Collection(Document):
    name: str
    description: str
    products: list[BackLink[Product]] = Field(json_schema_extra={"original_field":"collections"})

BEANIE_MODELS = [
    User,
    File,
    Product,
    Collection
]
