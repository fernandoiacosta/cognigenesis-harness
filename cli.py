from __future__ import annotations

import argparse
import json
from pathlib import Path

from harness import build_engine
from providers.base import ProviderError
from providers.factory import provider_identity


VERSION = "0.5.0"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cogni", description="Cognigenesis Harness CLI")
    parser.add_argument("objective", nargs="?", help="Objective, or 'chat' for interactive mode")
    parser.add_argument("--workspace", default="workspace", help="Sandbox workspace directory")
    parser.add_argument("--provider", default=None, choices=["ollama", "stub"])
    parser.add_argument("--model", default=None)
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--timeout", default=None, type=float)
    parser.add_argument("--version", action="version", version=f"cognigenesis-harness {VERSION}")
    return parser


def _make_engine(args: argparse.Namespace):
    workspace = Path(args.workspace).resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    return build_engine(
        workspace,
        provider_name=args.provider,
        model=args.model,
        base_url=args.base_url,
        timeout=args.timeout,
    ), workspace


def _print_chat_help() -> None:
    print(
        "Commands:\n"
        "  /help          Show this help\n"
        "  /new           Clear conversational context\n"
        "  /state         Show current runtime state\n"
        "  /capabilities  List registered capabilities\n"
        "  /provider      Show active provider/model\n"
        "  /workspace     Show active workspace\n"
        "  /exit          Leave chat\n"
    )


def _run_chat(args: argparse.Namespace) -> int:
    engine, workspace = _make_engine(args)
    provider_name, model_name = provider_identity(engine.provider)

    print(f"Cognigenesis Harness {VERSION}")
    print(f"Provider:  {provider_name}")
    print(f"Model:     {model_name}")
    print(f"Workspace: {workspace}")
    print("Type /help for commands.\n")

    while True:
        try:
            prompt = input("You > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting Cognigenesis chat.")
            return 0

        if not prompt:
            continue
        if prompt in {"/exit", "/quit"}:
            return 0
        if prompt == "/help":
            _print_chat_help()
            continue
        if prompt == "/new":
            engine.reset_conversation()
            print("Conversation context cleared.\n")
            continue
        if prompt == "/state":
            print(json.dumps(engine.state.snapshot(), indent=2, ensure_ascii=False))
            print()
            continue
        if prompt == "/capabilities":
            for capability in engine.registry.describe():
                print(f"- {capability['id']}: {capability['description']}")
            print()
            continue
        if prompt == "/provider":
            provider_name, model_name = provider_identity(engine.provider)
            print(f"{provider_name} / {model_name}\n")
            continue
        if prompt == "/workspace":
            print(f"{workspace}\n")
            continue
        if prompt.startswith("/"):
            print(f"Unknown command: {prompt}. Type /help.\n")
            continue

        try:
            result = engine.run(prompt)
        except ProviderError as exc:
            print(f"Cogni > Provider error: {exc}\n")
            continue
        except Exception as exc:
            print(f"Cogni > Runtime error: {exc}\n")
            continue

        print(f"Cogni > {result}\n")


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.objective == "chat":
        raise SystemExit(_run_chat(args))

    if not args.objective:
        parser.print_help()
        return

    engine, _workspace = _make_engine(args)
    try:
        print(engine.run(args.objective))
    except ProviderError as exc:
        raise SystemExit(f"Provider error: {exc}") from exc


if __name__ == "__main__":
    main()
