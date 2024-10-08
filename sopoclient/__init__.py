"""
A simple python wrapper for the HTTP for SOPO.

API key can be stored in the SOPO_API_KEY environment variable.
Host can be stored in the SOPO_HOST environment variable.
"""

import os
from pathlib import Path

import httpx
import xxhash
from rich.console import Console

from sopometa import ALL_METADATA_TYPE
from sopometa.simple import SimpleMetadata

# Rich printer
console = Console()


class Client:
    http: httpx.Client
    api_key: str
    host: str

    def __init__(self, api_key: str | None, host: str | None):
        self.api_key = api_key
        self.host = host

        if not self.api_key:
            self.api_key = os.getenv("SOPO_API_KEY")

        if not self.host:
            self.host = os.getenv("SOPO_HOST")

        self.http = httpx.Client(
            base_url=self.host, headers={"X-API-Key": self.api_key}
        )

    def create_product(
        self,
        name: str,
        description: str,
        metadata: ALL_METADATA_TYPE,
        sources: list[Path],
        source_descriptions: list[str | None],
        verbose: bool = False,
    ):
        """
        Create a product in SOPO.

        This is a multi-stage process, where we:

        a) Check and validate the sources.
        b) Make a request to SOPO to create the product.
        c) Upload the sources to the presigned URLs.
        d) Confirm the upload to SOPO.

        Arguments
        ---------
        name : str
            The name of the product.
        description : str
            The description of the product.
        metadata : ALL_METADATA_TYPE
            The metadata of the product, as a validated pydantic model.
        sources : list[Path]
            The list of paths to the sources of the product.
        verbose: bool (default False)
            If True, print additional information about the upload process.
        """

        # Check and validate the sources.
        assert len(sources) == len(source_descriptions)

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
                if verbose:
                    console.print("Successfully validated file:", file_info)

        # Make a request to SOPO to create the product.
        if metadata is None:
            metadata = SimpleMetadata()

        response = self.http.put(
            "/product/new",
            json={
                "name": name,
                "description": description,
                "metadata": metadata.model_dump(),
                "sources": source_metadata,
            },
        )

        response.raise_for_status()

        this_product_id = response.json()["id"]

        if verbose:
            console.print("Successfully created product in remote database.")

        # Upload the sources to the presigned URLs.
        for source in sources:
            with source.open("rb") as file:
                if verbose:
                    console.print("Uploading file:", source.name)

                individual_response = self.http.put(
                    response.json()["upload_urls"][source.name], data=file
                )

                individual_response.raise_for_status()

                if verbose:
                    console.print("Successfully uploaded file:", source.name)

        # Confirm the upload to SOPO.
        response = self.http.post(f"/product/{this_product_id}/confirm")

        response.raise_for_status()

        if verbose:
            console.print(
                f"Successfully completed upload of {name}.", style="bold green"
            )

    def delete_product(
        self,
        name: str,
    ):
        """
        Deletes a product.

        Arguments
        ---------
        name : str
            The name of the product.
        """

        response = self.http.delete(f"/product/{name}")

        response.raise_for_status()

        console.print(f"Successfully deleted product {name}.", style="bold green")

    def add_relationship(self, name_from: str, name_to: str):
        """
        Add a relationship link between two products. Note that relationships
        are not inherrently bidirectional.

        Arguments
        ---------

        name_from : str
            The name of the product to link from.
        name_to : str
            The name of the product to link to.
        """

        response = self.http.put(
            f"/relationships/product/{name_from}/related_to/{name_to}"
        )

        response.raise_for_status()

        console.print(
            f"Successfully added relationship between {name_from} and {name_to}.",
            style="bold green",
        )

    def remove_relationship(self, name_from: str, name_to: str):
        """
        Remove a relationship link between two products. Note that relationships
        are not inherrently bidirectional.

        Arguments
        ---------

        name_from : str
            The name of the product to link from.
        name_to : str
            The name of the product to link to.
        """

        response = self.http.delete(
            f"/relationships/product/{name_from}/related_to/{name_to}"
        )

        response.raise_for_status()

        console.print(
            f"Successfully removed relationship between {name_from} and {name_to}.",
            style="bold green",
        )

    def create_collection(
        self,
        name: str,
        description: str,
    ):
        """
        Create a collection.

        Arguments
        ---------
        name : str
            The name of the collection.
        description : str
            The description of the collection.
        """

        response = self.http.put(
            f"/relationships/collection/{name}", json={"description": description}
        )

        response.raise_for_status()

        console.print(f"Successfully created collection {name}.", style="bold green")

    def add_to_collection(self, name: str, product: str):
        """
        Add a product to a collection.

        Arguments
        ---------
        name : str
            The name of the collection.
        product : str
            The name of the product.
        """

        response = self.http.put(f"/relationships/collection/{name}/{product}")

        response.raise_for_status()

        console.print(
            f"Successfully added product {product} to collection {name}.",
            style="bold green",
        )

    def remove_from_collection(self, name: str, product: str):
        """
        Remove a product from a collection.

        Arguments
        ---------
        name : str
            The name of the collection.
        product : str
            The name of the product.
        """

        response = self.http.delete(f"/relationships/collection/{name}/{product}")

        response.raise_for_status()

        console.print(
            f"Successfully removed product {product} from collection {name}.",
            style="bold green",
        )

    def delete_collection(
        self,
        name: str,
    ):
        """
        Delete a collection.

        Arguments
        ---------
        name : str
            The name of the collection.
        """

        response = self.http.delete(f"/relationships/collection/{name}")

        response.raise_for_status()

        console.print(f"Successfully deleted collection {name}.", style="bold green")
