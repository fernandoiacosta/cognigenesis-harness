from cognigenesis.runtime.taskgraph import Task, TaskGraph, TaskStatus


def test_task_graph_unlocks_dependencies():
    graph = TaskGraph()
    first = graph.add(Task("research"))
    second = graph.add(Task("synthesize", dependencies=[first.id]))

    assert first.status == TaskStatus.READY
    assert second.status == TaskStatus.PENDING

    graph.update_status(first.id, TaskStatus.COMPLETED)
    assert second.status == TaskStatus.READY
