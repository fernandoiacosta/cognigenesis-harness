"""Observe model answers without rewriting them or imposing an output schema.

This is interpretation, not a tool call, authorization, truth check, or repair.
Ambiguous or missing fields are unknown; they are not manufactured.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Literal

FormatKind = Literal["json", "fenced_json", "embedded_json", "text", "empty"]
DECISIONS = frozenset({"yes", "no", "proceed", "defer", "insufficient", "likely", "unlikely"})
EXPLICIT_DECISION = re.compile(
    r"(?im)^\s*(?:\*\*)?(?:decision|verdict|recommendation)(?:\*\*)?\s*[:\-]\s*"
    r"(?:\*\*)?(yes|no|proceed|defer|insufficient|likely|unlikely)\b"
)
DIRECT_ANSWER = re.compile(r"(?i)^\s*(?:\*\*)?(yes|no|proceed|defer|insufficient|likely|unlikely)(?:\*\*)?(?:\s*[,.:;—-]|\s*$)")
CONFIDENCE = re.compile(r"(?im)^\s*(?:\*\*)?confidence(?:\*\*)?\s*[:\-]\s*(\d+(?:\.\d+)?)\s*(%)?")
EVIDENCE = re.compile(r"(?i)\bE\d+\b")
FIELD = re.compile(r"(?im)^\s*(?:[>*-]\s*)?(?:\*\*)?({name})(?:\*\*)?\s*[:\-]\s*(.+)$")


@dataclass(frozen=True)
class InterpretedOutput:
    raw: str
    format: FormatKind
    decision: str | None
    evidence_ids: tuple[str, ...]
    confidence: float | None
    uncertainties: tuple[str, ...]
    next_test: str | None
    ambiguous: bool = False

    def metadata(self) -> dict[str, Any]:
        """Exclude answer text and untrusted prose from observability events."""
        return {
            "format": self.format,
            "decision": self.decision,
            "evidence_ids": list(self.evidence_ids),
            "confidence": self.confidence,
            "has_uncertainties": bool(self.uncertainties),
            "has_next_test": bool(self.next_test),
            "ambiguous": self.ambiguous,
            "raw_sha256": hashlib.sha256(self.raw.encode("utf-8")).hexdigest(),
        }


def _json_object(text: str) -> tuple[dict[str, Any] | None, FormatKind]:
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        obj = None
    if isinstance(obj, dict):
        return obj, "json"

    fence = re.fullmatch(r"\s*```(?:json)?\s*\n?(\{.*\})\s*```\s*", text, re.I | re.S)
    if fence:
        try:
            obj = json.loads(fence.group(1))
        except json.JSONDecodeError:
            obj = None
        if isinstance(obj, dict):
            return obj, "fenced_json"

    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text):
        try:
            obj, _end = decoder.raw_decode(text[match.start():])
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and any(k in obj for k in ("decision", "verdict", "confidence", "evidence_used", "next_test")):
            return obj, "embedded_json"
    return None, "text"


def _normalize_decision(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    word = value.strip().lower()
    if word in DECISIONS:
        return word
    match = DIRECT_ANSWER.match(word)
    return match.group(1).lower() if match else None


def _confidence(value: Any, percent: bool = False) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (ValueError, TypeError, OverflowError):
        return None
    if percent:
        number /= 100.0
    return number if 0 <= number <= 1 else None


def _strings(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value.strip(),) if value.strip() else ()
    if isinstance(value, list):
        return tuple(v.strip() for v in value if isinstance(v, str) and v.strip())
    return ()


def _evidence(text: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(match.group(0).upper() for match in EVIDENCE.finditer(text)))


def _extract_field(text: str, names: tuple[str, ...]) -> tuple[str, ...]:
    values: list[str] = []
    for name in names:
        regex = re.compile(FIELD.pattern.format(name=re.escape(name)), FIELD.flags)
        values.extend(match.group(2).strip() for match in regex.finditer(text))
    return tuple(values)


def interpret_output(raw: str) -> InterpretedOutput:
    """Read explicit signals without changing the model response or taking actions."""
    if not isinstance(raw, str):
        raise TypeError("Model output must be a string")
    text = raw.strip()
    if not text:
        return InterpretedOutput(raw, "empty", None, (), None, (), None)

    obj, fmt = _json_object(text)
    if obj is not None:
        decision = _normalize_decision(obj.get("decision", obj.get("verdict")))
        evidence_values = obj.get("evidence_used", obj.get("evidence_ids", []))
        if isinstance(evidence_values, list):
            cited = _evidence(" ".join(str(v) for v in evidence_values))
        elif isinstance(evidence_values, str):
            cited = _evidence(evidence_values)
        else:
            cited = ()
        return InterpretedOutput(
            raw, fmt, decision, cited,
            _confidence(obj.get("confidence")),
            _strings(obj.get("uncertainties", obj.get("uncertainty"))),
            obj.get("next_test", "").strip() if isinstance(obj.get("next_test"), str) and obj["next_test"].strip() else None,
        )

    explicit = [match.group(1).lower() for match in EXPLICIT_DECISION.finditer(text)]
    ambiguous = len(set(explicit)) > 1
    if explicit:
        decision = explicit[0] if not ambiguous else None
    else:
        match = DIRECT_ANSWER.match(text.splitlines()[0])
        decision = match.group(1).lower() if match else None

    matches = list(CONFIDENCE.finditer(text))
    confidence = _confidence(matches[0].group(1), bool(matches[0].group(2))) if len(matches) == 1 else None
    uncertainty_lines = _extract_field(text, ("uncertainty", "uncertainties", "caveats"))
    next_test_lines = _extract_field(text, ("next test", "next_test", "follow-up test"))
    return InterpretedOutput(
        raw, "text", decision, _evidence(text), confidence,
        uncertainty_lines, next_test_lines[0] if len(next_test_lines) == 1 else None,
        ambiguous=ambiguous or len(matches) > 1,
    )
