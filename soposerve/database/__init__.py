"""
The database access layer for SOPO. Uses MongoDB and Beanie.
"""

from datetime import datetime
from enum import Enum

from beanie import BackLink, Document, Indexed, Link
from pydantic import BaseModel, Field

from sopometa import ALL_METADATA_TYPE


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


class CollectionPolicy(Enum):
    # What to do when versions are revved of products.
    # Keep track of all versions of the product in the collection.
    ALL = "all"
    # Keep track of all new versions of the product in the collection.
    # E.g. if v2 is added to a collection, v1 is _not_ but all future
    # versions will be tracked as part of that collection.
    NEW = "new"
    # Keep track of only the 'current' version of the product.
    CURRENT = "current"
    # Keep track of only a 'fixed' version of the product. So if v2 is
    # added to the collection, and v3 is created, only v2 is tracked in
    # the collection.
    FIXED = "fixed"


class ComplianceInformation(BaseModel):
    nersc_username: str | None


class User(Document):
    name: str = Indexed(str, unique=True)
    api_key: str
    privileges: list[Privilege]

    compliance: ComplianceInformation | None


class File(Document):
    name: str
    uploader: str
    uuid: str
    bucket: str
    size: int
    checksum: str
    available: bool = True


class Product(Document):
    name: str = Indexed(str)
    description: str
    metadata: ALL_METADATA_TYPE

    uploaded: datetime
    updated: datetime

    current: bool
    version: str

    sources: list[File]
    owner: Link[User]

    replaces: Link["Product"] | None = None

    child_of: list[Link["Product"]] = []
    parent_of: list[BackLink["Product"]] = Field(
        json_schema_extra={"original_field": "child_of"}, default=[]
    )

    collections: list[Link["Collection"]] = []
    collection_policies: list[CollectionPolicy] = []


class Collection(Document):
    # TODO: Implement updated time for collections.
    name: str = Indexed(str, unique=True)
    description: str
    products: list[BackLink[Product]] = Field(
        json_schema_extra={"original_field": "collections"}
    )


BEANIE_MODELS = [User, File, Product, Collection]
