# Model Qualification and Capability Alignment

Cognigenesis Harness must not assume that connecting a model makes that model trustworthy.

The harness separates **capability** from **authority**.

## Principle

> Capability should scale with demonstrated alignment and competence, not merely model availability.

A more capable harness can amplify both strengths and failure modes. Therefore every model should begin restricted and earn broader capability access through qualification evidence.

## Qualification Dimensions

Profiles measure:

- reasoning quality
- instruction fidelity
- tool-use reliability
- uncertainty calibration
- goal persistence
- resistance to hallucinating unavailable capabilities
- recovery behavior after failures
- protocol compatibility

## Trust Tiers

### Tier 0 — Observer

No mutation authority. Suitable for unqualified or unreliable models.

### Tier 1 — Basic

Low-risk workspace inspection and constrained operations.

### Tier 2 — Trusted

Broader workspace actions after demonstrated reliability.

### Tier 3 — Extended

Higher-risk capabilities may be considered, still subject to explicit runtime policy.

Trust tiers do not bypass policy. They add an additional gate.

## Rule

A capability is executable only when both conditions are true:

1. Runtime policy grants it.
2. The active model profile meets its minimum trust tier.

```text
MODEL
  │
  ▼
QUALIFICATION
  │
  ▼
MODEL PROFILE
  │
  ▼
TRUST TIER
  │
  ├─────────────┐
  ▼             ▼
POLICY       CAPABILITY
  │             │
  └──────┬──────┘
         ▼
      EXECUTE
```

## Conservative Default

Unknown models do not inherit trust from Cognigenesis. New providers begin with a conservative bootstrap profile until measured by an evaluation suite.

A high average score cannot hide a severe weakness in instruction fidelity, tool reliability, or capability-hallucination resistance. Critical-dimension floors cap the resulting trust tier.
