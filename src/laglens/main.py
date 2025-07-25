import asyncio
import time

from config import BINDINGS, CSS
from ping import get_latency_indicator, ping_server
from rich.panel import Panel
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Footer, Header, Static
from world_map import WorldMap

# Initialize the WorldMap instance
world_map = WorldMap(data_file="data/world_countries.json")


class LagLensApp(App):
    """A Textual application to visualize network latency."""

    BINDINGS = BINDINGS
    CSS = CSS

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        ascii_map = Static(id="ascii-map", classes="center-panel")

        yield Header()
        yield Horizontal(
            ascii_map,
            Static(id="ping-results", classes="right-panel"),
        )
        yield Footer()

    def on_mount(self) -> None:
        """Call when the app is mounted."""
        self.servers = [
            "google.com",
            "cloudflare.com",
            "aws.amazon.com",
            "microsoft.com",
            "github.com",
            "youtube.com",
            "baidu.com",
            "bad-host-name-xyz.com",
            "192.0.2.1",
            "openstack.org",
        ]
        self.results_text = "Initializing UI...\n"

        # Initial map update after a short delay to ensure widget sizes are initialized
        self.set_timer(0.5, self.update_world_map)

        asyncio.create_task(self.periodic_ping_updates())

    def update_world_map(self) -> None:
        """Update the world map dynamically based on widget size."""
        map_widget = self.query_one("#ascii-map", Static)
        width = map_widget.size.width
        height = map_widget.size.height

        if width > 0 and height > 0:
            map_text = world_map.draw(columns=width, lines=height)
            map_widget.update(map_text)
        else:
            self.log("Map widget size is not initialized yet.")

    async def periodic_ping_updates(self) -> None:
        """Run update_ping_results every 10 seconds."""
        while True:
            await self.update_ping_results()
            await asyncio.sleep(10)

    async def update_ping_results(self) -> None:
        """Perform pings asynchronously and update the TUI with results."""
        results_text = Text(
            f"--- Last Update: {time.strftime('%H:%M:%S')} ---\n\n", style="bold white"
        )

        tasks = [self.ping_server_async(server) for server in self.servers]
        results = await asyncio.gather(*tasks)

        for server, (latency, indicator_text) in zip(
            self.servers, results, strict=False
        ):
            results_text.append(f"{server:<25}: ")
            results_text.append(indicator_text)
            results_text.append("\n")

        ping_results_widget = self.query_one("#ping-results", Static)
        ping_results_widget.update(
            Panel(results_text, title="Latency Map Data", border_style="dim white")
        )

    async def ping_server_async(self, server: str) -> tuple:
        """Ping a server asynchronously and return latency and indicator text."""
        latency = await asyncio.to_thread(ping_server, server)
        indicator_text = get_latency_indicator(latency)
        return latency, indicator_text

    async def action_quit(self) -> None:
        """Quit the application."""
        self.exit()


if __name__ == "__main__":
    app = LagLensApp()
    app.run()
