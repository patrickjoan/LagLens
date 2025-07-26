from collections import defaultdict
from datetime import datetime, timedelta

from rich.text import Text
from textual.widgets import Static


class LatencyHistory:
    """Tracks latency measurements for multiple servers and computes statistics."""

    def __init__(self):
        """Initialize the latency history storage."""
        self.history = defaultdict(list)

    def add_measurement(self, server_ip: str, latency: float, timestamp: datetime):
        """Add a latency measurement for a given server at a specific timestamp.

        Args:
            server_ip (str): The IP address of the server.
            latency (float): The measured latency in milliseconds.
            timestamp (datetime): The time the measurement was taken.

        """
        self.history[server_ip].append({"latency": latency, "timestamp": timestamp})

    def get_statistics(self, server_ip: str, window_minutes: int = 60):
        """Get min, max, avg, jitter, and packet loss for a time window.

        Args:
            server_ip (str): The IP address of the server.
            window_minutes (int, optional): The time window in minutes. Defaults to 60.

        Returns:
            dict: A dictionary containing min, max, avg, jitter, and packet_loss.

        """
        recent = self._get_recent_data(server_ip, window_minutes)
        latencies = [m["latency"] for m in recent if m["latency"] is not None]

        if not latencies:
            return {
                "min": None,
                "max": None,
                "avg": None,
                "jitter": None,
                "packet_loss": None,
            }

        return {
            "min": min(latencies),
            "max": max(latencies),
            "avg": sum(latencies) / len(latencies),
            "jitter": self._calculate_jitter(latencies),
            "packet_loss": self._calculate_packet_loss(recent),
        }

    def _get_recent_data(self, server_ip: str, window_minutes: int):
        """Get measurements within the specified time window."""
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        return [
            m for m in self.history[server_ip]
            if m["timestamp"] >= cutoff_time
        ]

    def _calculate_packet_loss(self, recent):
        """Estimate packet loss as the percentage of missing measurements."""
        if not recent:
            return None

        # Count failed pings (None latency values)
        failed_count = sum(1 for m in recent if m["latency"] is None)
        total_count = len(recent)

        return (failed_count / total_count) * 100 if total_count > 0 else 0.0

    def _calculate_jitter(self, latencies):
        """Calculate jitter as the average absolute difference between consecutive measurements."""
        if len(latencies) < 2:
            return 0.0
        diffs = [abs(latencies[i] - latencies[i - 1]) for i in range(1, len(latencies))]
        return sum(diffs) / len(diffs)


class TrendWidget(Static):
    """Widget to display ASCII sparkline graphs of latency trends."""

    def __init__(self, latency_history: LatencyHistory):
        super().__init__()
        self.latency_history = latency_history

    def render_trend_graph(self, server_ip: str, minutes: int = 30) -> Text:
        """ASCII sparkline graph of latency trends"""
        history = self._get_recent_history(server_ip, minutes)
        return self._create_sparkline(history)

    def _get_recent_history(self, server_ip: str, minutes: int):
        """Get recent history data for sparkline"""
        return self.latency_history._get_recent_data(server_ip, minutes)

    def _create_sparkline(self, history):
        """Create ASCII sparkline from history data"""
        if not history:
            return Text("No data available", style="dim")

        latencies = [m["latency"] for m in history if m["latency"] is not None]
        if not latencies:
            return Text("No valid measurements", style="dim")

        # Normalize latencies to sparkline characters
        min_lat, max_lat = min(latencies), max(latencies)
        if min_lat == max_lat:
            return Text("▄" * len(latencies), style="green")

        # Map to sparkline characters
        sparkline_chars = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
        normalized = []

        for lat in latencies:
            # Normalize to 0-1 range
            norm = (lat - min_lat) / (max_lat - min_lat)
            # Map to character index
            char_idx = min(int(norm * len(sparkline_chars)), len(sparkline_chars) - 1)
            normalized.append(sparkline_chars[char_idx])

        # Color based on average latency
        avg_lat = sum(latencies) / len(latencies)
        if avg_lat < 100:
            style = "green"
        elif avg_lat < 300:
            style = "yellow"
        else:
            style = "red"

        return Text("".join(normalized), style=style)

