"""
Methods for interacting with the collections layer of the hippo API
"""

from pathlib import Path

from hipposerve.api.models.relationships import ReadCollectionResponse

from .core import Client, MultiCache, console
from .product import cache as cache_product
from .product import uncache as uncache_product
from hippoclient.product import set_visibility as set_product_visibility
from hipposerve.database import Visibility


def create(
    client: Client,
    name: str,
    description: str,
) -> str:
    """
    Create a new collection in hippo.

    Arguments
    ---------
    client : Client
        The client to use for interacting with the hippo API.
    name : str
        The name of the collection.
    description : str
        The description of the collection.

    Returns
    -------
    str
        The ID of the collection created.

    Raises
    ------
    httpx.HTTPStatusError
        If a request to the API fails
    """

    response = client.put(
        f"/relationships/collection/{name}", json={"description": description}
    )

    response.raise_for_status()

    if client.verbose:
        console.print(f"Successfully created collection {name}.", style="bold green")

    return response.json()


def read(
    client: Client,
    id: str,
) -> ReadCollectionResponse:
    """
    Read a collection from hippo.

    Arguments
    ---------
    client: Client
        The client to use for interacting with the hippo API.
    id : str
        The id of the collection to read.

    Returns
    -------
    ReadCollectionResponse
        The response from the API.

    Raises
    ------
    httpx.HTTPStatusError
        If a request to the API fails
    """

    response = client.get(f"/relationships/collection/{id}")

    response.raise_for_status()

    model = ReadCollectionResponse.model_validate_json(response.content)

    if client.verbose:
        console.print(f"Successfully read collection {model.name} ({id})")

    return model


def search(client: Client, name: str) -> list[ReadCollectionResponse]:
    """
    Search for collections in hippo.

    Arguments
    ---------
    client: Client
        The client to use for interacting with the hippo API.
    name : str
        The name of the collection to search for.

    Returns
    -------
    list[ReadCollectionResponse]
        The response from the API.

    Raises
    ------
    httpx.HTTPStatusError
        If a request to the API fails
    """

    response = client.get(f"/relationships/collection/search/{name}")

    response.raise_for_status()

    models = [ReadCollectionResponse.model_validate(x) for x in response.json()]

    if client.verbose:
        console.print(f"Successfully searched for collection {name}")

    return models


def add(client: Client, id: str, product: str) -> bool:
    """
    Add a product to a collection in hippo.

    Arguments
    ---------
    client: Client
        The client to use for interacting with the hippo API.
    id : str
        The id of the collection to add the product to.
    product : str
        The id of the product to add to the collection.

    Raises
    ------
    httpx.HTTPStatusError
        If a request to the API fails
    """

    response = client.put(f"/relationships/collection/{id}/{product}")

    response.raise_for_status()

    if client.verbose:
        console.print(
            f"Successfully added product {product} to collection {id}.",
            style="bold green",
        )

    return True


def remove(client: Client, id: str, product: str) -> bool:
    """
    Remove a product from a collection in hippo.

    Arguments
    ---------
    client: Client
        The client to use for interacting with the hippo API.
    name : str
        The id of the collection to remove the product from.
    product : str
        The id of the product to remove from the collection.

    Raises
    ------
    httpx.HTTPStatusError
        If a request to the API fails
    """

    response = client.delete(f"/relationships/collection/{id}/{product}")

    response.raise_for_status()

    if client.verbose:
        console.print(
            f"Successfully removed product {product} from collection {id}.",
            style="bold green",
        )

    return True


def delete(client: Client, id: str) -> bool:
    """
    Delete a collection from hippo.

    Arguments
    ----------
    client: Client
        The client to use for interacting with the hippo API.
    id : str
        The name of the collection to delete.

    Raises
    ------
    httpx.HTTPStatusError
        If a request to the API fails
    """

    response = client.delete(f"/relationships/collection/{id}")

    response.raise_for_status()

    if client.verbose:
        console.print(f"Successfully deleted collection {id}.", style="bold green")

    return True


def cache(client: Client, cache: MultiCache, id: str) -> list[Path]:
    """
    Cache a collection from hippo.

    Arguments
    ---------
    client: Client
        The client to use for interacting with the hippo API.
    cache : MultiCache
        The cache to use for storing the collection.
    id : str
        The id of the collection to cache.

    Returns
    -------
    list[Path]
        The paths to the cached files.

    Raises
    ------
    httpx.HTTPStatusError
        If a request to the API fails
    CacheNotWriteableError
        If the cache is not writeable
    """

    collection = read(client, id)

    paths = []

    for product in collection.products:
        paths += cache_product(client, cache, product.id)

    return paths


def uncache(client: Client, cache: MultiCache, id: str) -> None:
    """
    Remove a collection from local caches.

    Arguments
    ---------
    client: Client
        The client to use for interacting with the hippo API.
    cache : MultiCache
        The cache to use for storing the collection.
    id : str
        The id of the collection to uncache.

    Raises
    ------
    CacheNotWriteableError
        If the cache is not writeable
    """

    collection = read(client, id)

    for product in collection.products:
        uncache_product(client, cache, product.id)


def set_collection_visibility(client: Client, collection_id: str, visibility: str) -> None:
    """
    Update the visibility of all products in a collection.

    Arguments
    ---------
    client: Client
        The client to use for interacting with the hippo API.
    collection_id : str
        The ID of the collection whose products' visibility is being updated.
    visibility : str
        The new visibility level ('public', 'collaboration', or 'private').

    Raises
    ------
    ValueError
        If an invalid visibility level is provided.
    httpx.HTTPStatusError
        If a request to the API fails.
    """

    # Validate visibility
    try:
        visibility_enum = Visibility(visibility)
    except ValueError:
        raise ValueError("Invalid visibility level. Choose from 'public', 'collaboration', or 'private'.")

    # Fetch the collection details
    collection = read(client, collection_id)

    # Update visibility for each product in the collection
    console.print(f"Updating visibility to '{visibility}' for all products in collection '{collection.name}'...", style="blue")
    for product in collection.products:
        try:
            set_product_visibility(client, product.id, visibility_enum.value)
            console.print(f"Successfully updated visibility for product {product.id}.", style="green")
        except Exception as e:
            console.print(f"Failed to update product {product.id}: {str(e)}", style="red")

    console.print(f"Successfully updated visibility for all products in collection '{collection.name}'.", style="bold green")
