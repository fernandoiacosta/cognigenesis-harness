# Changelog

## 1.0.0

Productization and release-hardening pass.

### Runtime

- canonical multi-step tool transcript ordering
- durable conversation state across terminal restarts
- atomic/corruption-tolerant state writes
- strict capability JSON schemas
- Ollama model discovery and unified configuration resolution
- public-web research with private-network/SSRF blocking
- Windows UTF-8-safe shell/result handling

### Product UX

- themed Rich terminal output using Cognigenesis Prime Dark identity
- prompt-toolkit conversation history and suggestions
- `cogni setup`
- `cogni doctor`
- `cogni config`
- `cogni aionui`
- backward-compatible one-shot `cogni "..."`

### Packaging / installation

- packaged cognitive control plane
- packaged theme and logo
- OS-standard persistent configuration via `platformdirs`
- obsolete `config.yaml` removed
- verified Windows/macOS/Linux installers
- Windows user PATH repair for user-site fallback
- wheel/sdist build and installed-wheel CI validation

### ACP / AionUi

- one supported Python-native `cogni-acp` path
- absolute executable/environment configuration generator
- stable exported logo path
- legacy AionUi bridge detection
- no Node `.cmd` prompt-time wrapper

## 0.6.0

Added web research, Windows UTF-8 hardening, Ollama timeout classification, and diagnostics.

## 0.5.0

Added persistent in-process terminal/ACP conversation context.

## 0.4.0

Added real Ollama execution and Python-native ACP integration.
