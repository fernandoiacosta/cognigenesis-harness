#!/usr/bin/env python3
"""Create a credential-free PASS/FAIL record on an actual Codex device.

Dry-run is the default. Pass ``--apply`` only after reviewing the discovered
Codex home and proposed target. The applied adapter is always restored before
the script exits, including after verification failures.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cognigenesis.acceptance import run_codex_acceptance


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="temporarily apply, verify, and restore the reviewed adapter",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="report path (default: timestamped JSON in the current directory)",
    )
    args = parser.parse_args()

    code, report = run_codex_acceptance(apply=args.apply, output=args.output)
    print(json.dumps(report, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
