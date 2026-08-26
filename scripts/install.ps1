$ErrorActionPreference = 'Stop'
$Repo = 'fernandoiacosta/cognigenesis-harness'
$Package = "git+https://github.com/$Repo.git"

function Has-Command($Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

# Private-repository installs need authenticated Git access. If GitHub CLI is
# available, configure Git to reuse its authenticated credentials.
if (Has-Command 'gh') {
    & gh auth setup-git 2>$null
}

if (Has-Command 'uv') {
    & uv tool install --force $Package
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host 'Installed/updated: cogni, cogni-acp'
    exit 0
}

if (Has-Command 'pipx') {
    & pipx install --force $Package
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host 'Installed/updated: cogni, cogni-acp'
    exit 0
}

if (Has-Command 'py') {
    & py -m pip install --user --upgrade $Package
    Write-Host 'Installed/updated. Ensure your Python Scripts directory is on PATH.'
    Write-Host 'Commands: cogni, cogni-acp'
    exit $LASTEXITCODE
}

if (Has-Command 'python') {
    & python -m pip install --user --upgrade $Package
    Write-Host 'Installed/updated. Ensure your Python Scripts directory is on PATH.'
    Write-Host 'Commands: cogni, cogni-acp'
    exit $LASTEXITCODE
}

throw 'Python 3.11+ is required. Install Python or uv, then rerun this installer.'
