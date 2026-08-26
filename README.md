# Cognigenesis Harness

![Cognigenesis logo](assets/brand/cognigenesis-logo.svg)

A local-first conversational agent runtime with Ollama, ACP-over-stdio support for AionUi, trust-gated capabilities, persistent chat, and read-only web research.

## v0.6.0 — research + Windows hardening

This release fixes three concrete failure modes seen in AionUi/Windows:

1. **Long Ollama prompts timing out** — default timeout is now 300s and timeout errors are classified separately from connection failures.
2. **Windows cp1252 crashes on emoji/Unicode** — `cogni`, `cogni-acp`, and the direct harness entry point force UTF-8 stdio.
3. **"Research online" without a web tool** — Cognigenesis now registers read-only `web.search` and `web.fetch` capabilities and instructs Ollama to use them for current/online research requests.

It also adds:

```powershell
cogni doctor
```

which checks the installed executables, Python/stdout encoding, Ollama reachability/model availability, and warns if the old AionUi workaround script still exists at:

```text
%APPDATA%\AionUi\cognigenesis\cognigenesis_ollama.py
```

If that warning appears, AionUi may still be bypassing the packaged ACP agent.

## Install / upgrade

```powershell
python -m pip install --user --upgrade --force-reinstall "git+https://github.com/fernandoiacosta/cognigenesis-harness.git"
```

Verify:

```powershell
cogni --version
cogni doctor
where.exe cogni-acp
ollama list
```

Expected version: `cognigenesis-harness 0.6.0`.

## Terminal chat

```powershell
cogni chat --provider ollama --model hasi-edge-AG:latest --workspace .
```

One-shot execution still works:

```powershell
cogni --provider ollama --model hasi-edge-AG:latest "Research online and compare modern agent harnesses"
```

Default Ollama environment:

```text
COGNI_PROVIDER=ollama
COGNI_OLLAMA_BASE_URL=http://127.0.0.1:11434
COGNI_OLLAMA_MODEL=llama3.1:8b
COGNI_OLLAMA_TIMEOUT=300
```

For a slow local model, increase the timeout explicitly:

```powershell
$env:COGNI_OLLAMA_TIMEOUT = "600"
```

## AionUi custom ACP agent

Configure AionUi Custom Agent as:

```text
Display name: Cognigenesis
Command:      cogni-acp
Arguments:    <empty>
```

Recommended environment variables:

```text
COGNI_PROVIDER=ollama
COGNI_OLLAMA_BASE_URL=http://127.0.0.1:11434
COGNI_OLLAMA_MODEL=hasi-edge-AG:latest
COGNI_OLLAMA_TIMEOUT=300
```

**Do not point AionUi at the old local `cognigenesis_ollama.py` bridge.** The packaged `cogni-acp` process is the maintained path.

See [`AIONUI.md`](AIONUI.md).

## Research capabilities

Cognigenesis now exposes:

```text
web.search  Search the public web (read-only)
web.fetch   Fetch readable text from public HTTP(S) pages (read-only)
```

External content is explicitly marked untrusted. Web research does not grant filesystem mutation or shell authority.

## Conversation model

The same `ExecutionEngine` backs terminal chat and ACP sessions, retaining prior user/assistant turns across repeated calls.

## Brand and theme

Canonical assets:

```text
assets/brand/cognigenesis-logo.svg
assets/brand/theme.json
assets/brand/theme.css
```

See [`BRANDING.md`](BRANDING.md).

## Tests

CI covers Ubuntu, macOS, and Windows and includes Ollama provider tests, timeout classification, provider selection, persistent conversation history, ACP subprocess handshake, Windows-safe Python launch behavior, and web research parser/policy tests.
