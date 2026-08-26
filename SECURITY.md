# Security Model

## Trust Boundary

Markdown and retrieved content are behavioral/evidentiary inputs. They do not create executable authority. Only capabilities registered by trusted runtime code can execute.

## Model Trust Boundary

Connecting a model does not grant that model authority. Every model is associated with a `ModelProfile` and trust tier. Execution requires both:

1. runtime policy approval, and
2. a model trust tier at or above the capability minimum.

Unknown/unqualified models start restricted. Qualification is a risk-control mechanism, not proof of universal alignment.

## Cognitive Control Plane Packaging

The canonical `agent.md` used at runtime is packaged inside `cognigenesis.resources`. Installed behavior therefore does not silently disappear when the repository root is absent. The repository copy mirrors the packaged copy for review.

## Configuration

There is one supported user configuration source: the OS-standard Cognigenesis config directory resolved by `platformdirs`. Precedence is:

```text
CLI flags
→ environment variables
→ persisted user configuration
→ safe defaults
```

The previous unused `config.yaml` was removed to avoid configuration drift.

## ACP / AionUi Transport Boundary

`cogni-acp` is a transport adapter, not an authority adapter. Client-provided additional directories or MCP descriptors are not automatically registered as executable Cognigenesis capabilities.

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

ACP owns stdout. Non-protocol banners/debug prints must never be added to `cogni-acp`. Human diagnostics belong on stderr or in structured agent updates.

ACP cancellation is cooperative; blocking provider/tool calls can stop only when control returns unless a future provider adds native cancellation.

## Filesystem

Built-in filesystem/workspace operations resolve paths under the configured workspace and reject traversal outside it.

State files are written atomically using a temporary file followed by replacement. Corrupt state is preserved with a `.corrupt` suffix rather than overwritten silently.

## Web Research / SSRF

`web.search` and `web.fetch` are read-only evidence capabilities. Retrieved content is explicitly untrusted.

`web.fetch` only accepts HTTP(S) URLs whose resolved addresses are public/global. It blocks localhost, `.local`, private, loopback, link-local, reserved, multicast, and other non-global targets so the research tool is not an implicit private-network/metadata-service fetch primitive.

DNS rebinding and proxy-layer behavior remain environment-level risks; deployments with stronger network isolation requirements should enforce egress policy outside the process as well.

## Shell

`shell.run` is registered but **disabled by default**, including for highly qualified models. It requires explicit runtime opt-in plus the required trust tier.

Commands use argument arrays, `shell=False`, UTF-8 replacement decoding, a workspace cwd, and a bounded timeout. This is not equivalent to an OS sandbox; shell authority should remain disabled unless the operator deliberately accepts that risk or a stronger sandbox is added.

## Policy Source of Truth

`core/capability_policy.py` defines capability minimum trust tiers. `core/policy.py` enforces runtime authority. User configuration cannot self-grant capabilities that runtime policy does not expose.

## Extension Policy

Executable extension remains intentionally gated. A future extension system must include static inspection, sandbox execution, tests, explicit permission declaration, policy approval, model trust analysis, registration, observation, and rollback.
