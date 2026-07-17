[CmdletBinding()]
param(
  [switch]$SkipMedia
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

if (-not (Test-Path -LiteralPath ".env") -or -not (Test-Path -LiteralPath ".env.production")) {
  throw "PI OS is not configured."
}

& docker info *> $null
if ($LASTEXITCODE -ne 0) {
  throw "Docker Desktop is not running."
}

$runningServices = @(& docker compose --profile tunnel ps --status running --services 2>$null)
$appWasRunning = ($runningServices -contains "web") -or
                 ($runningServices -contains "streaming") -or
                 ($runningServices -contains "sidekiq") -or
                 ($runningServices -contains "nginx")
$tunnelWasRunning = $runningServices -contains "cloudflared"

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$snapshotName = "pi-os-$stamp"
$snapshotPath = Join-Path $PSScriptRoot "backups\$snapshotName"
New-Item -ItemType Directory -Path $snapshotPath -Force | Out-Null

$backupSucceeded = $false
try {
  if ($appWasRunning) {
    Write-Host "Pausing public/app services for a consistent snapshot..." -ForegroundColor Cyan
    & docker compose --profile tunnel stop cloudflared nginx web streaming sidekiq
    if ($LASTEXITCODE -ne 0) { throw "Could not pause application services." }
  }

  Write-Host "Ensuring database is running..." -ForegroundColor Cyan
  & docker compose up -d db redis
  if ($LASTEXITCODE -ne 0) { throw "Could not start database services." }

  $dbReady = $false
  for ($attempt = 1; $attempt -le 30; $attempt++) {
    & docker compose exec -T db pg_isready -U mastodon -d mastodon_production *> $null
    if ($LASTEXITCODE -eq 0) {
      $dbReady = $true
      break
    }
    Start-Sleep -Seconds 2
  }
  if (-not $dbReady) { throw "PostgreSQL did not become ready within 60 seconds." }

  Write-Host "Dumping PostgreSQL..." -ForegroundColor Cyan
  & docker compose exec -T db pg_dump -U mastodon -d mastodon_production -Fc -f "/backups/$snapshotName/database.dump"
  if ($LASTEXITCODE -ne 0) { throw "PostgreSQL backup failed." }

  Write-Host "Validating PostgreSQL dump..." -ForegroundColor Cyan
  & docker compose exec -T db pg_restore --list "/backups/$snapshotName/database.dump" *> $null
  if ($LASTEXITCODE -ne 0) { throw "PostgreSQL dump was created but could not be read back." }

  Copy-Item -LiteralPath ".env" -Destination (Join-Path $snapshotPath ".env")
  Copy-Item -LiteralPath ".env.production" -Destination (Join-Path $snapshotPath ".env.production")
  Copy-Item -LiteralPath "compose.yml" -Destination (Join-Path $snapshotPath "compose.yml")

  # Docker Compose writes transient container lifecycle messages to stderr even when
  # the command succeeds. Suppress those messages so Windows PowerShell 5.1 does not
  # convert them into a terminating NativeCommandError under ErrorActionPreference=Stop.
  $versionOutput = @(& docker compose run --rm --no-deps web bin/tootctl --version 2>$null)
  $versionExitCode = $LASTEXITCODE
  if ($versionExitCode -eq 0 -and $versionOutput.Count -gt 0) {
    $versionOutput | Set-Content -LiteralPath (Join-Path $snapshotPath "mastodon-version.txt") -Encoding UTF8
  } else {
    Write-Warning "Could not record the Mastodon version; continuing because the core backup is valid."
  }

  @(
    "created_at=$([DateTime]::UtcNow.ToString('o'))",
    "snapshot=$snapshotName",
    "contains_plaintext_secrets=true",
    "application_paused=$appWasRunning"
  ) | Set-Content -LiteralPath (Join-Path $snapshotPath "manifest.txt") -Encoding UTF8

  if (-not $SkipMedia) {
    if (Test-Path -LiteralPath ".\data\media") {
      $tar = Get-Command tar.exe -ErrorAction SilentlyContinue
      if ($tar) {
        $mediaArchive = Join-Path $snapshotPath "media.tar.gz"
        Write-Host "Archiving uploaded media..." -ForegroundColor Cyan
        & $tar.Source -czf $mediaArchive -C (Join-Path $PSScriptRoot "data\media") .
        if ($LASTEXITCODE -ne 0) { throw "Media archive failed." }

        Write-Host "Validating media archive..." -ForegroundColor Cyan
        & $tar.Source -tzf $mediaArchive *> $null
        if ($LASTEXITCODE -ne 0) { throw "Media archive was created but could not be read back." }
      } else {
        throw "tar.exe is unavailable. Re-run with -SkipMedia only if a database-only backup is intentional."
      }
    }
  }

  $backupSucceeded = $true
} finally {
  if ($appWasRunning) {
    Write-Host "Restoring previous running state..." -ForegroundColor Cyan
    if ($tunnelWasRunning) {
      & docker compose --profile tunnel up -d
    } else {
      & docker compose up -d
    }
    if ($LASTEXITCODE -ne 0) {
      Write-Warning "Backup finished, but the previous application state could not be restored automatically. Run .\start.ps1."
    }
  }

  if (-not $backupSucceeded -and (Test-Path -LiteralPath $snapshotPath)) {
    Remove-Item -LiteralPath $snapshotPath -Recurse -Force -ErrorAction SilentlyContinue
  }
}

if ($backupSucceeded) {
  Write-Host "Backup completed: $snapshotPath" -ForegroundColor Green
  Write-Warning "This snapshot contains plaintext secrets and private data. Move a copy to an encrypted offline location."
}
