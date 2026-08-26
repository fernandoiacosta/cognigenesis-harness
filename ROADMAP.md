# Roadmap

## v0.3 — ACP / AionUi Bridge

Completed:

- [x] ACP-over-stdio bridge using the current Python ACP SDK
- [x] `cogni-acp` package entry point
- [x] ACP initialization support
- [x] ACP session creation
- [x] prompt → Cognigenesis objective translation
- [x] agent-message updates back to ACP clients
- [x] cooperative `session/cancel` handling
- [x] per-session state isolation inside a shared project workspace
- [x] client-supplied additional directories/MCP descriptors kept outside automatic authority
- [x] AionUi Custom Agent setup documentation
- [x] cross-platform ACP import/executable CI checks

Next ACP hardening:

- [ ] subprocess-level ACP handshake integration test
- [ ] session resume/load once required by the target AionUi ACP surface
- [ ] provider-native cancellation for real model adapters
- [ ] ACP permission-request mapping for capabilities that require interactive operator approval
- [ ] streaming model output as incremental ACP message chunks

## v0.2 — Installation + Trust Gate

Completed:

- [x] installable `cogni` CLI
- [x] macOS/Linux installer
- [x] Windows PowerShell installer
- [x] private-repository authenticated installation path
- [x] `ModelProfile`
- [x] model trust tiers
- [x] per-capability minimum trust tiers
- [x] runtime-policy + model-trust dual gating
- [x] conservative default profile for unknown models
- [x] single authoritative capability-policy source

Still required before claiming measured model alignment:

- [ ] provider-specific qualification runners
- [ ] persisted evaluation evidence and profile provenance
- [ ] regression suites when provider/model versions change
- [ ] adversarial tool-use qualification cases

## Milestone 1 — Prove the Foundation

Do not add swarm orchestration, giant memory systems, or autonomous code mutation yet.

Required path:

```text
agent.md
↓
load Markdown graph
↓
qualified real model provider
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

## Milestone 2 — Qualified Provider Bus

- [ ] OpenAI adapter
- [ ] Anthropic adapter
- [ ] Ollama adapter
- [ ] normalized tool-call schema
- [ ] provider switching without kernel changes
- [ ] qualification run before mutation authority
- [ ] profile provenance tied to provider/model version

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

Only start after Milestone 1 is reliable and provider qualification is enforced.

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
→ model trust analysis
→ registration
→ retry original goal
→ create artifact
→ mark goal complete
```

## Architectural Constraint

Kernel complexity should grow slowly.

Capability space may grow rapidly.

Authority should grow only with evidence.
