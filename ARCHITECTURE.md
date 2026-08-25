# Cognigenesis Harness Architecture

## 1. From a large integrated agent to a minimal runtime

The development evolved from **build an agent** toward **build a minimal runtime that can grow an agent safely**.

The original Cognigenesis vision naturally implied permanent subsystems for reasoning, memory, research, coding, artifacts, planning, tools, governance, knowledge graphs, simulation, multi-agent behavior, and self-evolution. Conceptually this is powerful, but each permanent subsystem increases coupling and architectural entropy.

The decisive realization was:

> The system does not need to contain every capability. It needs to know how to reach capabilities.

## 2. Minimal execution kernel

The fundamental runtime remains approximately:

```python
while not done:
    response = model(context, tools)

    if response.tool_calls:
        results = execute(response.tool_calls)
        context += results
    else:
        return response
```

Everything else should justify its existence outside this loop.

## 3. Capability introspection

Capabilities live in a runtime registry and are discoverable rather than assumed from prompting.

Examples:

- `filesystem.read`
- `filesystem.write`
- `filesystem.list`
- `shell.run`
- `workspace.create_project`

The model asks what actually exists instead of inheriting a static claim about tools.

## 4. Markdown as cognitive control plane

Executable machinery belongs in Python or TypeScript.

Behavioral knowledge belongs in Markdown when possible:

- `agent.md`
- `modes/*.md`
- `protocols/*.md`
- `skills/**/SKILL.md`
- `memory/*.md`

This enables reversible, inspectable soft modification without rewriting trusted runtime code.

## 5. Authority boundary

Markdown may request or describe a capability, but declarations do not create executable power.

```text
Markdown declaration
        │
        ▼
Trusted registry lookup
    ┌───┴────┐
  found    missing
    │         │
 expose   capability gap
```

> Markdown describes capabilities. The runtime grants capabilities.

## 6. Soft and hard evolution

### Level 1 — Prompt evolution

Modify behavior documents such as `agent.md`, modes, and protocols.

### Level 2 — Skill evolution

Create reusable procedures from existing capabilities.

### Level 3 — Tool evolution

Add genuinely new executable primitives only when existing capabilities cannot express the required action.

Hard extensions must pass:

```text
generation
→ static inspection
→ sandbox
→ tests
→ permission analysis
→ registration
→ observation
→ rollback
```

## 7. State plane

Conversation history is not sufficient runtime state.

The harness tracks:

- objective
- completed goals
- open goals
- actions
- observations
- artifacts
- checkpoints
- next actions

The context compiler selects only relevant information for the model.

## 8. Semantic capabilities

Primitive tools remain available, but higher-order capabilities can safely compose them.

Example:

```text
workspace.create_project
        ↓
filesystem operations
        ↓
project artifacts
```

This makes agent actions easier to audit and reason about.

## 9. Capability-gap protocol

When functionality is unavailable, the system should explicitly surface a gap rather than hallucinate success.

Resolution order:

```text
missing capability
→ can an existing primitive do it?
→ can existing capabilities be composed?
→ can a new SKILL.md solve it?
→ is a genuinely new executable primitive required?
```

## 10. Architectural rule

Whenever something can safely move out of the kernel, move it out.

---

# 11. Deeper design philosophy

The architecture follows a deliberate asymmetry:

> Kernel complexity should grow slowly. Capability space can grow rapidly.

```text
     Kernel
       │
       │ stable
       ▼
┌──────────────┐
│              │
│ very small   │
│              │
└──────┬───────┘
       │
       │ supports
       ▼
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      CAPABILITY SPACE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
skills
tools
protocols
agents
memories
providers
artifacts
interfaces
workflows
extensions
future capabilities
```

The capability surface can become enormous. The kernel should not.

# 12. Horizontal extension instead of vertical accumulation

A conventional agent framework often grows vertically:

```text
v1  tool calls
v2  + planner
v3  + memory
v4  + browser
v5  + subagents
v6  + workflows
v7  + MCP
v8  + RAG
v9  + evaluation
```

