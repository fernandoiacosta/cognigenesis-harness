# AionUi Integration — Cognigenesis Harness 2.0 alpha

Cognigenesis Harness `2.0.0a1` is a Python-native ACP-over-stdio agent. The supported AionUi path remains the packaged `cogni-acp` executable—no local bridge script, Node wrapper, or `.cmd` spawn is required.

## 1. Install and configure Cognigenesis

```text
cogni setup
cogni doctor
```

Then generate the exact AionUi configuration for this machine:

```text
cogni aionui
```

That command prints:

- display name
- absolute `cogni-acp` executable path
- empty arguments
- Ollama environment variables
- exported Cognigenesis logo path

Use those values in **Settings → Agent Management → Custom Agents**.

## 2. Custom Agent values

Typical configuration:

```text
Display Name: Cognigenesis
Command:      C:\...\cogni-acp.exe   (Windows)
              /.../cogni-acp         (macOS/Linux)
Arguments:    <empty>
```

Environment:

```text
COGNI_PROVIDER=ollama
COGNI_OLLAMA_BASE_URL=http://127.0.0.1:11434
COGNI_OLLAMA_MODEL=<model selected by cogni setup>
COGNI_OLLAMA_TIMEOUT=300
PYTHONUTF8=1
```

For slower local models or long research tasks, raise `COGNI_OLLAMA_TIMEOUT` to `600` or more.

## 3. Logo

`cogni setup` exports a stable installed copy of the Cognigenesis logo to the OS user-data directory. `cogni aionui` prints that exact path. Use it in AionUi's **Upload image** field.

The repository source remains:

```text
assets/brand/cognigenesis-logo.svg
```

## 4. Remove the legacy workaround from the execution path

If any traceback contains:

```text
%APPDATA%\AionUi\cognigenesis\cognigenesis_ollama.py
```

that conversation is still using the old workaround instead of the packaged `cogni-acp` entry point.

Fix the Custom Agent command to the absolute path printed by:

```text
cogni aionui
```

Then fully restart AionUi and create a **new** Cognigenesis conversation. `cogni doctor` detects the legacy file and warns about it.

## 5. ACP lifecycle

```text
AionUi
  │ spawn Python-native cogni-acp
  ▼
initialize
  ▼
session/new
  ▼
session/prompt
  ▼
Cognigenesis ExecutionEngine
  ├─ durable conversation context
  ├─ policy/model-trust gate
  ├─ Ollama
  └─ registered tools
  ▼
session/update
  ▼
end_turn
```

Each ACP conversation owns one engine and one isolated state file:

```text
<workspace>/.cognigenesis/sessions/<session-id>.json
```

## 6. Research and tool use

The ACP agent uses the same runtime as the terminal. Research requests may call `web.search` and `web.fetch`; filesystem/workspace capabilities are trust-gated; shell authority is disabled by default.

The tool transcript follows the canonical chat ordering:

```text
user
→ assistant(tool_calls)
→ tool(result)
→ assistant
```

## 7. Windows hardening

The packaged ACP path avoids the failure modes observed during development:

- no Node `.cmd` wrapper during `session/prompt` → avoids `spawn EINVAL`
- UTF-8 stdio → avoids `cp1252`/emoji crashes
- absolute installed executable available from `cogni aionui` → avoids PATH ambiguity
- classified Ollama connection/model/timeout errors → avoids opaque upstream failures where possible

## 8. Verification

Before testing AionUi:

```text
cogni --version
cogni doctor
cogni "Say exactly: OK"
```

Then restart AionUi, open a new Cognigenesis conversation, and send the same prompt.
