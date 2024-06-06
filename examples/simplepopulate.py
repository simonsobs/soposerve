"""
Populates the simple example server with a bunch of ACT maps.
"""

from pathlib import Path

from sopoclient import Client
from sopometa import MapMetadata

API_KEY = "TEST_API_KEY"
SERVER_LOCATION = "http://127.0.0.1:8000"
COLLECTION_NAME = "ACT DR4 Maps"

if __name__ == "__main__":
    client = Client(api_key=API_KEY, host=SERVER_LOCATION)

    client.create_collection(
        name=COLLECTION_NAME,
        description="A collection of ACT DR4 maps.",
    )

    for fits_file in Path(".").glob("*.fits"):
        client.create_product(
            name=fits_file.stem,
            description="An ACT map.",
            metadata=MapMetadata.from_fits(fits_file),
            sources=[fits_file],
            verbose=True,
        )

        client.add_to_collection(
            name=COLLECTION_NAME,
            product=fits_file.stem,
        )
