import pytest

from cognigenesis.config import Settings
from providers.cloud import CloudProvider, LocalOpenAIProvider
from providers.factory import build_provider


def test_cloud_adapter_preserves_tools_and_reads_key(monkeypatch):
    monkeypatch.setattr('providers.factory.load_settings', lambda: Settings())
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
    captured = {}

    def fake_post(url, payload, headers, timeout):
        captured.update(url=url, payload=payload, headers=headers)
        return {'choices': [{'message': {'tool_calls': [{'function': {'name': 'task.add', 'arguments': '{"title":"x"}'}}]}}]}

    monkeypatch.setattr('providers.cloud._post', fake_post)
    provider = build_provider('openai', 'test-model')
    response = provider.generate({'system': 'system', 'objective': 'task', 'capabilities': [{'id': 'task.add', 'description': 'add', 'parameters': {'type': 'object'}}]})
    assert isinstance(provider, CloudProvider)
    assert captured['headers']['Authorization'] == 'Bearer test-key'
    assert captured['payload']['tools'][0]['function']['name'] == 'task.add'
    assert response.tool_calls[0].arguments == {'title': 'x'}


def test_litert_no_api_key_and_no_tool_calls(monkeypatch):
    monkeypatch.setattr('providers.factory.load_settings', lambda: Settings())
    captured = {}

    def fake_post(url, payload, headers, timeout):
        captured.update(url=url, payload=payload, headers=headers)
        return {'choices': [{'message': {'content': 'on device'}}]}

    monkeypatch.setattr('providers.cloud._post', fake_post)
    provider = build_provider('litert', 'local', 'http://127.0.0.1:9379')
    response = provider.generate({'system': 's', 'objective': 'q', 'capabilities': [{'id': 'task.add', 'description': 'add'}]})
    assert isinstance(provider, LocalOpenAIProvider)
    assert captured['url'] == 'http://127.0.0.1:9379/v1/chat/completions'
    assert 'tools' not in captured['payload']
    assert response.final == 'on device'


def test_edge_requires_server_address(monkeypatch):
    monkeypatch.setattr('providers.factory.load_settings', lambda: Settings())
    with pytest.raises(ValueError, match='server URL'):
        build_provider('edge', 'local')
