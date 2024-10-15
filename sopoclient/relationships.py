"""
Methods for adding and removing child relationships between products.
"""

from .core import Client, console

def add_child(
        client: Client,
        parent: str,
        child: str
) -> bool:
    """
    Add a child relationship between two products.

    Arguments
    ---------
    client : Client
        The client to use for interacting with the SOPO API.
    parent : str
        The name of the parent product.
    child : str
        The name of the child product.

    Returns
    -------
    bool
        True if the relationship was added successfully.

    Raises
    ------
    httpx.HTTPStatusError
        If a request to the API fails
    """

    response = client.put(
        f"/relationships/product/{parent}/child_of/{child}"
    )

    response.raise_for_status()

    if client.verbose:
        console.print(
            f"Successfully added child relationship between {parent} and {child}.",
            style="bold green",
        )

    return True


def remove_child(
        client: Client,
        parent: str,
        child: str
) -> bool:
    """
    Remove a child relationship between two products.

    Arguments
    ---------
    client : Client
        The client to use for interacting with the SOPO API.
    parent : str
        The name of the parent product.
    child : str
        The name of the child product.

    Returns
    -------
    bool
        True if the relationship was removed successfully.

    Raises
    ------
    httpx.HTTPStatusError
        If a request to the API fails
    """

    response = client.delete(
        f"/relationships/product/{parent}/child_of/{child}"
    )

    response.raise_for_status()

    if client.verbose:
        console.print(
            f"Successfully removed child relationship between {parent} and {child}.",
            style="bold green",
        )

    return True