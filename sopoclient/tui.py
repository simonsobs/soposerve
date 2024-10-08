from textual.app import App, ComposeResult
from textual.widgets import DirectoryTree, Footer, Header, Input, TextArea


class ProductBuilderApp(App):
    """
    A textual app to build a product upload. Can be modified in the future
    for building an 'updater'.
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Input()
        yield TextArea()
        yield DirectoryTree(".")
        yield Footer()


if __name__ == "__main__":
    app = ProductBuilderApp()
    app.run()
