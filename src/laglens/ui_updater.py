"""UI update handlers for LagLens application.
"""

import time
from datetime import datetime

from laglens.logger import get_logger
from rich.panel import Panel
from rich.text import Text
from textual.widgets import Sparkline, Static


class UIUpdater:
    """Handles UI updates for the LagLens application."""

    def __init__(self, app):
        """Initialize with reference to the main app."""
        self.app = app
        self.logger = get_logger("ui_updater")

    def update_world_map(self) -> None:
        """Update the world map dynamically based on widget size."""
        map_widget = self.app.query_one("#ascii-map", Static)
        width = map_widget.size.width
        height = map_widget.size.height

        if width > 0 and height > 0:
            servers_with_indicators = []
            for server in self.app.servers:
                indicator = self.get_server_indicator(server)
                servers_with_indicators.append(
                    {
                        "latitude": server["latitude"],
                        "longitude": server["longitude"],
                        "indicator": indicator,
                    }
                )

            map_text = self.app.world_map.draw(
                columns=width, lines=height, servers=servers_with_indicators
            )
            map_widget.update(map_text)
        else:
            self.logger.debug("Map widget size is not initialized yet.")

    def get_server_indicator(self, server) -> str:
        """Get the indicator for a server based on its current latency."""
        latency = self.app.latest_latencies.get(server["ip"])
        if latency is not None:
            if latency < 100:
                return "🟢"
            elif 100 <= latency <= 300:
                return "🟡"
            else:
                return "🔴"
        return "●"

    async def update_ping_results(self) -> None:
        """Perform pings asynchronously and update the TUI with results."""
        current_time = datetime.now()

        results_text = Text(
            f"--- Last Update: {time.strftime('%H:%M:%S')} ---\n\n", style="bold white"
        )

        tasks = [self.app.ping_server_async(server["ip"]) for server in self.app.servers]
        results = await self.app.gather_ping_results(tasks)

        for server, result in zip(self.app.servers, results, strict=False):
            server_ip = server["ip"]
            server_name = server["name"]

            if isinstance(result, Exception):
                self.app.latency_history.add_measurement(server_ip, None, current_time)
                results_text.append(f"{server_name:<20} : ", style="white")
                results_text.append("Error\n", style="bold red")
            else:
                latency, indicator_text = result
                self.app.latest_latencies[server_ip] = latency
                self.app.latency_history.add_measurement(server_ip, latency, current_time)

                results_text.append(f"{server_name:<20} : ", style="white")
                results_text.append(indicator_text)
                results_text.append("\n")

        ping_results_widget = self.app.query_one("#ping-results", Static)
        ping_results_widget.update(
            Panel(results_text, title="Latency Results", border_style="dim white")
        )

        self.update_server_containers()
        self.update_world_map()

    def update_server_containers(self) -> None:
        """Update each server's individual container with stats and sparkline."""
        for server in self.app.servers:
            server_ip = server["ip"]
            server_name = server["name"]

            server_stats = self.app.latency_history.get_statistics(
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
                stats_widget = self.app.query_one(f"#{stats_widget_id}", Static)
                stats_widget.update(
                    Panel(
                        stats_text,
                        title=f"{server_name[:15]} Stats",
                        border_style="dim white",
                    )
                )
            except Exception as e:
                self.logger.warning(f"Failed to update stats for {server_ip}: {e}")
                self.app.log(f"Failed to update stats for {server_ip}: {e}")

    def update_sparkline_for_server(self, server_ip: str):
        """Update the sparkline widget for a specific server."""
        try:
            sparkline_data = self.app.latency_history.get_sparkline_data(
                server_ip, minutes=30
            )

            # Check if sparkline exists, if not skip (new server with no data yet)
            if server_ip in self.app.sparklines:
                self.app.sparklines[server_ip].data = sparkline_data

                widget_id = f"sparkline-{server_ip.replace('.', '-')}"
                try:
                    sparkline_widget = self.app.query_one(f"#{widget_id}", Sparkline)
                    self.app.sparklines[server_ip].update_sparkline_widget(sparkline_widget)
                except Exception as widget_error:
                    self.logger.debug(f"Sparkline widget not found for {server_ip}: {widget_error}")
                    self.app.log(f"Sparkline widget not found for {server_ip}: {widget_error}")

        except Exception as e:
            self.logger.warning(f"Failed to update sparkline for {server_ip}: {e}")
            self.app.log(f"Failed to update sparkline for {server_ip}: {e}")
