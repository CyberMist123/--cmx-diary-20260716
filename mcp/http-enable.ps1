[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$marker = Join-Path $PSScriptRoot "runtime\http-enabled"
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $marker) | Out-Null
[System.IO.File]::WriteAllText($marker, "read-only`r`n")
& (Join-Path $PSScriptRoot "http-start.ps1")
Write-Host "Remote MCP will now start with PI OS." -ForegroundColor Green
