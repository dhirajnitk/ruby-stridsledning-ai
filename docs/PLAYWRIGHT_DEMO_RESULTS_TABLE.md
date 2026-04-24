# Playwright Test Results (Summary Table)

| Suite/Sequence                | Backend      | Tests/Flows | Passed | Video Output Folder         | Notes                                  |
|-------------------------------|--------------|-------------|--------|----------------------------|-----------------------------------------|
| test_dashboard.spec.js         | Mocked       | 10+         | All    | N/A                        | Map title assertion fixed               |
| test_tactical_legacy.spec.js   | Mocked       | 10+         | All    | N/A                        | Nav button assertion fixed              |
| test_user_journeys.spec.js     | Mocked       | 58          | 58     | N/A                        | 9 journeys, all pass                    |
| test_demo_sequences.spec.js    | Mocked       | 5           | 5      | scratch/demo-videos/        | ~1 min each, full-screen video          |
| test_live_sequences.spec.js    | Live Engine  | 5           | 5      | scratch/live-videos/        | Real backend, real neural output        |

---

## Key Fixes & Improvements
- Fixed selector and assertion issues in dashboard and tactical legacy specs
- Created robust user journey tests (mocked backend, real UI actions)
- Built and debugged 5 demo sequences (mocked backend, then live backend)
- Fixed SEQ-2 in live demo to wait for /theater and call /state directly
- Validated real backend output (real scores, assignments, base data)
- Ensured all video artifacts are generated and accessible

---

## Video Artifact Locations
- **Mocked backend demo videos:** `scratch/demo-videos/`
- **Live backend demo videos:** `scratch/live-videos/`
- Format: `.webm` (full-screen, ~1 min each)

---

## How to Reproduce
1. Run Playwright tests with the appropriate config:
   - Mocked: `npx playwright test --config=scratch/playwright.demo.config.js --reporter=line`
   - Live:   `npx playwright test --config=scratch/playwright.live.config.js --reporter=line`
2. Videos will be saved in the respective folders above.

---

## Backend Details
- **Mocked:** All API calls intercepted by `mockApi.js`
- **Live:** All API calls routed to FastAPI backend (`src/agent_backend.py`) via `liveApi.js`

---

## Additional Notes
- All tests and demos use real UI actions (clicks, navigation, typing)
- PowerShell script `scripts/run_demo.ps1` can be used to launch demo recording
- All configs and test specs are in `scratch/` and `tests/`

---

*See PLAYWRIGHT_DEMO_RESULTS.md for full narrative and details.*
