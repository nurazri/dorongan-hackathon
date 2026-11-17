param([int]$Port = 8765, [string]$PythonPath = '')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not $PythonPath) {
    $localPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    $bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    if (Test-Path -LiteralPath $localPython) { $PythonPath = $localPython }
    elseif (Test-Path -LiteralPath $bundledPython) { $PythonPath = $bundledPython }
    else { $PythonPath = 'python' }
}
if (-not (Test-Path -LiteralPath '.local\summary.json')) { throw 'Run Rebuild-Lab.ps1 first.' }
if (-not (Test-Path -LiteralPath 'ui\dist\interface\browser\index.html')) { throw 'Build the interface first: cd ui; npm ci; npm run build' }
Write-Host "Open http://127.0.0.1:$Port in your browser. Press Ctrl+C to stop."
& $PythonPath -u lab/server.py --port $Port
if ($LASTEXITCODE -ne 0) { throw "Server exited with code $LASTEXITCODE" }
