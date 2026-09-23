# Cognigenesis

![Cognigenesis logo](assets/brand/cognigenesis-logo.svg)

**Cognitive operating environment for models, agents, teams, tools, and reasoning scaffolding.**

Cognigenesis is the cognitive architecture. **Cognigenesis Harness** is the runtime substrate underneath it.

The project has entered the **2.0 alpha architecture**: the working v1 terminal/Ollama/ACP paths remain intact while the platform gains semantic events, explicit cognitive state, a shared task graph, typed agent-to-agent communication, and team/swarm primitives.

## What changed in 2.0a1

The platform now contains four explicit layers:

```text
Command Center / Terminal / ACP
             │
             ▼
      Agent Fabric / Teams
             │
             ▼
      Cognitive Architecture
             │
             ▼
        Harness Runtime
             │
             ▼
        Model Substrate
```

New live runtime primitives include:

- semantic `EventBus` for turns, models, tools, policy decisions, failures, and completion
- shared dependency-aware `TaskGraph`
- inspectable `CognitiveLedger` for hypotheses, evidence, contradictions, confidence, and open questions
- typed `AgentMessage` protocol for findings, hypotheses, critiques, decisions, handoffs, and artifacts
- `TeamManager` plus reusable Parallel Search, Adversarial Council, Red/Blue, Specialist Pipeline, and Consensus patterns
- UI-neutral `CommandCenterSnapshot` for the future graphical dashboard and full-screen TUI

The existing execution engine now emits those semantic events directly.

## Terminal

Install/upgrade from the private repo:

```powershell
python -m pip install --user --upgrade --force-reinstall "git+https://github.com/fernandoiacosta/cognigenesis-harness.git"
```

Then:

```text
cogni setup
cogni doctor
cogni chat
```

Inside chat:

```text
/help
/new
/state
/capabilities
/cognition
/tasks
/events
/provider
/workspace
/doctor
/exit
```

The response renderer now uses normal Rich wrapping inside terminal-width panels; long prose should no longer disappear beyond the right edge.

## Teams

Run a bounded multi-agent cognition pattern over the same runtime:

```powershell
cogni team --pattern adversarial-council "Evaluate this architecture and try to falsify its assumptions"
```

Available patterns:

```text
parallel-search
adversarial-council
red-blue
specialist-pipeline
consensus
```

Each agent gets an isolated session while sharing the mission task graph, cognitive ledger, event stream, and team message fabric.

## Command Center

Launch the first graphical Command Center:

```powershell
cogni command-center --workspace . --open
```

Then run `cogni chat --workspace .` or `cogni team ... --workspace .` in another terminal. The dashboard polls the same atomic workspace snapshot and displays:

- cognitive metrics, hypotheses, and evidence
- task graph
- teams and agents
- recent semantic runtime events

The current web dashboard is the first UI over the shared state contract, not a separate backend.

## AionUi / ACP

The supported ACP entry point remains:

```text
cogni-acp
```

Generate the exact machine-specific configuration with:

```text
cogni aionui
```

ACP and the terminal share the same execution engine. v2 runtime events are designed so ACP, the future TUI, tracing, and the graphical Command Center consume the same state rather than maintaining parallel implementations.

See [AIONUI.md](AIONUI.md).

## Cognitive architecture

Cognigenesis does **not** claim to expose hidden model chain-of-thought. It externalizes observable reasoning scaffolding:

```text
observation
   ↓
candidate hypotheses
   ↓
mechanisms
   ↓
evidence / contradictions
   ↓
verification
   ↓
confidence update
   ↓
decision / action
```

The goal is to make cognition increasingly architecture-enforced rather than relying only on system-prompt instructions.

## Validation

Controlled evaluation now begins with [Experiment 001](experiments/001/README.md), a pre-registered same-model comparison of the current Cognigenesis control plane against a minimal baseline. The fixed corpus, raw-output runner, deterministic scorer, thresholds, limitations, and integrity rules are committed before the first run. No performance claim should be made until the saved run returns `WIN`, `TIE`, `LOSS`, or `INVALID`.

## Teams and swarm

The harness remains a small per-agent runtime. Team coordination lives above it.

Typed inter-agent objects currently include:

```text
Task
Finding
Hypothesis
Evidence
Question
Critique
Decision
Handoff
Status
Artifact
```

This is the foundation for a Command Center that can visualize not only which agent is active, but **what cognitive work is moving between agents**.

## Current model/provider path

Ollama remains the local-first provider. Model qualification and trust gating remain active; mutation authority is separate from both model capability and user/operator permission.

## Architecture and roadmap

- [Cognigenesis Platform](docs/COGNIGENESIS_PLATFORM.md)
- [Architecture](ARCHITECTURE.md)
- [Roadmap](ROADMAP.md)
- [Security](SECURITY.md)
- [Installation](INSTALL.md)
- [Branding](BRANDING.md)

## Architectural invariant

> The harness is the kernel. Cognigenesis is the cognition layer. Teams, swarm orchestration, and the Command Center grow above them without turning the kernel into a monolith.

## Provider setup

Install on macOS/Linux (review the installer before piping it to a shell):

```sh
curl -fsSL https://raw.githubusercontent.com/fernandoiacosta/cognigenesis-harness/main/install.sh | sh
```

Choose a provider; API keys are stored in your OS credential manager, or you can set the documented environment variable instead:

```sh
cogni login openai --model gpt-4.1-mini
cogni login anthropic --model claude-sonnet-4-5
cogni login google --model gemini-2.5-flash
cogni login grok --model grok-3-mini
cogni login meta --model YOUR_MODEL --base-url https://YOUR_INFERENCE_HOST/v1/chat/completions
cogni login ollama --model llama3.1:8b --base-url http://192.168.1.20:11434
cogni login litert --model YOUR_IMPORTED_MODEL
```

`cogni login` configures API access. It does not authenticate a ChatGPT/Codex or Claude subscription. OpenAI, Anthropic, Google, xAI, and third-party Meta hosts require their own API key or host credentials. Environment overrides: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `XAI_API_KEY`, `COGNI_META_API_KEY`. `COGNI_PROVIDER`, `COGNI_MODEL`, `COGNI_OLLAMA_BASE_URL`, and `COGNI_CLOUD_BASE_URL` override saved settings. A single active provider/model is stored; switching providers requires another `cogni login` call.

Google AI Edge Gallery's official app does not currently offer an external model server. An unmerged community Edge Server PR proposes one. For **on-device Google models today**, import a model into Google's LiteRT-LM CLI and run `litert-lm serve`, then `cogni login litert --model YOUR_IMPORTED_MODEL` (default `http://127.0.0.1:9379`). `cogni login edge --model MODEL --base-url http://PHONE_IP:PORT` targets a server-enabled Gallery build when available. Both local adapters use OpenAI-compatible text chat; tool calling is not available in this integration. Keep LAN inference servers on trusted networks.

For remote Ollama, configure `--base-url` with the Ollama host's reachable address; server-side binding/firewall configuration is required on that machine. `cogni setup --base-url URL` also discovers its installed models.
