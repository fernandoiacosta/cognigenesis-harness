import json

from cognigenesis.config import Settings, load_settings, save_settings
from state.store import StateStore


def test_config_round_trip_and_env_override(tmp_path, monkeypatch):
    monkeypatch.setattr("cognigenesis.config.user_config_dir", lambda *args, **kwargs: str(tmp_path))
    monkeypatch.delenv("COGNI_OLLAMA_MODEL", raising=False)
    settings = Settings(model="local-model", ollama_timeout=444)
    save_settings(settings)
    loaded = load_settings()
    assert loaded.model == "local-model"
    assert loaded.ollama_timeout == 444

    monkeypatch.setenv("COGNI_OLLAMA_MODEL", "env-model")
    assert load_settings().model == "env-model"


def test_state_store_atomic_conversation_round_trip(tmp_path):
    path = tmp_path / "state.json"
    state = StateStore(path)
    state.set_conversation([{"role": "user", "content": "hello"}])
    assert path.exists()
    assert not path.with_suffix(".json.tmp").exists()
    reopened = StateStore(path)
    assert reopened.conversation() == [{"role": "user", "content": "hello"}]


def test_corrupt_state_is_preserved(tmp_path):
    path = tmp_path / "state.json"
    path.write_text("{broken", encoding="utf-8")
    state = StateStore(path)
    assert state.conversation() == []
    assert path.with_suffix(".json.corrupt").exists()
