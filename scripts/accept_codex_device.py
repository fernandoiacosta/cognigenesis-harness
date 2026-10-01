#!/usr/bin/env python3
"""Create a credential-free PASS/FAIL record on an actual Codex device.

Dry-run is the default. Pass ``--apply`` only after reviewing the discovered
Codex home and proposed target. The applied adapter is always restored before
the script exits, including after verification failures.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cognigenesis import __version__
from cognigenesis.integrations import (
    apply_plan,
    create_codex_plan,
    discover_codex,
    restore_integration,
    verify_integration,
)


def _sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _snapshot(target: Path, names: list[str]) -> dict[str, str | None]:
    return {name: _sha256(target / name) for name in names}


def _write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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

    started = datetime.now(timezone.utc)
    output = args.output or Path(
        f"codex-device-acceptance-{started.strftime('%Y%m%dT%H%M%SZ')}.json"
    )
    discovery = discover_codex()
    report: dict[str, Any] = {
        "result": "NOT_RUN",
        "scope": "actual Codex device lifecycle",
        "started_at": started.isoformat(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "cognigenesis_version": __version__,
        "real_device_acceptance": True,
        "credentials_inspected": False,
        "credentials_copied": False,
        "discovery": {
            "detected": discovery["detected"],
            "indicators": discovery["indicators"],
        },
    }

    if not discovery["detected"]:
        report.update(result="FAIL", failure="Codex was not detected")
        _write_report(output, report)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1

    plan = create_codex_plan()
    names = list(plan.files)
    target = Path(plan.target_dir)
    before = _snapshot(target, names)
    report.update(
        plan_id=plan.plan_id,
        adapter_version=plan.adapter_version,
        proposed_only=plan.proposed_only,
        proposed_files=names,
        before_hashes=before,
    )

    if not args.apply:
        report.update(
            result="DRY_RUN",
            next_action="Review this report, then rerun with --apply.",
        )
        _write_report(output, report)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    applied = False
    try:
        applied_record = apply_plan(plan)
        applied = True
        verified = verify_integration()
        report.update(
            activation_state=applied_record["activation_state"],
            observed_hashes=verified.get("observed_hashes", {}),
            hashes_verified=bool(verified.get("verified")),
        )
        if not verified.get("verified"):
            raise RuntimeError("installed adapter hashes did not verify")
    except Exception as exc:
        report.update(result="FAIL", failure=f"{type(exc).__name__}: {exc}")
    finally:
        if applied:
            try:
                restored = restore_integration()
                report["restore_reported"] = bool(restored.get("restored"))
            except Exception as exc:
                report["restore_reported"] = False
                report["restore_failure"] = f"{type(exc).__name__}: {exc}"

    after = _snapshot(target, names)
    report["after_hashes"] = after
    report["preexisting_content_restored"] = after == before
    if (
        report.get("result") != "FAIL"
        and report.get("hashes_verified")
        and report.get("restore_reported")
        and after == before
    ):
        report["result"] = "PASS"
    else:
        report["result"] = "FAIL"
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    _write_report(output, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
