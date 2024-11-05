"""
The text editor flow for hippo. Uses textual to launch a TUI app and edit
the text associated with a collection or product.
"""

from beanie import PydanticObjectId
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Button, Input, Label, RadioButton, RadioSet, TextArea

from . import product
from .core import Client


class EditorApp(App):
    _product_name = reactive("")
    _description = reactive("")
    _current_version: str
    _projected_version: str
    _version: int = 2

    def __init__(self, id: PydanticObjectId, client: Client):
        self._object_id = id
        self._client = client

        _product = product.read(client, id)

        self._current_version = _product.version
        self._projected_version = self.project_version()

        super().__init__()

        self._product_name = _product.name
        self._description = _product.description

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        with Vertical():
            yield Input(value=self._product_name, placeholder="Product Title:")
            with Horizontal():
                yield TextArea(text=self._description, language="markdown")
                with Vertical():
                    yield Label("Version Bump:")
                    yield RadioSet(
                        RadioButton("Major"),
                        RadioButton("Minor"),
                        RadioButton("Patch", value=True),
                        id="version",
                    )
                    yield Label(
                        f"{self._current_version} → {self._projected_version}",
                        id="versionproject",
                    )
                    yield Button("Save", variant="success", id="save")
                    yield Button("Cancel", variant="error", id="cancel")

    def project_version(self):
        split = [int(x) for x in self._current_version.split(".")]
        split[self._version] = split[self._version] + 1
        for index in range(self._version + 1, len(split)):
            split[index] = 0
        return ".".join([f"{x}" for x in split])

    def update_projected_version(self):
        self._projected_version = self.project_version()
        version_label = self.query_one("#versionproject")
        version_label.update(f"{self._current_version} → {self._projected_version}")

    @on(RadioSet.Changed)
    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Handle radio set changes."""
        self._version = {"Major": 0, "Minor": 1, "Patch": 2}[event.pressed.label.plain]
        self.update_projected_version()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "save":
            product.update(
                self._client,
                self._object_id,
                self.query_one(Input).value,
                self.query_one(TextArea).text,
                self._version,
            )
            exit(0)
        elif event.button.id == "cancel":
            exit(0)
        else:
            raise AttributeError(f"Unknown button pressed: {event.button.id}")


def edit_product(client: Client, id: PydanticObjectId):
    """
    Edit the text of a product. This downloads the metadata for the product,
    and then launches a text editor to edit the text. Once the text is saved,
    the updated metadata is uploaded (if changed).
    """

    app = EditorApp(id, client)
    app.run()
