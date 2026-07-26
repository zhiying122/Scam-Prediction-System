#Requires -Version 5.1
<#
.SYNOPSIS
  Start local infra + API Gateway + Streamlit Dashboard.

.DESCRIPTION
  Order: Docker daemon -> docker compose -> uvicorn :8001 -> streamlit :8502
  Optional: if dev_shims/ exists, prepends it to PYTHONPATH (Python 3.14 uuid_utils workaround).

.EXAMPLE
  .\scripts\start-dev.ps1
  .\scripts\start-dev.ps1 -SkipDocker
#>
[CmdletBinding()]
param(
    [switch]$SkipDocker,
    [int]$ApiPort = 8001,
    [int]$DashboardPort = 8502,
    [int]$DockerWaitSeconds = 90
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$RuntimeDir = Join-Path $Root ".dev"
$PidFile = Join-Path $RuntimeDir "pids.json"
$ApiOutLog = Join-Path $RuntimeDir "api.out.log"
$ApiErrLog = Join-Path $RuntimeDir "api.err.log"
$DashOutLog = Join-Path $RuntimeDir "dashboard.out.log"
$DashErrLog = Join-Path $RuntimeDir "dashboard.err.log"
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$ShimDir = Join-Path $Root "dev_shims"

function Write-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host "    OK  $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "    WARN  $msg" -ForegroundColor Yellow }
function Write-Fail($msg) { Write-Host "    FAIL  $msg" -ForegroundColor Red }

function Test-PortListening([int]$Port) {
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    return $null -ne $conn
}

function Wait-HttpOk([string]$Url, [int]$TimeoutSec = 60) {
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        try {
            $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
            if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { return $true }
        } catch {
            Start-Sleep -Seconds 2
        }
    }
    return $false
}

function Ensure-Docker {
    Write-Step "Checking Docker Desktop"
    docker info 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Docker daemon is ready"
        return
    }

    $dockerExe = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $dockerExe) {
        Write-Warn "Docker daemon not ready — starting Docker Desktop..."
        Start-Process $dockerExe | Out-Null
    } else {
        Write-Fail "Docker Desktop not found. Install it or re-run with -SkipDocker."
        exit 1
    }

    $deadline = (Get-Date).AddSeconds($DockerWaitSeconds)
    while ((Get-Date) -lt $deadline) {
        docker info 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Ok "Docker daemon is ready"
            return
        }
        Start-Sleep -Seconds 3
    }
    Write-Fail "Docker daemon did not become ready within ${DockerWaitSeconds}s"
    exit 1
}

# ── Preconditions ────────────────────────────────────────────────────────────
Write-Step "Checking project prerequisites"
if (-not (Test-Path $Python)) {
    Write-Fail "Missing .venv. Run: python -m venv .venv && .\.venv\Scripts\python.exe -m pip install -r requirements.txt"
    exit 1
}
Write-Ok ".venv found"

if (-not (Test-Path (Join-Path $Root ".env"))) {
    Write-Warn ".env not found — copy from .env.example before using LLM / DB features"
} else {
    Write-Ok ".env found"
}

New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null

$api = $null
$dash = $null

# ── Docker infra ──────────────────────────────────────────────────────────────
if (-not $SkipDocker) {
    Ensure-Docker
    Write-Step "Starting docker compose (postgres / redis / qdrant)"
    docker compose up -d
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "docker compose up failed"
        exit 1
    }
    Write-Ok "Containers requested"

    # Postgres / Redis health is enough for most local work; Qdrant healthcheck may be flaky.
    $deadline = (Get-Date).AddSeconds(60)
    $healthyEnough = $false
    do {
        $lines = @(docker compose ps --format json 2>$null)
        try {
            $rows = foreach ($line in $lines) {
                if ($line -and $line.Trim()) { $line | ConvertFrom-Json }
            }
            $pg = $rows | Where-Object { $_.Service -eq "postgres" } | Select-Object -First 1
            $rd = $rows | Where-Object { $_.Service -eq "redis" } | Select-Object -First 1
            $healthyEnough = ($pg.Health -eq "healthy") -and ($rd.Health -eq "healthy")
        } catch {
            $healthyEnough = $false
        }
        if ($healthyEnough) { break }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)

    if ($healthyEnough) {
        Write-Ok "postgres + redis healthy"
    } else {
        Write-Warn "postgres/redis not fully healthy yet — continuing anyway"
    }
} else {
    Write-Warn "Skipping Docker (-SkipDocker)"
}

