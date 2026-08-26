import pytest

from core.policy import Policy
from core.qualification import conservative_profile
from core.registry import CapabilityRegistry
from tools.web import _DuckDuckGoParser, _assert_public_url, _strip_html, register_web_tools


def test_duckduckgo_parser_extracts_title_url_and_snippet():
    parser = _DuckDuckGoParser()
    parser.feed(
        '<a class="result__a" href="https://duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com">Example</a>'
        '<div class="result__snippet">Useful result snippet.</div>'
    )
    assert parser.results == [
        {"title": "Example", "url": "https://example.com", "snippet": "Useful result snippet."}
    ]


def test_strip_html_removes_script_and_markup():
    assert _strip_html('<style>x</style><h1>Hello</h1><script>bad()</script><p>world</p>') == "Hello world"


def test_web_tools_are_registered_and_observer_authorized(tmp_path):
    registry = CapabilityRegistry()
    register_web_tools(registry)
    assert registry.get("web.search") is not None
    assert registry.get("web.fetch") is not None

    profile = conservative_profile("ollama", "test")
    policy = Policy(tmp_path, model_profile=profile)
    assert policy.authorize("web.search", {"query": "test"})[0]
    assert policy.authorize("web.fetch", {"url": "https://example.com"})[0]


def test_web_fetch_rejects_localhost_without_dns():
    with pytest.raises(PermissionError, match="localhost"):
        _assert_public_url("http://localhost:8080/private")


def test_web_fetch_rejects_private_ip(monkeypatch):
    monkeypatch.setattr(
        "tools.web.socket.getaddrinfo",
        lambda *args, **kwargs: [(None, None, None, None, ("192.168.1.20", 443))],
    )
    with pytest.raises(PermissionError, match="non-public"):
        _assert_public_url("https://example.test/private")


def test_web_fetch_allows_global_ip(monkeypatch):
    monkeypatch.setattr(
        "tools.web.socket.getaddrinfo",
        lambda *args, **kwargs: [(None, None, None, None, ("93.184.216.34", 443))],
    )
    _assert_public_url("https://example.com")
