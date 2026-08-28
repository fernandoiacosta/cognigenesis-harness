# Cognigenesis Roadmap

## 2.0a1 — Cognitive Operating Environment Foundation

Implemented:

- [x] preserve working v1 Ollama / CLI / ACP execution paths
- [x] semantic runtime EventBus
- [x] explicit turn/model/tool/policy/failure events
- [x] shared dependency-aware TaskGraph
- [x] CognitiveLedger for hypotheses/evidence/contradictions/questions
- [x] typed inter-agent AgentMessage protocol
- [x] TeamManager communication substrate
- [x] reusable swarm/team patterns
- [x] UI-neutral CommandCenterSnapshot
- [x] terminal cognition/task/event inspectors
- [x] terminal response wrapping regression fix

## 2.0a2 — Team Execution

Next:

- [ ] supervisor runtime operating over TaskGraph
- [ ] bounded agent workers sharing one mission state
- [ ] role/model assignment
- [ ] message delivery through runtime events
- [ ] explicit handoff lifecycle
- [ ] team cancellation and failure containment
- [ ] team-level evidence/cognitive ledger merge
- [ ] deterministic team integration tests

## 2.0a3 — Dynamic Swarm

- [ ] dynamic role generation from mission requirements
- [ ] Parallel Search executor
- [ ] Adversarial Council executor
- [ ] Red/Blue executor
- [ ] Specialist Pipeline executor
- [ ] Consensus executor
- [ ] bounded recursive delegation
- [ ] agent/model performance profiles for routing

## 2.0a4 — Full-screen TUI

- [ ] replace chat-loop presentation with application layout
- [ ] conversation viewport with reliable resize/wrap
- [ ] live tool/event cards
- [ ] task graph panel
- [ ] cognition panel
- [ ] team/activity panel
- [ ] permissions/approval dialogs
- [ ] session selector/resume
- [ ] multiline composer and attachments
- [ ] streamed model output

## 2.0a5 — Command Center GUI

- [ ] local web/desktop Command Center
- [ ] mission dashboard
- [ ] agent/team graph
- [ ] communication graph
- [ ] cognition graph
- [ ] task board
- [ ] evidence ledger
- [ ] artifacts
- [ ] runtime trace
- [ ] permissions
- [ ] model/provider health

The GUI consumes the same CommandCenterSnapshot/event stream as the TUI and ACP.

## 2.0a6 — Protocol and Capability Fabric

- [ ] MCP client/tool registry integration
- [ ] hierarchical AGENTS.md/project instructions
- [ ] progressive skill discovery/loading
- [ ] patch/diff editing capability
- [ ] sandbox abstraction
- [ ] interactive permission modes
- [ ] provider capability negotiation
- [ ] additional providers

## Long-term cognition development

- causal model objects
- competing-model comparison
- representation selection
- null-model generation
- contradiction tracking
- falsification planning
- experiment design
- invariant discovery
- calibrated confidence updates
- cognitive operator performance measurement
- self-improving team structures

## Non-negotiable invariant

> The harness remains a small authority boundary. Cognition, teams, swarm behavior, and interfaces grow around it rather than being embedded into one monolithic loop.