# ── Environment for child processes ───────────────────────────────────────────
if (Test-Path $ShimDir) {
    $env:PYTHONPATH = $ShimDir
    Write-Ok "Using PYTHONPATH=$ShimDir (uuid_utils shim for Python 3.14)"
} else {
    Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
}

# ── API Gateway ───────────────────────────────────────────────────────────────
Write-Step "Starting API Gateway on :$ApiPort"
if (Test-PortListening $ApiPort) {
    Write-Warn "Port $ApiPort already in use — skipping API start"
} else {
    New-Item -ItemType File -Force -Path $ApiOutLog | Out-Null
    New-Item -ItemType File -Force -Path $ApiErrLog | Out-Null
    $api = Start-Process -FilePath $Python `
        -ArgumentList @("-m", "uvicorn", "app.api_gateway.main:app", "--host", "0.0.0.0", "--port", "$ApiPort") `
        -WorkingDirectory $Root `
        -RedirectStandardOutput $ApiOutLog `
        -RedirectStandardError $ApiErrLog `
        -PassThru `
        -WindowStyle Hidden

    if (-not (Wait-HttpOk "http://localhost:$ApiPort/v1/health" 90)) {
        Write-Fail "API health check failed. See $ApiErrLog"
        exit 1
    }
    Write-Ok "API healthy (PID $($api.Id))"
}

# ── Dashboard ─────────────────────────────────────────────────────────────────
Write-Step "Starting Streamlit Dashboard on :$DashboardPort"
if (Test-PortListening $DashboardPort) {
    Write-Warn "Port $DashboardPort already in use — skipping Dashboard start"
} else {
    New-Item -ItemType File -Force -Path $DashOutLog | Out-Null
    New-Item -ItemType File -Force -Path $DashErrLog | Out-Null
    $dash = Start-Process -FilePath $Python `
        -ArgumentList @("-m", "streamlit", "run", "app/dashboard/streamlit_app.py", "--server.port", "$DashboardPort", "--server.headless", "true") `
        -WorkingDirectory $Root `
        -RedirectStandardOutput $DashOutLog `
        -RedirectStandardError $DashErrLog `
        -PassThru `
        -WindowStyle Hidden

    if (-not (Wait-HttpOk "http://localhost:$DashboardPort" 90)) {
        Write-Fail "Dashboard did not respond. See $DashErrLog"
        exit 1
    }
    Write-Ok "Dashboard ready (PID $($dash.Id))"
}

# Persist PIDs for stop-dev.ps1
$pidInfo = [ordered]@{
    api_port       = $ApiPort
    dashboard_port = $DashboardPort
}
if (Test-Path $PidFile) {
    try {
        $prev = Get-Content $PidFile -Raw | ConvertFrom-Json
        if (-not $api -and $prev.api) { $pidInfo.api = [int]$prev.api }
        if (-not $dash -and $prev.dashboard) { $pidInfo.dashboard = [int]$prev.dashboard }
    } catch { }
}
if ($api) { $pidInfo.api = $api.Id }
if ($dash) { $pidInfo.dashboard = $dash.Id }
($pidInfo | ConvertTo-Json) | Set-Content -Path $PidFile -Encoding UTF8

Write-Host ""
Write-Host "Local stack is up:" -ForegroundColor Green
Write-Host "  Dashboard   http://localhost:$DashboardPort"
Write-Host "  API docs    http://localhost:$ApiPort/docs"
Write-Host "  Health      http://localhost:$ApiPort/v1/health"
Write-Host ""
Write-Host "Stop with:  .\scripts\stop-dev.ps1"
Write-Host "Logs:       .dev\api.*.log  .dev\dashboard.*.log"
