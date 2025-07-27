"""
Form components for LagLens application.
"""

from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.widgets import Button, Input, Label


class AddServerForm:
    """Form for adding new servers to the monitoring list."""
    
    @staticmethod
    def create() -> Vertical:
        """Create the add server form for the bottom center panel."""
        return Vertical(
            ScrollableContainer(
                Horizontal(
                    Label("Name:", classes="form-label"),
                    Input(placeholder="e.g., us-west-1", id="server-name", classes="form-input"),
                    classes="form-row"
                ),
                Horizontal(
                    Label("IP Address:", classes="form-label"),
                    Input(placeholder="e.g., 192.168.1.1", id="server-ip", classes="form-input"),
                    classes="form-row"
                ),
                Horizontal(
                    Label("Latitude:", classes="form-label"),
                    Input(placeholder="e.g., 37.7749", id="server-latitude", classes="form-input"),
                    classes="form-row"
                ),
                Horizontal(
                    Label("Longitude:", classes="form-label"),
                    Input(placeholder="e.g., -122.4194", id="server-longitude", classes="form-input"),
                    classes="form-row"
                ),
                Horizontal(
                    Label("City:", classes="form-label"),
                    Input(placeholder="e.g., San Francisco, CA", id="server-city", classes="form-input"),
                    classes="form-row"
                ),
                Horizontal(
                    Button("Add Server", id="add-server-btn", classes="form-button"),
                    Button("Clear", id="clear-form-btn", classes="form-button"),
                    classes="form-row"
                ),
                classes="add-server-form"
            ),
            id="bottom-center",
            classes="bottom-center-panel"
        )
