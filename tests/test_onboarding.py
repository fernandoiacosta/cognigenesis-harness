from cognigenesis.config import Settings
from cognigenesis import onboarding


def test_guided_ollama_flow_saves_selected_server_and_model(monkeypatch):
    selected = iter(["ollama", "my-model:latest", "compact", "save"])
    saved = []
    monkeypatch.setattr(onboarding, "choose", lambda *a, **kw: next(selected))
    monkeypatch.setattr(onboarding, "_input", lambda label, default=None: default or "")
    monkeypatch.setattr(onboarding, "_models", lambda endpoint, **kw: ["my-model:latest"])
    monkeypatch.setattr(onboarding, "load_settings", lambda: Settings())
    monkeypatch.setattr(onboarding, "save_settings", saved.append)
    assert onboarding.run_wizard()
    assert (saved[0].provider, saved[0].model, saved[0].composer_style) == ("ollama", "my-model:latest", "compact")
    assert saved[0].ollama_base_url == "http://127.0.0.1:11434"


def test_cancel_does_not_save_configuration_or_credential(monkeypatch):
    selections = iter(["openai", "gpt-4.1-mini", "signal", "back"])
    saved = []
    monkeypatch.setattr(onboarding, "choose", lambda *a, **kw: next(selections))
    monkeypatch.setattr(onboarding, "_input", lambda label, default=None: default or ".")
    monkeypatch.setattr(onboarding, "_cloud_models", lambda provider, secret: [])
    monkeypatch.setattr(onboarding, "load_settings", lambda: Settings())
    monkeypatch.setattr(onboarding, "save_settings", saved.append)
    monkeypatch.setattr(onboarding.os, "getenv", lambda key: None)
    monkeypatch.setattr(onboarding.getpass, "getpass", lambda prompt: "test-secret")
    monkeypatch.setattr(onboarding.keyring, "set_password", lambda *a: saved.append("credential"))
    assert not onboarding.run_wizard()
    assert saved == []


def test_local_model_list_uses_openai_compatible_endpoint(monkeypatch):
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): return None
        def read(self): return b'{"data": [{"id": "gemma-local"}]}'
    seen = []
    monkeypatch.setattr(onboarding.request, "urlopen", lambda url, timeout: (seen.append(url) or Response()))
    assert onboarding._models("http://192.168.1.10:1234", openai_compatible=True) == ["gemma-local"]
    assert seen == ["http://192.168.1.10:1234/v1/models"]


def test_cloud_model_catalog_uses_header_and_filters_generation_models(monkeypatch):
    import io
    seen = {}
    payload = b'{"models":[{"name":"models/gemini-chat","supportedGenerationMethods":["generateContent"]},{"name":"models/embedding-only","supportedGenerationMethods":["embedContent"]}]}'
    class Response(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *args): self.close()
    def fetch(req, timeout):
        seen['key'] = req.get_header('X-goog-api-key')
        return Response(payload)
    monkeypatch.setattr(onboarding.request, "urlopen", fetch)
    monkeypatch.setattr(onboarding.os, "getenv", lambda key: None)
    assert onboarding._cloud_models('google', 'test-key') == ['gemini-chat']
    assert seen['key'] == 'test-key'
