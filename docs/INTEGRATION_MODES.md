# Cognigenesis Integration Modes

Author and rights holder: **Fernando Acosta**

Status: **Frozen implementation contract. The capabilities described here are not complete until the acceptance checks pass on a clean machine.**

## Objective

Cognigenesis Harness must support two explicit operating modes during guided setup while preserving its existing standalone behavior.

### Inside Armor

Inside Armor attaches Cognigenesis to an existing host harness such as Codex without representing Cognigenesis as a foundation-model identifier or replacing the host.

The adapter may provide Cognigenesis policy, cognitive scaffolding, memory, evaluation, and permissioned tool routing. It must:

- detect supported host installations without executing host code;
- show the files and settings it proposes to create or change;
- preserve existing configuration and create a restorable backup before mutation;
- never copy credentials into Cognigenesis configuration;
- support dry-run, apply, verify, and uninstall/restore operations;
- record the host, adapter version, source paths, hashes, and resulting activation state.

The first acceptance target is one complete Codex integration path. Other hosts remain adapters behind the same contract.

### Exoskeleton

Exoskeleton discovers installed harnesses and inventories their agents, skills, plugins, hooks, and MCP servers. Discovery is automatic; activation is permissioned.

The required sequence is:

```text
discover -> inventory -> normalize -> hash provenance -> inspect permissions
         -> resolve conflicts -> approve -> activate -> verify -> restore
```

Discovery must treat every external manifest and directory as untrusted input. It must not import Python modules, run package scripts, start MCP servers, follow commands embedded in documentation, or expose secrets.

Each normalized inventory record must include:

- source harness and source path;
- capability type and stable identifier;
- content or manifest hash;
- declared commands, network access, filesystem access, and credential requirements;
- compatibility and conflict results;
- state: `DISCOVERED`, `BLOCKED`, `APPROVED`, `ACTIVE`, `FAILED`, or `REMOVED`;
- activation and restoration evidence.

Unknown formats may be reported as discovered but unsupported. They must not be silently approximated.

## Fast decision-engine interface

Small non-generative decision models are optional routing components, not replacements for Cognigenesis reasoning or model providers.

The interface must accept typed decision requests and return a value, calibrated confidence when available, engine identity/version, latency, and failure status. The first open-source candidate is Laya, isolated behind a replaceable adapter so future engines can be added without changing the execution kernel.

Initial eligible uses:

- intent and task routing;
- risk or permission triage;
- confidence-gated escalation to a generative model;
- deterministic evaluation support where the decision schema is explicit.

Laya must not authorize consequential tool execution by itself. Low confidence, unsupported schemas, engine failure, or policy conflict must escalate or fail closed according to the caller's frozen policy.

## Required setup experience

Guided setup must offer:

```text
How should Cognigenesis operate?
  1. Standalone
  2. Inside Armor — augment one existing harness
  3. Exoskeleton — discover and organize installed harness capabilities
```

The confirmation screen must distinguish discovered, proposed, and activated capabilities. A user must be able to exit without modifying the machine.

Noninteractive equivalents must support explicit mode selection and JSON output. Proposed commands:

```text
cogni integrate discover --json
cogni integrate plan --mode inside-armor --host codex --json
cogni integrate plan --mode exoskeleton --json
cogni integrate apply PLAN_ID
cogni integrate verify
cogni integrate restore
cogni decision doctor --engine laya --json
```

Exact command spelling may change before implementation, but dry-run, apply, verify, and restore are mandatory behaviors.

## Acceptance checks

The smallest shippable vertical slice is complete only when all of the following are preserved in GitHub and pass:

1. A clean install reaches the three-mode setup screen.
2. Inside Armor detects Codex, previews changes, applies one adapter, verifies it, and restores the prior configuration.
3. Exoskeleton inventories at least one supported skill source and one MCP source without executing either.
4. A malicious manifest fixture cannot trigger code execution, path traversal, secret capture, or activation.
5. Re-running discovery is idempotent and does not duplicate records.
6. Existing provider/model selection and saved credentials survive mode changes.
7. Laya is optional: the harness starts and operates when it is absent.
8. A frozen routing corpus compares Laya with a deterministic baseline on accuracy, latency, calibration, abstention, and severe-error rate.
9. No superiority, security, or performance claim is emitted automatically from a passing smoke test.
10. Cross-platform tests, package build, installer validation, and the existing full regression suite remain green.

## Stopping rule

After the Codex Inside Armor path, bounded Exoskeleton inventory, malicious-manifest test, and optional Laya adapter pass, stop feature expansion. Run clean-device acceptance and preserve the evidence before adding another host harness, decision engine, dashboard surface, or provider.

## Non-goals for the first release

- executing every discovered plugin automatically;
- merging credentials or unrestricted host permissions;
- claiming compatibility with formats that have not been parsed and tested;
- replacing model-provider APIs or presenting Cognigenesis as a model ID;
- broad self-modification or uncontrolled learning from installed code;
- expanding Experiment 002 claims before real preserved results exist.
