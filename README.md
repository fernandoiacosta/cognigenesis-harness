# Cognigenesis Harness

A minimal, extensible agent runtime built around one central principle:

> Keep the execution kernel extremely small. Move cognition, procedures, and growth outward into composable capabilities and Markdown control documents.

The project evolved from the idea of a large integrated agent into a **minimal runtime that can safely grow an agent**.

## Five planes

1. **Cognitive Control Plane** — Markdown describing behavior, modes, procedures, skills, and memory.
2. **Execution Kernel** — A tiny recursive model/tool/observation loop.
3. **Capability Plane** — Trusted executable implementations.
4. **State Plane** — Goals, events, checkpoints, artifacts, and continuity.
5. **Evolution Plane** — Capability-gap detection, skill synthesis, bounded plugin synthesis, validation, promotion, and rollback.

## Model alignment and authority

Cognigenesis does **not** assume that connecting a model makes it trustworthy.

Models receive a `ModelProfile` measuring reasoning, instruction fidelity, tool reliability, uncertainty calibration, goal persistence, capability-hallucination resistance, recovery behavior, and protocol compatibility.

Capabilities are trust-gated:

```text
model
  ↓
qualification
  ↓
model profile
  ↓
trust tier
  ↓
policy + capability minimum tier
  ↓
execute or deny
```

Unknown models start restricted. A capable harness must not automatically amplify an unreliable model.

See [`ALIGNMENT.md`](ALIGNMENT.md).

## Install

Requires Python 3.11–3.14.

### Private-repository one-liner — macOS/Linux

Requires GitHub CLI authenticated to an account with repository access:

```bash
gh api repos/fernandoiacosta/cognigenesis-harness/contents/scripts/install.sh -H "Accept: application/vnd.github.raw+json" | sh
```

### Private-repository one-liner — Windows PowerShell

```powershell
$script = gh api repos/fernandoiacosta/cognigenesis-harness/contents/scripts/install.ps1 -H "Accept: application/vnd.github.raw+json"; Invoke-Expression ($script -join "`n")
```

Or install directly with authenticated Git credentials:

```bash
uv tool install git+https://github.com/fernandoiacosta/cognigenesis-harness.git
```

After installation:

```bash
cogni --help
cogni "Inspect this workspace and summarize its architecture."
```

See [`INSTALL.md`](INSTALL.md) for alternatives and the future public installer path.

## AionUi first-class custom agent

The regular `cogni` executable is a human-facing CLI. AionUi Custom Agents require ACP over stdio, so Cognigenesis now ships a separate ACP entry point:

```text
cogni-acp
```

In AionUi, add a custom agent under **Settings → Agent Management → Custom Agents** with:

```text
Display name: Cognigenesis
Command:      cogni-acp
Arguments:    <empty>
```

AionUi launches `cogni-acp` as a subprocess and communicates with it using Agent Client Protocol messages over stdin/stdout.

The ACP bridge:

- negotiates ACP initialization
- creates isolated Cognigenesis sessions per AionUi conversation
- uses the AionUi-selected project directory as the Cognigenesis workspace
- translates ACP prompts into Cognigenesis objectives
- streams the resulting agent message back through ACP session updates
- supports cooperative ACP cancellation
- preserves Cognigenesis policy and model-trust gates
- does not automatically grant client-provided additional directories or MCP servers

See [`AIONUI.md`](AIONUI.md) for setup and architecture details.

## Current status

Version `0.3.0` adds:

- first-class ACP-over-stdio bridge
- `cogni-acp` executable for AionUi and other ACP clients
- isolated ACP session state
- cooperative execution cancellation
- ACP bridge tests
- installable `cogni` CLI
- macOS/Linux installer
- Windows PowerShell installer
- model qualification profiles
- trust tiers
- per-capability minimum trust levels
- runtime policy + model-trust dual gating
- conservative default for unknown models
- single authoritative policy source

The default provider remains a deterministic stub. Real OpenAI, Anthropic, and Ollama adapters are deliberately outside the kernel and should be connected only with provider-specific qualification evidence.
