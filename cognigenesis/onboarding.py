"""Interactive first-run setup. No hidden subscription-token reuse."""
from __future__ import annotations

import getpass
import json
import os
import shutil
from urllib import request, error

import keyring
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, Layout, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.styles import Style

from cognigenesis.config import load_settings, save_settings
from providers.cloud import DEFAULT_MODELS, ENV_KEYS
from providers.ollama import list_models

PROVIDERS = [
    ("ollama", "Ollama", "Local or network server · no account"),
    ("openai", "OpenAI / Codex models", "Your OpenAI API key · ChatGPT subscription sign-in unavailable"),
    ("anthropic", "Anthropic / Claude models", "Your Anthropic API key · Claude subscription sign-in unavailable"),
    ("google", "Google Gemini API", "API key"),
    ("grok", "xAI Grok API", "API key"),
    ("meta", "Hosted Meta models", "Your inference endpoint and API key"),
    ("litert", "Google LiteRT-LM", "On-device server · no account"),
    ("edge", "AI Edge Gallery server build", "Requires a build exposing an API"),
    ("local", "OpenAI-compatible local", "LM Studio, llama.cpp, vLLM, etc."),
]

STYLE = Style.from_dict({
    "logo": "bold #62F5FF", "title": "bold #C96CFF", "muted": "#A7B0C3",
    "selected": "bold #62F5FF", "detail": "#8B7CFF", "success": "#54E6A8",
})


