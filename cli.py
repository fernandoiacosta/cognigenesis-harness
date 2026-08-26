from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style

from cognigenesis import __version__
from cognigenesis.bootstrap import (
    aionui_configuration,
    auto_setup,
    pull_model,
    qualify_settings,
    run_checks,
)
from cognigenesis.config import config_path, history_path, load_settings
from cognigenesis.console import (
    RuntimeIdentity,
    assistant_message,
    banner,
    console,
    error_message,
    status_table,
    success_message,
    warning_message,
)
from core.model_profile import TrustTier
from core.stdio import configure_utf8_stdio
from harness import build_engine
from providers.base import ProviderError
from providers.factory import provider_identity

VERSION = __version__
KNOWN_COMMANDS = {"run", "chat", "setup", "qualify", "doctor", "aionui", "config"}


def _provider_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workspace", default=None, help="Workspace directory (default: current directory/config)")
    parser.add_argument("--provider", default=None, choices=["ollama", "stub"])
    parser.add_argument("--model", default=None, help="Ollama model name")
    parser.add_argument("--base-url", default=None, help="Ollama base URL")
    parser.add_argument("--timeout", default=None, type=float, help="Provider timeout in seconds")


def _normalize_argv(argv: list[str]) -> list[str]:
    if not argv:
        return ["chat"] if sys.stdin.isatty() else []
    if argv[0] in {"-h", "--help", "--version"} or argv[0] in KNOWN_COMMANDS:
        return argv
    return ["run", *argv]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cogni", description="Cognigenesis Harness — local-first adaptive intelligence runtime")
    parser.add_argument("--version", action="version", version=f"cognigenesis-harness {VERSION}")
    sub = parser.add_subparsers(dest="command")

    run = sub.add_parser("run", help="Run one objective and exit")
    _provider_args(run)
    run.add_argument("objective", nargs="+", help="Objective to execute")

    chat = sub.add_parser("chat", help="Start the persistent themed chat interface")
    _provider_args(chat)

    setup = sub.add_parser("setup", help="Configure, discover, and qualify the local Ollama model")
    setup.add_argument("--model", default=None)
    setup.add_argument("--base-url", default=None)
    setup.add_argument("--timeout", type=float, default=None)
    setup.add_argument("--pull", action="store_true", help="Pull the selected Ollama model if it is missing")
    setup.add_argument("--skip-qualify", action="store_true", help="Skip first-run behavioral qualification")

    qualify = sub.add_parser("qualify", help="Evaluate the configured model and persist its trust profile")
    qualify.add_argument("--model", default=None)
    qualify.add_argument("--base-url", default=None)
    qualify.add_argument("--timeout", type=float, default=None)
    qualify.add_argument("--force", action="store_true", help="Rerun even when a saved profile exists")

    doctor = sub.add_parser("doctor", help="Diagnose installation, Ollama, model, qualification, PATH, and AionUi")
    doctor.add_argument("--json", action="store_true", dest="as_json")

    aionui = sub.add_parser("aionui", help="Show first-class AionUi custom-agent configuration")
    aionui.add_argument("--json", action="store_true", dest="as_json")

    config = sub.add_parser("config", help="Show the resolved persistent configuration")
    config.add_argument("--json", action="store_true", dest="as_json")
    return parser


def _resolved_workspace(raw: str | None) -> Path:
    settings = load_settings()
    value = raw or settings.default_workspace or "."
    path = Path(value).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _make_engine(args: argparse.Namespace):
    workspace = _resolved_workspace(getattr(args, "workspace", None))
    return build_engine(
        workspace,
        provider_name=getattr(args, "provider", None),
        model=getattr(args, "model", None),
        base_url=getattr(args, "base_url", None),
        timeout=getattr(args, "timeout", None),
    ), workspace


def _chat_help() -> None:
    console.print(
        "[cogni.muted]Commands[/]\n"
        "  [cogni.cyan]/help[/]          Show commands\n"
        "  [cogni.cyan]/new[/]           Clear conversational context\n"
        "  [cogni.cyan]/state[/]         Show current runtime state\n"
        "  [cogni.cyan]/capabilities[/]  List executable capabilities\n"
        "  [cogni.cyan]/provider[/]      Show active provider/model\n"
        "  [cogni.cyan]/workspace[/]     Show active workspace\n"
        "  [cogni.cyan]/doctor[/]        Run health diagnostics\n"
        "  [cogni.cyan]/exit[/]          Leave chat\n"
    )


