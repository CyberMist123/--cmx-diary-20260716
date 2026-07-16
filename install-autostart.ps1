[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot
$taskName = "PI-OS-Autostart"

function Test-Administrator {
  $identity = [System.Security.Principal.WindowsIdentity]::GetCurrent()
  $principal = New-Object System.Security.Principal.WindowsPrincipal($identity)
  return $principal.IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Administrator)) {
  $arguments = "-NoLogo -NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
  $process = Start-Process -FilePath "powershell.exe" -ArgumentList $arguments -Verb RunAs -Wait -PassThru
  exit $process.ExitCode
}

if (-not (Test-Path -LiteralPath ".pi-os-initialized")) {
  throw "PI OS is not initialized. Run setup.ps1 first."
}

$runner = Join-Path $PSScriptRoot "autostart-run.ps1"
if (-not (Test-Path -LiteralPath $runner)) {
  throw "Missing autostart-run.ps1."
}

$userId = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$actionArguments = "-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$runner`""
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $actionArguments -WorkingDirectory $PSScriptRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $userId
$principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -StartWhenAvailable `
  -RestartCount 3 `
  -RestartInterval (New-TimeSpan -Minutes 1) `
  -ExecutionTimeLimit (New-TimeSpan -Minutes 15) `
  -MultipleInstances IgnoreNew

Register-ScheduledTask `
  -TaskName $taskName `
  -Action $action `
  -Trigger $trigger `
  -Principal $principal `
  -Settings $settings `
  -Description "Start Docker Desktop if needed, then restore PI OS after Windows logon." `
  -Force | Out-Null

Start-ScheduledTask -TaskName $taskName

Write-Host "PI OS autostart installed." -ForegroundColor Green
Write-Host "Task: $taskName"
Write-Host "Behavior: starts after this Windows user logs in; Docker Desktop is launched if needed."
Write-Host "Log: $PSScriptRoot\logs\autostart.log"
