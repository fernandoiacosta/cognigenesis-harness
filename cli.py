from __future__ import annotations

import argparse
from pathlib import Path

from harness import build_engine


def main() -> None:
    parser = argparse.ArgumentParser(prog="cogni", description="Cognigenesis Harness CLI")
    parser.add_argument("objective", nargs="?", help="Objective for the harness")
    parser.add_argument("--workspace", default="workspace", help="Sandbox workspace directory")
    parser.add_argument("--version", action="version", version="cognigenesis-harness 0.2.0")
    args = parser.parse_args()

    if not args.objective:
        parser.print_help()
        return

    workspace = Path(args.workspace).resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    engine = build_engine(workspace)
    print(engine.run(args.objective))


if __name__ == "__main__":
    main()
