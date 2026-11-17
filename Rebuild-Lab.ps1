param([string]$DataSource = (Join-Path $env:USERPROFILE 'Downloads\hackathon-resources'), [string]$PythonPath = '')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not $PythonPath) {
    $localPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    $bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    if (Test-Path -LiteralPath $localPython) { $PythonPath = $localPython }
    elseif (Test-Path -LiteralPath $bundledPython) { $PythonPath = $bundledPython }
    else { $PythonPath = 'python' }
}
function Invoke-PythonStep([string[]]$StepArgs) {
    & $PythonPath @StepArgs
    if ($LASTEXITCODE -ne 0) { throw "Python step failed: $StepArgs" }
}
Invoke-PythonStep -StepArgs @('lab/setup_data.py', $DataSource)
Invoke-PythonStep -StepArgs @('starter/baseline.py')
Invoke-PythonStep -StepArgs @('lab/build.py')
Invoke-PythonStep -StepArgs @('evaluation/validate_submission.py', 'evaluation/results/experimental_temporal.csv')
Invoke-PythonStep -StepArgs @('evaluation/validate_submission.py', 'evaluation/results/experimental_control_v2.csv')
Invoke-PythonStep -StepArgs @('evaluation/validate_submission.py', 'evaluation/results/experimental_control_v5.csv')
Invoke-PythonStep -StepArgs @('evaluation/validate_submission.py', 'evaluation/results/baseline_smooth50.csv')
Write-Host 'Data pipeline rebuilt. Run Start-Lab.ps1 to inspect predictions.'
