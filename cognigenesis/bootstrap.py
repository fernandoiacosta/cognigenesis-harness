from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from cognigenesis.config import Settings, data_dir, load_settings, save_settings
from cognigenesis.resources import text as resource_text
from providers.ollama import choose_model, list_models


@dataclass
class Check:
    name: str
    ok: bool
    detail: str
    fix: str | None = None


def detect_legacy_aionui_bridge() -> Path | None:
    appdata = os.getenv("APPDATA")
    if not appdata:
        return None
    path = Path(appdata) / "AionUi" / "cognigenesis" / "cognigenesis_ollama.py"
    return path if path.exists() else None


def install_brand_assets() -> dict[str, Path]:
    brand_dir = data_dir() / "brand"
    brand_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "logo": brand_dir / "cognigenesis-logo.svg",
        "theme": brand_dir / "theme.json",
    }
    outputs["logo"].write_text(resource_text("cognigenesis-logo.svg"), encoding="utf-8")
    outputs["theme"].write_text(resource_text("theme.json"), encoding="utf-8")
    return outputs


def run_checks(settings: Settings | None = None) -> list[Check]:
    settings = settings or load_settings()
    checks: list[Check] = []
    checks.append(Check("Python", sys.version_info >= (3, 11), sys.version.split()[0], "Install Python 3.11+"))
    checks.append(Check("cogni", bool(shutil.which("cogni")), shutil.which("cogni") or "not on PATH", "Reinstall Cognigenesis or fix PATH"))
    checks.append(Check("cogni-acp", bool(shutil.which("cogni-acp")), shutil.which("cogni-acp") or "not on PATH", "Reinstall Cognigenesis or fix PATH"))

    try:
        models = list_models(settings.ollama_base_url, timeout=5)
        checks.append(Check("Ollama", True, f"reachable at {settings.ollama_base_url}"))
        selected = settings.model or choose_model(models)
        if selected and selected in models:
            checks.append(Check("Model", True, selected))
        elif selected:
            checks.append(Check("Model", False, f"missing: {selected}", f"ollama pull {selected}"))
        elif models:
            checks.append(Check("Model", True, models[0]))
        else:
            checks.append(Check("Model", False, "no local Ollama models", "ollama pull llama3.1:8b"))
    except Exception as exc:
        checks.append(Check("Ollama", False, f"not reachable: {exc}", "Start Ollama and run: ollama list"))

    legacy = detect_legacy_aionui_bridge()
    checks.append(Check(
        "AionUi bridge",
        legacy is None,
        "packaged cogni-acp path" if legacy is None else f"legacy bridge detected: {legacy}",
        None if legacy is None else "Set AionUi Custom Agent command to cogni-acp with no arguments; then create a new conversation.",
    ))

    assets = install_brand_assets()
    checks.append(Check("Brand assets", assets["logo"].exists() and assets["theme"].exists(), str(assets["logo"])))
    return checks


def auto_setup(*, model: str | None = None, base_url: str | None = None, timeout: float | None = None) -> tuple[Settings, list[Check]]:
    settings = load_settings()
    if base_url:
        settings.ollama_base_url = base_url.rstrip("/")
    if timeout is not None:
        settings.ollama_timeout = timeout

    try:
        models = list_models(settings.ollama_base_url, timeout=5)
    except Exception:
        models = []

    settings.provider = "ollama"
    settings.model = model or settings.model or choose_model(models)
    if settings.model is None:
        settings.model = "llama3.1:8b"
    save_settings(settings)
    install_brand_assets()
    return settings, run_checks(settings)


def aionui_configuration(settings: Settings | None = None) -> dict:
    settings = settings or load_settings()
    executable = shutil.which("cogni-acp") or "cogni-acp"
    assets = install_brand_assets()
    return {
        "display_name": "Cognigenesis",
        "command": executable,
        "arguments": [],
        "image": str(assets["logo"]),
        "environment": {
            "COGNI_PROVIDER": settings.provider,
            "COGNI_OLLAMA_BASE_URL": settings.ollama_base_url,
            "COGNI_OLLAMA_MODEL": settings.model or "llama3.1:8b",
            "COGNI_OLLAMA_TIMEOUT": str(int(settings.ollama_timeout)),
            "PYTHONUTF8": "1",
        },
    }
