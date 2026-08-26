# Security Model

## Trust Boundary

Markdown is untrusted behavioral input. It does not create executable authority.

Only capabilities registered by trusted runtime code can execute.

## Model Trust Boundary

Connecting a model does not grant that model authority.

Every model is associated with a `ModelProfile` and trust tier. The runtime requires both:

1. explicit capability approval by runtime policy, and
2. a model trust tier at or above the capability's minimum tier.

Unknown or unqualified models default to restricted authority. A strong harness must not automatically amplify an unreliable model.

Qualification is a risk-control mechanism, not proof of universal model alignment. Provider-specific evaluations must be run and updated as models change.

## ACP / AionUi Transport Boundary

`cogni-acp` is a transport adapter, not an authority adapter.

AionUi launches Cognigenesis as an ACP subprocess and supplies the user-selected project directory as the session working directory. The ACP bridge may also receive additional directory descriptors or MCP server descriptors from a client; these are **not automatically registered as Cognigenesis capabilities**.

The authority path remains:

```text
ACP client
  ↓
ACP stdio bridge
  ↓
Execution Kernel
  ↓
Runtime Policy + Model Trust Gate
  ↓
Capability Registry
```

ACP owns stdout for the lifetime of `cogni-acp`. Human-readable banners, debug prints, or other non-protocol stdout output can corrupt the JSON-RPC stream and must not be added to the ACP entry point. Diagnostics should use stderr or structured ACP updates.

Each ACP conversation receives a session-specific state file under `.cognigenesis/sessions/` so multiple conversations in the same project do not overwrite one shared runtime state document.

ACP cancellation is cooperative. The kernel checks the cancellation signal before model steps and before capability execution. A blocking provider or capability cannot be forcibly interrupted until control returns to the kernel; provider-specific adapters should implement native cancellation where available.

## Filesystem

All built-in filesystem and workspace operations resolve paths relative to the configured workspace and reject traversal outside it.

For ACP sessions, that workspace is the project directory selected by the client/user when the session is created.

## Shell

`shell.run` is registered but **disabled by default**, even for highly qualified models. It requires explicit runtime opt-in plus the required model trust tier.

Commands use `shlex.split` and `shell=False`, but running with the workspace as the current directory is not equivalent to an operating-system sandbox. Shell authority should remain disabled until a stronger process/filesystem sandbox is implemented or an operator deliberately accepts that risk.

## Policy Source of Truth

`core/capability_policy.py` defines capability minimum trust tiers. `core/policy.py` enforces runtime authority. `config.yaml` points to these sources rather than duplicating capability grants.

## Extension Policy

Executable extension remains intentionally gated. A future extension system must include:

- static inspection
- sandbox execution
- tests
- explicit permission declaration
- policy approval
- model trust-tier analysis
- registration
- observation
- rollback
