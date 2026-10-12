from cognigenesis.commandcenter.geometry import HTML, topology


def test_topology_uses_recorded_entities_and_edges_only():
    snapshot = {
        "updated_at": "2026-10-11T00:00:00Z",
        "tasks": [
            {"id": "t1", "title": "Research", "dependencies": ["t2"], "assigned_agent": "analyst"},
            {"id": "t2", "title": "Collect"},
        ],
        "teams": [{"id": "team1", "name": "Research team",
                   "agents": [{"id": "analyst", "name": "Analyst"}]}],
        "cognition": {"hypotheses": [{"id": "h1", "claim": "Hypothesis"}],
                      "evidence": [{"id": "e1", "claim": "Evidence", "hypothesis_id": "h1"}]},
        "events": [{"type": "tool.completed", "source": "runtime"}],
    }
    graph = topology(snapshot)
    ids = {n["id"] for n in graph["nodes"]}
    assert {"task:t1", "task:t2", "agent:analyst", "team:team1",
            "hypothesis:h1", "evidence:e1"} <= ids
    triples = {(e["source"], e["target"], e["relation"]) for e in graph["links"]}
    assert ("task:t1", "task:t2", "depends_on") in triples
    assert ("agent:analyst", "task:t1", "assigned") in triples
    assert ("evidence:e1", "hypothesis:h1", "supports") in triples
    assert graph["event_count"] == 1
    assert "source:runtime" not in ids


def test_missing_state_is_empty_and_page_has_no_external_dependencies():
    assert topology({}) == {"nodes": [], "links": [], "updated_at": None, "event_count": 0}
    assert "/api/topology" in HTML
    assert "requestAnimationFrame" in HTML
    assert "https://" not in HTML
