# Boreal Chessmaster - Windows Local Environment Launcher
# SAAB HACKATHON 2026 - FINAL MISSION PROTOCOL

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   Starting Boreal Command Suite (Local) " -ForegroundColor Cyan
Write-Host "   NATO/Sweden Doctrine: SYNCHRONIZED    " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Resolve paths relative to this script's location
$rootDir  = (Resolve-Path "$PSScriptRoot\..").Path          # ruby-stridsledning-ai/
$saabDir  = (Resolve-Path "$PSScriptRoot\..\..").Path       # Downloads/Saab/
$venvPath = Join-Path $saabDir ".venv_saab"
$venvPython = Join-Path $venvPath "Scripts\python.exe"

# 1. Environment Configuration
Write-Host "`n[1/5] Setting Environment Variables..." -ForegroundColor Yellow
$env:SAAB_MODE = "boreal"
$env:OPENROUTER_API_KEY = "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"
Write-Host "Environment configured." -ForegroundColor Green

# 2. Python Check
Write-Host "`n[2/5] Checking Python installation..." -ForegroundColor Yellow
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python is not installed or not in PATH." -ForegroundColor Red; exit
}
Write-Host "Found: $(python --version)" -ForegroundColor Green

# 3. Virtual Environment
Write-Host "`n[3/5] Syncing Dependencies (Parent Venv)..." -ForegroundColor Yellow
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating venv at $venvPath ..." -ForegroundColor Cyan
    python -m venv $venvPath
} else {
    Write-Host "Venv found: $venvPath" -ForegroundColor Cyan
}
& $venvPython -m pip install -r (Join-Path $rootDir "requirements.txt") --quiet
Write-Host "Dependencies OK." -ForegroundColor Green

# 4. Start Backend
Write-Host "`n[4/5] Launching Tactical Engine Backend..." -ForegroundColor Yellow
Start-Process -FilePath $venvPython `
    -ArgumentList "src\agent_backend.py" `
    -WorkingDirectory $rootDir `
    -WindowStyle Normal
Write-Host "Backend initializing on http://localhost:8000 ..." -ForegroundColor Green
Start-Sleep -Seconds 5

# 5. Start Frontend
Write-Host "`n[5/5] Opening Tactical Dashboard..." -ForegroundColor Yellow
Start-Process -FilePath $venvPython `
    -ArgumentList "-m http.server 3001 --directory `"$(Join-Path $rootDir 'frontend')`"" `
    -WorkingDirectory $rootDir `
    -WindowStyle Minimized
Start-Sleep -Seconds 2
Start-Process "http://localhost:3001/dashboard.html"

Write-Host "`n[SUCCESS] BOREAL COMMAND SUITE IS LIVE!" -ForegroundColor Green
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:3001/dashboard.html" -ForegroundColor Cyan
Write-Host "`nPress any key to exit this launcher (servers will stay running)..." -ForegroundColor DarkGray
Pause
