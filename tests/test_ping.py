from unittest.mock import patch

from rich.text import Text

from src.laglens.ping import get_latency_indicator, ping_server


def test_ping_server_success():
    """Test successful ping server operation."""
    with patch("src.laglens.ping.ping", return_value=42.7):
        assert ping_server("example.com") == 42


def test_ping_server_none():
    """Test ping server with None return value."""
    with patch("src.laglens.ping.ping", return_value=None):
        assert ping_server("example.com") is None


def test_ping_server_pingerror():
    """Test ping server with exception handling."""
    with patch("src.laglens.ping.ping", side_effect=Exception("fail")):
        assert ping_server("example.com") is None


def test_get_latency_indicator_none():
    """Test latency indicator with None input."""
    result = get_latency_indicator(None)
    assert isinstance(result, Text)
    assert "FAILED" in result.plain


def test_get_latency_indicator_green():
    """Test latency indicator with green (good) latency."""
    result = get_latency_indicator(50)
    assert "🟢" in result.plain
    assert "50" in result.plain


def test_get_latency_indicator_yellow():
    """Test latency indicator with yellow (medium) latency."""
    result = get_latency_indicator(200)
    assert "🟡" in result.plain


def test_get_latency_indicator_red():
    """Test latency indicator with red (high) latency."""
    result = get_latency_indicator(350)
    assert "🔴" in result.plain
