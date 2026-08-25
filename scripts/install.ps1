$ErrorActionPreference = 'Stop'
$Repo = 'fernandoiacosta/cognigenesis-harness'
$Package = "git+https://github.com/$Repo.git"

function Has-Command($Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

if (Has-Command 'uv') {
    & uv tool install $Package
    exit $LASTEXITCODE
}

if (Has-Command 'pipx') {
    & pipx install $Package
    exit $LASTEXITCODE
}

if (Has-Command 'py') {
    & py -m pip install --user $Package
    Write-Host 'Installed. Ensure your Python Scripts directory is on PATH, then run: cogni --help'
    exit $LASTEXITCODE
}

if (Has-Command 'python') {
    & python -m pip install --user $Package
    Write-Host 'Installed. Ensure your Python Scripts directory is on PATH, then run: cogni --help'
    exit $LASTEXITCODE
}

throw 'Python 3.11+ is required. Install Python or uv, then rerun this installer.'