def _prompt_session() -> PromptSession:
    style = Style.from_dict({"prompt": "#62F5FF bold", "continuation": "#8B7CFF"})
    return PromptSession(
        history=FileHistory(str(history_path())),
        auto_suggest=AutoSuggestFromHistory(),
        style=style,
        multiline=False,
    )


def _run_chat(args: argparse.Namespace) -> int:
    engine, workspace = _make_engine(args)
    provider_name, model_name = provider_identity(engine.provider)
    banner(VERSION, RuntimeIdentity(provider_name, model_name, str(workspace)))
    console.print(f"[cogni.muted]Trust:[/] {engine.policy.model_profile.tier.name}  [cogni.muted]• Type /help for commands.[/]\n")
    session = _prompt_session()

    while True:
        try:
            prompt = session.prompt([("class:prompt", "You › ")]).strip()
        except EOFError:
            console.print("[cogni.muted]Session closed.[/]")
            return 0
        except KeyboardInterrupt:
            console.print("[cogni.muted]Input cancelled.[/]")
            continue

        if not prompt:
            continue
        if prompt in {"/exit", "/quit"}:
            return 0
        if prompt == "/help":
            _chat_help(); continue
        if prompt == "/new":
            engine.reset_conversation(); success_message("Conversation context cleared."); continue
        if prompt == "/state":
            console.print_json(json.dumps(engine.state.snapshot(), ensure_ascii=False)); continue
        if prompt == "/capabilities":
            for capability in engine.registry.describe():
                console.print(f"[cogni.violet]•[/] [bold]{capability['id']}[/] [cogni.muted]{capability['description']}[/]")
            continue
        if prompt == "/provider":
            p, m = provider_identity(engine.provider)
            status_table([("provider", p, "cogni.green"), ("model", m, ""), ("trust", engine.policy.model_profile.tier.name, "cogni.violet")]); continue
        if prompt == "/workspace":
            console.print(str(workspace)); continue
        if prompt == "/doctor":
            _render_checks(run_checks()); continue
        if prompt.startswith("/"):
            warning_message(f"Unknown command: {prompt}. Type /help."); continue

        try:
            with console.status("[cogni.violet]Cognigenesis is working…[/]", spinner="dots"):
                result = engine.run(prompt)
            assistant_message(result)
        except ProviderError as exc:
            error_message(str(exc))
        except Exception as exc:
            error_message(f"Runtime error: {exc}")


def _render_checks(checks) -> int:
    rows = []
    failures = 0
    for check in checks:
        if check.ok:
            rows.append((check.name, check.detail, "cogni.green"))
        else:
            failures += 1
            rows.append((check.name, check.detail, "cogni.red"))
    status_table(rows)
    for check in checks:
        if not check.ok and check.fix:
            console.print(f"[cogni.amber]Fix {check.name}:[/] {check.fix}")
    return 0 if failures == 0 else 1


def _render_qualification(profile, evidence, created: bool) -> int:
    status_table([
        ("provider", profile.provider, "cogni.green"),
        ("model", profile.model, ""),
        ("trust tier", profile.tier.name, "cogni.violet"),
        ("score", f"{profile.score:.3f}", "cogni.cyan"),
        ("profile", "updated" if created else "existing", "cogni.green"),
    ])
    for item in evidence:
        marker = "✓" if item["passed"] else "✗"
        style = "cogni.green" if item["passed"] else "cogni.red"
        console.print(f"[{style}]{marker}[/] {item['case']}  [cogni.muted]{item['score']:.2f}[/]")
    if profile.tier >= TrustTier.TRUSTED:
        success_message("Model qualified for normal trust-gated workspace operation.")
        return 0
    warning_message("Model remains below TRUSTED. Mutation capabilities stay restricted; review the failed qualification cases.")
    return 1


