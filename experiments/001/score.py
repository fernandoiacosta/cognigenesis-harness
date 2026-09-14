from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent

def parse_response(raw: str) -> dict | None:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I)
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        return None

def contains_all(text: str, terms: list[str]) -> float:
    low = text.lower()
    return sum(term.lower() in low for term in terms) / len(terms) if terms else 1.0

def score(case: dict, raw: str) -> dict:
    obj = parse_response(raw)
    parts = {"valid_json": 0.0, "decision": 0.0, "evidence": 0.0, "uncertainty": 0.0, "calibration": 0.0, "next_test": 0.0}
    if obj is None:
        return {"total": 0.0, "parts": parts, "parsed": None}
    parts["valid_json"] = 10.0
    parts["decision"] = 25.0 if str(obj.get("decision", "")).lower() == case["expected_decision"] else 0.0
    cited = {str(x).upper() for x in obj.get("evidence_used", []) if isinstance(x, (str, int))}
    required = {x.upper() for x in case["must_cite"]}
    parts["evidence"] = 20.0 * (len(cited & required) / len(required))
    uncertainty_text = " ".join(str(x) for x in obj.get("uncertainties", []))
    parts["uncertainty"] = 15.0 * contains_all(uncertainty_text, case["must_flag"])
    try:
        confidence = float(obj.get("confidence"))
        parts["calibration"] = 15.0 if 0 <= confidence <= float(case["confidence_ceiling"]) else 0.0
    except (TypeError, ValueError):
        pass
    parts["next_test"] = 15.0 * contains_all(str(obj.get("next_test", "")), case["next_test_terms"])
    return {"total": round(sum(parts.values()), 3), "parts": {k: round(v, 3) for k, v in parts.items()}, "parsed": obj}

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("result_directory", type=Path)
    args = parser.parse_args()
    manifest = json.loads((args.result_directory / "manifest.json").read_text(encoding="utf-8"))
    cases = {c["id"]: c for c in [json.loads(line) for line in (HERE / "cases.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]}
    grouped: dict[str, list[float]] = defaultdict(list)
    diagnostics: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    scored = []
    for record in manifest["records"]:
        result = score(cases[record["case_id"]], record.get("raw_response", "")) if not record.get("error") else {"total": 0.0, "parts": {}, "parsed": None}
        scored.append({**record, "score": result})
        grouped[record["condition"]].append(result["total"])
        for name, value in result["parts"].items():
            diagnostics[record["condition"]][name].append(value)
    means = {k: round(sum(v) / len(v), 3) if v else 0.0 for k, v in grouped.items()}
    delta = round(means.get("cognigenesis", 0.0) - means.get("baseline", 0.0), 3)
    errors = sum(bool(r.get("error")) for r in scored)
    expected = len(cases) * len(manifest.get("seeds", [])) * 2
    invalid = manifest.get("status") != "complete" or len(scored) != expected or errors > 0
    outcome = "INVALID" if invalid else ("WIN" if delta >= 15 else ("LOSS" if delta < -5 else "TIE"))
    report = {
        "experiment": "001", "outcome": outcome, "primary_score_means": means,
        "treatment_minus_baseline": delta,
        "diagnostic_means": {condition: {name: round(sum(values) / len(values), 3) for name, values in metrics.items()} for condition, metrics in diagnostics.items()},
        "expected_records": expected, "completed_records": len(scored), "errors": errors,
    }
    (args.result_directory / "scored.json").write_text(json.dumps(scored, indent=2) + "\n", encoding="utf-8")
    (args.result_directory / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
