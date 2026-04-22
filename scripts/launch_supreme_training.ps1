# ====================================================
#    BOREAL STRATEGIC HUB: SUPREME INTUITION FORGE    
# ====================================================
# This script launches the high-intensity 30-epoch
# optimization cycle for the Hackathon Final Brain.

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "   INITIATING SUPREME NEURAL OPTIMIZATION           " -ForegroundColor Yellow
Write-Host "===================================================="
Write-Host "[INTEL] Target: 30 Epoch Strategic Convergence"
Write-Host "[INTEL] Data: 100,000 Baltic Mega-Corpus Samples"
Write-Host "[INTEL] Priority: High-Fidelity Strategic Intuition"
Write-Host "----------------------------------------------------"

# 1. Set Tactical Environment
$env:PYTHONPATH = "src"
$VENV_PYTHON = "c:\Users\dhiraj.kumar\Downloads\Saab\.venv_saab\Scripts\python.exe"

if (!(Test-Path $VENV_PYTHON)) {
    Write-Host "[ERROR] Python Virtual Environment not found at $VENV_PYTHON" -ForegroundColor Red
    exit
}

# 2. Launch Supreme Training
Write-Host "[LAUNCH] Commencing 30-Epoch Bake..." -ForegroundColor Green
& $VENV_PYTHON src/train_ppo_mega.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n====================================================" -ForegroundColor Green
    Write-Host "   MISSION COMPLETE: SUPREME BRAIN SECURED          " -ForegroundColor Yellow
    Write-Host "   Path: models/ppo_transformer_supreme.pth         "
    Write-Host "===================================================="
} else {
    Write-Host "`n[CRITICAL] Training failure. Check hardware/memory." -ForegroundColor Red
}
