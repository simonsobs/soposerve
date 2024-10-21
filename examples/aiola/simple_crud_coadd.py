# %% [markdown]
# This script helps you understand how products are accessed and uplodaed in the hippo
# framework. In general, you want to think of your analysis as a cycle of reading and
# re-distributing products to the server. Before running this, make sure to have the
# test server running and have already ran `simplepopulate.py`.
#
# In this script, we:
# 1. Read a collection.
# 2. Filter the products in the collection to find the ones we want
#    (in this case, the splits in a particular patch).
# 3. Read the data from the products.
# 4. Create a co-added map from the splits.
# 5. Write the co-added map to disk.
# 6. Upload the co-added map to hippo, and create the appropriate parent/child
#    relationships.
#
# By doing this, you ensure that you analysis is tracked and repeatable. We won't ever
# force folks to upload all of their source code, but it is extremely helpful to be able
# to know what data was used to create a particula result. That's only possible if your
# data is tracked, versioned, and has the correct relationships present.

# %%
# Just some standard imports; nothing to see here.
import numpy as np
from astropy.io import fits

# %% [markdown]
# The hippo API is broken down into modules that you can use to interact wtih certain
# sub-sections of the API. Here, we're going to be interacting with three main concepts:
#
# 1. Collections: A collection is a group of products that are related in some way. For
#    our case here, the colleciton is the DR4/S13 150 GHz data.
# 2. Products: A product is a single piece of data. In this case, we're going to be
#    working with the "splits" in a particular patch.
# 3. Relationships: Products can be related to one another. In this case, we're going to
#    be creating a parent/child relationship between the splits and the co-added map.
#
# There are two main objects of interest that are accessed through the core
# `ClientSettings` singleton:
#
# 1. The `client`: this object is your HTTP link to the hippo server.
# 2. The `cache`: this is an on-disk cache of products in hippo. This is the only
#    way you should interact with the filesystem for existing products when using hippo.
# %%
from hippoclient import collections, product, relationships
from hippoclient.core import ClientSettings

settings = ClientSettings()

client = settings.client
cache = settings.cache

# %% [markdown]
# There are python tools for programatically interacting with the hippo API, but it's
# important to use the right tool for the job. In this case, it's much easier to use the
# `henry` command-line tool to find the collection ID that you're interested in. You can
# do that through:
# ```
# henry collection search 'ACT DR4'
# ```
# which produces the following table:
# ```
#                                  Collections
# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃            ID            ┃ Name                    ┃ Description             ┃
# ┡━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━┩
# │ 67166b59bff07cc529e7e603 │ ACT DR4 Frequency Maps  │ These FITS files are    │
# │                          │ at 98 and 150 GHz       │ the maps made with the  │
# │                          │ presented in Aiola et   │ nighttime 2013(s13) to  │
# │                          │ al. 2020                │ 2016(s16) data from the │
# │                          │                         │ ACTPol camera on the    │
# │                          │                         │ ACT telescope at        │
# │                          │                         │ 98(f090) and 150(f150)  │
# │                          │                         │ GHz.                    │
# │                          │                         │                         │
# │                          │                         │ These maps and their    │
# │                          │                         │ properties are          │
# │                          │                         │ described in Aiola et   │
# │                          │                         │ al. (2020) and Choi et  │
# │                          │                         │ al. (2020)              │
# │                          │                         │                         │
# │                          │                         │ #### Naming and         │
# │                          │                         │ products                │
# │                          │                         │                         │
# │                          │                         │ The maps are released   │
# │                          │                         │ both as 2- or 4-way     │
# │                          │                         │ independet splits, used │
# │                          │                         │ to compute the power    │
# │                          │                         │ spectra, and as         │
# │                          │                         │ inverse-variance        │
# │                          │                         │ map-space co-added.     │
# │                          │                         │                         │
# │                          │                         │ ##### Naming convention │
# │                          │                         │                         │
# │                          │                         │ `act_{release}_{season… │
# └──────────────────────────┴─────────────────────────┴─────────────────────────┘
# ```
# The collection ID that you need is that one on the left (67166b59bff07cc529e7e603); this will
# be different in your case.

