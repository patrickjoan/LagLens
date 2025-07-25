from ping3 import errors, ping
from rich.text import Text


def ping_server(host: str, timeout: int = 5) -> int | None:
    """Ping a server using ping3 and return the response time in milliseconds.

    Args:
        host (str): The hostname or IP address to ping.
        timeout (int): Timeout in seconds for the ping.

    Returns:
        Optional[int]: Response time in milliseconds, or None if unreachable/error.

    """
    try:
        delay_seconds = ping(host, timeout=timeout, unit="ms")
        if delay_seconds is not None:
            return int(delay_seconds)
        else:
            return None
    except errors.PingError as e:
        print(f"Error pinging {host}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while pinging {host}: {e}")
        return None


def get_latency_indicator(latency_ms: float | None) -> Text:
    """Return a Rich Text object with emoji and color based on latency."""
    text = Text()
    if latency_ms is None:
        text.append("🔴 FAILED", style="red bold")
    elif latency_ms < 100:
        text.append(f"🟢 {latency_ms:} ms", style="green")
    elif 100 <= latency_ms <= 300:
        text.append(f"🟡 {latency_ms:} ms", style="yellow")
    else:  # latency_ms > 300
        text.append(f"🔴 {latency_ms:} ms", style="red")
    return text
