$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$pythonPath = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno virtual.' }
    & $pythonPath -m pip install -r requirements-lock.txt
    if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las dependencias.' }
    & $pythonPath -m pip install --no-deps --no-build-isolation -e .
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo instalar StatControl.' }
}
Write-Host 'StatControl Pro: http://127.0.0.1:8050'
& $pythonPath app.py