# %%
PATCH = "D6"
COLLECTION = None

if COLLECTION is None:
    raise ValueError(
        "Please set the COLLECTION variable to the ID of the collection you want to use."
    )

# Find our collection!
collection = collections.read(client=client, id=COLLECTION)

# Make sure the whole collection is cached on our machine. This will automatically
# download any missing files if they are needed.
collections.cache(client=client, cache=cache, id=COLLECTION)

# %% [markdown]
# If we view that collection, there are a number of patches and products including
# coadded maps. We just want splits:
# ```
# henry collection read 67166b59bff07cc529e7e603
# ```
# ACT DR4 Frequency Maps at 98 and 150 GHz presented in Aiola et al. 2020

# These FITS files are the maps made with the nighttime 2013(s13) to 2016(s16)
# data from the ACTPol camera on the ACT telescope at 98(f090) and 150(f150) GHz.

# These maps and their properties are described in Aiola et al. (2020) and Choi et
# al. (2020)

#                               Naming and products

# The maps are released both as 2- or 4-way independet splits, used to compute the
# power spectra, and as inverse-variance map-space co-added.

#                                Naming convention

# act_{release}_{season}_{patch}_{array}_{freq}_nohwp_night_3pass_{nway}_{set}_{pr
# oduct}.fits

#  • "release": these maps are part of the DR4 data release, and versioning allows
#    for future modifications of thise relase [possible tags: dr4.xy]
#  • "season": observation season [possible tags: s13, s14, s15, s16]
#  • "patch": survey patch [possible tags: D1, D5, D6, D56, D8, BN, AA]
#  • "array": telescope optic module on ACTPol camera [possible tags: pa1, pa2,
#    pa3]
#  • "freq": frequency tag [possible tags: f090, f150]
#  • "nway": number of independet splits [possible tags: 2way, 4way]
#  • "set": split identifier or co-add version [possible tags: set0, set1, set2,
#    set3, coadd]
#  • "product": see below for list of released products

#                                Available products

# More detailes availble in Sec. 5 of Aiola et al (2020)

#  • "map_srcfree": observed I,Q,U Stokes components with signal from point
#    sources subtracted [uK]
#  • "srcs": I,Q,U Stokes components of the point sources signal [uK]
#  • NOTE: "map_srcfree"+"srcs" is the observed sky
#  • "ivar": inverse-variance pixel weight [uK^-2]
#  • "xlink": cross-linking information encoded as I,Q,U Stokes components [uK^-2]

#                                 Post-processing

# The "map_srcfree", "srcs", and "ivar" maps are calibrated with a single
# coefficient, which is measured for each field and reported in Choi et al (2020).
# An extra polarization efficiency parameter is included (and let to vary) in the
# likelihood analysis and NOT considered here.

#                                     Remarks

#  • These maps are released following the IAU polarization convention
#    (POLCCONV='IAU' in FITS header).
#  • Baseline software to handle these maps is Pixell
#    (https://github.com/simonsobs/pixell).


