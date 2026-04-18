# Boreal Chessmaster - Windows Local Environment Launcher

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   Starting Boreal Chessmaster (Local)   " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# 1. Set the OpenRouter API Key
Write-Host "`n[1/5] Setting Environment Variables..." -ForegroundColor Yellow
$env:OPENROUTER_API_KEY="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"
Write-Host "OPENROUTER_API_KEY set successfully." -ForegroundColor Green

# 2. Check for Python Installation
Write-Host "`n[2/5] Checking Python installation..." -ForegroundColor Yellow
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python is not installed or not added to your PATH." -ForegroundColor Red
    Write-Host "Please download and install Python 3.10+ from python.org" -ForegroundColor Red
    Pause
    exit
}
$pythonVersion = python --version
Write-Host "Found: $pythonVersion" -ForegroundColor Green

# 3. Virtual Environment & Dependencies
Write-Host "`n[3/5] Setting up Virtual Environment and Installing Packages..." -ForegroundColor Yellow
$venvPath = ".\.venv_saab"
$venvPython = "$venvPath\Scripts\python.exe"
$venvPip = "$venvPath\Scripts\pip.exe"

if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment '.venv_saab'..." -ForegroundColor Cyan
    python -m venv $venvPath
} else {
    Write-Host "Virtual environment '.venv_saab' already exists." -ForegroundColor Cyan
}

Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Cyan
& $venvPip install -r requirements.txt

# 4. Start the Backend Server
Write-Host "`n[4/5] Starting FastAPI Backend Server..." -ForegroundColor Yellow
# Starts the backend in a separate visible terminal window so you can monitor engine logs
Start-Process -FilePath $venvPython -ArgumentList "src/agent_backend.py" -WindowStyle Normal
Write-Host "Backend initializing on http://localhost:8000..." -ForegroundColor Green

Start-Sleep -Seconds 4

# 5. Start the Frontend UI Server
Write-Host "`n[5/5] Starting Frontend Web Server & Opening Browser..." -ForegroundColor Yellow
# Starts the lightweight HTTP server minimized so it doesn't clutter the screen
Start-Process -FilePath $venvPython -ArgumentList "-m http.server 8080 --directory frontend" -WindowStyle Minimized

Start-Sleep -Seconds 2
Start-Process "http://localhost:8080"

Write-Host "`n[SUCCESS] System is LIVE!" -ForegroundColor Green
Write-Host "To stop the system later, simply close the newly opened Python command windows.`n" -ForegroundColor DarkGray
