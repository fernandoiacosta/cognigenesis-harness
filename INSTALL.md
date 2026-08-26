# Installation

Cognigenesis Harness supports macOS, Linux, and Windows with Python 3.11–3.14.

Because the repository is private, installation requires authenticated GitHub access.

## Direct pip install / upgrade

```bash
python -m pip install --user --upgrade --force-reinstall "git+https://github.com/fernandoiacosta/cognigenesis-harness.git"
```

Alternative isolated installs:

```bash
uv tool install --force git+https://github.com/fernandoiacosta/cognigenesis-harness.git
```

or:

```bash
pipx install --force git+https://github.com/fernandoiacosta/cognigenesis-harness.git
```

The package installs:

```text
cogni      Human-facing Cognigenesis CLI
cogni-acp  Python-native ACP-over-stdio agent for AionUi
```

## Ollama

Install/start Ollama separately, then verify:

```bash
ollama list
```

Pull a model if needed:

```bash
ollama pull llama3.1:8b
```

Configuration:

```text
COGNI_PROVIDER=ollama
COGNI_OLLAMA_BASE_URL=http://127.0.0.1:11434
COGNI_OLLAMA_MODEL=llama3.1:8b
COGNI_OLLAMA_TIMEOUT=120
```

The model can be any name returned by `ollama list`, including custom models such as `hasi-edge-AG:latest`.

## Verify terminal execution

```bash
cogni --version
cogni --provider ollama --model llama3.1:8b "Say OK"
```

## Verify ACP executable

macOS/Linux:

```bash
which cogni-acp
```

Windows:

```powershell
where.exe cogni-acp
```

`cogni-acp` is not interactive. It waits for ACP JSON-RPC on stdio and is intended to be spawned by AionUi or another ACP client.

See [`AIONUI.md`](AIONUI.md).
