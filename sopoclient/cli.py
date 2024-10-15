"""
A CLI interface to the SOPO client.
"""

import os

import rich
import typer

import sopoclient as sc

from . import helper

CLIENT: sc.Client
CONSOLE = rich.console.Console()

# Meta-setup
APP = typer.Typer()
product_app = typer.Typer()
APP.add_typer(product_app, name="product")
collection_app = typer.Typer()
APP.add_typer(collection_app, name="collection")


@product_app.command("read")
def product_read(id: str):
    """
    Read the information of a product by its ID. You can find the relationship
    between product names and IDs through the product search command.
    """
    global CLIENT, CONSOLE

    product = sc.product.read(client=CLIENT, id=id)

    CONSOLE.print(product)


@product_app.command("delete")
def product_delete(id: str):
    """
    Delete a product by its ID.
    """
    global CLIENT
    return sc.product.delete(client=CLIENT, id=id)


@product_app.command("search")
def product_search(text: str):
    """
    Search for products by name.
    """
    global CLIENT, CONSOLE

    response = sc.product.search(client=CLIENT, text=text)

    table = helper.render_product_metadata_list(response)

    CONSOLE.print(table)


@collection_app.command("read")
def collection_read(name: str):
    """
    Read the information of a collection by its name.
    """
    global CLIENT, CONSOLE

    collection = sc.collections.read(client=CLIENT, name=name)

    table = helper.render_product_metadata_list(collection.products)

    CONSOLE.print(collection.name + "\n", style="bold underline color(3)")
    CONSOLE.print(collection.description.strip("\n") + "\n")
    CONSOLE.print("Products" + "\n", style="bold color(2)")
    CONSOLE.print(table)


@collection_app.command("search")
def collection_search(name: str):
    """
    Read the information of a collection by its name.
    """
    global CLIENT, CONSOLE

    collections = sc.collections.search(client=CLIENT, name=name)

    table = helper.render_collection_metadata_list(collections)

    CONSOLE.print(table)


def main():
    global CLIENT, APP

    API_KEY = os.getenv("SOPO_API_KEY")
    HOST = os.getenv("SOPO_HOST")
    SOPO_VERBOSE = bool(os.getenv("SOPO_VERBOSE"))

    CLIENT = sc.Client(api_key=API_KEY, host=HOST, verbose=SOPO_VERBOSE)

    APP()
