$ErrorActionPreference = 'Stop'
$Repo = 'fernandoiacosta/cognigenesis-harness'
$Package = "git+https://github.com/$Repo.git"

Write-Host 'Cognigenesis Harness installer'
Write-Host '==============================='

function Has-Command($Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

if (Has-Command 'gh') {
    & gh auth setup-git 2>$null
}

$InstalledWith = $null
if (Has-Command 'uv') {
    & uv tool install --force $Package
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    $InstalledWith = 'uv'
} elseif (Has-Command 'pipx') {
    & pipx install --force $Package
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    $InstalledWith = 'pipx'
} elseif (Has-Command 'py') {
    & py -m pip install --user --upgrade --force-reinstall $Package
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    $Scripts = (& py -c "import sysconfig; print(sysconfig.get_path('scripts', scheme='nt_user'))").Trim()
    $InstalledWith = 'pip'
} elseif (Has-Command 'python') {
    & python -m pip install --user --upgrade --force-reinstall $Package
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    $Scripts = (& python -c "import sysconfig; print(sysconfig.get_path('scripts', scheme='nt_user'))").Trim()
    $InstalledWith = 'pip'
} else {
    throw 'Python 3.11+ is required. Install Python, uv, or pipx and rerun.'
}

if ($InstalledWith -eq 'pip' -and $Scripts) {
    $CurrentUserPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    $Parts = @($CurrentUserPath -split ';' | Where-Object { $_ })
    if ($Parts -notcontains $Scripts) {
        $NewUserPath = (($Parts + $Scripts) -join ';')
        [Environment]::SetEnvironmentVariable('Path', $NewUserPath, 'User')
        Write-Host "Added to user PATH: $Scripts"
    }
    if (($env:Path -split ';') -notcontains $Scripts) {
        $env:Path = "$Scripts;$env:Path"
    }
}

$Cogni = Get-Command cogni -ErrorAction SilentlyContinue
$Acp = Get-Command cogni-acp -ErrorAction SilentlyContinue
if (-not $Cogni) { throw 'Installation completed but cogni is not available on PATH.' }
if (-not $Acp) { throw 'Installation completed but cogni-acp is not available on PATH.' }

Write-Host ''
& cogni --version
& cogni setup
$SetupExit = $LASTEXITCODE

Write-Host ''
Write-Host 'Installed successfully.'
Write-Host 'Start Cognigenesis with: cogni chat'
Write-Host 'AionUi configuration:     cogni aionui'
Write-Host 'Health check:             cogni doctor'

if ($SetupExit -ne 0) {
    Write-Warning 'Cognigenesis installed correctly, but setup found a local dependency that needs attention. Run: cogni doctor'
}
