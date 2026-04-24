# ─────────────────────────────────────────────────────────────────────────────
# scripts/run_demo.ps1
# SAAB CORTEX-C2  ·  Full Demo Recording Launcher
#
# Runs all 5 simulation sequences in a visible, full-screen Chromium browser.
# Each sequence is ~1 minute.  Total run: ~5-6 minutes.
#
# Outputs
#   scratch\demo-videos\  — one .webm video per sequence
#   scratch\demo-report\  — HTML report with embedded video player
#
# Usage (from project root)
#   powershell -ExecutionPolicy Bypass -File scripts\run_demo.ps1
# ─────────────────────────────────────────────────────────────────────────────

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ── Resolve paths ─────────────────────────────────────────────────────────────
$projectRoot = Split-Path $PSScriptRoot -Parent
$videoDir    = Join-Path $projectRoot "scratch\demo-videos"
$reportPath  = Join-Path $projectRoot "scratch\demo-report\index.html"
$configFile  = Join-Path $projectRoot "scratch\playwright.demo.config.js"

Push-Location $projectRoot

# ── Banner ────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   SAAB CORTEX-C2  ·  DEMO RECORDING                     ║" -ForegroundColor Cyan
Write-Host "║   5 sequences  ·  ~1 minute each  ·  full video output   ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Sequence 1 — Strategic Portal Overview" -ForegroundColor Yellow
Write-Host "  Sequence 2 — Dashboard Command Mode Workflow" -ForegroundColor Yellow
Write-Host "  Sequence 3 — Cortex C2 Strategic Audit" -ForegroundColor Yellow
Write-Host "  Sequence 4 — Tactical Legacy Multi-Threat Engagement" -ForegroundColor Yellow
Write-Host "  Sequence 5 — Kinetic 3D Full Weapons Demo" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Videos will be saved to: $videoDir" -ForegroundColor Green
Write-Host "  Report  will be saved to: $reportPath" -ForegroundColor Green
Write-Host ""
Write-Host "  Starting in 3 seconds..." -ForegroundColor White
Start-Sleep -Seconds 3

# ── Run Playwright demo suite ─────────────────────────────────────────────────
Write-Host ""
Write-Host "[RUN] npx playwright test --config=$configFile" -ForegroundColor Cyan

$exitCode = 0
try {
    & npx playwright test --config=$configFile
    $exitCode = $LASTEXITCODE
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    $exitCode = 1
}

# ── Results ───────────────────────────────────────────────────────────────────
Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "✓ ALL 5 SEQUENCES PASSED" -ForegroundColor Green
} else {
    Write-Host "✗ Some sequences failed — check report for details" -ForegroundColor Red
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan

# ── Open video directory ──────────────────────────────────────────────────────
if (Test-Path $videoDir) {
    Write-Host ""
    Write-Host "Opening video folder: $videoDir" -ForegroundColor Yellow
    # List discovered videos
    $videos = Get-ChildItem -Path $videoDir -Filter "*.webm" -Recurse | Sort-Object LastWriteTime -Descending
    if ($videos.Count -gt 0) {
        Write-Host ""
        Write-Host "  Recorded videos ($($videos.Count) files):" -ForegroundColor White
        foreach ($v in $videos) {
            $mb = [math]::Round($v.Length / 1MB, 1)
            Write-Host "    $($v.Name)  [$mb MB]  ->  $($v.FullName)" -ForegroundColor Gray
        }
    }
    Start-Process "explorer.exe" $videoDir
}

# ── Open HTML report ──────────────────────────────────────────────────────────
if (Test-Path $reportPath) {
    Write-Host ""
    Write-Host "Opening HTML report: $reportPath" -ForegroundColor Yellow
    Start-Process $reportPath
} else {
    # Generate the report if it wasn't auto-created
    Write-Host "Generating HTML report..." -ForegroundColor Yellow
    & npx playwright show-report scratch/demo-report
}

Write-Host ""
Write-Host "Demo recording complete." -ForegroundColor Green
Pop-Location
exit $exitCode
