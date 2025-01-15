"""
Methods for interacting with the product layer of the hippo API.
"""

from pathlib import Path

import xxhash

from hippometa import ALL_METADATA_TYPE
from hippometa.simple import SimpleMetadata
from hipposerve.api.models.product import ReadProductResponse
from hipposerve.database import ProductMetadata, Visibility
from hipposerve.service.product import PostUploadFile

from .core import Client, MultiCache, console


def create(
    client: Client,
    name: str,
    description: str,
    metadata: ALL_METADATA_TYPE,
    sources: list[Path],
    source_descriptions: list[str | None],
    visibility: str = "collaboration",
) -> str:
    """
    Create a product in hippo.

    This is a multi-stage process, where we:

    a) Check and validate the sources.
    b) Make a request to hippo to create the product.
    c) Upload the sources to the presigned URLs.
    d) Confirm the upload to hippo.

    Arguments
    ---------
    client: Client
        The client to use for interacting with the hippo API.
    name : str
        The name of the product.
    description : str
        The description of the product.
    metadata : ALL_METADATA_TYPE
        The metadata of the product, as a validated pydantic model.
    sources : list[Path]
        The list of paths to the sources of the product.

    Returns
    -------
    str
        The ID of the product created.

    Raises
    ------
    httpx.HTTPStatusError
        If a request to the API fails
    """

    # Validate visibility
    if visibility not in ["public", "collaboration", "private"]:
        raise ValueError(
            "Invalid visibility level. Choose from 'public', 'collaboration', or 'private'."
        )

    # Check and validate the sources.
    assert len(sources) == len(source_descriptions)

    # Co-erce sources to paths as they will inevitably be strings...
    sources = [Path(x) for x in sources]

    source_metadata = []

    for source, source_description in zip(sources, source_descriptions):
        with source.open("rb") as file:
            file_info = {
                "name": source.name,
                "size": source.stat().st_size,
                "checksum": f"xxh64:{xxhash.xxh64(file.read()).hexdigest()}",
                "description": source_description,
            }
            source_metadata.append(file_info)
            if client.verbose:
                console.print("Successfully validated file:", file_info)

    # Make a request to hippo to create the product.
    if metadata is None:
        metadata = SimpleMetadata()

    response = client.put(
        "/product/new",
        json={
            "name": name,
            "description": description,
            "metadata": metadata.model_dump(),
            "sources": source_metadata,
            "visibility": visibility,
        },
    )

    response.raise_for_status()

    this_product_id = response.json()["id"]

    if client.verbose:
        console.print(
            f"Successfully created product {this_product_id} in remote database."
        )

    # Upload the sources to the presigned URLs.
    for source in sources:
        with source.open("rb") as file:
            if client.verbose:
                console.print("Uploading file:", source.name)

            retry = True
            upload_url = response.json()["upload_urls"][source.name]

            # We need to handle our own redirects because otherwise the head of the file will be incorrect,
            # and we will end up with Content-Length errors.
            while retry:
                if client.use_multipart_upload:
                    if client.verbose:
                        console.print("Using multipart upload")
                    individual_response = client.put(
                        upload_url,
                        files={"upload-file": (source.name, file)},
                        follow_redirects=False,
                    )
                else:
                    if client.verbose:
                        console.print("Using regular upload")
                    individual_response = client.put(
                        upload_url.strip(),
                        data=file,
                        follow_redirects=True,
                    )

                if client.verbose:
                    console.print(individual_response.content.decode("utf-8"))

                if individual_response.status_code in [301, 302, 307, 308]:
                    if client.verbose:
                        console.print(
                            f"Redirected to {individual_response.headers['Location']} from {upload_url}"
                        )
                    upload_url = individual_response.headers["Location"]
                    file.seek(0)
                    continue
                else:
                    retry = False
                    if client.verbose:
                        console.print("Retry set to false, file uploaded or failed")
                    individual_response.raise_for_status()
                    break

            if client.verbose:
                console.print("Successfully uploaded file:", source.name)

    # Confirm the upload to hippo.
    response = client.post(f"/product/{this_product_id}/confirm")

    response.raise_for_status()

    if client.verbose:
        console.print(f"Successfully completed upload of {name}.", style="bold green")

    return this_product_id


def read_with_versions(client: Client, id: str) -> ReadProductResponse:
    """
    Read a product from hippo by ID. Always returns the requested version,
    without information about other versions.

    Arguments
    ---------
    client: Client
        The client to use for interacting with the hippo API.
    id : str
        The ID of the product to read.

    Returns
    -------
    ReadProductResponse
        The response from the API.

    Raises
    ------
    httpx.HTTPStatusError
        If a request to the API fails
    """

    response = client.get(f"/product/{id}")

    response.raise_for_status()

    model = ReadProductResponse.model_validate_json(response.content)

    if client.verbose:
        console.print(f"Successfully read product {id}")

    return model