#                                     Products
# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
# ┃            ID            ┃ Name                 ┃ Version ┃     Uploaded     ┃
# ┡━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
# │ 67166b5abff07cc529e7e604 │ ACT DR4 (Patch D5)   │  1.0.0  │ 2024-10-21 14:55 │
# │                          │ 4-way (set2)         │         │                  │
# │ 67166b5cbff07cc529e7e605 │ ACT DR4 (Patch D6)   │  1.0.0  │ 2024-10-21 14:55 │
# │                          │ 4-way (coadd)        │         │                  │
# │ 67166b5dbff07cc529e7e606 │ ACT DR4 (Patch D6)   │  1.0.0  │ 2024-10-21 14:55 │
# │                          │ 4-way (set0)         │         │                  │
# │ 67166b5fbff07cc529e7e607 │ ACT DR4 (Patch D1)   │  1.0.0  │ 2024-10-21 14:55 │
# │                          │ 4-way (set2)         │         │                  │
# │ 67166b60bff07cc529e7e608 │ ACT DR4 (Patch D1)   │  1.0.0  │ 2024-10-21 14:55 │
# │                          │ 4-way (set1)         │         │                  │
# │ 67166b62bff07cc529e7e609 │ ACT DR4 (Patch D5)   │  1.0.0  │ 2024-10-21 14:55 │
# │                          │ 4-way (set0)         │         │                  │
# │ 67166b64bff07cc529e7e60a │ ACT DR4 (Patch D6)   │  1.0.0  │ 2024-10-21 14:55 │
# │                          │ 4-way (set3)         │         │                  │
# │ 67166b65bff07cc529e7e60b │ ACT DR4 (Patch D5)   │  1.0.0  │ 2024-10-21 14:55 │
# │                          │ 4-way (set1)         │         │                  │
# │ 67166b67bff07cc529e7e60c │ ACT DR4 (Patch D1)   │  1.0.0  │ 2024-10-21 14:55 │
# │                          │ 4-way (set0)         │         │                  │
# │ 67166b69bff07cc529e7e60d │ ACT DR4 (Patch D5)   │  1.0.0  │ 2024-10-21 14:55 │
# │                          │ 4-way (coadd)        │         │                  │
# │ 67166b6bbff07cc529e7e60e │ ACT DR4 (Patch D6)   │  1.0.0  │ 2024-10-21 14:55 │
# │                          │ 4-way (set1)         │         │                  │
# │ 67166b6cbff07cc529e7e60f │ ACT DR4 (Patch D5)   │  1.0.0  │ 2024-10-21 14:55 │
# │                          │ 4-way (set3)         │         │                  │
# │ 67166b6ebff07cc529e7e610 │ ACT DR4 (Patch D6)   │  1.0.0  │ 2024-10-21 14:55 │
# │                          │ 4-way (set2)         │         │                  │
# │ 67166b70bff07cc529e7e611 │ ACT DR4 (Patch D1)   │  1.0.0  │ 2024-10-21 14:55 │
# │                          │ 4-way (coadd)        │         │                  │
# │ 67166b72bff07cc529e7e612 │ ACT DR4 (Patch D1)   │  1.0.0  │ 2024-10-21 14:55 │
# │                          │ 4-way (set3)         │         │                  │
# └──────────────────────────┴──────────────────────┴─────────┴──────────────────┘
# ```
# We can view an individual product with its ID:
# ```
# ACT DR4 (Patch D6) 4-way (coadd)

