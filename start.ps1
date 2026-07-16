[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

if (-not (Test-Path -LiteralPath ".env") -or -not (Test-Path -LiteralPath ".env.production")) {
  throw "PI OS is not configured. Run .\setup.ps1 first."
}

& docker info *> $null
if ($LASTEXITCODE -ne 0) {
  throw "Docker Desktop is not running."
}

$tokenLine = Get-Content -LiteralPath ".env" | Where-Object { $_ -match "^CLOUDFLARE_TUNNEL_TOKEN=" } | Select-Object -Last 1
$token = if ($tokenLine) { $tokenLine -replace "^CLOUDFLARE_TUNNEL_TOKEN=", "" } else { "" }

if ([string]::IsNullOrWhiteSpace($token) -or $token -eq "MISSING") {
  & docker compose --profile tunnel stop cloudflared *> $null
  & docker compose up -d
} else {
  & docker compose --profile tunnel up -d
}

if ($LASTEXITCODE -ne 0) {
  throw "Failed to start PI OS. Run .\status.ps1 for details."
}

Write-Host "PI OS started." -ForegroundColor Green
Write-Host "Local health: http://127.0.0.1:8080/_pi/health"
