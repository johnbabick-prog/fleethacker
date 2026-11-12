$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "Fleet Tech"

function Write-Ok($msg) {
    Write-Host "  [OK] $msg" -ForegroundColor Green
}

function Write-Fail($msg) {
    Write-Host "  [FAIL] $msg" -ForegroundColor Red
}

function Find-DockerDesktop {
    $pf86 = [Environment]::GetFolderPath("ProgramFilesX86")
    $candidates = @(
        (Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe")
        (Join-Path $env:LocalAppData "Docker\Docker Desktop.exe")
    )
    if ($pf86) { $candidates += (Join-Path $pf86 "Docker\Docker\Docker Desktop.exe") }
    foreach ($p in $candidates) {
        if (Test-Path -LiteralPath $p) { return $p }
    }
    try {
        $reg = Get-ItemProperty "HKLM:\SOFTWARE\Docker Inc.\Docker\1.0" -ErrorAction SilentlyContinue
        if ($reg -and $reg.AppPath) {
            $p = Join-Path $reg.AppPath "Docker Desktop.exe"
            if (Test-Path -LiteralPath $p) { return $p }
        }
    } catch {}
    return $null
}

function Wait-ForDocker($timeoutSeconds) {
    $elapsed = 0
    while ($elapsed -lt $timeoutSeconds) {
        try {
            $null = & docker info 2>&1
            if ($LASTEXITCODE -eq 0) { return $true }
        } catch {}
        Start-Sleep -Seconds 5
        $elapsed += 5
        Write-Host "  Waiting for Docker engine... ($elapsed/$timeoutSeconds sec)"
    }
    return $false
}

# ==============================================================
Write-Host ""
Write-Host "  ============================================"
Write-Host "     Fleet Tech - Starting..."
Write-Host "  ============================================"
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$tarPath   = Join-Path $scriptDir "fleethacker-image.tar"

# ---- Check Docker is installed ----
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCmd) {
    Write-Fail "Docker is not installed. Please double-click setup.bat first."
    Read-Host "  Press Enter to exit"
    exit 1
}

# ---- Start Docker if not running ----
$dockerRunning = $false
try {
    $null = & docker info 2>&1
    if ($LASTEXITCODE -eq 0) { $dockerRunning = $true }
} catch {}

if (-not $dockerRunning) {
    Write-Host "  Starting Docker Desktop..."
    $dockerExe = Find-DockerDesktop
    if (-not $dockerExe) {
        Write-Fail "Cannot find Docker Desktop. Please open it manually and try again."
        Read-Host "  Press Enter to exit"
        exit 1
    }
    Start-Process -FilePath $dockerExe

    if (-not (Wait-ForDocker 180)) {
        Write-Fail "Docker did not start in time."
        Write-Host "  Please open Docker Desktop manually, wait for it to say 'running',"
        Write-Host "  then try again."
        Read-Host "  Press Enter to exit"
        exit 1
    }
}
Write-Ok "Docker is running."

# ---- Check image exists; auto-load if tar is present ----
$imageExists = $false
try {
    $null = & docker image inspect fleethacker:latest 2>&1
    if ($LASTEXITCODE -eq 0) { $imageExists = $true }
} catch {}

if (-not $imageExists) {
    if (Test-Path -LiteralPath $tarPath) {
        Write-Host "  Image not loaded yet. Loading from tar..."
        $proc = Start-Process -FilePath "docker" -ArgumentList "load","-i","`"$tarPath`"" -NoNewWindow -Wait -PassThru
        if ($proc.ExitCode -ne 0) {
            Write-Fail "Failed to load image."
            Read-Host "  Press Enter to exit"
            exit 1
        }
    } else {
        Write-Fail "Fleet Tech image not found. Please run setup.bat first."
        Read-Host "  Press Enter to exit"
        exit 1
    }
}

# ---- Stop any previous instance ----
& docker rm -f fleethacker 2>&1 | Out-Null

# ---- Run container ----
Write-Host "  Starting Fleet Tech..."
$dockerArgs = @("run", "-d", "--name", "fleethacker", "--restart", "unless-stopped", "-p", "8765:8765",
    "-e", "HATCH_LLM_URL=https://api.edgerunnerai.com/chat/completions",
    "-e", "HATCH_MODEL=EdgeRunner-Light")

# Read API key from env var or from key file next to this script
$apiKey = $env:EDGERUNNER_API_KEY
$keyFile = Join-Path $scriptDir "api_key.txt"
if (-not $apiKey -and (Test-Path -LiteralPath $keyFile)) {
    $apiKey = (Get-Content -LiteralPath $keyFile -Raw).Trim()
}
if ($apiKey) {
    $dockerArgs += @("-e", "HATCH_API_KEY=$apiKey")
} else {
    Write-Host "  WARNING: No API key found. AI chat will not work." -ForegroundColor Yellow
    Write-Host "  Set EDGERUNNER_API_KEY env var or put key in api_key.txt" -ForegroundColor Yellow
}

$dockerArgs += "fleethacker:latest"
& docker @dockerArgs 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    # Diagnose: check if port is in use
    try {
        $portCheck = & netstat -ano 2>&1 | Select-String ":8765\s"
        if ($portCheck) {
            Write-Fail "Port 8765 is already in use by another program."
            Write-Host "  Close whatever is using that port and try again."
        } else {
            Write-Fail "Could not start the container."
            Write-Host "  Try opening Docker Desktop and checking for errors."
        }
    } catch {
        Write-Fail "Could not start the container."
    }
    Read-Host "  Press Enter to exit"
    exit 1
}

# ---- Wait for healthy ----
Write-Host "  Waiting for app to be ready..."
$healthy = $false
for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Seconds 2
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8765/healthz" -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -eq 200) {
            $healthy = $true
            break
        }
    } catch {}
}

if (-not $healthy) {
    Write-Host ""
    Write-Host "  App is taking longer than expected." -ForegroundColor Yellow
    try {
        $status = & docker ps -a --filter "name=fleethacker" --format "{{.Status}}" 2>&1
        Write-Host "  Container status: $status"
    } catch {}
    Write-Host ""
    Write-Host "  To see the error, open PowerShell and run:"
    Write-Host "    docker logs fleethacker"
    Write-Host ""
    Read-Host "  Press Enter to exit"
    exit 1
}

# ---- Open browser ----
Write-Host ""
Write-Host "  ============================================" -ForegroundColor Green
Write-Host "     Fleet Tech is running!" -ForegroundColor Green
Write-Host "" -ForegroundColor Green
Write-Host "     Opening browser to http://localhost:8765" -ForegroundColor Green
Write-Host "" -ForegroundColor Green
Write-Host "     Press any key to stop Fleet Tech." -ForegroundColor Green
Write-Host "  ============================================" -ForegroundColor Green
Write-Host ""

# Use cmd /c start to reliably open default browser on all Windows versions
# Empty title ("") is required — without it, start treats the URL as a window title
& cmd /c start "" "http://localhost:8765"

# ---- Wait for user to close ----
Write-Host "  Press any key to stop Fleet Tech..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Write-Host "  Stopping Fleet Tech..."
& docker stop fleethacker 2>&1 | Out-Null
& docker rm fleethacker 2>&1 | Out-Null
Write-Host "  Done."
Start-Sleep -Seconds 2
