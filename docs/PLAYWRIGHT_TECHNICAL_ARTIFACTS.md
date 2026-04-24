# Playwright Automation: Technical Artifacts

This file lists the key scripts, configs, and test specs used for Playwright automation, demo recording, and live backend validation.

---

## 1. Playwright Configurations
- `scratch/playwright.config.js` — Default (mocked backend)
- `scratch/playwright.demo.config.js` — Demo mode (slowMo, video, mocked backend)
- `scratch/playwright.live.config.js` — Live backend, video recording

## 2. API Interception Helpers
- `scratch/mockApi.js` — Mocks all backend API calls
- `scratch/liveApi.js` — No API interception (all calls go to real backend, only blocks .mp4/.pth)

## 3. Test Specs
- `tests/test_dashboard.spec.js` — Dashboard UI and map title validation
- `tests/test_tactical_legacy.spec.js` — Navigation and legacy tactical UI
- `tests/test_user_journeys.spec.js` — 9 user journeys, 58 tests (mocked backend)
- `tests/test_demo_sequences.spec.js` — 5 demo flows, ~1 min each (mocked backend, video)
- `tests/test_live_sequences.spec.js` — 5 demo flows, ~1 min each (real backend, video)

## 4. Demo Launcher Script
- `scripts/run_demo.ps1` — PowerShell script to launch demo recording

## 5. Backend Engine
- `src/agent_backend.py` — FastAPI backend (real neural engine)

---

## 6. Output Folders
- `scratch/demo-videos/` — Mocked backend demo videos
- `scratch/live-videos/` — Live backend demo videos

---

*For results, see PLAYWRIGHT_DEMO_RESULTS.md and PLAYWRIGHT_DEMO_RESULTS_TABLE.md.*
