[CmdletBinding()]
param(
  [int]$TimeoutSeconds = 360
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

$taskName = "PI-OS-Autostart"
$logPath = Join-Path $PSScriptRoot "logs\autostart.log"
$healthUrl = "http://127.0.0.1:8080/_pi/health"

if (-not (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue)) {
  throw "Scheduled task '$taskName' is not installed. Run .\install-autostart.ps1 first."
}

$startedAt = Get-Date
$lastLogLine = "Starting scheduled task..."
$lastShownLogLine = $null

Start-ScheduledTask -TaskName $taskName

try {
  while ($true) {
    $elapsed = [int]((Get-Date) - $startedAt).TotalSeconds
    $percent = [Math]::Min(99, [Math]::Floor(($elapsed / [Math]::Max(1, $TimeoutSeconds)) * 100))

    if (Test-Path -LiteralPath $logPath) {
      $candidate = Get-Content -LiteralPath $logPath -Tail 1 -ErrorAction SilentlyContinue
      if (-not [string]::IsNullOrWhiteSpace($candidate)) {
        $lastLogLine = $candidate
        if ($candidate -ne $lastShownLogLine) {
          Write-Host $candidate
          $lastShownLogLine = $candidate
        }
      }
    }

    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    $taskState = if ($task) { [string]$task.State } else { "Unknown" }

    Write-Progress `
      -Activity "PI OS autostart validation" `
      -Status ("{0}s / {1}s | Task: {2} | {3}" -f $elapsed, $TimeoutSeconds, $taskState, $lastLogLine) `
      -PercentComplete $percent

    try {
      $response = Invoke-WebRequest -UseBasicParsing -Uri $healthUrl -TimeoutSec 3
      if ($response.StatusCode -eq 200) {
        Write-Progress -Activity "PI OS autostart validation" -Completed
        Write-Host "PI OS autostart is healthy." -ForegroundColor Green
        Write-Host "Health: $healthUrl"
        exit 0
      }
    } catch {
      # Keep waiting. The latest autostart.log line remains visible in the progress status.
    }

    if ($elapsed -ge $TimeoutSeconds) {
      Write-Progress -Activity "PI OS autostart validation" -Completed
      Write-Host "Autostart did not become healthy within $TimeoutSeconds seconds." -ForegroundColor Red
      if (Test-Path -LiteralPath $logPath) {
        Write-Host "Latest autostart log:" -ForegroundColor Yellow
        Get-Content -LiteralPath $logPath -Tail 30
      }
      exit 1
    }

    Start-Sleep -Seconds 2
  }
} finally {
  Write-Progress -Activity "PI OS autostart validation" -Completed
}
