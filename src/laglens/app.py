import asyncio
import time
from datetime import datetime
from statistics import LatencyHistory, LatencySparkline

from config.servers import AWS_SERVERS
from config.textual_config import BINDINGS
from ping import get_latency_indicator, ping_server
from rich.panel import Panel
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Footer, Header, Static, Sparkline
from world_map import WorldMap


class LagLensApp(App):
    """A Textual application to visualize network latency."""

    BINDINGS = BINDINGS
    CSS_PATH = "config/laglens.tcss"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.world_map = WorldMap(data_file="data/world_countries.json")
        self.latency_history = LatencyHistory()
        self.sparklines = {}  # Store sparkline instances for each server

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        ascii_map = Static(id="ascii-map", classes="center-panel")

        yield Header()
        yield Horizontal(
            ascii_map,
            ScrollableContainer(
                Static(id="ping-results", classes="right-top-panel"),
                ScrollableContainer(
                    *self._create_server_containers(),
                    id="servers-container",
                    classes="right-bottom-panel"
                ),
                classes="right-panel"
            ),
        )
        yield Footer(show_command_palette=False)

    def _create_server_containers(self):
        """Create individual server containers with stats and sparklines."""
        server_containers = []
        
        for server in AWS_SERVERS:
            server_ip = server["ip"]
            server_name = server["name"]
            
            # Create LatencySparkline instance for this server
            latency_sparkline = LatencySparkline([0.0])
            self.sparklines[server_ip] = latency_sparkline
            
            # Create sparkline widget
            sparkline_widget_id = f"sparkline-{server_ip.replace('.', '-')}"
            sparkline_widget = latency_sparkline.create_sparkline(
                widget_id=sparkline_widget_id,
                widget_classes="server-sparkline"
            )
            
            # Create server container with stats and sparkline
            server_container = Vertical(
                Static(
                    id=f"stats-{server_ip.replace('.', '-')}", 
                    classes="server-stats"
                ),
                sparkline_widget,
                id=f"server-container-{server_ip.replace('.', '-')}",
                classes="individual-server-container"
            )
            
            server_containers.append(server_container)
        
        return server_containers

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

        # Update individual server containers
        self.update_server_containers()
        self.update_world_map()

    def update_server_containers(self) -> None:
        """Update each server's individual container with stats and sparkline."""
        for server in self.servers:
            server_ip = server["ip"]
            server_name = server["name"]
            
            # Get server statistics
            server_stats = self.latency_history.get_statistics(server_ip, window_minutes=60)
            
            # Create stats text for this server
            stats_text = Text(f"{server_name}\n", style="bold white")
            
            if server_stats["avg"] is not None:
                stats_text.append(f"Avg: {server_stats['avg']:.1f}ms\n", style="white")
                stats_text.append(f"Min: {server_stats['min']:.1f}ms\n", style="green")
                stats_text.append(f"Max: {server_stats['max']:.1f}ms\n", style="red")
                stats_text.append(f"Jitter: {server_stats['jitter']:.1f}ms\n", style="yellow")
                stats_text.append(f"Loss: {server_stats['packet_loss']:.1f}%", style="magenta")
                
                # Update sparkline
                self.update_sparkline_for_server(server_ip)
            else:
                stats_text.append("No data available", style="dim")
            
            # Update the stats widget for this server
            try:
                stats_widget_id = f"stats-{server_ip.replace('.', '-')}"
                stats_widget = self.query_one(f"#{stats_widget_id}", Static)
                stats_widget.update(
                    Panel(
                        stats_text, 
                        title=f"{server_name[:15]} Stats", 
                        border_style="dim blue"
                    )
                )
            except Exception as e:
                self.log(f"Failed to update stats for {server_ip}: {e}")

    def update_sparkline_for_server(self, server_ip: str):
        """Update the sparkline widget for a specific server."""
        try:
            sparkline_data = self.latency_history.get_sparkline_data(server_ip, minutes=30)
            
            if server_ip in self.sparklines:
                self.sparklines[server_ip].data = sparkline_data
                
                widget_id = f"sparkline-{server_ip.replace('.', '-')}"
                sparkline_widget = self.query_one(f"#{widget_id}", Sparkline)
                self.sparklines[server_ip].update_sparkline_widget(sparkline_widget)
            
        except Exception as e:
            self.log(f"Failed to update sparkline for {server_ip}: {e}")

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
