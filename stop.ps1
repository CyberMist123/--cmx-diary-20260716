[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

& docker compose --profile tunnel down
if ($LASTEXITCODE -ne 0) {
  throw "Failed to stop PI OS cleanly."
}

Write-Host "PI OS stopped. PostgreSQL/Redis named volumes and .\data\media remain intact." -ForegroundColor Green
Write-Warning "Do not run 'docker compose down -v' unless you intentionally want to delete the database volumes."
