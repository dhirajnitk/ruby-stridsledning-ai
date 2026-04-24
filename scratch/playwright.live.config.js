/**
 * SAAB C2 LIVE ENGINE DEMO CONFIG
 *
 * Unlike the mock demo config, this starts the REAL Python backend on
 * port 8000 so every button click hits the actual neural tactical engine.
 *
 * Two web servers:
 *   1. Python HTTP server  → serves frontend/ at port 3001
 *   2. Uvicorn FastAPI     → runs agent_backend.py at port 8000
 *
 * All API calls (health, theater, state, evaluate_advanced, ws/logs)
 * go to the LIVE engine.  Only .mp4/.pth binary assets are blocked.
 *
 * Usage:  npx playwright test --config=scratch/playwright.live.config.js
 * Videos: scratch/live-videos/<sequence>/video.webm
 * Report: scratch/live-report/index.html
 */
const { defineConfig } = require('@playwright/test');
const path = require('path');

const VENV_PYTHON = 'C:\\Users\\dhiraj.kumar\\Downloads\\Saab\\.venv_saab\\Scripts\\python.exe';

module.exports = defineConfig({
  testDir: path.join(__dirname, '..', 'tests'),
  testMatch: '**/test_live_sequences.spec.js',

  // Each sequence: allow up to 3 min for real AI computation
  timeout: 240_000,
  workers: 1,  // sequential — one sequence at a time
  retries: 1,  // retry once on flaky network timing

  reporter: [
    ['line'],
    ['html', { outputFolder: path.join(__dirname, 'live-report'), open: 'never' }],
  ],
  outputDir: path.join(__dirname, 'live-videos'),

  use: {
    baseURL: 'http://localhost:3001',
    headless: false,
    viewport: { width: 1920, height: 1080 },

    launchOptions: {
      slowMo: 900,
      args: ['--no-sandbox', '--start-maximized', '--disable-infobars'],
    },

    video: { mode: 'on', size: { width: 1920, height: 1080 } },
    screenshot: 'on',

    actionTimeout: 45_000,
    navigationTimeout: 45_000,
  },

  webServer: [
    // 1. Serve the frontend pages at port 3001
    {
      command: 'python -m http.server 3001',
      cwd: path.join(__dirname, '..', 'frontend'),
      port: 3001,
      reuseExistingServer: true,
      timeout: 20_000,
    },
    // 2. Start the REAL tactical AI backend at port 8000
    {
      command: `"${VENV_PYTHON}" src/agent_backend.py`,
      cwd: path.join(__dirname, '..'),
      port: 8000,
      reuseExistingServer: true,
      timeout: 60_000,   // model loading can take time
      env: {
        SAAB_MODE: 'boreal',
        PYTHONUNBUFFERED: '1',
      },
    },
  ],
});
