"""
An example of what using the hippo API looks like to create the worlds worst
coadded map.
"""

import sys

import numpy as np
from astropy.io import fits

from hippoclient import collections, product
from hippoclient.core import ClientSettings

settings = ClientSettings()

client = settings.client
cache = settings.cache

PATCH = "D6"
COLLECTION = sys.argv[1]

# Find our collection!
collection = collections.read(client=client, id=COLLECTION)

# Make sure the whole collection is cached on our machine.
collections.cache(client=client, cache=cache, id=COLLECTION)

# If we view that collection, there are a number of patches and products including
# coadded maps. We just want splits.


def product_valid(product):
    return (
        "source_free_split" in product.metadata.maps and product.metadata.patch == PATCH
    )


products_in_patch = [
    product.id for product in collection.products if product_valid(product)
]

print(f"Found {len(products_in_patch)} products in patch {PATCH}.")
print("Products: " + ", ".join(products_in_patch))


def coadd_maps(product_ids: list[str], client, cache) -> np.array:
    sum_of_ivars = None
    sum_of_weighted_maps = None

    for product_id in product_ids:
        # Read the full product.
        map_set = product.read(client=client, id=product_id)

        paths = cache.names_to_paths(map_set.sources)

        source_free = paths[map_set.metadata.maps["source_free_split"].filename]
        source_free_ivar = paths[map_set.metadata.maps["ivar_split"].filename]

        with fits.open(source_free) as hdul:
            data = hdul[0].data

        with fits.open(source_free_ivar) as hdul:
            ivar = hdul[0].data

        if sum_of_ivars is None:
            sum_of_ivars = ivar
            sum_of_weighted_maps = data * ivar
        else:
            sum_of_ivars += ivar
            sum_of_weighted_maps += data * ivar

    coadded_map = sum_of_weighted_maps / sum_of_ivars

    return coadded_map


coadded_map = coadd_maps(
    products_in_patch,
    client,
    cache,
)

fits.PrimaryHDU(coadded_map).writeto(f"coadd_{PATCH}.fits", overwrite=True)
