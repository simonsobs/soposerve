"""
A map set.
"""

from typing import Literal

from pydantic import BaseModel

from hippometa.base import BaseMetadata

MAP_TYPES = Literal[
    "coadd",
    "split",
    "source_only",
    "source_only_split",
    "source_free",
    "source_free_split",
    "ivar_coadd",
    "ivar_split",
    "xlink_coadd",
    "xlink_split",
]


class MapSetMap(BaseModel):
    map_type: MAP_TYPES
    filename: str
    units: str | None = None


class MapSet(BaseMetadata):
    """
    A set of maps corresponding to the same observation. An easy way to package
    up e.g. a coadd mapp and its associated ivar map.
    """

    metadata_type: Literal["mapset"] = "mapset"
    maps: dict[MAP_TYPES, MapSetMap]

    pixelisation: Literal["healpix", "cartesian"]

    telescope: str | None = None
    instrument: str | None = None
    release: str | None = None
    season: str | None = None
    patch: str | None = None
    frequency: str | None = None
    polarization_convention: str | None = None

    tags: list[str] | None = None
