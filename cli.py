from __future__ import annotations

import argparse
from pathlib import Path

from harness import build_engine
from providers.base import ProviderError

VERSION = "0.4.0"


def main() -> None:
    parser = argparse.ArgumentParser(prog="cogni", description="Cognigenesis Harness CLI")
    parser.add_argument("objective", nargs="?", help="Objective for the harness")
    parser.add_argument("--workspace", default="workspace", help="Sandbox workspace directory")
    parser.add_argument("--provider", default=None, choices=["ollama", "stub"], help="Model provider (default: ollama or COGNI_PROVIDER)")
    parser.add_argument("--model", default=None, help="Model name (or COGNI_OLLAMA_MODEL)")
    parser.add_argument("--base-url", default=None, help="Ollama base URL (or COGNI_OLLAMA_BASE_URL)")
    parser.add_argument("--timeout", default=None, type=float, help="Provider timeout seconds (or COGNI_OLLAMA_TIMEOUT)")
    parser.add_argument("--version", action="version", version=f"cognigenesis-harness {VERSION}")
    args = parser.parse_args()

    if not args.objective:
        parser.print_help()
        return

    workspace = Path(args.workspace).resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    try:
        engine = build_engine(
            workspace,
            provider_name=args.provider,
            model=args.model,
            base_url=args.base_url,
            timeout=args.timeout,
        )
        print(engine.run(args.objective))
    except ProviderError as exc:
        parser.exit(2, f"Provider error: {exc}\n")


if __name__ == "__main__":
    main()
