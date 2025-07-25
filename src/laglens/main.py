import time

from ping3 import errors, ping
from rich.panel import Panel
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Header, Static


def ping_server(host: str, timeout: int = 2) -> int | None:
    """Ping a server using ping3 and return the response time in milliseconds.

    Args:
        host (str): The hostname or IP address to ping.
        timeout (float): Timeout in seconds for the ping.

    Returns:
        Optional[int]: Response time in milliseconds, or None if unreachable/error.

    """
    try:
        delay_seconds = ping(host, timeout=timeout, unit="s")
        if delay_seconds is not None:
            return delay_seconds * 1000
        else:
            return None
    except errors.PingError as e:
        print(f"Error pinging {host}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while pinging {host}: {e}")
        return None


def get_latency_indicator(latency_ms: float | None) -> Text:
    """Returns a Rich Text object with emoji and color based on latency."""
    text = Text()
    if latency_ms is None:
        text.append("🔴 FAILED", style="red bold")
    elif latency_ms < 100:
        text.append(f"🟢 {latency_ms:.2f} ms", style="green")
    elif 100 <= latency_ms <= 300:
        text.append(f"🟡 {latency_ms:.2f} ms", style="yellow")
    else:  # latency_ms > 300
        text.append(f"🔴 {latency_ms:.2f} ms", style="red")
    return text


class LagLensApp(App):
    """A Textual application to visualize network latency."""

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit App"),
    ]

    CSS = """
    Screen {
        background: #202020; /* Dark background */
    }
    #ping-results {
        height: 1fr; /* Take up available vertical space */
        width: 1fr; /* Take up available horizontal space */
        padding: 1 2; /* Vertical horizontal padding */
        background: #252525;
        border: solid #404040;
        overflow-y: auto; /* Enable scrolling if content overflows */
    }
    Header {
        background: #303030;
        color: white;
    }
    Footer {
        background: #303030;
        color: white;
    }
    """

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Container(
            Static("Pinging servers...\n", id="ping-results"), id="main-container"
        )
        yield Footer()

    async def on_mount(self) -> None:
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

        self.update_ping_results()
        # Periodically update results (e.g., every 5 seconds)
        # IMPORTANT: For real-time updates, you'll need `asyncio.sleep` and `async_ping` later.
        # For now, this `set_interval` will call `update_ping_results` every 5 seconds.
        # This will block the UI for the duration of the pings.
        self.set_interval(5, self.update_ping_results, pause=False)

    def update_ping_results(self) -> None:
        """Perform pings and update the TUI with results."""
        results_text = Text(
            f"--- Last Update: {time.strftime('%H:%M:%S')} ---\n\n", style="bold white"
        )

        for server in self.servers:
            latency = ping_server(server)  # Synchronous call
            indicator_text = get_latency_indicator(latency)
            results_text.append(f"{server:<25}: ")
            results_text.append(indicator_text)
            results_text.append("\n")

        # Get a reference to the Static widget by its ID
        ping_results_widget = self.query_one("#ping-results", Static)
        ping_results_widget.update(
            Panel(results_text, title="Latency Map Data", border_style="dim white")
        )

    def action_toggle_dark(self) -> None:
        """Toggle dark mode."""
        self.dark = not self.dark

    async def action_quit(self) -> None:
        """Quit the application."""
        self.exit()


if __name__ == "__main__":
    app = LagLensApp()
    app.run()

# if __name__ == "__main__":
#     servers_to_test = [
#         "google.com",
#         "cloud.google.com",
#         "aws.amazon.com",
#         "1.1.1.1",
#         "8.8.8.8",
#         "bad-host-name-xyz.com",
#         "192.0.2.1",
#     ]
#
#     print("--- Starting Latency Check ---")
#     for server in servers_to_test:
#         latency_ms = ping_server(server)
#         if latency_ms is not None:
#             print(f"Ping to {server:<25}: {latency_ms:.4f} ms")
#         else:
#             print(f"Ping to {server:<25}: Unreachable or Failed")
#         time.sleep(1)
#
#     print("--- Latency Check Complete ---")
