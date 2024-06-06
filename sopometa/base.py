"""
Base metadata type that all metadata must inherit from
"""

from pydantic import BaseModel


class BaseMetadata(BaseModel):
    metadata_type: str

    pass