# Versions: 1.0.0
# ACT DR4 4-way Co-added Maps. Includes all the maps from the co-added maps, see
# the collection for more details (Patch D6).
# MapSet(
#     metadata_type='mapset',
#     maps={
#         'ivar_coadd': MapSetMap(
#             map_type='ivar_coadd',
#             filename='act_dr4.01_s13_D6_pa1_f150_nohwp_night_3pass_4way_coadd_iv
# ar.fits',
#             units='uK^-2'
#         ),
#         'source_free': MapSetMap(
#             map_type='source_free',
#             filename='act_dr4.01_s13_D6_pa1_f150_nohwp_night_3pass_4way_coadd_ma
# p_srcfree.fits',
#             units='uK'
#         ),
#         'xlink_coadd': MapSetMap(
#             map_type='xlink_coadd',
#             filename='act_dr4.01_s13_D6_pa1_f150_nohwp_night_3pass_4way_coadd_xl
# ink.fits',
#             units='uK^-2'
#         ),
#         'source_only': MapSetMap(
#             map_type='source_only',
#             filename='act_dr4.01_s13_D6_pa1_f150_nohwp_night_3pass_4way_coadd_sr
# cs.fits',
#             units='uK'
#         )
#     },
#     pixelisation='healpix',
#     telescope='ACT',
#     instrument='ACTPol',
#     release='DR4',
#     season='s13',
#     patch='D6',
#     frequency='150',
#     polarization_convention='IAU',
#     tags=None
# )
#                                     Sources
# ┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━┓
# ┃ Name              ┃ Description      ┃ UUID              ┃ Size [B] ┃ Cached ┃
# ┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━┩
# │ act_dr4.01_s13_D… │ Inverse-variance │ 16c2aa03-5f50-47… │ 23195520 │ Yes    │
# │                   │ map              │                   │          │        │
# │ act_dr4.01_s13_D… │ I, Q, U          │ ccdcee57-94cf-49… │ 69575040 │ Yes    │
# │                   │ source-free map  │                   │          │        │
# │ act_dr4.01_s13_D… │ Cross-linking    │ 0d6d1a64-ddf3-4b… │ 69575040 │ Yes    │
# │                   │ map              │                   │          │        │
# │ act_dr4.01_s13_D… │ I, Q, U point    │ 2a6ed4ad-7b40-4b… │ 69575040 │ Yes    │
# │                   │ source map       │                   │          │        │
# └───────────────────┴──────────────────┴───────────────────┴──────────┴────────┘
#
# Relationships
#
# Collections: 67166b59bff07cc529e7e603
# ```
# So we can see that each map has four files associated with it: the source-free map,
# the inverse-variance map, the cross-linking map, and the source map. The coadds have
# `coadd` maps associated with them. Let's filter out our patch and only look at the
# splits:


# %%
def product_valid(product):
    return (
        "source_free_split" in product.metadata.maps and product.metadata.patch == PATCH
    )


products_in_patch = [
    product.id for product in collection.products if product_valid(product)
]

print(f"Found {len(products_in_patch)} products in patch {PATCH}.")
print("Products: " + ", ".join(products_in_patch))

# %% [markdown]
# Now that we have the products we want, we can read them and coadd them. To do this, we
# need to call the `product.read` function for each product, which gets us the programatically-
# accessible version of what we just read from `henry` above. We can then ask the `cache`
# for the relationship between filenames and the full on-disk path in the cache using the
# `names_to_paths` function. We can then read the data from the FITS files and coadd them.


# %%
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

# %% [markdown]
# Now we have a coadded map, we can save it to disk and upload it to hippo. In general, we would
# want to use pixell for this and include much more metadata, but for this simple test we can use
# the basic `SimpleMetadata` module.

fits.PrimaryHDU(coadded_map).writeto(f"coadd_{PATCH}.fits", overwrite=True)


# Now send it back to the server.
metadata = product.SimpleMetadata()

new_product_id = product.create(
    client=client,
    name=f"Coadded DR4 Map (Patch {PATCH})",
    description=f"A coadded map of all the splits in patch {PATCH}.",
    metadata=metadata,
    sources=[f"coadd_{PATCH}.fits"],
    source_descriptions=[f"The coadded map of all the splits in patch {PATCH}."],
)

# Create child relationships to all the splits.
for product_id in products_in_patch:
    relationships.add_child(client=client, parent=product_id, child=new_product_id)

