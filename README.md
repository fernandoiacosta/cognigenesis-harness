# Cognigenesis Harness

A minimal, extensible agent runtime built around one central principle:

> Keep the execution kernel extremely small. Move cognition, procedures, and growth outward into composable capabilities and Markdown control documents.

## Runtime architecture

```text
objective
  ↓
Markdown control plane
  ↓
context compiler
  ↓
selected model provider
  ↓
execution kernel
  ↓
policy + model trust gate
  ↓
capability registry
  ↓
observation / repeat
```

## v0.4.0: real Ollama execution

Normal execution is now **Ollama-backed by default**. `StubProvider` remains available only when explicitly selected for tests/demo mode.

Default Ollama settings:

```text
COGNI_PROVIDER=ollama
COGNI_OLLAMA_BASE_URL=http://127.0.0.1:11434
COGNI_OLLAMA_MODEL=llama3.1:8b
COGNI_OLLAMA_TIMEOUT=120
```

Any installed Ollama model can be selected, including custom models such as `hasi-edge-AG:latest`.

## Install / upgrade

Requires Python 3.11–3.14 and authenticated access to this private repository.

```powershell
python -m pip install --user --upgrade --force-reinstall "git+https://github.com/fernandoiacosta/cognigenesis-harness.git"
```

Verify:

```powershell
cogni --version
where.exe cogni-acp
ollama list
```

## Terminal usage

```powershell
cogni --provider ollama --model llama3.1:8b "Say OK"
```

Or configure once for the current shell:

```powershell
$env:COGNI_OLLAMA_MODEL = "hasi-edge-AG:latest"
cogni "Say OK"
```

If Ollama is unavailable, Cognigenesis returns an actionable provider error. If the model is missing, it names the model and suggests `ollama pull <model>`.

## AionUi custom ACP agent

Cognigenesis ships a Python-native ACP-over-stdio entry point:

```text
cogni-acp
```

Configure AionUi:

```text
Display name: Cognigenesis
Command:      cogni-acp
Arguments:    <empty>
```

Recommended AionUi environment variables:

```text
COGNI_PROVIDER=ollama
COGNI_OLLAMA_BASE_URL=http://127.0.0.1:11434
COGNI_OLLAMA_MODEL=hasi-edge-AG:latest
COGNI_OLLAMA_TIMEOUT=120
```

The ACP bridge is Python-native and does not launch Node `.cmd` wrappers during `session/prompt`, avoiding the Windows `spawn EINVAL` workaround that was previously required.

See [`AIONUI.md`](AIONUI.md).

## Model alignment and authority

Connecting a model does not automatically grant it authority. Models receive conservative trust profiles until qualified, and capabilities require both runtime-policy approval and a sufficient trust tier.

See [`ALIGNMENT.md`](ALIGNMENT.md) and [`SECURITY.md`](SECURITY.md).

## Tests

CI runs on Ubuntu, macOS, and Windows across supported Python versions. It includes:

- mocked Ollama HTTP response tests
- explicit provider-selection tests
- ACP subprocess handshake/prompt smoke tests
- Windows-safe Python argument-array launch path
- optional live Ollama ACP round trip with `COGNI_TEST_OLLAMA=1`
