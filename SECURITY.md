# Security Model

## Trust Boundary

Markdown is untrusted behavioral input. It does not create executable authority.

Only capabilities registered by trusted runtime code can execute.

## Filesystem

All built-in filesystem and workspace operations resolve paths relative to the configured workspace and reject traversal outside it.

## Shell

Commands are tokenized with `shlex.split` and executed with `shell=False` inside the workspace.

## Extension Policy

Executable extension is intentionally not implemented in v0.1. A future extension system must include:

- static inspection
- sandbox execution
- tests
- explicit permission declaration
- policy approval
- registration
- observation
- rollback
