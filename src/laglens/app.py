import asyncio
import time
from datetime import datetime
from statistics import LatencyHistory, TrendWidget

from config.servers import AWS_SERVERS
from config.textual_config import BINDINGS
from ping import get_latency_indicator, ping_server
from rich.panel import Panel
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Static
from world_map import WorldMap


class LagLensApp(App):
    """A Textual application to visualize network latency."""

    BINDINGS = BINDINGS
    CSS_PATH = "config/laglens.tcss"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.world_map = WorldMap(data_file="data/world_countries.json")
        self.latency_history = LatencyHistory()
        self.trend_widget = TrendWidget(self.latency_history)

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        ascii_map = Static(id="ascii-map", classes="center-panel")

        yield Header()
        yield Horizontal(
            ascii_map,
            Vertical(
                Static(id="ping-results"),
                Static(id="statistics", classes="right-bottom-panel"),
            ),
        )
        yield Footer(show_command_palette=False)

    def on_mount(self) -> None:
        """Call when the app is mounted."""
        self.servers = AWS_SERVERS
        self.results_text = "Initializing UI...\n"
        self.latest_latencies = {}

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
                indicator = self.get_server_indicator(server)
                servers_with_indicators.append(
                    {
                        "latitude": server["latitude"],
                        "longitude": server["longitude"],
                        "indicator": indicator,
                    }
                )

            map_text = self.world_map.draw(
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
        current_time = datetime.now()

        results_text = Text(
            f"--- Last Update: {time.strftime('%H:%M:%S')} ---\n\n", style="bold white"
        )

        # Create tasks for pinging servers
        tasks = [self.ping_server_async(server["ip"]) for server in self.servers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for server, result in zip(self.servers, results, strict=False):
            server_ip = server["ip"]

            if isinstance(result, Exception):
                self.latency_history.add_measurement(server_ip, None, current_time)
                results_text.append(f"{server['name']:<25}: Error\n", style="bold red")
            else:
                latency, indicator_text = result
                self.latest_latencies[server_ip] = latency

                self.latency_history.add_measurement(server_ip, latency, current_time)

                results_text.append(f"{server['name']:<25}: ")
                results_text.append(indicator_text)
                results_text.append("\n")

        # Update the UI
        ping_results_widget = self.query_one("#ping-results", Static)
        ping_results_widget.update(
            Panel(results_text, title="Latency Results", border_style="dim white")
        )

        self.update_statistics_panel()

        self.update_world_map()

    def update_statistics_panel(self) -> None:
        """Update the statistics panel with current server statistics."""
        stats_text = Text("--- Server Statistics (Last Hour) ---\n\n", style="bold white")

        for server in self.servers:
            server_ip = server["ip"]
            server_stats = self.latency_history.get_statistics(server_ip, window_minutes=60)

            stats_text.append(f"{server['name'][:20]:<20}\n", style="bold white")

            if server_stats["avg"] is not None:
                stats_text.append(f"  Avg: {server_stats['avg']:.1f}ms\n", style="white")
                stats_text.append(f"  Min: {server_stats['min']:.1f}ms\n", style="green")
                stats_text.append(f"  Max: {server_stats['max']:.1f}ms\n", style="red")
                stats_text.append(f"  Jitter: {server_stats['jitter']:.1f}ms\n", style="yellow")
                stats_text.append(f"  Loss: {server_stats['packet_loss']:.1f}%\n", style="magenta")

                # Add trend sparkline
                trend = self.trend_widget.render_trend_graph(server_ip, minutes=30)
                stats_text.append("  Trend: ")
                stats_text.append(trend)
                stats_text.append("\n")
            else:
                stats_text.append("  No data available\n", style="dim")

            stats_text.append("\n")

        stats_widget = self.query_one("#statistics", Static)
        stats_widget.update(
            Panel(stats_text, title="Statistics", border_style="dim white")
        )

    async def ping_server_async(self, server: str) -> tuple:
        """Ping a server asynchronously and return latency and indicator text."""
        try:
            latency = await asyncio.to_thread(ping_server, server, timeout=10)
            indicator_text = get_latency_indicator(latency)
            return latency, indicator_text
        except Exception as e:
            self.log(f"Error pinging server {server}: {e}")
            raise

    async def action_quit(self) -> None:
        """Quit the application."""
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
                "recent_measurements": self.latency_history._get_recent_data(server_ip, 60)
            }

        import json
        with open(filename, 'w') as f:
            json.dump(all_stats, f, indent=2, default=str)

        self.notify(f"Statistics saved to {filename}")
