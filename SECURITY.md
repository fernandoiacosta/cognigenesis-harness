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

## Filesystem

All built-in filesystem and workspace operations resolve paths relative to the configured workspace and reject traversal outside it.

## Shell

Commands are tokenized with `shlex.split` and executed with `shell=False` inside the workspace. `shell.run` requires a higher model trust tier than read-only filesystem capabilities.

## Policy Source of Truth

`core/capability_policy.py` is the authoritative capability/trust mapping. `config.yaml` points to this source rather than duplicating the allowlist.

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
