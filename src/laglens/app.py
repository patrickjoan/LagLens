import asyncio
import time
from datetime import datetime
from statistics import LatencyHistory, LatencySparkline

from config.servers import AWS_SERVERS
from config.config import BINDINGS
from ping import get_latency_indicator, ping_server
from rich.panel import Panel
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.widgets import Footer, Header, Sparkline, Static, Input, Button, Label
from textual.message import Message
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
        self.world_map = WorldMap(data_file="data/world_countries.json")
        self.latency_history = LatencyHistory()
        self.sparklines = {}
        self.runtime_servers = list(AWS_SERVERS)

    @property 
    def servers(self):
        """Return current runtime servers."""
        return self.runtime_servers

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        ascii_map = Static(id="ascii-map", classes="map-panel")
        
        add_server_form = self._create_add_server_form()

        yield Header()
        yield Horizontal(
            Vertical(
                ascii_map,
                add_server_form,
                classes="center-panel"
            ),
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
        self.clear_form()

    def _create_add_server_form(self) -> Vertical:
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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "add-server-btn":
            self.add_new_server()
        elif event.button.id == "clear-form-btn":
            self.clear_form()

    def add_new_server(self) -> None:
        """Add a new server from form data."""
        try:
            name = self.query_one("#server-name", Input).value.strip()
            ip = self.query_one("#server-ip", Input).value.strip()
            latitude_str = self.query_one("#server-latitude", Input).value.strip()
            longitude_str = self.query_one("#server-longitude", Input).value.strip()
            city = self.query_one("#server-city", Input).value.strip()

            if not all([name, ip, latitude_str, longitude_str]):
                self.notify("Please fill in all required fields (Name, IP, Latitude, Longitude)", severity="error")
                return

            try:
                latitude = float(latitude_str)
                longitude = float(longitude_str)
                
                if not (-90 <= latitude <= 90):
                    self.notify("Latitude must be between -90 and 90", severity="error")
                    return
                if not (-180 <= longitude <= 180):
                    self.notify("Longitude must be between -180 and 180", severity="error")
                    return
                    
            except ValueError:
                self.notify("Latitude and Longitude must be valid numbers", severity="error")
                return

            if any(server['ip'] == ip for server in self.runtime_servers):
                self.notify(f"Server with IP {ip} already exists", severity="error")
                return

            if any(server['name'] == name for server in self.runtime_servers):
                self.notify(f"Server with name '{name}' already exists", severity="error")
                return

            new_server = {
                "name": name,
                "ip": ip,
                "latitude": latitude,
                "longitude": longitude,
                "city": city if city else f"Unknown Location"
            }

            self.runtime_servers.append(new_server)

            self.latency_history.history[ip] = []

            self._refresh_server_containers()

            self.clear_form()

            self.notify(f"Successfully added server: {name} ({ip})", severity="information")
            self.log(f"Added new server: {new_server}")

        except Exception as e:
            self.notify(f"Error adding server: {str(e)}", severity="error")
            self.log(f"Error adding server: {e}")

    def clear_form(self) -> None:
        """Clear all form inputs."""
        self.query_one("#server-name", Input).value = ""
        self.query_one("#server-ip", Input).value = ""
        self.query_one("#server-latitude", Input).value = ""
        self.query_one("#server-longitude", Input).value = ""
        self.query_one("#server-city", Input).value = ""

    def _refresh_server_containers(self) -> None:
        """Refresh the server containers to include newly added servers."""
        try:
            servers_container = self.query_one("#servers-container", ScrollableContainer)
            
            new_server = self.runtime_servers[-1]
            server_ip = new_server["ip"]
            server_name = new_server["name"]
            
            if server_ip not in self.sparklines:
                latency_sparkline = LatencySparkline([0.0])
                self.sparklines[server_ip] = latency_sparkline
                
                sparkline_widget_id = f"sparkline-{server_ip.replace('.', '-')}"
                sparkline_widget = latency_sparkline.create_sparkline(
                    widget_id=sparkline_widget_id, widget_classes="server-sparkline"
                )

                server_container = Vertical(
                    Static(
                        id=f"stats-{server_ip.replace('.', '-')}", classes="server-stats"
                    ),
                    sparkline_widget,
                    id=f"server-container-{server_ip.replace('.', '-')}",
                    classes="individual-server-container",
                )
                
                servers_container.mount(server_container)
                
        except Exception as e:
            self.log(f"Error refreshing server containers: {e}")

    def _create_server_containers(self):
        """Create individual server containers with stats and sparklines."""
        server_containers = []

        for server in self.runtime_servers:
            server_ip = server["ip"]
            server_name = server["name"]

            # Only create new sparkline if it doesn't exist
            if server_ip not in self.sparklines:
                latency_sparkline = LatencySparkline([0.0])
                self.sparklines[server_ip] = latency_sparkline
            else:
                # Use existing sparkline data
                latency_sparkline = self.sparklines[server_ip]

            sparkline_widget_id = f"sparkline-{server_ip.replace('.', '-')}"
            sparkline_widget = latency_sparkline.create_sparkline(
                widget_id=sparkline_widget_id, widget_classes="server-sparkline"
            )

            server_container = Vertical(
                Static(
                    id=f"stats-{server_ip.replace('.', '-')}", classes="server-stats"
                ),
                sparkline_widget,
                id=f"server-container-{server_ip.replace('.', '-')}",
                classes="individual-server-container",
            )

            server_containers.append(server_container)

        return server_containers

    def on_mount(self) -> None:
        """Call when the app is mounted."""
        self.results_text = "Initializing UI...\n"
        self.latest_latencies = {}

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
            server_name = server["name"]

            if isinstance(result, Exception):
                self.latency_history.add_measurement(server_ip, None, current_time)
                # Use fixed width for server name and right-align the status
                results_text.append(f"{server_name:<20} : ", style="white")
                results_text.append("Error\n", style="bold red")
            else:
                latency, indicator_text = result
                self.latest_latencies[server_ip] = latency
                self.latency_history.add_measurement(server_ip, latency, current_time)

                # Format: server_name (left-aligned, 20 chars) : indicator + latency
                results_text.append(f"{server_name:<20} : ", style="white")
                results_text.append(indicator_text)
                results_text.append("\n")

        ping_results_widget = self.query_one("#ping-results", Static)
        ping_results_widget.update(
            Panel(results_text, title="Latency Results", border_style="dim white")
        )

        self.update_server_containers()
        self.update_world_map()

    def update_server_containers(self) -> None:
        """Update each server's individual container with stats and sparkline."""
        for server in self.servers:
            server_ip = server["ip"]
            server_name = server["name"]

            server_stats = self.latency_history.get_statistics(
                server_ip, window_minutes=60
            )

            stats_text = Text(f"{server_name}\n", style="bold white")

            if server_stats["avg"] is not None:
                stats_text.append(f"Avg: {server_stats['avg']:.1f}ms\n", style="white")
                stats_text.append(f"Min: {server_stats['min']:.1f}ms\n", style="white")
                stats_text.append(f"Max: {server_stats['max']:.1f}ms\n", style="white")
                stats_text.append(
                    f"Jitter: {server_stats['jitter']:.1f}ms\n", style="yellow"
                )
                stats_text.append(
                    f"Loss: {server_stats['packet_loss']:.1f}%", style="magenta"
                )

                self.update_sparkline_for_server(server_ip)
            else:
                stats_text.append("No data available", style="dim")

            try:
                stats_widget_id = f"stats-{server_ip.replace('.', '-')}"
                stats_widget = self.query_one(f"#{stats_widget_id}", Static)
                stats_widget.update(
                    Panel(
                        stats_text,
                        title=f"{server_name[:15]} Stats",
                        border_style="dim white",
                    )
                )
            except Exception as e:
                self.log(f"Failed to update stats for {server_ip}: {e}")

    def update_sparkline_for_server(self, server_ip: str):
        """Update the sparkline widget for a specific server."""
        try:
            sparkline_data = self.latency_history.get_sparkline_data(
                server_ip, minutes=30
            )

            # Check if sparkline exists, if not skip (new server with no data yet)
            if server_ip in self.sparklines:
                self.sparklines[server_ip].data = sparkline_data

                widget_id = f"sparkline-{server_ip.replace('.', '-')}"
                try:
                    sparkline_widget = self.query_one(f"#{widget_id}", Sparkline)
                    self.sparklines[server_ip].update_sparkline_widget(sparkline_widget)
                except Exception as widget_error:
                    self.log(f"Sparkline widget not found for {server_ip}: {widget_error}")

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
                "recent_measurements": self.latency_history._get_recent_data(
                    server_ip, 60
                ),
            }

        import json

        with open(filename, "w") as f:
            json.dump(all_stats, f, indent=2, default=str)

        self.notify(f"Statistics saved to {filename}")
