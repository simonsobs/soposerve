"""
The database access layer for SOPO. Uses MongoDB and Beanie.
"""

from datetime import datetime
from enum import Enum

from beanie import BackLink, Document, Indexed, Link
from pydantic import BaseModel, Field

from soposerve.database.metadata import ALL_METADATA_TYPE


class Privilege(Enum):
    # Product management. Note that _for now_ users can update any other
    # user's products.
    CREATE_PRODUCT = "create_products"
    LIST_PRODUCT = "list_products"
    READ_PRODUCT = "read_products"
    DOWNLOAD_PRODUCT = "download_products"
    CONFIRM_PRODUCT = "confirm_product"
    DELETE_PRODUCT = "delete_products"
    UPDATE_PRODUCT = "update_products"

    # Collection management. Note that _for now_ users can update any
    # collection
    CREATE_COLLECTION = "create_collection"
    READ_COLLECTION = "read_collection"
    UPDATE_COLLECTION = "update_collection"
    DELETE_COLLECTION = "delete_collection"
    CREATE_RELATIONSHIP = "create_relationship"
    DELETE_RELATIONSHIP = "delete_relationship"

    # User management
    CREATE_USER = "create_user"
    READ_USER = "read_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"


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
