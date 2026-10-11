param([Parameter(Mandatory=$true)][string]$InputDocx,
      [Parameter(Mandatory=$true)][string]$OutputPdf)
$ErrorActionPreference = 'Stop'
$word = $null
$doc = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $word.AutomationSecurity = 3
    $doc = $word.Documents.Open($InputDocx, $false, $true)
    $doc.Repaginate()
    $doc.ExportAsFixedFormat($OutputPdf,17)
    Write-Output ('Rendered pages: ' + $doc.ComputeStatistics(2))
} finally {
    if ($null -ne $doc) { $doc.Close(0) }
    if ($null -ne $word) { $word.Quit() }
}
