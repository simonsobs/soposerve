from pathlib import Path
from typing import Literal

import astropy.io.fits as fits_io

from sopometa.base import BaseMetadata


class MapMetadata(BaseMetadata):
    """
    This is a re-implementation of the archaic
    FITS metadata, and is named as such.
    """

    metadata_type: Literal["map"] = "map"

    NAXIS: list[int] = []
    CTYPE: list[str] = []
    CUNIT: list[str] = []
    CRVAL: list[float] = []
    CDELT: list[float] = []
    CRPIX: list[float] = []
    EQUINOX: str | None = None
    DATEREF: str | None = None
    RADESYS: str | None = None

    TELESCOP: str | None = None
    INSTRUME: str | None = None
    RELEASE: str | None = None
    SEASON: str | None = None
    PATCH: str | None = None
    FREQ: str | None = None
    ACTTAGS: str | None = None

    POLCCONV: str | None = None
    BUNIT: str | None = None
    EXTNAME: str | None = None
    FILENAME: str | None = None
    CHECKSUM: str | None = None
    DATASUM: str | None = None

    @classmethod
    def from_fits(self, filename: Path) -> "MapMetadata":
        """
        This method reads the FITS header of a file and
        returns a MapMetadata object with the header
        information.
        """
        with fits_io.open(filename) as hdul:
            header = hdul[0].header

        return MapMetadata(
            NAXIS=[header[f"NAXIS{x}"] for x in range(1, header["NAXIS"] + 1)],
            CTYPE=[header[f"CTYPE{x}"] for x in range(1, header["NAXIS"] + 1)],
            CUNIT=[header[f"CUNIT{x}"] for x in range(1, header["NAXIS"] + 1)],
            CRVAL=[header[f"CRVAL{x}"] for x in range(1, header["NAXIS"] + 1)],
            CDELT=[header[f"CDELT{x}"] for x in range(1, header["NAXIS"] + 1)],
            CRPIX=[header[f"CRPIX{x}"] for x in range(1, header["NAXIS"] + 1)],
            EQUINOX=header.get("EQUINOX"),
            DATEREF=header.get("DATEREF"),
            RADESYS=header.get("RADESYS"),
            TELESCOP=header.get("TELESCOP"),
            INSTRUME=header.get("INSTRUME"),
            RELEASE=header.get("RELEASE"),
            SEASON=header.get("SEASON"),
            PATCH=header.get("PATCH"),
            FREQ=header.get("FREQ"),
            ACTTAGS=header.get("ACTTAGS"),
            POLCCONV=header.get("POLCCONV"),
            BUNIT=header.get("BUNIT"),
            EXTNAME=header.get("EXTNAME"),
            FILENAME=header.get("FILENAME"),
            CHECKSUM=header.get("CHECKSUM"),
            DATASUM=header.get("DATASUM"),
        )
