# Boreal Chessmaster - Windows Local Environment Launcher
# 🛡️ SAAB HACKATHON 2026 - FINAL MISSION PROTOCOL

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   Starting Boreal Command Suite (Local) " -ForegroundColor Cyan
Write-Host "   NATO/Sweden Doctrine: SYNCHRONIZED    " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# 1. Environment Configuration
Write-Host "`n[1/5] Setting Environment Variables..." -ForegroundColor Yellow
$env:PYTHONPATH = ".\.local_lib"
$env:SAAB_MODE = "sweden" # Toggle to 'boreal' for different theater
$env:OPENROUTER_API_KEY="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"
Write-Host "PYTHONPATH set to .local_lib (DLL Resolution Active)." -ForegroundColor Green

# 2. Python Check
Write-Host "`n[2/5] Checking Python installation..." -ForegroundColor Yellow
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python is not installed." -ForegroundColor Red; exit
}
$pythonVersion = python --version
Write-Host "Found: $pythonVersion" -ForegroundColor Green

# 3. Virtual Environment
Write-Host "`n[3/5] Syncing Dependencies (Parent Venv)..." -ForegroundColor Yellow
$venvPath = "..\.venv_saab"
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating venv in parent..." -ForegroundColor Cyan
    python -m venv $venvPath
}
$venvPython = "$venvPath\Scripts\python.exe"
& $venvPython -m pip install -r requirements.txt

# 4. Start Backend
Write-Host "`n[4/5] Launching Tactical Engine Backend..." -ForegroundColor Yellow
Start-Process -FilePath $venvPython -ArgumentList "src/agent_backend.py" -WindowStyle Normal
Write-Host "Backend initializing on http://localhost:8000..." -ForegroundColor Green
Start-Sleep -Seconds 5

# 5. Start Frontend
Write-Host "`n[5/5] Opening Tactical Dashboard..." -ForegroundColor Yellow
# Dashboard is in root directory
Start-Process -FilePath $venvPython -ArgumentList "-m http.server 8080" -WindowStyle Minimized
Start-Sleep -Seconds 2
Start-Process "http://localhost:8080/dashboard.html"

Write-Host "`n[SUCCESS] BOREAL COMMAND SUITE IS LIVE!" -ForegroundColor Green
Write-Host "Press any key to exit this launcher (Backend will stay running)..." -ForegroundColor Gray
Pause
