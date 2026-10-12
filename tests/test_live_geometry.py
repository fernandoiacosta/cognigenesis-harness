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
        "cognition": {"hypotheses": [{"id": "h1", "claim": "Hypothesis", "evidence_ids": ["e1"]}],
                      "evidence": [{"id": "e1", "claim": "Evidence", "polarity": "supports"}]},
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
    assert topology({}) == {"nodes": [], "links": [], "updated_at": None, "event_count": 0, "truncated": False}
    assert "/api/topology" in HTML
    assert "requestAnimationFrame" in HTML
    assert "https://" not in HTML


def test_real_runtime_snapshot_preserves_evidence_polarity_and_entity_names():
    from cognigenesis.cognition.ledger import CognitiveLedger, Evidence, Hypothesis
    from cognigenesis.fabric.team import AgentSpec, TeamManager
    from cognigenesis.runtime.taskgraph import Task, TaskGraph

    ledger = CognitiveLedger()
    hypothesis = ledger.add_hypothesis(Hypothesis(claim="A claim"))
    for polarity in ("supports", "contradicts", "neutral"):
        ledger.add_evidence(Evidence(claim=polarity, polarity=polarity), hypothesis.id)
    teams = TeamManager()
    agent = AgentSpec(name="Analyst", role="research")
    team = teams.create_team("Research", "Objective", [agent])
    tasks = TaskGraph()
    dependency = tasks.add(Task(title="Collect"))
    task = tasks.add(Task(title="Analyze", dependencies=[dependency.id]))
    tasks.assign(task.id, agent.id)
    graph = topology({"tasks": tasks.snapshot(), "teams": teams.snapshot(), "cognition": ledger.snapshot()})
    nodes = {n["id"]: n for n in graph["nodes"]}
    assert nodes[f"task:{dependency.id}"]["label"] == "Collect"
    assert nodes[f"agent:{agent.id}"]["label"] == "Analyst"
    triples = {(e["source"], e["target"], e["relation"]) for e in graph["links"]}
    for evidence in ledger.evidence.values():
        assert (f"evidence:{evidence.id}", f"hypothesis:{hypothesis.id}", evidence.polarity) in triples
    assert (f"team:{team.id}", f"agent:{agent.id}", "contains") in triples


def test_long_ids_do_not_collide_and_malformed_collections_are_ignored():
    prefix = "x" * 160
    graph = topology({"tasks": [{"id": prefix + "a", "dependencies": "wrong"},
                                {"id": prefix + "b", "dependencies": [None, {}]}],
                      "teams": {}, "cognition": {"hypotheses": 123}, "events": "wrong"})
    assert len(graph["nodes"]) == 2
    assert graph["links"] == []
    assert topology([])["nodes"] == []


def test_projection_is_bounded_and_reports_truncation():
    from cognigenesis.commandcenter.geometry import MAX_LINKS, MAX_NODES
    graph = topology({"tasks": [{"id": str(i), "dependencies": [f"d{i}-{j}" for j in range(50)]}
                                for i in range(500)]})
    assert len(graph["nodes"]) <= MAX_NODES
    assert len(graph["links"]) <= MAX_LINKS
    assert graph["truncated"]
    ids = {n["id"] for n in graph["nodes"]}
    assert all(e["source"] in ids and e["target"] in ids for e in graph["links"])
