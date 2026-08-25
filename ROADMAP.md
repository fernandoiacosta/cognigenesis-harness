# Roadmap

## Milestone 1 — Prove the Foundation

Do not add swarm orchestration, giant memory systems, or autonomous code mutation yet.

Required path:

```text
agent.md
↓
load Markdown graph
↓
real model provider
↓
capability registry
↓
workspace capability
↓
recursive execution
↓
goal tracking
↓
session log
```

### Acceptance test

```bash
cogni "Create a Python CLI project for tracking expenses"
```

Success means the runtime can load Architect mode, create a goal, inspect workspace state, generate a project plan, call `workspace.create_project`, run tests through `shell.run`, observe the result, mark the goal complete, and persist the session.

## Milestone 2 — Real Provider Bus

- [ ] OpenAI adapter
- [ ] Anthropic adapter
- [ ] Ollama adapter
- [ ] normalized tool-call schema
- [ ] provider switching without kernel changes

## Milestone 3 — Markdown Graph

- [ ] front-matter metadata
- [ ] mode selection
- [ ] protocol selection
- [ ] skill discovery
- [ ] selective context compilation
- [ ] working/project memory loading

## Milestone 4 — State Continuity

- [ ] goals API
- [ ] session JSONL
- [ ] checkpoints
- [ ] artifact ledger
- [ ] explicit next-action state

## Milestone 5 — Semantic Capabilities

- [ ] richer workspace manager
- [ ] repository operations
- [ ] artifact abstractions
- [ ] bounded shell policy
- [ ] capability introspection tool

## Milestone 6 — Capability-Gap Evolution

Only start after Milestone 1 is reliable.

Target test:

```bash
cogni "Inspect this SQLite database and create an HTML report"
```

Expected behavior:

```text
discover sqlite capability missing
→ test existing compositions
→ declare CAPABILITY_GAP
→ propose extension
→ static validation
→ sandbox
→ tests
→ permission analysis
→ registration
→ retry original goal
→ create artifact
→ mark goal complete
```

## Architectural Constraint

Kernel complexity should grow slowly.

Capability space may grow rapidly.
