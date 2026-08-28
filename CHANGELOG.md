# Changelog

## 2.0.0a1

Cognigenesis transitions from a productized single-agent harness toward a cognitive operating environment while preserving the v1 Ollama/terminal/ACP paths.

### Cognition
- Added explicit CognitiveLedger for hypotheses, mechanisms, evidence, contradictions, confidence, and open questions.
- Added live `cognition.*` capabilities and compiled cognitive state.
- Updated the cognitive control plane to use scaffolding selectively for complex reasoning.

### Runtime
- Added semantic EventBus and typed turn/model/tool/policy/cognition/task/agent events.
- Added dependency-aware shared TaskGraph and `task.*` capabilities.
- Isolated event subscribers from runtime failure.

### Teams
- Added typed AgentMessage protocol and TeamManager.
- Added Parallel Search, Adversarial Council, Red/Blue, Specialist Pipeline, and Consensus patterns.
- Added functional bounded TeamRunner with isolated agent sessions and shared mission state.
- Added `cogni team --pattern ...`.

### Command Center
- Added atomic `.cognigenesis/command-center.json` workspace snapshot.
- Added first local graphical dashboard via `cogni command-center`.
- Dashboard renders cognition metrics, hypotheses/evidence, tasks, teams/agents, and runtime event stream.

### Terminal
- Fixed long response overflow by removing Rich soft-wrap misuse and restoring width-aware panel wrapping.
- Added `/cognition`, `/tasks`, and `/events` inspectors.

### Compatibility
- Existing `cogni chat`, one-shot execution, Ollama provider, qualification, policy gates, and `cogni-acp` remain supported.

## 1.0.0

Productized local-first harness release: real Ollama execution, persistent terminal chat, model qualification, trust-gated tools, web research, ACP/AionUi support, cross-platform setup/doctor/install flow, and packaged branding.
