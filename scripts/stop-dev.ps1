#Requires -Version 5.1
<#
.SYNOPSIS
  Stop API Gateway + Streamlit started by start-dev.ps1.

.PARAMETER AlsoDocker
  Also run `docker compose stop` (containers kept; data volumes preserved).

.EXAMPLE
  .\scripts\stop-dev.ps1
  .\scripts\stop-dev.ps1 -AlsoDocker
#>
[CmdletBinding()]
param(
    [switch]$AlsoDocker
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$RuntimeDir = Join-Path $Root ".dev"
$PidFile = Join-Path $RuntimeDir "pids.json"

function Write-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host "    OK  $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "    WARN  $msg" -ForegroundColor Yellow }

function Stop-ByPort([int]$Port, [string]$Label) {
    $pids = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique)
    foreach ($procId in $pids) {
        try {
            Stop-Process -Id $procId -Force -ErrorAction Stop
            Write-Ok "Stopped $Label on :$Port (PID $procId)"
        } catch {
            Write-Warn "Could not stop PID $procId on :$Port — $($_.Exception.Message)"
        }
    }
    if ($pids.Count -eq 0) {
        Write-Warn "Nothing listening on :$Port ($Label)"
    }
}

function Stop-ByPid([int]$ProcId, [string]$Label) {
    if ($ProcId -le 0) { return }
    $p = Get-Process -Id $ProcId -ErrorAction SilentlyContinue
    if (-not $p) {
        Write-Warn "$Label PID $ProcId already gone"
        return
    }
    try {
        Stop-Process -Id $ProcId -Force -ErrorAction Stop
        Write-Ok "Stopped $Label (PID $ProcId)"
    } catch {
        Write-Warn "Could not stop $Label PID $ProcId — $($_.Exception.Message)"
    }
}

$apiPort = 8001
$dashPort = 8502

Write-Step "Stopping app processes"
if (Test-Path $PidFile) {
    try {
        $info = Get-Content $PidFile -Raw | ConvertFrom-Json
        if ($info.api_port) { $apiPort = [int]$info.api_port }
        if ($info.dashboard_port) { $dashPort = [int]$info.dashboard_port }
        if ($info.api) { Stop-ByPid ([int]$info.api) "API" }
        if ($info.dashboard) { Stop-ByPid ([int]$info.dashboard) "Dashboard" }
    } catch {
        Write-Warn "Could not read $PidFile — falling back to ports"
    }
} else {
    Write-Warn "No .dev\pids.json — stopping by port only"
}

# Always clear listeners (covers orphaned children / restart without pid file)
Stop-ByPort $apiPort "API"
Stop-ByPort $dashPort "Dashboard"

if (Test-Path $PidFile) {
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

if ($AlsoDocker) {
    Write-Step "Stopping docker compose services"
    docker compose stop
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "docker compose stop done (volumes kept)"
    } else {
        Write-Warn "docker compose stop failed — is Docker running?"
    }
}

Write-Host ""
Write-Host "Local app processes stopped." -ForegroundColor Green
if (-not $AlsoDocker) {
    Write-Host "Docker left running. To stop containers too:  .\scripts\stop-dev.ps1 -AlsoDocker"
}
