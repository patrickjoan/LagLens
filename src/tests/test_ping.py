from unittest.mock import patch

from rich.text import Text

from laglens.ping import get_latency_indicator, ping_server


def test_ping_server_success():
    with patch("laglens.ping.ping", return_value=42.7):
        assert ping_server("example.com") == 42


def test_ping_server_none():
    with patch("laglens.ping.ping", return_value=None):
        assert ping_server("example.com") is None


def test_ping_server_pingerror():
    with patch("laglens.ping.ping", side_effect=Exception("fail")):
        assert ping_server("example.com") is None


def test_get_latency_indicator_none():
    result = get_latency_indicator(None)
    assert isinstance(result, Text)
    assert "FAILED" in result.plain


def test_get_latency_indicator_green():
    result = get_latency_indicator(50)
    assert "🟢" in result.plain
    assert "50" in result.plain


def test_get_latency_indicator_yellow():
    result = get_latency_indicator(200)
    assert "🟡" in result.plain


def test_get_latency_indicator_red():
    result = get_latency_indicator(350)
    assert "🔴" in result.plain