def read(client: Client, id: str) -> ProductMetadata:
    """
    Read a product from hippo by ID. Always returns the requested version,
    without information about other versions.

    Arguments
    ---------
    client: Client
        The client to use for interacting with the hippo API.
    id : str
        The ID of the product to read.

    Returns
    -------
    ReadProductResponse
        The response from the API.

    Raises
    ------
    httpx.HTTPStatusError
        If a request to the API fails
    """

    model = read_with_versions(client, id)

    # This model includes version history. We don't want that.
    model = model.versions[model.requested]

    if client.verbose:
        console.print(f"Successfully read product ({model.name})")

    return model


def delete(client: Client, id: str) -> bool:
    """
    Delete a product from hippo.

    Arguments
    ----------
    client: Client
        The client to use for interacting with the hippo API.
    id : str
        The ID of the product to delete.

    Raises
    ------
    httpx.HTTPStatusError
        If a request to the API fails
    """

    response = client.delete(f"/product/{id}")

    response.raise_for_status()

    if client.verbose:
        console.print(f"Successfully deleted product {id}.", style="bold green")

    return True


def search(client: Client, text: str) -> list[ProductMetadata]:
    """
    Search for text information in products (primarily names).

    Arguments
    ----------
    client: Client
        The client to use for interacting with the hippo API.
    text : str
        The text to search for.

    Returns
    -------
    list[ProductMetadata]
        The list of products that match the search query.

    Raises
    ------
    httpx.HTTPStatusError
        If a request to the API fails
    """

    response = client.get(f"/product/search/{text}")

    response.raise_for_status()

    models = [ProductMetadata.model_validate(x) for x in response.json()]

    if client.verbose:
        console.print(f"Successfully searched for products matching {text}")

    return models


def cache(client: Client, cache: MultiCache, id: str) -> list[Path]:
    """
    Cache a product from hippo.

    Arguments
    ----------
    client: Client
        The client to use for interacting with the hippo API.
    cache: MultiCache
        The cache to use for storing the product.
    id : str
        The ID of the product to cache.

    Returns
    -------
    list[Path]
        The list of paths to the cached sources.

    Raises
    ------
    httpx.HTTPStatusError
        If a request to the API fails
    CacheNotWriteableError
        If the cache is not writeable
    """

    response = client.get(f"/product/{id}/files")

    response.raise_for_status()

    post_upload_files = [
        PostUploadFile.model_validate(x) for x in response.json()["files"]
    ]

    if client.verbose:
        console.print(f"Successfully read product {id}")

    response_paths = []

    for file in post_upload_files:
        # See if it's already cached.
        try:
            cached = cache.available(file.uuid)
            response_paths.append(cached)

            if client.verbose:
                console.print(f"Found cached file {file.name}", style="green")

            continue
        except FileNotFoundError:
            if client.verbose:
                console.print(
                    f"File {file.name} ({file.uuid}) not found in cache", style="red"
                )
            cached = None

        cached = cache.get(
            id=file.uuid,
            path=file.object_name,
            checksum=file.checksum,
            size=file.size,
            presigned_url=file.url,
        )

        response_paths.append(cached)

        if client.verbose:
            console.print(f"Cached file {file.name} ({file.uuid})", style="yellow")

    return response_paths


def uncache(client: Client, cache: MultiCache, id: str) -> None:
    """
    Clear the cache of a product.

    Arguments
    ----------
    client: Client
        The client to use for interacting with the hippo API.
    cache: MultiCache
        The cache to use for storing the product.
    id : str
        The ID of the product to remove from the cache.
    """

    product = read(client, id)

    for vid, version in product.versions.items():
        for source in version.sources:
            cache.remove(source.uuid)

            if client.verbose:
                console.print(f"Removed file {source.name} ({source.uuid}) from cache")

    return


def set_visibility(client: Client, id: str, visibility: str) -> None:
    """
    Update the visibility of a product.

    Arguments
    ---------
    client: Client
        The client to use for interacting with the hippo API.
    collection_id : str
        The ID of the product whose visibility is being updated.
    visibility : str
        The new visibility level ('public', 'collaboration', or 'private').

    Raises
    ------
    ValueError
        If an invalid visibility level is provided.
    """
    # Validate the provided visibility level
    try:
        visibility_enum = Visibility(visibility)  # Convert string to Visibility enum
    except ValueError:
        raise ValueError(
            "Invalid visibility level. Choose from 'public', 'collaboration', or 'private'."
        )

    response = client.get(f"/product/{id}/set-visibility/{visibility}")

    response.raise_for_status()

    if client.verbose:
        console.print(
            f"Successfully updated product {id} to {visibility_enum.value} visibility.",
            style="bold green",
        )
