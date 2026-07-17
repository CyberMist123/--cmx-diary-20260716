[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$BotId,
    [Parameter(Mandatory = $true)][string]$DisplayName,
    [ValidateSet("reader", "resident", "personal")][string]$Profile = "resident",
    [string]$MediaRoot = "",
    [ValidateSet("residents", "direct", "public_explicit")][string]$DefaultAudience = "residents",
    [switch]$AllowPublic
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

$Root = $PSScriptRoot
$Authorize = Join-Path $Root ".venv\Scripts\cmx-authorize.exe"
if (-not (Test-Path -LiteralPath $Authorize)) {
    throw "CMX browser authorization helper is missing. Pull main and run install.ps1 first."
}
if (-not $MediaRoot) {
    $MediaRoot = Join-Path $Root ("spool\" + $BotId)
}

$arguments = @(
    "--id", $BotId,
    "--display-name", $DisplayName,
    "--profile", $Profile,
    "--media-root", $MediaRoot,
    "--default-audience", $DefaultAudience
)
if ($AllowPublic) {
    $arguments += "--allow-public"
}

Write-Host "Opening CMX in your browser for resident authorization..." -ForegroundColor Cyan
Write-Host "Log in as the AI resident account and click Authorize. No token copy/paste is required." -ForegroundColor DarkGray
Write-Host ""

& $Authorize @arguments
if ($LASTEXITCODE -ne 0) {
    throw "Browser authorization failed with exit code $LASTEXITCODE"
}

Write-Host ""
Write-Host "Resident authorization and MCP setup completed." -ForegroundColor Green
Write-Host "Run smoke.ps1 -BotId $BotId to verify the independent STDIO MCP." -ForegroundColor Cyan
