[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

& docker compose --profile tunnel down
if ($LASTEXITCODE -ne 0) {
  throw "Failed to stop PI OS cleanly."
}

Write-Host "PI OS stopped. Data remains under .\data." -ForegroundColor Green
