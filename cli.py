from __future__ import annotations

import argparse
import json
import getpass
import keyring
import os
import sys
import webbrowser
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
from cognigenesis.commandcenter.server import serve_command_center
from cognigenesis.config import config_path, history_path, load_settings, save_settings
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
from cognigenesis.fabric.patterns import TeamPattern
from core.model_profile import TrustTier
from core.stdio import configure_utf8_stdio
from harness import build_engine, build_team_runner
from providers.base import ProviderError
from providers.factory import provider_identity

VERSION = __version__
KNOWN_COMMANDS = {"run", "chat", "team", "command-center", "setup", "qualify", "doctor", "aionui", "config", "login", "harness"}


def _provider_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workspace", default=None, help="Workspace directory (default: current directory/config)")
    parser.add_argument("--provider", default=None, choices=["ollama", "openai", "anthropic", "google", "grok", "meta", "edge", "litert", "stub"])
    parser.add_argument("--model", default=None, help="Model name")
    parser.add_argument("--base-url", default=None, help="Provider base URL")
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

    harness = sub.add_parser("harness", help="Start Cognigenesis Harness")
    _provider_args(harness)

    team = sub.add_parser("team", help="Run a bounded Cognigenesis multi-agent team")
    _provider_args(team)
    team.add_argument(
        "--pattern",
        choices=[pattern.value for pattern in TeamPattern],
        default=TeamPattern.ADVERSARIAL_COUNCIL.value,
        help="Team coordination pattern",
    )
    team.add_argument("objective", nargs="+", help="Mission for the team")

    command_center = sub.add_parser("command-center", help="Launch the local Cognigenesis graphical Command Center")
    command_center.add_argument("--workspace", default=None)
    command_center.add_argument("--host", default="127.0.0.1")
    command_center.add_argument("--port", default=8765, type=int)
    command_center.add_argument("--open", action="store_true", dest="open_browser", help="Open the dashboard in the default browser")

    setup = sub.add_parser("setup", help="Configure, discover, and qualify the local Ollama model")
    setup.add_argument("--model", default=None)
    setup.add_argument("--base-url", default=None)
    setup.add_argument("--timeout", type=float, default=None)
    setup.add_argument("--pull", action="store_true", help="Pull the selected Ollama model if it is missing")
    setup.add_argument("--skip-qualify", action="store_true", help="Skip first-run behavioral qualification")

    login = sub.add_parser("login", help="Configure a provider and securely store its API key")
    login.add_argument("provider", choices=["ollama", "openai", "anthropic", "google", "grok", "meta", "edge", "litert"])
    login.add_argument("--model", default=None)
    login.add_argument("--base-url", default=None)

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
        "  [cogni.cyan]/cognition[/]     Inspect hypotheses/evidence/questions\n"
        "  [cogni.cyan]/tasks[/]         Inspect the shared task graph\n"
        "  [cogni.cyan]/events[/]        Inspect recent semantic runtime events\n"
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
        if prompt == "/cognition":
            console.print_json(json.dumps(engine.cognition.snapshot(), ensure_ascii=False))
            continue
        if prompt == "/tasks":
            console.print_json(json.dumps(engine.tasks.snapshot(), ensure_ascii=False))
            continue
        if prompt == "/events":
            console.print_json(json.dumps([event.to_dict() for event in engine.events.history(limit=30)], ensure_ascii=False))
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




def _run_command_center(args: argparse.Namespace) -> int:
    workspace = _resolved_workspace(args.workspace)
    url = f"http://{args.host}:{args.port}"
    banner(VERSION)
    status_table([
        ("mode", "Command Center", "cogni.magenta"),
        ("workspace", str(workspace), ""),
        ("url", url, "cogni.cyan"),
    ])
    console.print("[cogni.muted]The dashboard reads the same persisted task/cognition/team/event state produced by chat and team runs.[/]")
    if args.open_browser:
        webbrowser.open(url)
    try:
        serve_command_center(workspace, host=args.host, port=args.port)
    except KeyboardInterrupt:
        console.print("\n[cogni.muted]Command Center stopped.[/]")
    except OSError as exc:
        error_message(f"Could not start Command Center: {exc}")
        return 1
    return 0


def _run_team(args: argparse.Namespace) -> int:
    workspace = _resolved_workspace(args.workspace)
    pattern = TeamPattern(args.pattern)
    runner, platform = build_team_runner(
        workspace,
        provider_name=args.provider,
        model=args.model,
        base_url=args.base_url,
        timeout=args.timeout,
    )
    banner(VERSION)
    status_table([
        ("mode", "team", "cogni.violet"),
        ("pattern", pattern.value, "cogni.cyan"),
        ("workspace", str(workspace), ""),
        ("model", args.model or load_settings().model or "configured/default", ""),
    ])
    objective = " ".join(args.objective)
    try:
        with console.status(f"[cogni.violet]Running {pattern.value} team…[/]", spinner="dots"):
            result = runner.run(pattern, objective, model=args.model)
    except ProviderError as exc:
        error_message(str(exc))
        return 2
    except Exception as exc:
        error_message(f"Team runtime error: {exc}")
        return 1

    console.print("\n[cogni.muted]Team activity[/]")
    for run in result.runs:
        console.print(
            f"[cogni.violet]•[/] [bold]{run.agent_name}[/] "
            f"[cogni.muted]{run.role}[/] → completed"
        )
    console.print()
    assistant_message(result.final)
    return 0


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

    if args.command == "login":
        from providers.cloud import DEFAULT_MODELS, ENV_KEYS
        settings = load_settings()
        name = args.provider
        if name in ENV_KEYS and not os.getenv(ENV_KEYS[name]):
            secret = getpass.getpass(f"{name} API key (stored in OS credential manager): ").strip()
            if not secret:
                parser.error("An API key is required; alternatively set " + ENV_KEYS[name])
            try:
                keyring.set_password("cognigenesis-harness", name, secret)
            except Exception as exc:
                parser.error(f"Credential storage unavailable: {exc}. Set {ENV_KEYS[name]} in your environment instead.")
        if name == "meta" and not args.base_url:
            parser.error("Meta needs --base-url for your inference host")
        if name == "edge" and not args.base_url:
            parser.error("Edge Gallery requires --base-url for a server-enabled build; stock Gallery has no server")
        if name == "ollama" and args.base_url:
            settings.ollama_base_url = args.base_url.rstrip("/")
        if name in {"edge", "litert", "meta"}:
            settings.cloud_base_url = args.base_url or ("http://127.0.0.1:9379" if name == "litert" else settings.cloud_base_url)
        settings.provider = name
        settings.model = args.model or DEFAULT_MODELS.get(name) or (settings.model if name == "ollama" else None)
        if name in {"meta", "edge", "litert"} and not settings.model:
            parser.error("Specify --model for this provider")
        save_settings(settings)
        success_message(f"Configured {name} / {settings.model or 'automatic'}. Run: cogni chat")
        return
    if args.command in {"chat", "harness"}:
        raise SystemExit(_run_chat(args))
    if args.command == "team":
        raise SystemExit(_run_team(args))
    if args.command == "command-center":
        raise SystemExit(_run_command_center(args))
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
