# AionUi Integration

Cognigenesis can run in AionUi in two ways:

1. **Skill/launcher mode** — AionUi invokes Cognigenesis as an imported skill or external launcher.
2. **First-class custom agent mode** — AionUi spawns `cogni-acp` as an ACP-compliant agent over stdio.

The second mode is implemented by `acp_bridge.py` and is the preferred path when Cognigenesis should appear alongside other AionUi agents.

## Why the plain CLI failed

The normal `cogni` command is a human-facing CLI. It reads command-line arguments and prints a final result.

AionUi Custom Agents expect an Agent Client Protocol (ACP) process. AionUi launches the agent as a subprocess and communicates over stdin/stdout using ACP JSON-RPC messages such as:

```text
initialize
↓
session/new
↓
session/prompt
↓
session/update
↓
session/prompt response
```

Registering the plain `cogni` CLI as a custom agent therefore fails during ACP initialization.

## ACP entry point

After installing Cognigenesis Harness v0.3.0 or later:

```bash
cogni-acp
```

`cogni-acp` is not an interactive terminal command. It is a stdio protocol server intended to be launched by an ACP client such as AionUi.

Do not add banners or normal stdout logging to this entry point. ACP owns stdout.

## Add Cognigenesis to AionUi

In AionUi:

1. Open **Settings → Agent Management → Custom Agents**.
2. Add a custom agent.
3. Set the display name to `Cognigenesis`.
4. Set the command to:

   ```text
   cogni-acp
   ```

5. Leave arguments empty.
6. Save the agent.
7. Start a new AionUi conversation and choose Cognigenesis.
8. Select the project/working directory for the conversation.

AionUi passes that selected directory to Cognigenesis as the ACP session working directory.

## PATH verification

If AionUi cannot find the agent, verify from a fresh terminal:

macOS/Linux:

```bash
which cogni-acp
```

Windows:

```powershell
where.exe cogni-acp
```

Then restart AionUi so it inherits the updated PATH.

## Session isolation

Each ACP conversation receives:

- its own ACP session ID
- its own execution engine instance
- its own cancellation signal
- its own state file under:

```text
<project>/.cognigenesis/sessions/<session-id>.json
```

The project workspace is shared intentionally; runtime session state is not.

## Capability boundary

ACP transport does not bypass Cognigenesis governance.

AionUi may provide a working directory, additional directories, or MCP server descriptors during session setup. Cognigenesis does **not** automatically grant those as executable authority.

The existing Cognigenesis policy and model-trust gates remain authoritative.

```text
AionUi
  ↓
ACP stdio
  ↓
Cognigenesis ACP bridge
  ↓
Execution Kernel
  ↓
Policy + Model Trust Gate
  ↓
Capability Registry
```

## Cancellation

ACP `session/cancel` sets a cooperative cancellation signal in the Cognigenesis execution kernel. The kernel checks cancellation before model steps and before capability execution.

This prevents Cognigenesis from advertising cancellation while ignoring it. A blocking provider or tool call can still only stop when control returns to the kernel; future provider adapters should support provider-native cancellation where available.

## Current limitation

The ACP bridge solves the AionUi transport/integration problem. It does not change the current model-provider status: the repository still defaults to the deterministic stub provider until a real, qualified provider adapter is enabled.