# %% [markdown]
# We can now search for our own product:
# ```
# henry product search 'Coadded DR4 Map (Patch D6)'
# ```
# ```
#                                     Products
# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
# ┃            ID            ┃ Name                 ┃ Version ┃     Uploaded     ┃
# ┡━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
# │ 67168da3bff07cc529e7ea3b │ Coadded DR4 Map      │  1.0.0  │ 2024-10-21 17:21 │
# │                          │ (Patch D6)           │         │                  │
# │ 67166b5fbff07cc529e7e607 │ ACT DR4 (Patch D1)   │  1.0.0  │ 2024-10-21 14:55 │
# │                          │ 4-way (set2)         │         │                  │
# │ 67166b5abff07cc529e7e604 │ ACT DR4 (Patch D5)   │  1.0.0  │ 2024-10-21 14:55 │
# │                          │ 4-way (set2)         │         │                  │
# │ 67166b72bff07cc529e7e612 │ ACT DR4 (Patch D1)   │  1.0.0  │ 2024-10-21 14:55 │
# │                          │ 4-way (set3)         │         │                  │
# │ 67166b62bff07cc529e7e609 │ ACT DR4 (Patch D5)   │  1.0.0  │ 2024-10-21 14:55 │
# │                          │ 4-way (set0)         │         │                  │
# │ 67166b60bff07cc529e7e608 │ ACT DR4 (Patch D1)   │  1.0.0  │ 2024-10-21 14:55 │
# │                          │ 4-way (set1)         │         │                  │
# │ 67166b5dbff07cc529e7e606 │ ACT DR4 (Patch D6)   │  1.0.0  │ 2024-10-21 14:55 │
# │                          │ 4-way (set0)         │         │                  │
# │ 67166b6cbff07cc529e7e60f │ ACT DR4 (Patch D5)   │  1.0.0  │ 2024-10-21 14:55 │
# │                          │ 4-way (set3)         │         │                  │
# │ 67166b67bff07cc529e7e60c │ ACT DR4 (Patch D1)   │  1.0.0  │ 2024-10-21 14:55 │
# │                          │ 4-way (set0)         │         │                  │
# │ 67166b6bbff07cc529e7e60e │ ACT DR4 (Patch D6)   │  1.0.0  │ 2024-10-21 14:55 │
# │                          │ 4-way (set1)         │         │                  │
# │ 67166b64bff07cc529e7e60a │ ACT DR4 (Patch D6)   │  1.0.0  │ 2024-10-21 14:55 │
# │                          │ 4-way (set3)         │         │                  │
# │ 67166b70bff07cc529e7e611 │ ACT DR4 (Patch D1)   │  1.0.0  │ 2024-10-21 14:55 │
# │                          │ 4-way (coadd)        │         │                  │
# │ 67166b65bff07cc529e7e60b │ ACT DR4 (Patch D5)   │  1.0.0  │ 2024-10-21 14:55 │
# │                          │ 4-way (set1)         │         │                  │
# │ 67166b69bff07cc529e7e60d │ ACT DR4 (Patch D5)   │  1.0.0  │ 2024-10-21 14:55 │
# │                          │ 4-way (coadd)        │         │                  │
# │ 67166b5cbff07cc529e7e605 │ ACT DR4 (Patch D6)   │  1.0.0  │ 2024-10-21 14:55 │
# │                          │ 4-way (coadd)        │         │                  │
# │ 67166b6ebff07cc529e7e610 │ ACT DR4 (Patch D6)   │  1.0.0  │ 2024-10-21 14:55 │
# │                          │ 4-way (set2)         │         │                  │
# └──────────────────────────┴──────────────────────┴─────────┴──────────────────┘
# ```
# And...
# ```
# henry product read 67168da3bff07cc529e7ea3b
# ```
# Coadded DR4 Map (Patch D6)
#
# Versions: 1.0.0
# A coadded map of all the splits in patch D6.
# SimpleMetadata(metadata_type='simple')
#                                     Sources
# ┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━┓
# ┃ Name          ┃ Description        ┃ UUID                ┃ Size [B] ┃ Cached ┃
# ┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━┩
# │ coadd_D6.fits │ The coadded map of │ cc2743eb-d497-4ec8… │ 69572160 │ No     │
# │               │ all the splits in  │                     │          │        │
# │               │ patch D6.          │                     │          │        │
# └───────────────┴────────────────────┴─────────────────────┴──────────┴────────┘
#
# Relationships
#
# Collections:
# Parents: 67166b5dbff07cc529e7e606, 67166b64bff07cc529e7e60a,
# 67166b6bbff07cc529e7e60e, 67166b6ebff07cc529e7e610
# ```
# Note here that we do not have a `cached` version of this file. But we have it on disk!
# That's because hippo doesn't know about your own filesystem, just the cache. You'll need
# to download it back from hippo to get it back into your cache.

# %%
