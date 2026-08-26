# Install Cognigenesis Harness v1.0

Supported: Windows, macOS, Linux; Python 3.11–3.14.

The repository is private, so the installer must run under a GitHub-authenticated account with repository access. `gh auth setup-git` is used automatically when GitHub CLI is available.

## Recommended install

### Windows PowerShell

```powershell
$script = gh api repos/fernandoiacosta/cognigenesis-harness/contents/scripts/install.ps1 -H "Accept: application/vnd.github.raw+json"; Invoke-Expression ($script -join "`n")
```

The Windows installer:

- force-upgrades the package
- prefers `uv`, then `pipx`, then Python user-site installation
- repairs the user Scripts directory in PATH when needed
- verifies `cogni` and `cogni-acp`
- runs `cogni --version`
- runs first-use `cogni setup`

### macOS / Linux

```bash
gh api repos/fernandoiacosta/cognigenesis-harness/contents/scripts/install.sh -H "Accept: application/vnd.github.raw+json" | sh
```

The POSIX installer performs the same package/command verification and shows the exact user Scripts path when the shell PATH needs it.

## Direct package install

```bash
python -m pip install --user --upgrade --force-reinstall "git+https://github.com/fernandoiacosta/cognigenesis-harness.git"
```

Isolated alternatives:

```bash
uv tool install --force git+https://github.com/fernandoiacosta/cognigenesis-harness.git
pipx install --force git+https://github.com/fernandoiacosta/cognigenesis-harness.git
```

Then run:

```text
cogni setup
cogni doctor
cogni chat
```

## Ollama

Cognigenesis uses Ollama by default. Start Ollama and inspect installed models:

```text
ollama list
```

`cogni setup` auto-selects models in this order when present:

1. `hasi-edge-AG:latest`
2. `llama3.1:8b`
3. first installed Ollama model

If none are installed:

```text
ollama pull llama3.1:8b
cogni setup
```

Environment variables override persistent settings:

```text
COGNI_PROVIDER=ollama
COGNI_OLLAMA_BASE_URL=http://127.0.0.1:11434
COGNI_OLLAMA_MODEL=hasi-edge-AG:latest
COGNI_OLLAMA_TIMEOUT=300
```

## Configuration locations

Cognigenesis uses OS-standard user directories through `platformdirs`. Run:

```text
cogni config --json
```

for resolved settings, and:

```text
cogni doctor
```

for executable paths, Ollama/model status, brand-asset export, and legacy AionUi bridge detection.

## Installed commands

```text
cogni       Human terminal application
cogni-acp   ACP-over-stdio process for AionUi/ACP clients
```

`cogni-acp` is intentionally silent when launched manually because ACP owns stdin/stdout.

## Upgrade

Re-run the same installer. It is designed to force-upgrade an existing Cognigenesis installation rather than leaving an older console-script entry point behind.

## Uninstall

Use the tool that installed it:

```text
uv tool uninstall cognigenesis-harness
pipx uninstall cognigenesis-harness
python -m pip uninstall cognigenesis-harness
```

Persistent user configuration and conversation data are intentionally not deleted automatically.
