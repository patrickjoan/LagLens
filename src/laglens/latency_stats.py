from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime, timedelta

from textual.color import Color
from textual.widgets import Sparkline


class LatencyHistory:
    """Tracks latency measurements for multiple servers and computes statistics."""

    def __init__(self):
        """Initialize the latency history storage."""
        self.history = defaultdict(list)

    def add_measurement(self, server_ip: str, latency: float, timestamp: datetime):
        """Add a latency measurement for a given server at a specific timestamp."""
        self.history[server_ip].append({"latency": latency, "timestamp": timestamp})

    def get_statistics(self, server_ip: str, window_minutes: int = 60):
        """Get min, max, avg, jitter, and packet loss for a time window."""
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

    def get_sparkline_data(self, server_ip: str, minutes: int = 30) -> Sequence[float]:
        """Get latency data formatted for Sparkline widget."""
        recent_data = self._get_recent_data(server_ip, minutes)
        latencies = [m["latency"] for m in recent_data if m["latency"] is not None]

        if not latencies:
            return [0.0]

        # Limit to reasonable number of points for display
        max_points = 50
        if len(latencies) > max_points:
            step = len(latencies) // max_points
            latencies = latencies[::step]

        return [float(lat) for lat in latencies]

    def _get_recent_data(self, server_ip: str, window_minutes: int):
        """Get measurements within the specified time window."""
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        return [m for m in self.history[server_ip] if m["timestamp"] >= cutoff_time]

    def _calculate_packet_loss(self, recent):
        """Estimate packet loss as the percentage of missing measurements."""
        if not recent:
            return None

        failed_count = sum(1 for m in recent if m["latency"] is None)
        total_count = len(recent)

        return (failed_count / total_count) * 100 if total_count > 0 else 0.0

    def _calculate_jitter(self, latencies):
        """Calculate jitter as the average absolute difference between consecutive measurements."""
        if len(latencies) < 2:
            return 0.0
        diffs = [abs(latencies[i] - latencies[i - 1]) for i in range(1, len(latencies))]
        return sum(diffs) / len(diffs)


class LatencySparkline:
    """Simple class to create and manage Sparkline widgets for latency data."""

    def __init__(self, data: Sequence[float] | None = None):
        """Initialize with optional latency data."""
        self.data = list(data) if data else [0.0]

    def create_sparkline(
        self, widget_id: str | None = None, widget_classes: str = "latency-sparkline"
    ) -> Sparkline:
        """Create a new Sparkline widget with the current data."""
        sparkline = Sparkline(data=self.data, id=widget_id, classes=widget_classes)

        # Set colors based on average latency using Color objects
        if self.data and len(self.data) > 0:
            avg_latency = sum(self.data) / len(self.data)

            if avg_latency < 100:
                sparkline.min_color = Color.parse("green")
                sparkline.max_color = Color.parse("lime")
            elif avg_latency < 300:
                sparkline.min_color = Color.parse("yellow")
                sparkline.max_color = Color.parse("orange")
            else:
                sparkline.min_color = Color.parse("red")
                sparkline.max_color = Color.parse("bright_red")

        return sparkline

    def update_sparkline_widget(self, sparkline: Sparkline):
        """Update an existing Sparkline widget with current data."""
        sparkline.data = self.data

        # Update colors based on current average using Color objects
        if self.data and len(self.data) > 0:
            avg_latency = sum(self.data) / len(self.data)

            if avg_latency < 100:
                sparkline.min_color = Color.parse("green")
                sparkline.max_color = Color.parse("lime")
            elif avg_latency < 300:
                sparkline.min_color = Color.parse("yellow")
                sparkline.max_color = Color.parse("orange")
            else:
                sparkline.min_color = Color.parse("red")
                sparkline.max_color = Color.parse("bright_red")

    @staticmethod
    def from_latency_history(
        latency_history: LatencyHistory, server_ip: str, minutes: int = 30
    ) -> "LatencySparkline":
        """Create a LatencySparkline from LatencyHistory data."""
        data = latency_history.get_sparkline_data(server_ip, minutes)
        return LatencySparkline(data)
