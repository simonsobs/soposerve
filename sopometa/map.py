from typing import Literal

from sopometa.base import BaseMetadata


class MapMetadata(BaseMetadata):
    """
    This is a re-implementation of the archaic
    FITS metadata, and is named as such.
    """

    metadata_type: Literal["map"] = "map"

    NPIX1: int
    NPIX2: int
    NPIX3: int | None
