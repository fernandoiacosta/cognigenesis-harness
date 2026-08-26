# Cognigenesis Harness v1.0 Architecture

## Product invariant

> Keep the execution kernel small. Move cognition, capabilities, interfaces, providers, and growth outward while keeping authority explicit.

Cognigenesis Harness is not intended to hard-code every AI feature into a permanent subsystem. It provides a stable runtime that can discover and use bounded capabilities.

## Runtime

```text
Human terminal / ACP client
          │
          ▼
   Interface layer
   ├─ cogni (Rich + prompt-toolkit)
   └─ cogni-acp (ACP stdio)
          │
          ▼
Packaged Cognitive Control Plane
          │
          ▼
    Context Compiler
          │
          ├─ durable conversation
          ├─ runtime state
          └─ capability schemas
          │
          ▼
      Model Provider
        (Ollama)
          │
          ▼
    Execution Kernel
          │
     ┌────┴────┐
     ▼         ▼
   Policy   Model Trust
     └────┬────┘
          ▼
 Capability Registry
          │
 ┌────────┼─────────────┐
 ▼        ▼             ▼
files   web/research   workspace
                     shell (off by default)
```

## Canonical chat/tool transcript

Multi-step execution preserves the standard ordering expected by chat/tool APIs:

```text
user
→ assistant(tool_calls)
→ tool(result)
→ assistant(tool_calls) ...
→ assistant(final)
```

The current user message remains before all tool activity. This is important for reliable local-model reasoning across multiple tool steps.

## Cognitive control plane

Behavioral rules are Markdown. The canonical runtime copy is packaged under:

```text
cognigenesis/resources/agent.md
```

The repository-root `agent.md` mirrors it for review. Installed behavior therefore does not depend on the original Git checkout being present.

Markdown can request or describe actions; it cannot grant executable authority.

## Capability plane

Capabilities are registered Python implementations with:

- stable ID
- description
- risk classification
- explicit JSON input schema
- trusted execution function

Current built-ins include:

```text
filesystem.read
filesystem.write
filesystem.list
workspace.create_project
web.search
web.fetch
shell.run
```

The model receives the actual runtime registry and JSON schemas rather than relying on prompt claims about what might exist.

## Authority plane

Execution requires two independent gates:

```text
runtime policy allows capability
AND
model trust tier >= capability minimum
```

`shell.run` is registered but disabled by runtime policy by default. Read-only public-web research is available at low trust; mutation remains more restricted.

## Provider plane

Ollama is the v1 local-first provider. Resolution precedence is:

```text
CLI flag
→ environment variable
→ persisted user configuration
→ autodiscovered/default model
```

First-use setup prefers:

1. `hasi-edge-AG:latest`
2. `llama3.1:8b`
3. first installed Ollama model

`StubProvider` is retained only for explicit tests/demo mode.

## State plane

Workspace state lives under `.cognigenesis/` and is written atomically.

The state store tracks:

- current objective
- recent runtime events
- artifacts/goals scaffolding
- bounded durable conversation history

Terminal chat reopens the workspace conversation after process restart. `/new` clears it.

ACP sessions isolate state under:

```text
.cognigenesis/sessions/<session-id>.json
```

## Research boundary

`web.search` and `web.fetch` are evidence tools, not execution-authority tools.

- fetched content is explicitly untrusted
- important claims should be verified across sources
- `web.fetch` blocks localhost/private/non-global network targets
- web content cannot grant shell/filesystem authority

## Interface plane

### Terminal

`cogni` owns human interaction:

- styled Prime Dark theme
- Markdown response rendering
- persistent input history
- auto-suggestions
- setup/doctor/config/AionUi commands
- one-shot compatibility

### ACP

`cogni-acp` owns machine interaction:

- Python-native stdio transport
- ACP initialization/session/prompt/update/cancel flow
- no Node/`.cmd` prompt-time wrapper
- UTF-8-only protocol stream
- same execution engine and provider as the terminal

## Configuration

There is one persistent configuration source resolved by `platformdirs`. The obsolete repository `config.yaml` was removed.

```text
CLI
→ environment
→ user config
→ defaults
```

This avoids code/config drift between terminal, ACP, and installed environments.

## Packaging

v1 is packaged as an installable wheel/sdist. The wheel includes:

- runtime packages
- cognitive control resource
- theme tokens
- Cognigenesis logo
- both console entry points

CI verifies those resources from outside the repository after installing the built wheel.

## Installation flow

```text
platform installer
→ authenticated package install/upgrade
→ executable verification
→ PATH repair (Windows user-site fallback)
→ cogni setup
→ Ollama/model diagnostics
→ exported brand assets
→ ready terminal + AionUi configuration
```

## Evolution principle

Soft evolution—Markdown rules, modes, protocols, and skills—should remain cheap, inspectable, and reversible.

Hard executable extension should require a later governed pipeline:

```text
proposal
→ static inspection
→ sandbox
→ tests
→ permission analysis
→ policy approval
→ registration
→ observation
→ rollback
```

The architecture should continue following one asymmetry:

> Kernel complexity grows slowly; capability space may grow rapidly; authority grows only with evidence.
