"""
Methods for interacting with the collections layer of the SOPO API
"""

from soposerve.api.models.relationships import ReadCollectionResponse

from .core import Client, console


def create(
    client: Client,
    name: str,
    description: str,
) -> str:
    """
    Create a new collection in SOPO.

    Arguments
    ---------
    client : Client
        The client to use for interacting with the SOPO API.
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
    name: str,
) -> ReadCollectionResponse:
    """
    Read a collection from SOPO.

    Arguments
    ---------
    client: Client
        The client to use for interacting with the SOPO API.
    name : str
        The name of the collection to read.

    Returns
    -------
    ReadCollectionResponse
        The response from the API.

    Raises
    ------
    httpx.HTTPStatusError
        If a request to the API fails
    """

    response = client.get(f"/relationships/collection/{name}")

    response.raise_for_status()

    model = ReadCollectionResponse.model_validate_json(response.content)

    if client.verbose:
        console.print(f"Successfully read collection {name}.")

    return model


def add(client: Client, name: str, product: str) -> bool:
    """
    Add a product to a collection in SOPO.

    Arguments
    ---------
    client: Client
        The client to use for interacting with the SOPO API.
    name : str
        The name of the collection to add the product to.
    product : str
        The name of the product to add to the collection (not the ID).

    Raises
    ------
    httpx.HTTPStatusError
        If a request to the API fails
    """

    response = client.put(f"/relationships/collection/{name}/{product}")

    response.raise_for_status()

    if client.verbose:
        console.print(
            f"Successfully added product {product} to collection {name}.",
            style="bold green",
        )

    return True


def remove(client: Client, name: str, product: str) -> bool:
    """
    Remove a product from a collection in SOPO.

    Arguments
    ---------
    client: Client
        The client to use for interacting with the SOPO API.
    name : str
        The name of the collection to remove the product from.
    product : str
        The name of the product to remove from the collection (not the ID).

    Raises
    ------
    httpx.HTTPStatusError
        If a request to the API fails
    """

    response = client.delete(f"/relationships/collection/{name}/{product}")

    response.raise_for_status()

    if client.verbose:
        console.print(
            f"Successfully removed product {product} from collection {name}.",
            style="bold green",
        )

    return True


def delete(client: Client, name: str) -> bool:
    """
    Delete a collection from SOPO.

    Arguments
    ----------
    client: Client
        The client to use for interacting with the SOPO API.
    name : str
        The name of the collection to delete.

    Raises
    ------
    httpx.HTTPStatusError
        If a request to the API fails
    """

    response = client.delete(f"/relationships/collection/{name}")

    response.raise_for_status()

    if client.verbose:
        console.print(f"Successfully deleted collection {name}.", style="bold green")

    return True
