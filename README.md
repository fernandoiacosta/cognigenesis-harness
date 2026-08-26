# Cognigenesis Harness

![Cognigenesis logo](assets/brand/cognigenesis-logo.svg)

**Local-first adaptive intelligence runtime for Ollama, terminal chat, web research, trusted tools, and first-class ACP/AionUi integration.**

Cognigenesis Harness v1.0 is designed as a product rather than a collection of wrappers: one configuration source, one execution kernel, one capability registry, one persistent conversation model, and two supported interfaces—`cogni` for humans and `cogni-acp` for ACP clients.

## Quick start

### Windows PowerShell

```powershell
$script = gh api repos/fernandoiacosta/cognigenesis-harness/contents/scripts/install.ps1 -H "Accept: application/vnd.github.raw+json"; Invoke-Expression ($script -join "`n")
```

### macOS / Linux

```bash
gh api repos/fernandoiacosta/cognigenesis-harness/contents/scripts/install.sh -H "Accept: application/vnd.github.raw+json" | sh
```

The installer upgrades/reinstalls the package, verifies `cogni` and `cogni-acp`, repairs the Windows user PATH when a user-site install needs it, exports the brand assets, and runs first-use setup.

Then:

```text
cogni chat
```

## Terminal experience

`cogni chat` is a persistent themed conversation interface with Markdown rendering, command history, auto-suggestions, runtime status, and durable workspace conversation state.

```text
cogni chat --workspace .
```

Useful commands:

```text
/help          commands
/new           clear this workspace conversation
/state         runtime state
/capabilities  registered capabilities
/provider      active provider/model
/workspace     active workspace
/doctor        health diagnostics
/exit          exit
```

One-shot compatibility remains:

```text
cogni "Research current agent harnesses and compare them"
cogni run --model hasi-edge-AG:latest "Say OK"
```

## First-use setup and diagnostics

```text
cogni setup
cogni doctor
cogni config
```

`setup` discovers local Ollama models and prefers `hasi-edge-AG:latest`, then `llama3.1:8b`, then the first installed model. Configuration is persisted in the OS-standard user config directory and may be overridden by CLI flags or environment variables.

Supported environment overrides:

```text
COGNI_PROVIDER=ollama
COGNI_OLLAMA_BASE_URL=http://127.0.0.1:11434
COGNI_OLLAMA_MODEL=hasi-edge-AG:latest
COGNI_OLLAMA_TIMEOUT=300
```

If Ollama is unavailable or a model is missing, Cognigenesis returns a specific actionable error rather than a generic upstream failure.

## AionUi / ACP

Cognigenesis ships a Python-native ACP-over-stdio process:

```text
cogni-acp
```

Generate the exact local AionUi settings with:

```text
cogni aionui
```

The command prints the absolute installed `cogni-acp` path, environment variables, and the exported Cognigenesis logo path. The ACP bridge never needs the old Node/`.cmd` wrapper workaround.

See [AIONUI.md](AIONUI.md).

## Runtime architecture

```text
user / AionUi
      │
      ▼
terminal UI / ACP stdio
      │
      ▼
Cognitive Control Plane (packaged)
      │
      ▼
Context Compiler + durable conversation
      │
      ▼
Provider (Ollama by default)
      │
      ▼
Execution Kernel
      │
      ├── policy gate
      ├── model-trust gate
      └── capability registry
              │
              ├── filesystem.*
              ├── workspace.*
              ├── web.search / web.fetch
              └── shell.run (registered, disabled by default)
```

The model sees explicit JSON schemas for tools. Multi-step execution preserves the canonical `user → assistant(tool_calls) → tool(result) → assistant` transcript expected by chat/tool APIs.

## Research

`web.search` and `web.fetch` are read-only. Retrieved content is labeled untrusted, and `web.fetch` rejects localhost, private, reserved, and other non-public network addresses to prevent the research tool from becoming an SSRF path.

## State and conversation continuity

Conversation history is persisted per workspace using atomic writes under `.cognigenesis/`. Closing and reopening `cogni chat --workspace .` restores the bounded recent conversation. `/new` clears it.

ACP sessions use isolated state files under:

```text
<workspace>/.cognigenesis/sessions/<session-id>.json
```

## Brand and theme

Canonical repository assets:

```text
assets/brand/cognigenesis-logo.svg
assets/brand/theme.json
assets/brand/theme.css
```

Installed copies are exported by `cogni setup` to the OS user data directory so external clients can use them without locating the Git checkout.

See [BRANDING.md](BRANDING.md).

## Installation quality gate

CI runs on Windows, macOS, and Ubuntu across Python 3.11–3.14. It executes the test suite, builds a real wheel/sdist, installs the built wheel, verifies packaged cognitive/theme resources outside the repository, checks both executables, validates AionUi configuration output, runs ACP subprocess smoke tests, and syntax-checks the platform installers.

See [INSTALL.md](INSTALL.md), [SECURITY.md](SECURITY.md), and [ARCHITECTURE.md](ARCHITECTURE.md).
