# Cognigenesis 2.0 Architecture

## Thesis

Cognigenesis is the **cognition layer**. Cognigenesis Harness is the small runtime/authority boundary underneath it.

The platform is no longer framed as a single-agent CLI with add-ons. It is a cognitive operating environment:

```text
                  COGNIGENESIS
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
   Command Center      TUI             ACP/AionUi
        │               │                │
        └───────────────┼────────────────┘
                        ▼
                  Semantic Event Bus
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
    Task Graph     Cognitive Ledger    Agent Fabric
                        │                │
                        └───────┬────────┘
                                ▼
                         Execution Engine
                                │
                     Policy + Model Trust
                                │
                         Capability Registry
                                │
                         Model / Provider
```

## One runtime, multiple interfaces

Terminal, ACP, and the graphical Command Center must not implement separate agent logic.

The execution engine emits semantic events. Interfaces consume events and shared state.

Examples:

- `turn.started`
- `model.started`
- `tool.requested`
- `tool.completed`
- `policy.denied`
- `cognition.updated`
- `task.updated`
- `agent.message`
- `turn.completed`

Observability subscribers are isolated: a GUI/logger failure cannot break the runtime.

## Cognitive architecture

Cognigenesis does not expose hidden chain-of-thought. It maintains explicit external reasoning state.

The current CognitiveLedger contains:

```text
Hypothesis
├─ claim
├─ mechanism
├─ confidence
├─ status
└─ linked evidence

Evidence
├─ claim
├─ source
├─ polarity
└─ confidence

OpenQuestion
├─ question
├─ priority
└─ resolved
```

The model can manipulate this state through trusted `cognition.*` capabilities. The ledger is included in compiled context so later turns and team members can inspect it.

## Task graph

The shared TaskGraph represents dependency-aware mission execution:

```text
pending → ready → running → completed
                  ├→ blocked
                  ├→ failed
                  └→ cancelled
```

The model can inspect/update it through `task.*`. Team execution also uses the same graph.

## Agent fabric

Agents exchange typed objects rather than relying only on prose chat.

Current message kinds:

```text
task
finding
hypothesis
evidence
question
critique
decision
handoff
status
artifact
```

Agent messages emit `agent.message` events and appear in the Command Center state.

## Team runtime

The first bounded TeamRunner is synchronous and deterministic by design. Each agent receives:

- its own persisted session state;
- a role-specific prompt;
- the shared CognitiveLedger;
- the shared TaskGraph;
- the same capability/policy system.

Current patterns:

- Parallel Search
- Adversarial Council
- Red Team / Blue Team
- Specialist Pipeline
- Consensus

The swarm layer is above the single-agent kernel; it does not alter the fundamental execution loop.

## Command Center

Every active workspace gets:

```text
.cognigenesis/command-center.json
```

This atomic UI-neutral snapshot contains:

- tasks;
- cognition;
- teams/agents;
- recent runtime events.

`cogni command-center` launches the first graphical surface and polls that state.

The final Command Center should grow from this contract rather than inventing a second backend.

## Capability plane

Current built-ins include:

```text
filesystem.*
workspace.*
web.search
web.fetch
cognition.*
task.*
shell.run
```

Cognitive and task capabilities manipulate internal scaffolding. External mutation remains subject to stronger trust and policy gates.

## Authority plane

Capability is not authority.

```text
registered capability
      AND
runtime policy
      AND
model trust floor
      AND
future operator permission
      ↓
execution
```

Shell remains disabled by default.

## Provider plane

Ollama remains the local-first provider. Providers receive:

- actual runtime capability schemas;
- bounded conversation history;
- runtime state;
- cognitive ledger;
- task graph.

Provider breadth and native streaming come later without changing the core architecture.

## ACP

`cogni-acp` remains a Python-native ACP-over-stdio interface over the same engine.

The next ACP stage is to map semantic runtime events to richer ACP updates (tool progress, reasoning-status objects, permissions, and streaming) rather than returning only final text.

## Evolution invariant

> The harness is the kernel. Cognigenesis is the cognition layer. Teams, swarms, and interfaces grow around them. Authority remains explicit.
