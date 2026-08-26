# AionUi Integration

Cognigenesis Harness v0.4.0 is a Python-native ACP agent backed by Ollama by default.

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

Expected version: `cognigenesis-harness 0.4.0`.

## Ollama setup

Verify Ollama is running and inspect local models:

```powershell
ollama list
```

Pull the default model if needed:

```powershell
ollama pull llama3.1:8b
```

Or use another installed model, for example:

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

```powershell
cogni --provider ollama --model llama3.1:8b "Say OK"
```

Or, using environment configuration:

```powershell
$env:COGNI_OLLAMA_MODEL = "hasi-edge-AG:latest"
cogni "Say OK"
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

The AionUi host controls the surrounding application theme; the Cognigenesis theme defines Cognigenesis-owned surfaces, launchers, dashboards, future ACP UI, and supporting documentation.

If AionUi does not inherit your shell environment, add these in the agent's **Environment Variables** section:

```text
COGNI_PROVIDER=ollama
COGNI_OLLAMA_BASE_URL=http://127.0.0.1:11434
COGNI_OLLAMA_MODEL=hasi-edge-AG:latest
COGNI_OLLAMA_TIMEOUT=120
```

Use a model name shown by `ollama list`.

## Windows spawn behavior

`cogni-acp` is a Python-native ACP stdio server. It does not spawn a Node `.cmd` wrapper during `session/prompt`, avoiding the Windows `spawn EINVAL` failure mode seen with wrapper-based bridges.

The package entry point launches Python code directly. The ACP regression test also launches the bridge with `sys.executable`, `-m`, `acp_bridge` as an argument array rather than through a `.cmd` shell wrapper.

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
Cognigenesis execution kernel
  ↓
Ollama /api/chat
  ↓
session/update
  ↓
end_turn
```

Each ACP session gets isolated state under:

```text
<project>/.cognigenesis/sessions/<session-id>.json
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