def choose(title: str, choices: list[tuple[str, str, str]], *, step: int, total: int = 5, search: bool = True) -> str | None:
    """Arrow keys and incremental filtering; Escape cancels this step."""
    if not choices:
        return None
    selected = 0
    query = ""
    matches = choices[:]
    keys = KeyBindings()

    def render():
        fragments = [
            ("class:logo", "\n   ◈  C O G N I G E N E S I S\n"),
            ("class:muted", f"   Setup  {step} / {total}    {'━' * step}{'─' * (total - step)}\n\n"),
            ("class:title", f"   {title}\n\n"),
        ]
        if search:
            fragments.append(("class:muted", f"   Search  {query}▌\n\n"))
        rows = max(4, min(10, (shutil.get_terminal_size().lines - 13) // 2))
        start = max(0, min(selected - rows + 1, len(matches) - rows))
        for index, (value, label, detail) in enumerate(matches[start:start + rows], start=start):
            prefix = "   ❯ " if index == selected else "     "
            fragments.append(("class:selected" if index == selected else "", prefix + label + "\n"))
            fragments.append(("class:detail", "       " + detail + "\n"))
        if not matches:
            fragments.append(("class:muted", "     No matches. Backspace to broaden your search.\n"))
        fragments.append(("class:muted", "\n   ↑↓ select  ·  Enter confirm  ·  Esc back" + ("  ·  type to search" if search else "") + "\n"))
        return fragments

    @keys.add("up")
    def up(event):
        nonlocal selected
        selected = (selected - 1) % len(matches) if matches else 0

    @keys.add("down")
    def down(event):
        nonlocal selected
        selected = (selected + 1) % len(matches) if matches else 0

    @keys.add("enter")
    def confirm(event):
        event.app.exit(result=matches[selected][0] if matches else None)

    @keys.add("escape")
    @keys.add("c-c")
    def cancel(event):
        event.app.exit(result=None)

    @keys.add("backspace")
    def backspace(event):
        nonlocal query, matches, selected
        query = query[:-1]
        matches = [row for row in choices if query.casefold() in (row[1] + " " + row[2] + " " + row[0]).casefold()]
        selected = 0

    @keys.add("<any>")
    def type_search(event):
        nonlocal query, matches, selected
        if search and event.data.isprintable():
            query += event.data
            matches = [row for row in choices if query.casefold() in (row[1] + " " + row[2] + " " + row[0]).casefold()]
            selected = 0

    return Application(layout=Layout(HSplit([Window(FormattedTextControl(render), wrap_lines=True)])),
                       key_bindings=keys, style=STYLE, full_screen=True, mouse_support=False).run()


def _models(endpoint: str, *, openai_compatible: bool) -> list[str]:
    if not openai_compatible:
        return list_models(endpoint, timeout=5)
    url = endpoint.rstrip("/") + "/v1/models"
    try:
        with request.urlopen(url, timeout=5) as response:
            body = json.load(response)
        return [str(item["id"]) for item in body.get("data", []) if item.get("id")]
    except (OSError, ValueError, KeyError, error.URLError):
        return []


def _cloud_models(provider: str, secret: str | None) -> list[str]:
    """List account-visible IDs; authentication stays in request headers."""
    if provider not in {"openai", "anthropic", "google", "grok"}:
        return []
    key = os.getenv(ENV_KEYS[provider]) or secret
    if not key:
        try:
            key = keyring.get_password("cognigenesis-harness", provider)
        except Exception:
            return []
    if not key:
        return []
    urls = {
        "openai": "https://api.openai.com/v1/models",
        "anthropic": "https://api.anthropic.com/v1/models?limit=100",
        "google": "https://generativelanguage.googleapis.com/v1beta/models?pageSize=1000",
        "grok": "https://api.x.ai/v1/models",
    }
    headers = ({"x-api-key": key, "anthropic-version": "2023-06-01"} if provider == "anthropic"
               else {"x-goog-api-key": key} if provider == "google"
               else {"Authorization": f"Bearer {key}"})
    try:
        with request.urlopen(request.Request(urls[provider], headers=headers), timeout=8) as response:
            body = json.load(response)
        rows = body.get("models", []) if provider == "google" else body.get("data", [])
        models = []
        for item in rows:
            if provider == "google" and "generateContent" not in item.get("supportedGenerationMethods", []):
                continue
            name = item.get("name" if provider == "google" else "id", "")
            if name:
                models.append(str(name).removeprefix("models/"))
        return sorted(set(models), key=str.casefold)
    except (OSError, ValueError, KeyError, error.URLError):
        return []


def _input(label: str, default: str | None = None) -> str:
    from prompt_toolkit import prompt
    suffix = f" [{default}]" if default else ""
    return prompt(f"  {label}{suffix}: ").strip() or (default or "")


def run_wizard() -> bool:
    """Persist only a complete selection; never save a partially configured provider."""
    settings = load_settings()
    provider = choose("Choose a model provider", PROVIDERS, step=1)
    if provider is None:
        return False

    print("\n  ◈ Connection  ·  step 2 / 5")
    endpoint = None
    if provider == "ollama":
        endpoint = _input("Ollama address (local or LAN)", settings.ollama_base_url)
    elif provider in {"litert", "edge", "local"}:
        defaults = {"litert": "http://127.0.0.1:9379", "local": "http://127.0.0.1:1234"}
        endpoint = _input("Server origin (no /v1 suffix)", defaults.get(provider))
    elif provider == "meta":
        endpoint = _input("Full /v1/chat/completions endpoint")
    else:
        print("  API keys are separate from consumer subscriptions. No browser tokens are imported.")

    secret = None
    if provider in ENV_KEYS:
        env_name = ENV_KEYS[provider]
        env_key = os.getenv(env_name)
        try:
            stored_key = keyring.get_password("cognigenesis-harness", provider)
        except Exception:
            stored_key = None
        if env_key:
            print(f"  Using {env_name} from your environment.")
        elif stored_key:
            action = choose("Connect your account", [
                ("existing", "Use saved API key", "Stored in the operating system credential manager"),
                ("replace", "Use a different API key", "Enter a new key without displaying it"),
            ], step=2, search=False)
            if action is None:
                return False
            if action == "replace":
                secret = getpass.getpass(f"  New {provider} API key (hidden): ").strip()
        else:
            secret = getpass.getpass(f"  {provider} API key (hidden; leave blank to cancel): ").strip()
        if secret == "" or (not env_key and not stored_key and not secret):
            return False
    if provider in {"meta", "edge"} and not endpoint:
        print("  This provider requires a server address.")
        return False

    models = []
    if provider in {"ollama", "litert", "edge", "local"} and endpoint:
        try:
            models = _models(endpoint, openai_compatible=provider != "ollama")
        except (OSError, ValueError, error.URLError) as exc:
            print(f"  Could not list models at {endpoint}: {exc}")
    if provider in {"openai", "anthropic", "google", "grok"}:
        models = _cloud_models(provider, secret)
    model_rows = [(name, name, "Installed on your server" if provider in {"ollama", "litert", "edge", "local"} else "Listed for this API key") for name in models]
    if provider in DEFAULT_MODELS and DEFAULT_MODELS[provider]:
        name = DEFAULT_MODELS[provider]
        if name not in models:
            model_rows.append((name, name, "Suggested ID · availability depends on your account"))
    model_rows.append(("__manual__", "Enter a model ID", "Use the exact ID offered by your provider"))
    selection = choose("Choose a default model", model_rows, step=3)
    if selection is None:
        return False
    model = _input("Exact model ID") if selection == "__manual__" else selection
    if not model:
        return False

    composer = choose("Choose your terminal layout", [
        ("signal", "Signal (recommended)", "◈ cogni  ·  model  ·  workspace  ›  your next move"),
        ("compact", "Compact", "cogni ›  a clean single-line prompt"),
        ("minimal", "Minimal", "›  only the prompt"),
    ], step=4, search=False)
    if composer is None:
        return False

    print("\n  ◈ Workspace  ·  step 5 / 5")
    workspace = _input("Default workspace", settings.default_workspace or ".")
    if not workspace:
        return False
    summary = [
        ("save", "Save and start", f"{provider} / {model}  ·  {workspace}"),
        ("back", "Cancel", "Keep your current configuration"),
    ]
    if choose("Review your setup", summary, step=5, search=False) != "save":
        return False
    if secret is not None:
        try:
            keyring.set_password("cognigenesis-harness", provider, secret)
        except Exception as exc:
            print(f"  Credential store unavailable: {exc}. Set {ENV_KEYS[provider]} and rerun setup.")
            return False
    settings.provider = provider
    settings.model = model
    settings.default_workspace = workspace
    settings.composer_style = composer
    if provider == "ollama":
        settings.ollama_base_url = endpoint.rstrip("/")
    elif provider in {"meta", "litert", "edge", "local"}:
        settings.cloud_base_url = endpoint.rstrip("/") if endpoint else None
    save_settings(settings)
    print(f"\n  ✓ Cognigenesis is ready with {provider} / {model}.")
    print("  Run: cogni harness\n")
    return True
