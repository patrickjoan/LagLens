import asyncio
import json
from datetime import datetime
from statistics import LatencyHistory

from config.config import BINDINGS
from config.servers import AWS_SERVERS
from logger import get_logger
from ping import get_latency_indicator, ping_server
from server_manager import ServerManager
from textual.app import App, ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.widgets import Button, Footer, Header, Input, Static
from ui.forms import AddServerForm
from ui_updater import UIUpdater
from world_map import WorldMap


class LagLensApp(App):
    """A Textual application to visualize network latency."""

    BINDINGS = BINDINGS
    CSS_PATH = "config/laglens.tcss"

    def __init__(self, **kwargs):
        """Initialize the main application.

        Args:
            **kwargs: Arbitrary keyword arguments passed to the superclass.

        Attributes:
            world_map (WorldMap): Instance for displaying the world map.
            latency_history (LatencyHistory): Tracks latency data over time.
            sparklines (dict): Stores sparkline instances for each server.

        """
        super().__init__(**kwargs)
        self.logger = get_logger("app")
        self.world_map = WorldMap(data_file="data/world_countries.json")
        self.latency_history = LatencyHistory()
        self.sparklines = {}
        self.runtime_servers = list(AWS_SERVERS)

        # Initialize managers
        self.server_manager = ServerManager(self)
        self.ui_updater = UIUpdater(self)

    @property
    def servers(self):
        """Return current runtime servers."""
        return self.runtime_servers

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        ascii_map = Static(id="ascii-map", classes="map-panel")

        add_server_form = AddServerForm.create()

        yield Header()
        yield Horizontal(
            Vertical(ascii_map, add_server_form, classes="center-panel"),
            ScrollableContainer(
                Static(id="ping-results", classes="right-top-panel"),
                ScrollableContainer(
                    *self._create_server_containers(),
                    id="servers-container",
                    classes="right-bottom-panel",
                ),
                classes="right-panel",
            ),
        )
        yield Footer(show_command_palette=False)

    def action_focus_add_server(self) -> None:
        """Focus on the add server form."""
        try:
            name_input = self.query_one("#server-name", Input)
            name_input.focus()
        except Exception:
            pass

    def action_clear_form(self) -> None:
        """Clear the add server form."""
        self.server_manager.clear_form()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "add-server-btn":
            self.add_new_server()
        elif event.button.id == "clear-form-btn":
            self.clear_form()

    def add_new_server(self) -> None:
        """Add a new server from form data."""
        try:
            name, ip, latitude_str, longitude_str, city = (
                self.server_manager.get_form_data()
            )

            is_valid, error_msg, latitude, longitude = (
                self.server_manager.validate_server_data(
                    name, ip, latitude_str, longitude_str
                )
            )

            if not is_valid:
                self.notify(error_msg, severity="error")
                return

            new_server = self.server_manager.add_server(
                name, ip, latitude, longitude, city
            )
            self.server_manager.add_new_server_container(new_server)
            self.server_manager.clear_form()

            self.notify(
                f"Successfully added server: {name} ({ip})", severity="information"
            )
            self.logger.info(f"Added new server: {new_server}")

        except Exception as e:
            self.notify(f"Error adding server: {str(e)}", severity="error")
            self.logger.error(f"Error adding server: {e}", exc_info=True)

    def clear_form(self) -> None:
        """Clear all form inputs."""
        self.server_manager.clear_form()

    def _create_server_containers(self):
        """Create individual server containers with stats and sparklines."""
        return [
            self.server_manager.create_server_container(server)
            for server in self.runtime_servers
        ]

    def on_mount(self) -> None:
        """Call when the app is mounted."""
        self.results_text = "Initializing UI...\n"
        self.latest_latencies = {}

        self.set_timer(0.5, self.update_world_map)

        asyncio.create_task(self.periodic_ping_updates())

    def update_world_map(self) -> None:
        """Update the world map dynamically based on widget size."""
        self.ui_updater.update_world_map()

    def get_server_indicator(self, server) -> str:
        """Get the indicator for a server based on its current latency."""
        return self.ui_updater.get_server_indicator(server)

    async def periodic_ping_updates(self) -> None:
        """Run update_ping_results every 5 seconds."""
        while True:
            await self.ui_updater.update_ping_results()
            await asyncio.sleep(5)

    async def gather_ping_results(self, tasks):
        """Gather ping results from async tasks."""
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def update_ping_results(self) -> None:
        """Perform pings asynchronously and update the TUI with results."""
        await self.ui_updater.update_ping_results()

    def update_server_containers(self) -> None:
        """Update each server's individual container with stats and sparkline."""
        self.ui_updater.update_server_containers()

    def update_sparkline_for_server(self, server_ip: str):
        """Update the sparkline widget for a specific server."""
        self.ui_updater.update_sparkline_for_server(server_ip)

    async def ping_server_async(self, server: str) -> tuple:
        """Ping a server asynchronously and return latency and indicator text."""
        try:
            latency = await asyncio.to_thread(ping_server, server, timeout=10)
            indicator_text = get_latency_indicator(latency)
            return latency, indicator_text
        except Exception as e:
            self.logger.error(f"Error pinging server {server}: {e}")
            raise

    async def action_quit(self) -> None:
        """Quit the application."""
        self.logger.info("Application quit requested")
        self.exit()

    def action_save_statistics(self) -> None:
        """Save current statistics to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"laglens_stats_{timestamp}.json"

        all_stats = {}
        for server in self.servers:
            server_ip = server["ip"]
            all_stats[server["name"]] = {
                "ip": server_ip,
                "statistics": self.latency_history.get_statistics(server_ip),
                "recent_measurements": self.latency_history._get_recent_data(
                    server_ip, 60
                ),
            }

        try:
            with open(filename, "w") as f:
                json.dump(all_stats, f, indent=2, default=str)

            self.logger.info(f"Statistics saved to {filename}")
            self.notify(f"Statistics saved to {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save statistics: {e}")
            self.notify(f"Failed to save statistics: {e}", severity="error")
