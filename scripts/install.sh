#!/usr/bin/env sh
set -eu

REPO="fernandoiacosta/cognigenesis-harness"

if command -v uv >/dev/null 2>&1; then
  exec uv tool install "git+https://github.com/${REPO}.git"
fi

if command -v pipx >/dev/null 2>&1; then
  exec pipx install "git+https://github.com/${REPO}.git"
fi

if command -v python3 >/dev/null 2>&1; then
  python3 -m pip install --user "git+https://github.com/${REPO}.git"
  printf '\nInstalled. Ensure your user Python bin directory is on PATH, then run: cogni --help\n'
  exit 0
fi

printf 'Python 3.11+ is required. Install Python or uv, then rerun this installer.\n' >&2
exit 1
