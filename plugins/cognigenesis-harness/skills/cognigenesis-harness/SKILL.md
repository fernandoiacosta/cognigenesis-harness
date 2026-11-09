---
name: cognigenesis-harness
description: Operate the installed Cognigenesis Harness for diagnostics, team runs, or ACP integration.
---

# Cognigenesis Harness

For a runtime request, check `cogni --help` and `cogni doctor` in the requested environment. If absent, explain how to install the runtime with `python -m pip install git+https://github.com/fernandoiacosta/cognigenesis-harness.git` in a virtual environment. Use `cogni setup` interactively for provider configuration. For an authorized team run, inspect `cogni team --help` and run the selected pattern with the user's mission as one argument. For ACP configuration use `cogni aionui`; the stdio entry point is `cogni-acp`. Return the actual output or failure and distinguish runtime diagnostics from model results. Keep credentials out of chat.

Source: https://github.com/fernandoiacosta/cognigenesis-harness
