# Model Qualification and Capability Alignment

Cognigenesis Harness separates **capability** from **authority**.

> Capability should scale with demonstrated alignment and competence, not merely model availability.

## Trust tiers

### Observer

Unqualified/default state. Read-only public research is available; workspace mutation is not.

### Basic

Low-risk workspace inspection may be considered.

### Trusted

Normal trust-gated workspace operations may execute when runtime policy also permits them.

### Extended

Reserved for stronger external evidence. The built-in v1 qualification suite **cannot** grant this tier.

## Built-in v1 qualification

Run:

```text
cogni qualify
```

or simply:

```text
cogni setup
```

when a local Ollama model is available. Setup automatically qualifies models that do not already have a successful saved profile.

The bounded suite checks:

- instruction fidelity
- capability-boundary discipline
- uncertainty behavior
- tool-failure discipline

The resulting `ModelProfile` also carries conservative estimates for reasoning, goal persistence, recovery, and protocol compatibility. Evidence and profile metadata are persisted in the Cognigenesis user-data directory.

A successful built-in suite can promote a model to **Trusted**, enabling normal mutation capabilities that already pass runtime policy. It cannot grant Extended authority.

Failed or low-trust profiles remain restricted and are automatically reevaluated by `cogni setup`; `cogni qualify --force` explicitly reruns the suite.

## Dual-gate rule

A capability executes only when both conditions are true:

1. runtime policy grants it
2. the active persisted model profile meets its minimum trust tier

```text
MODEL
  │
  ▼
QUALIFICATION EVIDENCE
  │
  ▼
MODEL PROFILE
  │
  ▼
TRUST TIER
  │
  ├───────────────┐
  ▼               ▼
RUNTIME POLICY  CAPABILITY MINIMUM
  │               │
  └───────┬───────┘
          ▼
        EXECUTE
```

## Conservative default

Unknown model identifiers do not inherit trust from Cognigenesis. A changed model name/version with no matching saved profile starts from the conservative profile.

A high average score cannot hide severe weaknesses in instruction fidelity, tool reliability, or capability-hallucination resistance; critical-dimension floors cap the tier.

## What qualification does not prove

The built-in suite is a practical runtime risk control, not proof of general intelligence, universal safety, or correctness. Higher-risk future capabilities should require deeper provider/model-version-specific evaluation and adversarial evidence before any Extended promotion mechanism is introduced.
