#!/usr/bin/env sh
# Cognigenesis Harness installer for macOS, Linux, and Termux.
set -eu

REPO='fernandoiacosta/cognigenesis-harness'
PACKAGE="git+https://github.com/$REPO.git"
IS_TERMUX=0
case "${PREFIX:-}" in */com.termux/files/usr) IS_TERMUX=1 ;; esac
case "$(uname -o 2>/dev/null || true)" in Android) IS_TERMUX=1 ;; esac

COLOR=0
if [ -t 1 ] && [ -z "${NO_COLOR:-}" ] && [ "${TERM:-dumb}" != dumb ]; then COLOR=1; fi
if [ "$COLOR" -eq 1 ]; then
  C=$(printf '\033[38;5;51m'); V=$(printf '\033[38;5;141m'); G=$(printf '\033[38;5;85m'); M=$(printf '\033[38;5;244m'); R=$(printf '\033[0m')
else C=''; V=''; G=''; M=''; R=''; fi

banner() {
  printf '\n%s  ╭──────────────────────────────────────────╮%s\n' "$V" "$R"
  printf '%s  │   ◈  C O G N I G E N E S I S             │%s\n' "$C" "$R"
  printf '%s  │      install the harness                 │%s\n' "$V" "$R"
  printf '%s  ╰──────────────────────────────────────────╯%s\n\n' "$V" "$R"
}
step() { printf '%s  ◆%s  %s\n' "$C" "$R" "$1"; }
done_step() { printf '%s  ✓%s  %s\n' "$G" "$R" "$1"; }
fail() { printf '%s  ✗%s  %s\n' "$V" "$R" "$1" >&2; exit 1; }

banner
if [ "$IS_TERMUX" -eq 1 ]; then
  step 'Android / Termux detected — no sudo required'
fi

if ! command -v git >/dev/null 2>&1; then
  if [ "$IS_TERMUX" -eq 1 ]; then
    step 'Installing Git with Termux pkg'
    pkg install -y git || fail 'Could not install Git. Try: pkg update && pkg install git'
  else fail 'Git is required. Install Git and rerun this command.'; fi
fi

if [ "$IS_TERMUX" -eq 1 ] && ! command -v python3 >/dev/null 2>&1; then
  step 'Installing Python with Termux pkg'
  pkg install -y python || fail 'Could not install Python. Try: pkg update && pkg install python'
fi

if ! command -v python3 >/dev/null 2>&1; then
  fail 'Python 3.11–3.14 is required. Install Python and rerun.'
fi
python3 -c 'import sys; assert (3, 11) <= sys.version_info[:2] < (3, 15)' 2>/dev/null || fail 'Python 3.11–3.14 is required.'
done_step "Python $(python3 -c 'import sys; print(".".join(map(str,sys.version_info[:3])))') and Git ready"

# Keep provider keys and existing configuration untouched on upgrades.
if command -v gh >/dev/null 2>&1; then gh auth setup-git >/dev/null 2>&1 || true; fi
if [ "$IS_TERMUX" -eq 1 ]; then
  # Termux's Python lives inside its own prefix; use its native pip, never sudo.
  METHOD='Termux Python'
  step "Installing with $METHOD"
  python3 -m pip install --upgrade "$PACKAGE" || fail 'Package installation failed; inspect the pip error above.'
  SCRIPTS="$(python3 -c 'import sysconfig; print(sysconfig.get_path("scripts"))')"
elif command -v uv >/dev/null 2>&1; then
  METHOD='uv tool'
  step "Installing with $METHOD"
  uv tool install --force "$PACKAGE" || fail 'Package installation failed; inspect the uv error above.'
  SCRIPTS=''
elif command -v pipx >/dev/null 2>&1; then
  METHOD='pipx'
  step "Installing with $METHOD"
  pipx install --force "$PACKAGE" || fail 'Package installation failed; inspect the pipx error above.'
  SCRIPTS=''
else
  METHOD='Python user site'
  step "Installing with $METHOD"
  python3 -m pip install --user --upgrade "$PACKAGE" || fail 'Package installation failed; inspect the pip error above.'
  SCRIPTS="$(python3 -c 'import sysconfig; print(sysconfig.get_path("scripts", scheme="posix_user"))')"
fi

if [ -n "$SCRIPTS" ]; then
  case ":$PATH:" in *":$SCRIPTS:"*) ;; *) PATH="$SCRIPTS:$PATH"; export PATH ;; esac
fi
command -v cogni >/dev/null 2>&1 || fail 'Installed, but cogni is not on PATH. Open a new terminal or add the Python scripts directory.'
command -v cogni-acp >/dev/null 2>&1 || fail 'Installed, but cogni-acp is not on PATH. Open a new terminal or add the Python scripts directory.'
done_step "Harness installed via $METHOD"

printf '\n%s  ◈ READY%s  ' "$G" "$R"
cogni --version
printf '%s  ───────────────────────────────────────────%s\n' "$M" "$R"
printf '  Connect a model:  cogni login ollama --base-url http://YOUR_HOST:11434\n'
printf '  Or use a cloud:   cogni login openai\n'
printf '  Start:            cogni chat\n'
if [ -n "$SCRIPTS" ]; then
  printf '\n  If cogni is missing in your next shell, add this to your shell profile:\n'
  printf '  export PATH="%s:$PATH"\n' "$SCRIPTS"
fi
printf '\n'
