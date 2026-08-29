from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir, user_data_dir


APP_NAME = "Cognigenesis"
APP_AUTHOR = "JajaLabs"
DEFAULT_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_TIMEOUT = 300.0


@dataclass
class Settings:
    provider: str = "ollama"
    model: str | None = None
    ollama_base_url: str = DEFAULT_BASE_URL
    ollama_timeout: float = DEFAULT_TIMEOUT
    theme: str = "prime-dark"
    default_workspace: str = "."


def config_dir() -> Path:
    return Path(user_config_dir(APP_NAME, APP_AUTHOR))


def data_dir() -> Path:
    return Path(user_data_dir(APP_NAME, APP_AUTHOR))


def config_path() -> Path:
    return config_dir() / "config.json"


def history_path() -> Path:
    path = data_dir() / "history"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def load_settings() -> Settings:
    path = config_path()
    data: dict[str, Any] = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}

    settings = Settings(
        provider=str(data.get("provider", "ollama")),
        model=data.get("model"),
        ollama_base_url=str(data.get("ollama_base_url", DEFAULT_BASE_URL)),
        ollama_timeout=float(data.get("ollama_timeout", DEFAULT_TIMEOUT)),
        theme=str(data.get("theme", "prime-dark")),
        default_workspace=str(data.get("default_workspace", ".")),
    )

    # Environment variables override persisted configuration.
    settings.provider = os.getenv("COGNI_PROVIDER", settings.provider)
    settings.model = os.getenv("COGNI_OLLAMA_MODEL", settings.model)
    settings.ollama_base_url = os.getenv("COGNI_OLLAMA_BASE_URL", settings.ollama_base_url)
    settings.ollama_timeout = float(os.getenv("COGNI_OLLAMA_TIMEOUT", settings.ollama_timeout))
    return settings


def save_settings(settings: Settings) -> Path:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(settings), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
