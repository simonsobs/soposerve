"""
A simple command-line utility for uploading files
to the example SOPO server running at 127.0.0.1:8000.
"""

from pathlib import Path

from sopoclient import Client

API_KEY = "TEST_API_KEY"
SERVER_LOCATION = "http://127.0.0.1:8000"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="""Upload a product to the example SOPO server.""",
    )
    parser.add_argument("name", help="The name of the product to create.")
    parser.add_argument("description", help="The description of the product.")
    parser.add_argument(
        "sources", nargs="+", help="The sources (files) to upload.", type=Path
    )

    args = parser.parse_args()

    client = Client(api_key=API_KEY, host=SERVER_LOCATION)

    client.create_product(
        name=args.name,
        description=args.description,
        metadata=None,
        sources=args.sources,
        verbose=True,
    )
