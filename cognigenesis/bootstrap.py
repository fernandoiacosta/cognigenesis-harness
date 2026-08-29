from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from cognigenesis.config import Settings, data_dir, load_settings, save_settings
from cognigenesis.profiles import load_profile, save_profile
from cognigenesis.resources import text as resource_text
from core.model_profile import TrustTier
from core.qualification import qualify_provider
from providers.factory import build_provider, provider_identity
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
    outputs = {"logo": brand_dir / "cognigenesis-logo.svg", "theme": brand_dir / "theme.json"}
    outputs["logo"].write_text(resource_text("cognigenesis-logo.svg"), encoding="utf-8")
    outputs["theme"].write_text(resource_text("theme.json"), encoding="utf-8")
    return outputs


def pull_model(model: str) -> None:
    executable = shutil.which("ollama")
    if not executable:
        raise RuntimeError("Ollama CLI is not installed or not on PATH.")
    subprocess.run([executable, "pull", model], check=True)


def qualify_settings(settings: Settings | None = None, *, force: bool = False):
    settings = settings or load_settings()
    provider = build_provider(
        settings.provider,
        model=settings.model,
        base_url=settings.ollama_base_url,
        timeout=settings.ollama_timeout,
    )
    provider_name, model_name = provider_identity(provider)
    existing = load_profile(provider_name, model_name)
    if existing is not None and existing.tier >= TrustTier.TRUSTED and not force:
        return existing, [], False

    profile, evidence = qualify_provider(provider, provider_name, model_name)
    save_profile(profile, evidence)
    return profile, evidence, True


def run_checks(settings: Settings | None = None) -> list[Check]:
    settings = settings or load_settings()
    checks: list[Check] = []
    checks.append(Check("Python", sys.version_info >= (3, 11), sys.version.split()[0], "Install Python 3.11+"))
    checks.append(Check("cogni", bool(shutil.which("cogni")), shutil.which("cogni") or "not on PATH", "Reinstall Cognigenesis or fix PATH"))
    checks.append(Check("cogni-acp", bool(shutil.which("cogni-acp")), shutil.which("cogni-acp") or "not on PATH", "Reinstall Cognigenesis or fix PATH"))

    selected: str | None = settings.model
    try:
        models = list_models(settings.ollama_base_url, timeout=5)
        checks.append(Check("Ollama", True, f"reachable at {settings.ollama_base_url}"))
        selected = selected or choose_model(models)
        if selected and selected in models:
            checks.append(Check("Model", True, selected))
        elif selected:
            checks.append(Check("Model", False, f"missing: {selected}", f"ollama pull {selected}"))
        elif models:
            selected = models[0]
            checks.append(Check("Model", True, selected))
        else:
            checks.append(Check("Model", False, "no local Ollama models", "cogni setup --pull"))
    except Exception as exc:
        checks.append(Check("Ollama", False, f"not reachable: {exc}", "Start Ollama and run: ollama list"))

    if selected:
        profile = load_profile("ollama", selected)
        if profile:
            qualified = profile.tier >= TrustTier.TRUSTED
            checks.append(Check("Qualification", qualified, f"{profile.tier.name} (score {profile.score:.3f})", None if qualified else "cogni qualify --force"))
        else:
            checks.append(Check("Qualification", False, f"no saved profile for {selected}", "cogni qualify"))

    legacy = detect_legacy_aionui_bridge()
    packaged_acp = shutil.which("cogni-acp")
    if packaged_acp:
        detail = f"packaged ACP: {packaged_acp}"
        if legacy:
            detail += f" (unused legacy file still present: {legacy})"
        checks.append(Check(
            "AionUi bridge",
            True,
            detail,
            None,
        ))
    else:
        checks.append(Check(
            "AionUi bridge",
            False,
            "packaged cogni-acp executable is not available on PATH",
            "Reinstall Cognigenesis, then set the AionUi Custom Agent command to the absolute cogni-acp executable path.",
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
