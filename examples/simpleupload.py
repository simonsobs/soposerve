"""
A simple command-line utility for uploading files
to the example SOPO server running at 127.0.0.1:8000.
"""

import os

import requests
import xxhash

SERVER_LOCATION = "http://127.0.0.1:8000"


def create_user(username: str):
    # We don't care about the return value here, as
    # we won't bother with the API key.
    requests.put(
        SERVER_LOCATION + f"/users/create/{username}", json={"privileges": [0, 1, 2]}
    )

    return


def process_source(source: str):
    with open(source, "rb") as file:
        return {
            "name": source,
            "size": os.path.getsize(source),
            "checksum": f"xxh64:{xxhash.xxh64(file.read()).hexdigest()}",
        }


def create_product(username: str, name: str, description: str, sources: list[str]):
    response = requests.put(
        SERVER_LOCATION + f"/product/create/{name}",
        json={
            "description": description,
            "sources": [process_source(s) for s in sources],
        },
    )

    if response.status_code != 200:
        print("Failed to create product.")
        print(response.json())
        return

    presigned = response.json()["upload_urls"]

    for source in sources:
        with open(source, "rb") as file:
            requests.put(presigned[source], data=file)

    return


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="""
            Upload a file to the example SOPO server. Your username
            doesn't matter, as it's created when you try to upload
            a file.
        """,
    )
    parser.add_argument("username", help="The username to authenticate with.")
    parser.add_argument("name", help="The name of the product to create.")
    parser.add_argument("description", help="The description of the product.")
    parser.add_argument("sources", nargs="+", help="The sources (files) to upload.")

    args = parser.parse_args()

    create_user(args.username)
    create_product(args.username, args.name, args.description, args.sources)
