"""
The database access layer for SOPO. Uses MongoDB and Beanie.
"""

from enum import Enum

from beanie import BackLink, Document, Indexed, Link
from pydantic import BaseModel, Field


class Privilege(Enum):
    LIST = 0
    DOWNLOAD = 1
    UPLOAD = 2

class ComplianceInformation(BaseModel):
    nersc_username: str | None

class User(Document):
    name: Indexed(str, unique=True)
    api_key: str
    privileges: list[Privilege]

    compliance: ComplianceInformation | None

class File(Document):
    name: Indexed(str, unique=True)
    uploader: str
    uuid: str
    bucket: str
    size: int
    checksum: str

class Product(Document):
    name: Indexed(str, unique=True)
    description: str
    owner: Link[User]
    sources: list[File]
    collections: list[Link["Collection"]]

class Collection(Document):
    name: Indexed(str, unique=True)
    description: str
    products: list[BackLink[Product]] = Field(json_schema_extra={"original_field":"collections"})

BEANIE_MODELS = [
    User,
    File,
    Product,
    Collection
]
