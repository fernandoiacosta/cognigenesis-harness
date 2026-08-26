# Roadmap

## v1.0 — Productized Local-First Harness

Shipped:

- [x] real Ollama provider
- [x] persistent multi-turn terminal chat
- [x] durable conversation state across process restarts
- [x] canonical assistant/tool transcript ordering
- [x] strict tool JSON schemas
- [x] read-only web research
- [x] public-network-only `web.fetch` boundary
- [x] trust-gated capability execution
- [x] shell disabled by default
- [x] Python-native ACP-over-stdio agent
- [x] AionUi first-class custom-agent path
- [x] Windows UTF-8 hardening
- [x] Windows `.cmd`/spawn workaround eliminated from prompt execution
- [x] `cogni setup`
- [x] `cogni doctor`
- [x] `cogni config`
- [x] `cogni aionui`
- [x] Prime Dark terminal theme
- [x] packaged logo/theme/control-plane resources
- [x] one cross-platform persisted configuration source
- [x] verified Windows/macOS/Linux installers
- [x] wheel/sdist packaging validation in CI
- [x] ACP subprocess smoke tests
- [x] state corruption recovery and atomic writes

## Optional post-v1 extensions

These are enhancements, not prerequisites for a workable harness:

### Provider breadth

- OpenAI provider adapter
- Anthropic provider adapter
- additional local providers
- provider-native streaming/cancellation

### Research breadth

- pluggable search backends (Brave/Tavily/Serper/etc.)
- source ranking/provenance ledger
- structured citation objects

### ACP breadth

- session resume/load if AionUi requires it
- interactive ACP permission requests
- incremental streaming ACP updates

### Qualified model promotion

- provider/model-version-specific evaluation runners
- persisted qualification evidence
- adversarial tool-use qualification
- automatic trust downgrade on regression

### Governed extension system

- extension proposals
- static validation
- sandbox tests
- permission analysis
- promotion/rollback

## Non-negotiable architectural constraint

> Kernel complexity should grow slowly. Capability space may grow rapidly. Authority grows only with evidence.
