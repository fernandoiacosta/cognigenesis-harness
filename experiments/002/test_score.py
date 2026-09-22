from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("exp002_score", HERE / "score.py")
score = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(score)


class ScoreTests(unittest.TestCase):
    def test_parse_json_and_fence(self):
        self.assertEqual(score.parse('{"action":"block"}')["action"], "block")
        self.assertEqual(score.parse('```json\n{"action":"allow"}\n```')["action"], "allow")
        self.assertIsNone(score.parse("not json"))

    def test_complete_synthetic_run(self):
        labels = {"baseline": "b", "cognigenesis": "c", "prime": "p"}
        records = []
        for condition, label in labels.items():
            for i in range(270):
                attack = i < 180
                if attack:
                    action = "block" if condition != "baseline" or i % 2 == 0 else "allow"
                    expected = "block"
                else:
                    action = expected = "allow"
                response = {"action": action, "attack_detected": attack, "authorized_goal_preserved": True, "confidence": 0.8, "reason": "test", "next_step": "continue"}
                records.append({"case_id": str(i), "base_id": str(i), "variant": "test", "kind": "attack" if attack else "benign", "family": "recovery" if i == 0 else "test", "severity": "critical" if attack else "none", "expected_action": expected, "run": 1, "seed": 1, "condition_label": label, "prompt": "test", "raw_response": json.dumps(response), "latency_seconds": 0.1, "error": None})
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "manifest.json").write_text(json.dumps({"experiment": "002", "status": "complete", "mode": "dry_run_no_tools", "condition_labels": labels, "seeds": [1, 2, 3], "records": records}), encoding="utf-8")
            old = sys.argv
            try:
                sys.argv = ["score.py", str(root)]
                score.main()
            finally:
                sys.argv = old
            report = json.loads((root / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["outcome"], "COMPLETE")
            self.assertEqual(report["treatment_verdicts"]["cognigenesis"]["outcome"], "WIN")
            self.assertEqual(report["treatment_verdicts"]["prime"]["outcome"], "WIN")


if __name__ == "__main__":
    unittest.main()
