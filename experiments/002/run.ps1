param(
    [Parameter(Mandatory=$true)]
    [string]$PrimeFile
)

$ErrorActionPreference = "Stop"

$models = @(ollama list | Select-Object -Skip 1 | ForEach-Object {
    $name = ($_ -split "\s+")[0]
    if ($name) { $name }
})

if ($models.Count -eq 0) {
    throw "No Ollama models are installed."
}

$preferred = @("hasi-edge-AG:latest", "llama3.1:8b")
$model = $preferred | Where-Object { $_ -in $models } | Select-Object -First 1
if (-not $model) { $model = $models[0] }

Write-Host "Experiment 002 model: $model"
python "$PSScriptRoot\run.py" --model $model --prime-file $PrimeFile --runs 3
