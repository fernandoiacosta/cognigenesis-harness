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


def test_page_csp_pins_inline_scripts():
    import base64
    import hashlib
    import re
    from cognigenesis.commandcenter.geometry import HTML

    for page in (HTML, server.HTML):
        csp = server._page_csp(page)
        assert "frame-ancestors 'none'" in csp
        assert "'unsafe-inline'" not in csp.split("style-src")[0]
        for script in re.findall(r"<script>(.*?)</script>", page, re.DOTALL):
            digest = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
            assert f"'sha256-{digest}'" in csp


def test_geometry_http_boundary_and_content(tmp_path, monkeypatch):
    import json
    from http.client import HTTPConnection
    from http.server import ThreadingHTTPServer
    from queue import Queue
    from threading import Thread
    from cognigenesis.commandcenter.store import CommandCenterStore

    ready = Queue()

    def factory(address, handler):
        http = ThreadingHTTPServer((address[0], 0), handler)
        ready.put(http)
        return http

    monkeypatch.setattr(server, "ThreadingHTTPServer", factory)
    store = CommandCenterStore(tmp_path / ".cognigenesis" / "command-center.json")
    store.save({"tasks": [{"id": "t", "title": "<script>untrusted</script>", "metadata": {"api_key": "secret"}}]})
    thread = Thread(target=server.serve_command_center, args=(tmp_path,), daemon=True)
    thread.start()
    # Hosted macOS runners can take more than five seconds to schedule a new
    # Python thread under load. Startup time is not part of this boundary test.
    http = ready.get(timeout=30)

    def request(path, headers=None):
        connection = HTTPConnection("127.0.0.1", http.server_port, timeout=10)
        try:
            connection.request("GET", path, headers=headers or {})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    try:
        status, headers, body = request("/geometry")
        assert status == 200
        assert headers["Content-Security-Policy"] == server._page_csp(server.GEOMETRY_HTML)
        assert b"untrusted" not in body
        status, headers, body = request("/api/topology")
        assert status == 200
        assert json.loads(body)["nodes"][0]["label"] == "<script>untrusted</script>"
        assert b"secret" not in body
        assert headers["Cache-Control"] == "no-store"
        assert request("/api/topology", {"Host": "attacker.example"})[0] == 403
        assert request("/api/topology", {"Sec-Fetch-Site": "cross-site"})[0] == 403
        assert request("/geometry", {"Sec-Fetch-Site": "none"})[0] == 200
    finally:
        http.shutdown()
        thread.join(timeout=10)
