[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
& (Join-Path $PSScriptRoot "http-stop.ps1")
$marker = Join-Path $PSScriptRoot "runtime\http-enabled"
Remove-Item -LiteralPath $marker -Force -ErrorAction SilentlyContinue
Write-Host "Remote MCP autostart disabled. Existing OAuth grants remain stored for re-enable." -ForegroundColor Yellow
