from typing import Literal

from sopometa.base import BaseMetadata


class SimpleMetadata(BaseMetadata):
    """
    Simple metadata type for example purposes.
    """

    metadata_type: Literal["simple"] = "simple"
