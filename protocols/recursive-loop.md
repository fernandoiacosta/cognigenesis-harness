# Recursive Execution Loop

```text
objective
↓
compile relevant context
↓
model
↓
final? ── yes → return
↓ no
tool request
↓
policy
↓
registry
↓
execute
↓
observation
↓
state update
↓
repeat
```

The loop is intentionally generic. Domain intelligence should live outside the kernel.
