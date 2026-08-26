# AionUi Integration

Cognigenesis Harness v0.5.0 is a Python-native ACP agent backed by Ollama by default, with persistent multi-turn conversation context per ACP session.

## Install / upgrade

Because this repository is private, install from an authenticated Git checkout:

```powershell
python -m pip install --user --upgrade --force-reinstall "git+https://github.com/fernandoiacosta/cognigenesis-harness.git"
```

Verify:

```powershell
cogni --version
where.exe cogni-acp
```

Expected version: `cognigenesis-harness 0.5.0`.

## Ollama setup

Verify Ollama is running and inspect local models:

```powershell
ollama list
```

Pull the default model if needed:

```powershell
ollama pull llama3.1:8b
```

Or use another installed model:

```powershell
$env:COGNI_OLLAMA_MODEL = "hasi-edge-AG:latest"
```

Supported environment variables:

```text
COGNI_PROVIDER=ollama
COGNI_OLLAMA_BASE_URL=http://127.0.0.1:11434
COGNI_OLLAMA_MODEL=llama3.1:8b
COGNI_OLLAMA_TIMEOUT=120
```

## Test in the terminal first

One-shot:

```powershell
cogni --provider ollama --model llama3.1:8b "Say OK"
```

Interactive chat:

```powershell
cogni chat --provider ollama --model llama3.1:8b --workspace .
```

## Configure AionUi Custom Agent

Open **Settings → Agent Management → Custom Agents** and use:

```text
Display Name: Cognigenesis
Command: cogni-acp
Arguments: <leave empty>
```

### Logo

Use the Cognigenesis brand mark instead of the generic robot avatar.

Canonical source:

```text
assets/brand/cognigenesis-logo.svg
```

AionUi's Custom Agent form exposes **Upload image**. Export the SVG to a 512×512 PNG and upload that PNG as the agent image.

Branding source of truth:

```text
BRANDING.md
assets/brand/theme.json
assets/brand/theme.css
```

If AionUi does not inherit your shell environment, add these in the agent's **Environment Variables** section:

```text
COGNI_PROVIDER=ollama
COGNI_OLLAMA_BASE_URL=http://127.0.0.1:11434
COGNI_OLLAMA_MODEL=hasi-edge-AG:latest
COGNI_OLLAMA_TIMEOUT=120
```

Use a model name shown by `ollama list`.

## Persistent ACP conversation context

Each AionUi conversation owns one Cognigenesis `ExecutionEngine`. Repeated `session/prompt` calls reuse that engine and therefore preserve prior user/assistant turns in model context.

```text
session/new
  ↓
engine created
  ↓
prompt 1 → history retained
  ↓
prompt 2 → prior turn included
  ↓
prompt 3 → prior turns included
```

This is real multi-turn context, not just shared files or a changing state snapshot.

Each ACP session also gets isolated runtime state under:

```text
<project>/.cognigenesis/sessions/<session-id>.json
```

## Windows spawn behavior

`cogni-acp` is a Python-native ACP stdio server. It does not spawn a Node `.cmd` wrapper during `session/prompt`, avoiding the Windows `spawn EINVAL` failure mode seen with wrapper-based bridges.

The package entry point launches Python code directly. The ACP regression test launches the bridge with `sys.executable`, `-m`, `acp_bridge` as an argument array rather than through a `.cmd` shell wrapper.

## ACP lifecycle

```text
AionUi
  ↓ spawn cogni-acp
initialize
  ↓
session/new
  ↓
session/prompt
  ↓
Cognigenesis execution kernel + conversation history
  ↓
Ollama /api/chat
  ↓
session/update
  ↓
end_turn
```

## Actionable provider errors

If Ollama is down, Cognigenesis reports:

```text
Provider error: Ollama is not reachable at http://127.0.0.1:11434. Start Ollama and verify it with: ollama list
```

If the configured model is missing, Cognigenesis reports the model and suggests:

```text
ollama pull <model>
```

Known provider failures are returned to AionUi as agent messages with a normal ACP `end_turn` instead of leaking an opaque internal error whenever possible.
