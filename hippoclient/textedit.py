"""
The text editor flow for hippo. Uses textual to launch a TUI app and edit
the text associated with a collection or product.
"""

from pathlib import Path

import xxhash
from beanie import PydanticObjectId
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import (
    Button,
    Checkbox,
    Footer,
    Input,
    Label,
    RadioButton,
    RadioSet,
    Select,
    TabbedContent,
    TabPane,
    TextArea,
)

from hippometa import ALL_METADATA

from . import product
from .core import Client


class EditorApp(App):
    CSS_PATH = "textedit.tcss"
    _product_name = reactive("")
    _description = reactive("")
    _sources = reactive(None)
    _metadata = reactive(None)
    _current_version: str
    _projected_version: str
    _version: int = 2
    _drop_sources = []
    _replace_sources = []
    _new_sources = []

    BINDINGS = [
        ("d", "show_tab('details-tab')", "Details"),
        ("s", "show_tab('sources-tab')", "Sources"),
        ("m", "show_tab('metadata-tab')", "Metadata"),
    ]

    def __init__(self, id: PydanticObjectId, client: Client):
        self._object_id = id
        self._client = client

        _product = product.read(client, id)

        self._current_version = _product.version
        self._projected_version = self.project_version()

        super().__init__()

        self._product_name = _product.name
        self._description = _product.description
        self._sources = _product.sources
        self._metadata = _product.metadata

    def compose(self) -> ComposeResult:
        # """Create child widgets for the app."""
        yield Footer()

        with TabbedContent():
            with TabPane("Details", id="details-tab"):
                with Vertical(classes="title"):
                    yield Label("Product Title:", variant="accent")
                    yield Input(
                        value=self._product_name,
                        placeholder="Product title...",
                        id="product-title",
                    )
                with Vertical(classes="description"):
                    yield Label("Product Description:", variant="accent")
                    yield TextArea(
                        text=self._description,
                        language="markdown",
                        id="product-description",
                    )
                with Vertical(classes="versioning"):
                    yield Label("Version Bump:", variant="accent")
                    yield RadioSet(
                        RadioButton("Major"),
                        RadioButton("Minor"),
                        RadioButton("Patch", value=True),
                        id="version",
                    )
                    yield Label(
                        f"{self._current_version} → {self._projected_version}",
                        id="versionproject",
                        variant="success",
                    )
                with Horizontal(classes="save-or-cancel"):
                    yield Button("Save", variant="success", id="save")
                    yield Button("Cancel", variant="error", id="cancel")

            with TabPane("Sources", id="sources-tab"):
                for source in self._sources:
                    with Horizontal(classes="sources existing-source"):
                        with Vertical():
                            yield Label("File Name:", variant="accent")
                            yield Input(
                                value=source.name,
                                placeholder="",
                                id=f"edit-source-name-{source.uuid}",
                            )
                        with Vertical():
                            yield Label("Source Description:", variant="accent")
                            yield Input(
                                value=source.description,
                                placeholder="Description...",
                                id=f"edit-source-desc-{source.uuid}",
                            )
                        with Vertical():
                            yield Label("Is Primary Source?", variant="accent")
                            yield Checkbox(
                                "Primary",
                                classes="primary-source-checkbox",
                                id=f"edit-primary-source-checkbox-{source.uuid}",
                            )
                        with Vertical():
                            yield Label("Delete Source?", variant="accent")
                            yield Checkbox(
                                "Yes",
                                classes="delete-source-checkbox",
                                id=f"delete_source_checkbox_{source.uuid}",
                            )
                with Horizontal(classes="sources new-source"):
                    with Vertical():
                        yield Label("File Path:", variant="accent")
                        yield Input(
                            value=None,
                            placeholder="Path to new source file...",
                            id="new-source-file-path",
                        )
                    with Vertical():
                        yield Label("Source Description:", variant="accent")
                        yield Input(
                            value=None,
                            placeholder="Source description...",
                            id="new-source-file-desc",
                        )
                    with Vertical():
                        yield Label("Is Primary Source?", variant="accent")
                        yield Checkbox(
                            "Primary",
                            classes="primary-source-checkbox",
                            id="new-primary-source-checkbox",
                        )
                with Horizontal(classes="save-or-cancel"):
                    yield Button("Save", variant="success", id="save")
                    yield Button("Cancel", variant="error", id="cancel")

            with TabPane("Metadata", id="metadata-tab"):
                class_schema = self._metadata.model_json_schema()
                class_title = class_schema["title"]
                class_fields = class_schema["properties"]
                yield Label("Metadata Type:", variant="primary")
                metadata_options = []
                for v in ALL_METADATA:
                    if v is None:
                        continue
                    schema = v.model_json_schema()
                    name = schema["title"]
                    metadata_options.append(name)
                yield Select.from_values(metadata_options, value=class_title)
                with Horizontal(classes="metadata-inputs-container"):
                    for field_key, field_data in class_fields.items():
                        if (
                            field_key == "metadata_type"
                            or "additionalProperties" in field_data
                        ):
                            continue
                        with Vertical():
                            yield Label(field_data["title"], variant="accent")
                            if "enum" in field_data:
                                yield Select.from_values(
                                    field_data["enum"],
                                    value=getattr(self._metadata, field_key),
                                )
                            else:
                                yield Input(
                                    value=getattr(self._metadata, field_key),
                                    placeholder=f"Enter {field_data['title'].lower()}...",
                                )
                with Horizontal(classes="save-or-cancel"):
                    yield Button("Save", variant="success", id="save")
                    yield Button("Cancel", variant="error", id="cancel")

    def action_show_tab(self, tab: str) -> None:
        """Switch to a new tab."""
        self.get_child_by_type(TabbedContent).active = tab

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
        if event.radio_set.id == "version":
            self._version = {"Major": 0, "Minor": 1, "Patch": 2}[
                event.pressed.label.plain
            ]
            self.update_projected_version()

    @on(Checkbox.Changed)
    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox.has_class("delete-source-checkbox"):
            split_id = event.checkbox.id.split("_")
            uuid = split_id[len(split_id) - 1]
            toggled_source = [source for source in self._sources if source.uuid == uuid]
            if toggled_source[0].name in self._drop_sources:
                self._drop_sources.remove(toggled_source[0].name)
            else:
                self._drop_sources.append(toggled_source[0].name)
            return
        # selected_checkbox_id = None
        # if event.checkbox.has_focus:
        #     selected_checkbox_id = event.checkbox.id
        # new_source_checkbox = self.query_one("#new-primary-source-checkbox")
        # existing_source_checkbox = self.query_one("#edit-primary-source-checkbox")
        # if new_source_checkbox.has_focus and existing_source_checkbox.value == True:
        #     existing_source_checkbox.value = False
        # if existing_source_checkbox.has_focus and new_source_checkbox.value == True:
        #     new_source_checkbox.value = False

    def get_new_source(self):
        file_path = self.query_one("#new-source-file-path").value
        source_desc = self.query_one("#new-source-file-desc").value
        if file_path:
            source = Path(file_path)
            with source.open("rb") as file:
                file_info = {
                    "name": source.name,
                    "size": source.stat().st_size,
                    "checksum": f"xxh64:{xxhash.xxh64(file.read()).hexdigest()}",
                    "description": source_desc,
                }
                return [file_info]
        else:
            return []

    def get_replace_sources(self):
        source_data = []
        for source in self._sources:
            source_name = self.query_one(f"#edit-source-name-{source.uuid}").value
            source_desc = self.query_one(f"#edit-source-desc-{source.uuid}").value
            is_set_to_delete = self.query_one(
                f"#delete_source_checkbox_{source.uuid}"
            ).value
            if (
                source_name != source.name or source_desc != source.description
            ) and is_set_to_delete is False:
                source_metadata = {
                    "name": source_name,
                    "size": source.size,
                    "checksum": source.checksum,
                    "description": source.description,
                }
                source_data.append(source_metadata)
        return source_data

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "save":
            product.update(
                self._client,
                self._object_id,
                self.query_one("#product-title").value,
                self.query_one("#product-description").text,
                self._version,
                None,
                # self._metadata,
                self.get_new_source(),
                self.get_replace_sources(),
                self._drop_sources,
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
