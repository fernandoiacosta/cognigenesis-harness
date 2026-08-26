#!/usr/bin/env sh
set -eu

REPO="fernandoiacosta/cognigenesis-harness"
PACKAGE="git+https://github.com/${REPO}.git"

echo "Cognigenesis Harness installer"
echo "==============================="

if command -v gh >/dev/null 2>&1; then
  gh auth setup-git >/dev/null 2>&1 || true
fi

if command -v uv >/dev/null 2>&1; then
  uv tool install --force "$PACKAGE"
elif command -v pipx >/dev/null 2>&1; then
  pipx install --force "$PACKAGE"
elif command -v python3 >/dev/null 2>&1; then
  python3 -m pip install --user --upgrade --force-reinstall "$PACKAGE"
  SCRIPTS="$(python3 -c 'import sysconfig; print(sysconfig.get_path("scripts", scheme="posix_user"))')"
  case ":$PATH:" in
    *":$SCRIPTS:"*) ;;
    *)
      echo ""
      echo "Python installed Cognigenesis into: $SCRIPTS"
      echo "Add this directory to PATH if cogni is not found:"
      echo "  export PATH=\"$SCRIPTS:\$PATH\""
      export PATH="$SCRIPTS:$PATH"
      ;;
  esac
else
  echo "Python 3.11+ is required. Install Python, uv, or pipx and rerun." >&2
  exit 1
fi

if ! command -v cogni >/dev/null 2>&1; then
  echo "Installation completed, but cogni is not on PATH in this shell." >&2
  exit 2
fi
if ! command -v cogni-acp >/dev/null 2>&1; then
  echo "Installation completed, but cogni-acp is not on PATH in this shell." >&2
  exit 2
fi

echo ""
cogni --version
cogni setup || true

echo ""
echo "Installed successfully."
echo "Start Cognigenesis with: cogni chat"
echo "AionUi configuration:     cogni aionui"
echo "Health check:             cogni doctor"
