$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
# Prefer the user's existing Anaconda environment when available.
$taskPython = if (Test-Path -LiteralPath 'E:\anaconda\python.exe') { 'E:\anaconda\python.exe' } else { 'python' }
$env:LOKY_MAX_CPU_COUNT = '2'
foreach ($script in @('download_data.py','verify_models.py','experiment.py','make_figures.py','audit_results.py')) {
    & $taskPython (Join-Path 'src' $script)
    if ($LASTEXITCODE -ne 0) { throw "Failed: $script" }
}
Write-Output 'Complete: results and figures are updated. See README.md for report rebuilding.'
