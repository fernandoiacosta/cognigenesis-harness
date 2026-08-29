from pathlib import Path

from cognigenesis import __version__
from cognigenesis.bootstrap import aionui_configuration
from cognigenesis.resources import text as resource_text
from harness import build_engine
from providers.ollama import choose_model
from cli import _normalize_argv


def test_v1_version_and_packaged_control_plane():
    assert __version__ == "2.0.0a1"
    control = resource_text("agent.md")
    assert "Cognigenesis Cognitive Agent" in control
    assert "Completion Principle" in control


def test_cli_backward_compatibility_normalizes_one_shot():
    assert _normalize_argv(["Say OK"]) == ["run", "Say OK"]
    assert _normalize_argv(["chat"]) == ["chat"]
    assert _normalize_argv(["doctor"]) == ["doctor"]


def test_preferred_model_selection():
    assert choose_model(["qwen:latest", "hasi-edge-AG:latest"]) == "hasi-edge-AG:latest"
    assert choose_model(["qwen:latest", "llama3.1:8b"]) == "llama3.1:8b"
    assert choose_model(["qwen:latest"]) == "qwen:latest"
    assert choose_model([]) is None


def test_engine_exposes_strict_tool_schemas(tmp_path: Path):
    engine = build_engine(tmp_path, provider_name="stub")
    capabilities = {item["id"]: item for item in engine.registry.describe()}
    assert capabilities["filesystem.read"]["parameters"]["required"] == ["path"]
    assert capabilities["web.search"]["parameters"]["required"] == ["query"]
    assert capabilities["workspace.create_project"]["parameters"]["required"] == ["name"]


def test_aionui_configuration_uses_packaged_acp(tmp_path, monkeypatch):
    monkeypatch.setattr("cognigenesis.bootstrap.shutil.which", lambda name: r"C:\Tools\cogni-acp.exe" if name == "cogni-acp" else None)
    monkeypatch.setattr("cognigenesis.bootstrap.data_dir", lambda: tmp_path)
    cfg = aionui_configuration()
    assert cfg["command"].endswith("cogni-acp.exe")
    assert cfg["arguments"] == []
    assert cfg["environment"]["PYTHONUTF8"] == "1"
