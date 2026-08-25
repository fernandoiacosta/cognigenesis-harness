#!/usr/bin/env sh
set -eu

REPO="fernandoiacosta/cognigenesis-harness"
PACKAGE="git+https://github.com/${REPO}.git"

# Private-repository installs need authenticated Git access. If GitHub CLI is
# available, configure Git to reuse its authenticated credentials.
if command -v gh >/dev/null 2>&1; then
  gh auth setup-git >/dev/null 2>&1 || true
fi

if command -v uv >/dev/null 2>&1; then
  uv tool install "$PACKAGE"
  printf '\nInstalled: cogni\n'
  exit 0
fi

if command -v pipx >/dev/null 2>&1; then
  pipx install "$PACKAGE"
  printf '\nInstalled: cogni\n'
  exit 0
fi

if command -v python3 >/dev/null 2>&1; then
  python3 -m pip install --user "$PACKAGE"
  printf '\nInstalled. Ensure your user Python bin directory is on PATH, then run: cogni --help\n'
  exit 0
fi

printf 'Python 3.11+ is required. Install Python or uv, then rerun this installer.\n' >&2
exit 1
