from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal
from uuid import uuid4


EvidencePolarity = Literal["supports", "contradicts", "neutral"]


@dataclass
class Evidence:
    claim: str
    source: str | None = None
    polarity: EvidencePolarity = "neutral"
    confidence: float = 0.5
    id: str = field(default_factory=lambda: uuid4().hex)


@dataclass
class Hypothesis:
    claim: str
    mechanism: str = ""
    confidence: float = 0.5
    evidence_ids: list[str] = field(default_factory=list)
    status: Literal["active", "rejected", "accepted", "untested"] = "untested"
    id: str = field(default_factory=lambda: uuid4().hex)


@dataclass
class OpenQuestion:
    question: str
    priority: int = 1
    resolved: bool = False
    id: str = field(default_factory=lambda: uuid4().hex)


class CognitiveLedger:
    """Explicit, inspectable reasoning state around the model.

    This does not claim access to hidden chain-of-thought. It stores observable
    cognitive objects: hypotheses, evidence, contradictions, uncertainty, and
    open questions that the runtime can require, inspect, compare, and persist.
    """

    def __init__(self) -> None:
        self.hypotheses: dict[str, Hypothesis] = {}
        self.evidence: dict[str, Evidence] = {}
        self.questions: dict[str, OpenQuestion] = {}

    def add_hypothesis(self, hypothesis: Hypothesis) -> Hypothesis:
        hypothesis.confidence = _clamp(hypothesis.confidence)
        self.hypotheses[hypothesis.id] = hypothesis
        return hypothesis

    def add_evidence(self, evidence: Evidence, hypothesis_id: str | None = None) -> Evidence:
        evidence.confidence = _clamp(evidence.confidence)
        self.evidence[evidence.id] = evidence
        if hypothesis_id:
            hypothesis = self.hypotheses[hypothesis_id]
            if evidence.id not in hypothesis.evidence_ids:
                hypothesis.evidence_ids.append(evidence.id)
        return evidence

    def add_question(self, question: OpenQuestion) -> OpenQuestion:
        self.questions[question.id] = question
        return question

    def contradictions(self) -> list[Evidence]:
        return [e for e in self.evidence.values() if e.polarity == "contradicts"]

    def active_hypotheses(self) -> list[Hypothesis]:
        return [h for h in self.hypotheses.values() if h.status in {"active", "untested"}]

    def snapshot(self) -> dict:
        return {
            "hypotheses": [asdict(item) for item in self.hypotheses.values()],
            "evidence": [asdict(item) for item in self.evidence.values()],
            "open_questions": [asdict(item) for item in self.questions.values()],
            "metrics": {
                "active_hypotheses": len(self.active_hypotheses()),
                "contradictions": len(self.contradictions()),
                "unresolved_questions": sum(not q.resolved for q in self.questions.values()),
            },
        }


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
