"""
Helpers for rendering cli elements.
"""

import rich

from hipposerve.api.models.relationships import (
    ReadCollectionProductResponse,
    ReadCollectionResponse,
)
from hipposerve.database import ProductMetadata


def render_product_metadata_list(
    input: list[ProductMetadata | ReadCollectionProductResponse],
) -> rich.table.Table:
    """
    Render a list of product meadata into a rich table.
    """

    table = rich.table.Table("ID", "Name", "Version", "Uploaded")

    for product in input:
        table.add_row(
            str(product.id),
            product.name,
            product.version,
            product.uploaded.strftime("%Y-%m-%d %H:%M"),
        )

    return table


def render_collection_metadata_list(
    input: list[ReadCollectionResponse],
) -> rich.table.Table:
    """
    Render a list of collection metadata into a rich table.
    """

    table = rich.table.Table("ID", "Name", "Description")

    for collection in input:
        description = collection.description.strip("\n")

        # Truncate it if it's too long
        if len(description) > 512:
            description = description[:512] + "..."

        table.add_row(str(collection.id), collection.name, description)

    return table
