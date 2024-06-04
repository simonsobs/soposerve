"""
Individual product metadata.
"""

from typing import Literal, Union

from pydantic import BaseModel


class BaseMetadata(BaseModel):
    metadata_type: str

    pass

class SimpleMetadata(BaseMetadata):
    """
    Simple metadata type for example purposes.
    """

    metadata_type: Literal["simple"] = "simple"


class MapMetadata(BaseMetadata):
    """
    This is a re-implementation of the archaic
    FITS metadata, and is named as such.
    """

    metadata_type: Literal["map"] = "map"

    NPIX1: int
    NPIX2: int
    NPIX3: int | None


class PowerSpectrumMetadata(BaseMetadata):
    metadata_type: Literal["power_spectrum"] = "power_spectrum"

    n_bins: int


ALL_METADATA = [MapMetadata, PowerSpectrumMetadata, SimpleMetadata, None]
ALL_METADATA_TYPE = Union[MapMetadata, PowerSpectrumMetadata, SimpleMetadata, None]