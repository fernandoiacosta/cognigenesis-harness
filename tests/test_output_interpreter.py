from cognigenesis.runtime.output_interpreter import interpret_output
from cognigenesis.runtime.events import EventType
from harness import build_engine


def test_preserves_raw_json_and_extracts_fields():
    raw = '{"decision":"no","confidence":0.8,"evidence_used":["E1","E2"],"uncertainties":["small sample"],"next_test":"repeat"}'
    result = interpret_output(raw)
    assert result.raw == raw
    assert result.format == "json"
    assert result.decision == "no"
    assert result.evidence_ids == ("E1", "E2")
    assert result.confidence == 0.8
    assert result.next_test == "repeat"


def test_fenced_json_and_embedded_json():
    fenced = interpret_output('```json\n{"decision":"defer","evidence_used":["E3"]}\n```')
    assert fenced.format == "fenced_json"
    assert fenced.decision == "defer"
    embedded = interpret_output('Review:\n{"decision":"no","evidence_used":["E4"]}\nThank you.')
    assert embedded.format == "embedded_json"
    assert embedded.evidence_ids == ("E4",)


def test_plain_prose_preserves_text_and_extracts_explicit_fields():
    raw = "No, the case is not established by E1 and E2.\nConfidence: 75%\nUncertainty: missing baseline\nNext test: randomized pilot"
    result = interpret_output(raw)
    assert result.raw == raw
    assert result.format == "text"
    assert result.decision == "no"
    assert result.confidence == 0.75
    assert result.evidence_ids == ("E1", "E2")
    assert result.uncertainties == ("missing baseline",)
    assert result.next_test == "randomized pilot"


def test_no_hallucinated_confidence_or_implicit_decision():
    result = interpret_output("There is no good evidence of causal benefit. We need another test.")
    assert result.decision is None
    assert result.confidence is None
    assert result.next_test is None


def test_conflicting_decisions_are_unknown():
    result = interpret_output("Decision: yes\nDecision: no\nEvidence: E1")
    assert result.ambiguous
    assert result.decision is None


def test_bad_confidence_is_unknown_not_clamped():
    assert interpret_output("Decision: defer\nConfidence: 150%").confidence is None
    assert interpret_output('{"decision":"yes","confidence":2}').confidence is None


def test_observability_metadata_has_no_raw_answer():
    result = interpret_output("Decision: no\nEvidence: E1\nPrivate user note: secret")
    meta = result.metadata()
    assert "raw" not in meta
    assert "secret" not in str(meta)
    assert meta["raw_sha256"]


def test_engine_records_interpretation_but_returns_original_text(tmp_path):
    engine = build_engine(tmp_path, provider_name="stub")
    answer = engine.run("hello")
    assert answer
    assert engine.last_interpretation is not None
    assert engine.last_interpretation.raw == answer
    assert any(e.type == EventType.OUTPUT_INTERPRETED for e in engine.events.history())
    recorded = [e.payload for e in engine.events.history() if e.type == EventType.OUTPUT_INTERPRETED]
    assert all("raw" not in e for e in recorded)
