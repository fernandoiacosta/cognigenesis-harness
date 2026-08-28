from cognigenesis.cognition.ledger import CognitiveLedger, Evidence, Hypothesis, OpenQuestion


def test_cognitive_ledger_tracks_hypotheses_contradictions_and_questions():
    ledger = CognitiveLedger()
    hypothesis = ledger.add_hypothesis(Hypothesis("A causes B", confidence=0.7))
    ledger.add_evidence(Evidence("counterexample", polarity="contradicts"), hypothesis.id)
    ledger.add_question(OpenQuestion("What discriminating test should we run?"))

    snapshot = ledger.snapshot()
    assert snapshot["metrics"]["active_hypotheses"] == 1
    assert snapshot["metrics"]["contradictions"] == 1
    assert snapshot["metrics"]["unresolved_questions"] == 1
