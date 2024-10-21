"""
An example of what using the hippo API looks like to create the worlds worst
coadded map.
"""

import sys

from astropy.io import fits

from hippoclient import collections, product
from hippoclient.core import ClientSettings

settings = ClientSettings()

client = settings.client
cache = settings.multi_cache

PATCH = "D6"
COLLECTION = sys.argv[1]

# Find our collection!
collection = collections.read(client=client, id=COLLECTION)

products_in_patch = []

# Find the maps in our patch that are splits.
for map_set in collection.products:
    metadata = map_set.metadata
    if metadata.patch == PATCH:
        if "source_free_split" in metadata.maps:
            products_in_patch.append(map_set.id)
            # Make sure this product is cached!
            product.cache(client=client, cache=cache, id=map_set.id)

print(f"Found {len(products_in_patch)} products in patch {PATCH}.")
print("Products: " + ", ".join(products_in_patch))


def coadd_maps(product_ids: list[str], client, cache, output_filename: str):
    sum_of_ivars = None
    sum_of_weighted_maps = None

    for product_id in product_ids:
        # Read the full product.
        map_set = product.read(client=client, id=product_id)
        map_set = map_set.versions[map_set.requested]

        uuid_from_filename = lambda fn: list(
            filter(lambda x: fn == x.name, map_set.sources)
        )[0].uuid

        source_free_filename = map_set.metadata.maps["source_free_split"].filename
        source_free_uuid = uuid_from_filename(source_free_filename)
        source_free_ivar_filename = map_set.metadata.maps["ivar_split"].filename
        source_free_ivar_uuid = uuid_from_filename(source_free_ivar_filename)

        # Get the filenames from the cache.
        source_free = cache.available(source_free_uuid)
        source_free_ivar = cache.available(source_free_ivar_uuid)

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

    with fits.open(output_filename, "ostream") as hdul:
        hdul.append(fits.PrimaryHDU(coadded_map))
        hdul.writeto(output_filename, overwrite=True)

    return


coadd_maps(products_in_patch, client, cache, f"coadd_{PATCH}.fits")
