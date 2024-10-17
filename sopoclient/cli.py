"""
A CLI interface to the SOPO client.
"""

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
def collection_read(id: str):
    """
    Read the information of a collection by its name.
    """
    global CLIENT, CONSOLE

    collection = sc.collections.read(client=CLIENT, id=id)

    table = helper.render_product_metadata_list(collection.products)

    CONSOLE.print(collection.name + "\n", style="bold underline color(3)")
    CONSOLE.print(rich.markdown.Markdown(collection.description.strip("\n")))
    CONSOLE.print("\n" + "Products" + "\n", style="bold color(2)")
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
    from core import ClientSettings

    settings = ClientSettings()

    global CLIENT, APP

    CLIENT = sc.Client(
        api_key=settings.api_key, host=settings.host, verbose=settings.verbose
    )

    APP()
