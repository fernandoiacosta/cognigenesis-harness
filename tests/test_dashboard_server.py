import pytest

from cognigenesis.commandcenter import server
from cognigenesis.config import Settings


def test_dashboard_keeps_credentials_and_endpoints_out_of_config(monkeypatch):
    monkeypatch.setattr(server, "load_settings", lambda: Settings(
        provider="ollama", model="gemma3:4b", ollama_base_url="http://secret@192.168.1.20:11434"))
    config = server.dashboard_config()
    assert config == {"provider": "ollama", "model": "gemma3:4b", "connection": "network"}
    assert "secret" not in str(config)
    assert "/api/config" in server.HTML
    assert "Export snapshot" in server.HTML


def test_dashboard_refuses_network_bind(tmp_path):
    with pytest.raises(ValueError, match="localhost"):
        server.serve_command_center(tmp_path, host="0.0.0.0")
    assert server._loopback("127.0.0.1")
    assert server._loopback("::1")
    assert not server._loopback("192.168.1.2")
