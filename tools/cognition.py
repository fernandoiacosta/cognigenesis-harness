from __future__ import annotations

from cognigenesis.cognition.ledger import CognitiveLedger, Evidence, Hypothesis, OpenQuestion
from core.registry import CapabilityRegistry
from core.types import Capability


def register_cognition_tools(registry: CapabilityRegistry, ledger: CognitiveLedger) -> None:
    def add_hypothesis(args: dict):
        item = ledger.add_hypothesis(Hypothesis(
            claim=str(args["claim"]),
            mechanism=str(args.get("mechanism", "")),
            confidence=float(args.get("confidence", 0.5)),
            status=str(args.get("status", "untested")),
        ))
        return {"hypothesis": item.__dict__, "metrics": ledger.snapshot()["metrics"]}

    def add_evidence(args: dict):
        item = ledger.add_evidence(
            Evidence(
                claim=str(args["claim"]),
                source=args.get("source"),
                polarity=str(args.get("polarity", "neutral")),
                confidence=float(args.get("confidence", 0.5)),
            ),
            hypothesis_id=args.get("hypothesis_id"),
        )
        return {"evidence": item.__dict__, "metrics": ledger.snapshot()["metrics"]}

    def add_question(args: dict):
        item = ledger.add_question(OpenQuestion(
            question=str(args["question"]),
            priority=int(args.get("priority", 1)),
        ))
        return {"question": item.__dict__, "metrics": ledger.snapshot()["metrics"]}

    registry.register(Capability(
        "cognition.hypothesis.add",
        "Record an explicit candidate hypothesis with mechanism and confidence. Use for complex or uncertain reasoning, not trivial chat.",
        add_hypothesis,
        parameters={
            "type": "object",
            "properties": {
                "claim": {"type": "string"},
                "mechanism": {"type": "string"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "status": {"type": "string", "enum": ["active", "rejected", "accepted", "untested"]},
            },
            "required": ["claim"],
            "additionalProperties": False,
        },
    ))
    registry.register(Capability(
        "cognition.evidence.add",
        "Record evidence that supports, contradicts, or is neutral toward a hypothesis.",
        add_evidence,
        parameters={
            "type": "object",
            "properties": {
                "claim": {"type": "string"},
                "source": {"type": ["string", "null"]},
                "polarity": {"type": "string", "enum": ["supports", "contradicts", "neutral"]},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "hypothesis_id": {"type": ["string", "null"]},
            },
            "required": ["claim"],
            "additionalProperties": False,
        },
    ))
    registry.register(Capability(
        "cognition.question.add",
        "Record an unresolved question that should remain visible across the reasoning process.",
        add_question,
        parameters={
            "type": "object",
            "properties": {
                "question": {"type": "string"},
                "priority": {"type": "integer", "minimum": 1, "maximum": 5},
            },
            "required": ["question"],
            "additionalProperties": False,
        },
    ))
    registry.register(Capability(
        "cognition.snapshot",
        "Inspect the current explicit cognitive ledger: hypotheses, evidence, contradictions, and open questions.",
        lambda _args: ledger.snapshot(),
        parameters={"type": "object", "properties": {}, "additionalProperties": False},
    ))
