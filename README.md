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

## Core principle

The system does not need to contain every capability. It needs to know how to reach capabilities.

Capabilities are discoverable at runtime rather than assumed from prompting. Markdown describes behavior and requested authority; trusted runtime code grants authority. Prefer soft evolution before hard executable extension.

Run:

```bash
python harness.py "Inspect this workspace and summarize its architecture."
```

The initial implementation uses a deterministic stub provider so the runtime can be tested without credentials. Real provider adapters remain outside the kernel.
