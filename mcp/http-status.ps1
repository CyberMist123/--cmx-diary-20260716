[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$Port = 8766
try {
    $response = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/_cmx/mcp-health" -TimeoutSec 5
    if ($response.StatusCode -ne 200) { throw "HTTP $($response.StatusCode)" }
    Write-Host "CMX profiled remote MCP: OK" -ForegroundColor Green
Write-Host $response.Content
    exit 0
} catch {
    Write-Host "CMX profiled remote MCP: FAIL - $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