def _run_qualify(args: argparse.Namespace) -> int:
    banner(VERSION)
    settings, _ = auto_setup(model=args.model, base_url=args.base_url, timeout=args.timeout)
    try:
        with console.status("[cogni.violet]Qualifying model behavior…[/]", spinner="dots"):
            profile, evidence, created = qualify_settings(settings, force=args.force)
    except Exception as exc:
        error_message(f"Qualification failed: {exc}")
        return 1
    return _render_qualification(profile, evidence, created)


def _run_setup(args: argparse.Namespace) -> int:
    banner(VERSION)
    settings, checks = auto_setup(model=args.model, base_url=args.base_url, timeout=args.timeout)
    if args.pull:
        try:
            console.print(f"[cogni.violet]Pulling Ollama model:[/] {settings.model}")
            pull_model(settings.model or "llama3.1:8b")
            settings, checks = auto_setup(model=settings.model, base_url=settings.ollama_base_url, timeout=settings.ollama_timeout)
        except Exception as exc:
            error_message(f"Could not pull model: {exc}")

    model_ok = any(check.name == "Model" and check.ok for check in checks)
    if model_ok and not args.skip_qualify:
        try:
            existing_ok = any(check.name == "Qualification" and check.ok for check in checks)
            if not existing_ok:
                console.print("[cogni.violet]Running bounded model qualification…[/]")
                profile, evidence, created = qualify_settings(settings)
                _render_qualification(profile, evidence, created)
                checks = run_checks(settings)
        except Exception as exc:
            warning_message(f"Qualification did not complete: {exc}. You can retry with: cogni qualify --force")
            checks = run_checks(settings)

    console.print(f"[cogni.muted]Config:[/] {config_path()}")
    console.print(f"[cogni.muted]Provider:[/] {settings.provider}")
    console.print(f"[cogni.muted]Model:[/] {settings.model}")
    code = _render_checks(checks)
    if code == 0:
        success_message("Cognigenesis is ready. Run: cogni chat")
    return code


def _run_doctor(as_json: bool) -> int:
    checks = run_checks()
    if as_json:
        print(json.dumps([check.__dict__ for check in checks], indent=2, ensure_ascii=False))
        return 0 if all(check.ok for check in checks) else 1
    banner(VERSION)
    return _render_checks(checks)


def _run_aionui(as_json: bool) -> int:
    cfg = aionui_configuration()
    if as_json:
        print(json.dumps(cfg, indent=2, ensure_ascii=False)); return 0
    banner(VERSION)
    status_table([
        ("Display name", cfg["display_name"], "cogni.cyan"),
        ("Command", cfg["command"], "cogni.green"),
        ("Arguments", "<empty>", ""),
        ("Logo", cfg["image"], "cogni.magenta"),
    ])
    console.print("[cogni.muted]Environment[/]")
    for key, value in cfg["environment"].items():
        console.print(f"  [cogni.violet]{key}[/]={value}")
    return 0


def main() -> None:
    configure_utf8_stdio()
    argv = _normalize_argv(sys.argv[1:])
    parser = _parser()
    if not argv:
        parser.print_help(); return
    args = parser.parse_args(argv)

    if args.command == "chat":
        raise SystemExit(_run_chat(args))
    if args.command == "setup":
        raise SystemExit(_run_setup(args))
    if args.command == "qualify":
        raise SystemExit(_run_qualify(args))
    if args.command == "doctor":
        raise SystemExit(_run_doctor(args.as_json))
    if args.command == "aionui":
        raise SystemExit(_run_aionui(args.as_json))
    if args.command == "config":
        settings = load_settings()
        if args.as_json:
            print(json.dumps(settings.__dict__, indent=2, ensure_ascii=False))
        else:
            banner(VERSION); status_table([(k, str(v), "") for k, v in settings.__dict__.items()])
        return
    if args.command == "run":
        engine, _workspace = _make_engine(args)
        objective = " ".join(args.objective)
        try:
            result = engine.run(objective)
            if sys.stdout.isatty() and not os.getenv("NO_COLOR"):
                assistant_message(result)
            else:
                print(result)
        except ProviderError as exc:
            error_message(str(exc))
            raise SystemExit(2) from exc
        return

    parser.print_help()


if __name__ == "__main__":
    main()
