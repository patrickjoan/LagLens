"""Server management functionality for LagLens application.
"""

from statistics import LatencySparkline

from logger import get_logger
from textual.containers import ScrollableContainer, Vertical
from textual.widgets import Input, Static


class ServerManager:
    """Manages server operations including adding, validation, and container creation."""

    def __init__(self, app):
        """Initialize with reference to the main app."""
        self.app = app
        self.logger = get_logger("server_manager")

    def validate_server_data(self, name: str, ip: str, latitude_str: str, longitude_str: str) -> tuple[bool, str, float, float]:
        """Validate server input data. Returns (is_valid, error_message, latitude, longitude)."""
        # Validate required fields
        if not all([name, ip, latitude_str, longitude_str]):
            return False, "Please fill in all required fields (Name, IP, Latitude, Longitude)", 0.0, 0.0

        # Validate and convert coordinates
        try:
            latitude = float(latitude_str)
            longitude = float(longitude_str)

            # Basic coordinate validation
            if not (-90 <= latitude <= 90):
                return False, "Latitude must be between -90 and 90", 0.0, 0.0
            if not (-180 <= longitude <= 180):
                return False, "Longitude must be between -180 and 180", 0.0, 0.0

        except ValueError:
            return False, "Latitude and Longitude must be valid numbers", 0.0, 0.0

        # Check if server already exists
        if any(server['ip'] == ip for server in self.app.runtime_servers):
            return False, f"Server with IP {ip} already exists", 0.0, 0.0

        if any(server['name'] == name for server in self.app.runtime_servers):
            return False, f"Server with name '{name}' already exists", 0.0, 0.0

        return True, "", latitude, longitude

    def add_server(self, name: str, ip: str, latitude: float, longitude: float, city: str) -> dict:
        """Add a new server to the runtime list."""
        new_server = {
            "name": name,
            "ip": ip,
            "latitude": latitude,
            "longitude": longitude,
            "city": city if city else "Unknown Location"
        }

        self.app.runtime_servers.append(new_server)
        self.app.latency_history.history[ip] = []

        return new_server

    def get_form_data(self) -> tuple[str, str, str, str, str]:
        """Extract data from the form inputs."""
        name = self.app.query_one("#server-name", Input).value.strip()
        ip = self.app.query_one("#server-ip", Input).value.strip()
        latitude_str = self.app.query_one("#server-latitude", Input).value.strip()
        longitude_str = self.app.query_one("#server-longitude", Input).value.strip()
        city = self.app.query_one("#server-city", Input).value.strip()

        return name, ip, latitude_str, longitude_str, city

    def clear_form(self):
        """Clear all form inputs."""
        self.app.query_one("#server-name", Input).value = ""
        self.app.query_one("#server-ip", Input).value = ""
        self.app.query_one("#server-latitude", Input).value = ""
        self.app.query_one("#server-longitude", Input).value = ""
        self.app.query_one("#server-city", Input).value = ""

    def create_server_container(self, server: dict) -> Vertical:
        """Create a single server container with stats and sparkline."""
        server_ip = server["ip"]
        server_name = server["name"]

        # Only create new sparkline if it doesn't exist
        if server_ip not in self.app.sparklines:
            latency_sparkline = LatencySparkline([0.0])
            self.app.sparklines[server_ip] = latency_sparkline
        else:
            # Use existing sparkline data
            latency_sparkline = self.app.sparklines[server_ip]

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

        return server_container

    def add_new_server_container(self, new_server: dict):
        """Add a new server container to the UI without refreshing existing ones."""
        try:
            servers_container = self.app.query_one("#servers-container", ScrollableContainer)

            server_ip = new_server["ip"]

            if server_ip not in self.app.sparklines:
                latency_sparkline = LatencySparkline([0.0])
                self.app.sparklines[server_ip] = latency_sparkline

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
            self.logger.error(f"Error adding server container: {e}")
            self.app.log(f"Error adding server container: {e}")
