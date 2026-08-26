# AionUi Integration

Cognigenesis Harness v0.6.0 is a Python-native ACP agent backed by Ollama by default, with persistent multi-turn context and read-only web research.

## Install / upgrade

```powershell
python -m pip install --user --upgrade --force-reinstall "git+https://github.com/fernandoiacosta/cognigenesis-harness.git"
```

Verify:

```powershell
cogni --version
cogni doctor
where.exe cogni-acp
```

Expected version: `cognigenesis-harness 0.6.0`.

## Important: remove the old local workaround from the execution path

If an AionUi error traceback contains:

```text
%APPDATA%\AionUi\cognigenesis\cognigenesis_ollama.py
```

then that conversation is **not using the packaged `cogni-acp` agent**. It is still using the legacy local bridge.

Configure the Custom Agent as:

```text
Display Name: Cognigenesis
Command: cogni-acp
Arguments: <leave empty>
```

Then restart AionUi and start a new Cognigenesis conversation. `cogni doctor` will warn if the legacy file is still present.

## Ollama setup

```powershell
ollama list
```

Pull a model if needed:

```powershell
ollama pull llama3.1:8b
```

Recommended environment variables:

```text
COGNI_PROVIDER=ollama
COGNI_OLLAMA_BASE_URL=http://127.0.0.1:11434
COGNI_OLLAMA_MODEL=hasi-edge-AG:latest
COGNI_OLLAMA_TIMEOUT=300
```

For a slower model or long research task, use `600` or higher for `COGNI_OLLAMA_TIMEOUT`.

## Test in terminal first

```powershell
cogni --provider ollama --model hasi-edge-AG:latest "Say OK"
cogni --provider ollama --model hasi-edge-AG:latest "Research online and compare current agent harnesses"
```

Interactive chat:

```powershell
cogni chat --provider ollama --model hasi-edge-AG:latest --workspace .
```

## Web research

v0.6 registers two read-only capabilities:

```text
web.search
web.fetch
```

When the user asks to research online, compare current systems, verify claims, or retrieve current information, the Ollama provider is instructed to call these tools before answering and cite returned URLs.

External pages are marked untrusted and cannot grant mutation authority.

## Logo

Canonical source:

```text
assets/brand/cognigenesis-logo.svg
```

Export to 512×512 PNG for AionUi's **Upload image** field.

## Persistent ACP context

Each AionUi conversation owns one Cognigenesis `ExecutionEngine`; repeated `session/prompt` calls reuse its prior user/assistant history.

Runtime state is isolated under:

```text
<project>/.cognigenesis/sessions/<session-id>.json
```

## Windows behavior

`cogni-acp` is Python-native and does not spawn Node `.cmd` wrappers during `session/prompt`, avoiding the earlier `spawn EINVAL` failure mode.

v0.6 also forces UTF-8 stdio, preventing Windows `cp1252` crashes when model output contains emoji or other Unicode characters.

## Actionable errors

If Ollama is down:

```text
Provider error: Ollama is not reachable at http://127.0.0.1:11434...
```

If generation exceeds the configured timeout:

```text
Provider error: Ollama timed out after <N>s while generating with model '<model>'...
```

If the model is missing:

```text
ollama pull <model>
```

Known provider/runtime failures are returned as agent messages with an ACP `end_turn` whenever possible instead of opaque `UNKNOWN_UPSTREAM_ERROR` failures.
