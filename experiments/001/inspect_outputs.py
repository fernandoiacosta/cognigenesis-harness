"""Supplementary interpretation of frozen Experiment 001 model outputs.

This does NOT alter its frozen prompts, original scorer, or declared outcome.
It measures extractable decisions separately from answer formatting.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
import sys

# Also works from a source checkout without a package installation.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from cognigenesis.runtime.output_interpreter import interpret_output

HERE = Path(__file__).resolve().parent


def inspect(result_dir: Path) -> dict:
    manifest = json.loads((result_dir / "manifest.json").read_text(encoding="utf-8"))
    cases = {
        case["id"]: case
        for case in (
            json.loads(line)
            for line in (HERE / "cases.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }
    counts: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    individual = []

    for item in manifest.get("records", []):
        cond = item["condition"]
        stat = counts[cond]
        stat["n"] += 1
        error = item.get("error")
        if error:
            stat["errors"] += 1
            individual.append({"case_id": item["case_id"], "condition": cond, "error": str(error)})
            continue
        interpreted = interpret_output(item.get("raw_response", ""))
        case = cases[item["case_id"]]
        stat["json_format"] += interpreted.format in {"json", "fenced_json", "embedded_json"}
        stat["understood_decision"] += interpreted.decision is not None
        stat["ambiguous"] += interpreted.ambiguous
        stat["matches_frozen_label"] += interpreted.decision == case["expected_decision"]
        stat["has_confidence_label"] += interpreted.confidence is not None
        stat["has_uncertainties"] += bool(interpreted.uncertainties)
        stat["has_next_test"] += bool(interpreted.next_test)
        expected_ids = set(case["must_cite"])
        stat["frozen_evidence_recall_sum"] += (
            len(set(interpreted.evidence_ids) & expected_ids) / len(expected_ids)
            if expected_ids else 1
        )
        individual.append({
            "case_id": item["case_id"],
            "seed": item.get("seed"),
            "condition": cond,
            **interpreted.metadata(),
            "matches_frozen_label": interpreted.decision == case["expected_decision"],
        })

    totals = {k: dict(v) for k, v in counts.items()}
    result = {
        "experiment": "001",
        "status": "SUPPLEMENTARY_DIAGNOSTIC_NOT_FROZEN_SCORE",
        "note": (
            "Label matching is not independent reasoning correctness; plain-text "
            "extraction is conservative and cannot verify whether a rationale is sound."
        ),
        "model": manifest.get("model"),
        "model_digest": manifest.get("model_digest"),
        "counts_by_condition": totals,
        "records": individual,
    }
    path = result_dir / "output_interpretation.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("result_directory", type=Path)
    args = parser.parse_args()
    report = inspect(args.result_directory)
    print(json.dumps({k: v for k, v in report.items() if k != "records"}, indent=2))


if __name__ == "__main__":
    main()
