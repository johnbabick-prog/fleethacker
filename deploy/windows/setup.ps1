$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "Fleet Tech - Setup"

function Write-Step($num, $total, $msg) {
    Write-Host "`n  [$num/$total] $msg" -ForegroundColor Cyan
}

function Write-Ok($msg) {
    Write-Host "  [OK] $msg" -ForegroundColor Green
}

function Write-Fail($msg) {
    Write-Host "  [FAIL] $msg" -ForegroundColor Red
}

function Test-Admin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]$identity
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
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
Write-Host "     Fleet Tech - One-Time Setup"
Write-Host "  ============================================"
Write-Host ""

$scriptPath = $MyInvocation.MyCommand.Path
$scriptDir  = Split-Path -Parent $scriptPath
$tarPath    = Join-Path $scriptDir "fleethacker-image.tar"

# ---- Step 1: Admin + WSL2 ----
Write-Step 1 4 "Checking WSL2..."

if (-not (Test-Admin)) {
    Write-Host "  Setup needs admin rights for WSL2 and Docker install."
    Write-Host "  Relaunching as Administrator..."
    # Use an encoded command to avoid path-escaping issues entirely
    $cmd = "Set-Location '$scriptDir'; & '$scriptPath'"
    $bytes = [System.Text.Encoding]::Unicode.GetBytes($cmd)
    $encoded = [Convert]::ToBase64String($bytes)
    Start-Process powershell -Verb RunAs -ArgumentList "-ExecutionPolicy Bypass -NoProfile -EncodedCommand $encoded"
    exit
}

$wslReady = $false
try {
    $null = & wsl --status 2>&1
    if ($LASTEXITCODE -eq 0) { $wslReady = $true }
} catch {}

if (-not $wslReady) {
    Write-Host "  Enabling WSL2 (this may take a few minutes)..."
    try {
        # Win11 / recent Win10 method
        & wsl --install --no-distribution 2>&1 | ForEach-Object { Write-Host "  $_" }
    } catch {
        # Fallback for older Win10
        Write-Host "  Trying legacy method..."
        & dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart 2>&1 | Out-Null
        & dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart 2>&1 | Out-Null
    }
    Write-Host ""
    Write-Host "  ============================================" -ForegroundColor Yellow
    Write-Host "     WSL2 has been enabled." -ForegroundColor Yellow
    Write-Host "     You MUST restart your computer now." -ForegroundColor Yellow
    Write-Host "" -ForegroundColor Yellow
    Write-Host "     After restart, double-click setup.bat again." -ForegroundColor Yellow
    Write-Host "  ============================================" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "  Press Enter to exit"
    exit
}
Write-Ok "WSL2 is available."

# ---- Step 2: Docker Desktop ----
Write-Step 2 4 "Checking Docker Desktop..."

$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCmd) {
    Write-Host "  Docker Desktop is not installed. Downloading..."

    # Detect architecture (handle WoW64: 32-bit PS on 64-bit OS)
    $arch = "amd64"
    if ($env:PROCESSOR_ARCHITECTURE -eq "ARM64") {
        $arch = "arm64"
    } elseif ($env:PROCESSOR_ARCHITEW6432 -eq "ARM64") {
        $arch = "arm64"
    }

    $url = "https://desktop.docker.com/win/main/$arch/Docker%20Desktop%20Installer.exe"
    $installer = Join-Path $env:TEMP "DockerDesktopInstaller.exe"

    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Write-Host "  Downloading ($arch)..."
        Invoke-WebRequest -Uri $url -OutFile $installer -UseBasicParsing
    } catch {
        Write-Fail "Download failed: $_"
        Write-Host "  Please install Docker Desktop manually from:"
        Write-Host "  https://www.docker.com/products/docker-desktop/"
        Read-Host "  Press Enter to exit"
        exit 1
    }

    Write-Host "  Installing Docker Desktop (this takes a few minutes)..."
    try {
        $proc = Start-Process -FilePath $installer -ArgumentList "install","--quiet","--accept-license" -Wait -PassThru
        if ($proc.ExitCode -ne 0) { throw "Exit code: $($proc.ExitCode)" }
    } catch {
        Write-Host "  Silent install failed, launching interactive installer..."
        Start-Process -FilePath $installer -Wait
    }
    Remove-Item -LiteralPath $installer -ErrorAction SilentlyContinue

    # Refresh PATH from registry so we can find docker without logoff
    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath    = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path    = "$machinePath;$userPath"

    $dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $dockerCmd) {
        Write-Host ""
        Write-Host "  Docker installed but not yet on PATH." -ForegroundColor Yellow
        Write-Host "  Please LOG OUT and LOG BACK IN, then run setup.bat again." -ForegroundColor Yellow
        Read-Host "  Press Enter to exit"
        exit
    }
}
Write-Ok "Docker Desktop is installed."

# ---- Step 3: Start Docker engine ----
Write-Step 3 4 "Starting Docker engine..."

$dockerRunning = $false
try {
    $null = & docker info 2>&1
    if ($LASTEXITCODE -eq 0) { $dockerRunning = $true }
} catch {}

if (-not $dockerRunning) {
    $dockerExe = Find-DockerDesktop
    if (-not $dockerExe) {
        Write-Fail "Cannot find Docker Desktop executable."
        Write-Host "  Please open Docker Desktop manually, wait for it to start,"
        Write-Host "  then run setup.bat again."
        Read-Host "  Press Enter to exit"
        exit 1
    }
    Write-Host "  Launching Docker Desktop..."
    Start-Process -FilePath $dockerExe

    if (-not (Wait-ForDocker 180)) {
        Write-Fail "Docker did not start within 3 minutes."
        Write-Host "  Please open Docker Desktop, wait until it says 'running',"
        Write-Host "  then run setup.bat again."
        Read-Host "  Press Enter to exit"
        exit 1
    }
}
Write-Ok "Docker engine is running."

# ---- Step 4: Load image ----
Write-Step 4 4 "Loading Fleet Tech image..."

$imageExists = $false
try {
    $null = & docker image inspect fleethacker:latest 2>&1
    if ($LASTEXITCODE -eq 0) { $imageExists = $true }
} catch {}

if ($imageExists) {
    Write-Ok "Image already loaded."
} else {
    if (-not (Test-Path -LiteralPath $tarPath)) {
        Write-Fail "fleethacker-image.tar not found."
        Write-Host "  Expected at: $tarPath"
        Write-Host "  Make sure it is in the same folder as setup.bat."
        Read-Host "  Press Enter to exit"
        exit 1
    }
    Write-Host "  Loading image (this may take a minute)..."
    # Use Start-Process to safely handle paths with spaces
    $proc = Start-Process -FilePath "docker" -ArgumentList "load","-i","`"$tarPath`"" -NoNewWindow -Wait -PassThru
    if ($proc.ExitCode -ne 0) {
        Write-Fail "Failed to load image."
        Read-Host "  Press Enter to exit"
        exit 1
    }
    Write-Ok "Image loaded successfully."
}

Write-Host ""
Write-Host "  ============================================" -ForegroundColor Green
Write-Host "     Setup complete!" -ForegroundColor Green
Write-Host "" -ForegroundColor Green
Write-Host "     Double-click 'Fleet Tech.bat' to run." -ForegroundColor Green
Write-Host "  ============================================" -ForegroundColor Green
Write-Host ""
Read-Host "  Press Enter to close"
