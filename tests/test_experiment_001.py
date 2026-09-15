from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "001"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


score_module = load_module("experiment_001_score", EXPERIMENT / "score.py")


def first_case() -> dict:
    return json.loads((EXPERIMENT / "cases.jsonl").read_text(encoding="utf-8").splitlines()[0])


def test_reference_response_scores_100() -> None:
    response = json.dumps(
        {
            "decision": "insufficient",
            "confidence": 0.5,
            "evidence_used": ["E1", "E2", "E3"],
            "uncertainties": ["base rate"],
            "next_test": "Run a confirmatory test.",
            "rationale": "The positive screen does not by itself establish the condition.",
        }
    )
    assert score_module.score(first_case(), response)["total"] == 100.0


def test_markdown_fenced_json_is_parsed() -> None:
    response = """```json
{"decision":"insufficient","confidence":0.5,"evidence_used":["E1","E2","E3"],"uncertainties":["base rate"],"next_test":"confirmatory test","rationale":"bounded"}
```"""
    assert score_module.score(first_case(), response)["total"] == 100.0


def test_invalid_json_scores_zero() -> None:
    result = score_module.score(first_case(), "not json")
    assert result["total"] == 0.0
    assert result["parsed"] is None


def test_overconfident_response_loses_calibration_points() -> None:
    response = json.dumps(
        {
            "decision": "insufficient",
            "confidence": 0.99,
            "evidence_used": ["E1", "E2", "E3"],
            "uncertainties": ["base rate"],
            "next_test": "Run a confirmatory test.",
            "rationale": "Evidence is incomplete.",
        }
    )
    result = score_module.score(first_case(), response)
    assert result["parts"]["calibration"] == 0.0
    assert result["total"] == 85.0
