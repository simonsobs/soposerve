"""
The database access layer for SOPO. Uses MongoDB and Beanie.
"""

from enum import Enum

from beanie import BackLink, BeanieModel, Link
from pydantic import BaseModel


class Privilege(Enum):
    LIST = 0
    DOWNLOAD = 1
    UPLOAD = 2

class ComplianceInformation(BaseModel):
    nersc_username: str | None

class User(BeanieModel):
    name: str
    api_key: str
    privileges: list[Privilege]

    compliance: ComplianceInformation | None

class File(BeanieModel):
    name: str
    uploader: Link[User]
    uuid: str
    bucket: str
    size: int
    checksum: str

class Product(BeanieModel):
    name: str
    description: str
    owner: Link[User]
    sources: list[File]
    collections: list[Link["Collection"]]

class Collection(BeanieModel):
    name: str
    description: str
    products: list[BackLink[Product]]

BEANIE_MODELS = [
    User,
    File,
    Product,
    Collection
]