Eventually those concepts become embedded in core execution.

The Cognigenesis Harness instead attempts to make them horizontal extensions:

```text
                 µKERNEL
                    │
        ┌───────────┼────────────┐
        ▼           ▼            ▼
      skill       memory      subagent
        ▼           ▼            ▼
      plugin      plugin       plugin
```

A future multi-agent or swarm layer should be introducible without changing the fundamental recursive execution loop.

# 13. Externalizing useful AI operation

A useful AI assistant already operates conceptually as:

```text
understand intent
↓
inspect available tools
↓
choose capability
↓
execute
↓
inspect result
↓
adjust
↓
produce artifact or answer
```

The harness externalizes this pattern as:

```text
model
+
context compiler
+
capability registry
+
state
+
execution loop
```

The goal is not to simulate fictional intelligence. It is to build a clean runtime around explicit capability orchestration.

# 14. Target project structure

```text
cogni-harness/
│
├── harness.py
├── agent.md
├── config.yaml
├── workspace/
│
├── modes/
│   ├── architect.md
│   ├── investigator.md
│   └── oracle.md
│
├── protocols/
│   ├── core.md
│   ├── recursive-loop.md
│   ├── capability-gap.md
│   └── architect-cycle.md
│
├── skills/
│   ├── coding/SKILL.md
│   ├── research/SKILL.md
│   ├── project-synthesis/SKILL.md
│   └── repository-audit/SKILL.md
│
├── tools/
│   ├── filesystem.py
│   ├── shell.py
│   └── workspace.py
│
├── providers/
│   ├── ollama.py
│   ├── openai.py
│   └── anthropic.py
│
├── artifacts/schemas/
├── memory/
│   ├── working.md
│   └── projects/
├── state/
│   ├── sessions.jsonl
│   ├── goals.json
│   └── checkpoints/
└── extensions/
```

# 15. Conceptual runtime

```text
                    USER
                      │
                      ▼
                   GOAL
                      │
                      ▼
              MARKDOWN GRAPH
                      │
                      ▼
              CONTEXT COMPILER
                      │
                      ▼
                 MODEL BUS
                      │
                      ▼
              EXECUTION KERNEL
               ▲            │
               │            ▼
          OBSERVATION   ACTION REQUEST
               │            │
               │            ▼
               │          POLICY
               │            │
               │            ▼
               │     CAPABILITY REGISTRY
               │            │
               │       ┌────┴─────┐
               │       ▼          ▼
               │     FOUND      MISSING
               │       │          │
               │       ▼          ▼
               └── EXECUTE    CAPABILITY GAP
                                  │
                                  ▼
                            EVOLUTION LAYER
```

# 16. Foundation-first milestone

Do not add glamorous capabilities yet.

Defer:

- swarms
- enormous memory architectures
- autonomous recursive code mutation
- broad plugin synthesis

First prove:

```text
agent.md
↓
load Markdown graph
↓
real model provider
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

Reference demonstration:

```text
$ cogni "Create a Python CLI project for tracking expenses"

[architect mode loaded]
[goal] Create functioning expense-tracker project
[gather] workspace empty
[model] project architecture prepared
[action] workspace.create_project
[result] files created
[action] shell.run: python -m pytest
[result] tests passed
[learn] project operational
[goal completed]
```

# 17. Evolution milestone

Only after the foundation works reliably should capability-gap evolution be enabled.

Reference demonstration:

```text
$ cogni "Inspect this SQLite database and create an HTML report"

[capability discovery]
sqlite inspection: unavailable

[CAPABILITY_GAP]

existing tools sufficient?
No.

[extension proposal]
sqlite_inspector.py

[validation]
passed

[sandbox]
passed

[registration]
sqlite.inspect

[retry]
[execution]
success
[artifact]
report.html
[goal completed]
```

At that point the system transitions from a configurable agent into a small trusted runtime supporting an adaptive and expandable cognitive environment.

> Push mutable intelligence outward while keeping executable authority explicit, inspectable, bounded, and minimal.
