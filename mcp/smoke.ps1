[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$BotId
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

$Root = $PSScriptRoot
$Smoke = Join-Path $Root ".venv\Scripts\cmx-smoke.exe"

if (-not (Test-Path -LiteralPath $Smoke)) {
    throw "CMX MCP smoke command is missing. Run install.ps1 after pulling the latest main branch."
}

Write-Host "Running independent CMX MCP STDIO smoke for: $BotId" -ForegroundColor Cyan
& $Smoke --bot $BotId
if ($LASTEXITCODE -ne 0) {
    throw "CMX MCP smoke failed with exit code $LASTEXITCODE"
}

Write-Host ""
Write-Host "Independent CMX MCP smoke passed." -ForegroundColor Green
