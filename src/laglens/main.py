import asyncio
import time

from config.textual_config import BINDINGS, CSS
from ping import get_latency_indicator, ping_server
from rich.panel import Panel
from rich.text import Text
from config.servers import AWS_SERVERS
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
        yield Footer(show_command_palette=False)

    def on_mount(self) -> None:
        """Call when the app is mounted."""
        # self.servers = GLOBAL_SERVERS
        self.servers = AWS_SERVERS
        self.results_text = "Initializing UI...\n"
        self.latest_latencies = {}  # Store latest ping results by server IP

        # Initial map update after a short delay to ensure widget sizes are initialized
        self.set_timer(0.5, self.update_world_map)

        asyncio.create_task(self.periodic_ping_updates())

    def update_world_map(self) -> None:
        """Update the world map dynamically based on widget size."""
        map_widget = self.query_one("#ascii-map", Static)
        width = map_widget.size.width
        height = map_widget.size.height

        if width > 0 and height > 0:
            servers_with_indicators = []
            for server in self.servers:
                indicator = self.get_server_indicator(server)  # "🔴", "🟡", "🟢", etc.
                servers_with_indicators.append(
                    {
                        "latitude": server["latitude"],
                        "longitude": server["longitude"],
                        "indicator": indicator,
                    }
                )

            map_text = world_map.draw(
                columns=width, lines=height, servers=servers_with_indicators
            )
            map_widget.update(map_text)
        else:
            self.log("Map widget size is not initialized yet.")
    def get_server_indicator(self, server) -> str:
        """Get the indicator for a server based on its current latency."""
        latency = self.latest_latencies.get(server["ip"])
        if latency is not None:
            if latency < 100:
                return "🟢"
            elif 100 <= latency <= 300:
                return "🟡"
            else:
                return "🔴"
        return "●"

    async def periodic_ping_updates(self) -> None:
        """Run update_ping_results every 5 seconds."""
        while True:
            await self.update_ping_results()
            await asyncio.sleep(5)

    async def update_ping_results(self) -> None:
        """Perform pings asynchronously and update the TUI with results."""
        results_text = Text(
            f"--- Last Update: {time.strftime('%H:%M:%S')} ---\n\n", style="bold white"
        )

        # Create tasks for pinging servers
        tasks = [self.ping_server_async(server["ip"]) for server in self.servers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for server, result in zip(self.servers, results, strict=False):
            if isinstance(result, Exception):
                # Handle errors gracefully
                results_text.append(f"{server['name']:<25}: Error\n", style="bold red")
            else:
                latency, indicator_text = result
                self.latest_latencies[server["ip"]] = latency
                results_text.append(f"{server['name']:<25}: ")
                results_text.append(indicator_text)
                results_text.append("\n")

        # Update the UI
        ping_results_widget = self.query_one("#ping-results", Static)
        ping_results_widget.update(
            Panel(results_text, title="Latency Map Data", border_style="dim white")
        )

        self.update_world_map()

    async def ping_server_async(self, server: str) -> tuple:
        """Ping a server asynchronously and return latency and indicator text."""
        try:
            latency = await asyncio.to_thread(ping_server, server)
            indicator_text = get_latency_indicator(latency)
            return latency, indicator_text
        except Exception as e:
            self.log(f"Error pinging server {server}: {e}")
            raise

    async def action_quit(self) -> None:
        """Quit the application."""
        self.exit()


if __name__ == "__main__":
    app = LagLensApp()
    app.run()
