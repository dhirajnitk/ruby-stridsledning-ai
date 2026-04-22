# BOREAL CHESSMASTER: UNIFIED STRATEGIC PIPELINE
# Tasks: 1. 100k Mega-Forge | 2. Tabula Rasa Training

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "    BOREAL STRATEGIC HUB: THE ENDGAME PIPELINE      " -ForegroundColor Yellow
Write-Host "===================================================="
Write-Host "[1/2] Launching Phase 3: 100,000 Sample Mega-Forge..." -ForegroundColor Cyan
Write-Host "      (Estimated Time: 2-3 Hours)"
Write-Host "----------------------------------------------------"

# Set tactical environment
$env:PYTHONPATH = "src"
$VENV_PYTHON = "c:\Users\dhiraj.kumar\Downloads\Saab\.venv_saab\Scripts\python.exe"

# STEP 1: FORGE
& $VENV_PYTHON src/forge_strategic_dataset.py --phases ppo

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[2/2] Forge Successful. Launching Tabula Rasa Training..." -ForegroundColor Green
    Write-Host "      (Baking 100k samples into a fresh neural policy)"
    Write-Host "----------------------------------------------------"
    
    # STEP 2: TRAIN
    & $VENV_PYTHON src/train_ppo_mega.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n====================================================" -ForegroundColor Green
        Write-Host "   MISSION COMPLETE: FINAL HACKATHON MODEL FORGED   " -ForegroundColor Yellow
        Write-Host "   Path: models/ppo_hackathon_final.pth             "
        Write-Host "===================================================="
    } else {
        Write-Host "`n[CRITICAL] Training failure. Check neural constraints." -ForegroundColor Red
    }
} else {
    Write-Host "`n[CRITICAL] Forge failure. Check hardware and storage." -ForegroundColor Red
}
