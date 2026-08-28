# Cognigenesis Platform

Cognigenesis is the **cognition layer**. Cognigenesis Harness is the runtime substrate that lets that cognition interact with models, tools, memory, teams, and interfaces.

The v2 direction is a cognitive operating environment rather than another monolithic agent CLI.

## Layer model

```text
Command Center / TUI / ACP
          │
          ▼
Agent Fabric + Teams + Swarm Patterns
          │
          ▼
Cognitive Architecture
hypotheses • evidence • contradictions • questions • verification
          │
          ▼
Harness Runtime
sessions • events • tasks • tools • permissions • persistence
          │
          ▼
Model Substrate
Ollama today; additional providers later
```

## Runtime invariant

One runtime backs all interfaces.

```text
              ┌── Terminal / future TUI
Runtime Core ─┼── ACP / AionUi
              └── future Command Center GUI
```

Interfaces consume semantic runtime events rather than provider logs.

## Semantic event bus

The runtime emits typed events such as:

- `turn.started`
- `model.started`
- `tool.requested`
- `tool.started`
- `tool.completed`
- `policy.denied`
- `capability.gap`
- `turn.completed`
- `turn.failed`

The TUI, ACP bridge, tracing, and future GUI can subscribe to the same stream.

## Cognitive exoskeleton

Cognigenesis does not claim access to hidden model chain-of-thought. It externalizes observable reasoning state into inspectable objects:

- hypotheses
- mechanisms
- evidence
- contradictions
- confidence
- open questions
- verification status

This makes cognitive scaffolding architectural rather than merely prompt-enforced.

## Task graph

Complex work is represented as a dependency graph with explicit states:

```text
pending → ready → running → completed
                  ├→ blocked
                  └→ failed
```

The graph is shared by a single agent, a team, and future swarm orchestration.

## Agent fabric

Agents exchange typed messages rather than only arbitrary chat prose.

Current message kinds:

- task
- finding
- hypothesis
- evidence
- question
- critique
- decision
- handoff
- status
- artifact

This gives the Command Center a meaningful communication graph.

## Team patterns

v2 starts with reusable coordination patterns:

- Parallel Search
- Adversarial Council
- Red Team / Blue Team
- Specialist Pipeline
- Consensus

The pattern layer defines team topology without embedding swarm logic in the single-agent execution kernel.

## Command Center

The future graphical surface should render the same neutral platform state:

```text
Mission
├─ Task Graph
├─ Cognitive Ledger
├─ Agents / Teams
├─ Communication Graph
├─ Runtime Events
├─ Evidence
├─ Artifacts
└─ Permissions
```

The current `CommandCenterSnapshot` is the UI-neutral projection that future TUI/GUI implementations will consume.

## Near-term build order

1. semantic event bus + task graph
2. cognition ledger
3. typed inter-agent protocol
4. team/supervisor execution
5. dynamic swarm orchestration
6. full-screen TUI
7. graphical Command Center
8. ACP/MCP interoperability expansion
9. model/agent performance routing
10. advanced cognitive operators and self-improving team structures

The harness remains the kernel. The product above it is Cognigenesis.
