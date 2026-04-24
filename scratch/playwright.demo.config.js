/**
 * SAAB C2 DEMO RECORDING CONFIG
 *
 * Runs 5 human-like demo sequences (~1 minute each) with:
 *   - Headed browser (visible window)
 *   - slowMo: 900ms per action (looks deliberate)
 *   - Video recording of every sequence
 *   - 1280×800 viewport → clean HD-quality .webm files
 *
 * Usage:  npx playwright test --config=scratch/playwright.demo.config.js
 * Videos: scratch/demo-videos/<sequence-name>/video.webm
 * Report: scratch/demo-report/index.html
 */
const { defineConfig } = require('@playwright/test');
const path = require('path');

module.exports = defineConfig({
  testDir: path.join(__dirname, '..', 'tests'),
  testMatch: '**/test_demo_sequences.spec.js',
  timeout: 200_000,   // 3 min 20 s per sequence (generous)
  workers: 1,         // sequential — one sequence at a time
  reporter: [
    ['line'],
    ['html', { outputFolder: path.join(__dirname, 'demo-report'), open: 'never' }],
  ],
  outputDir: path.join(__dirname, 'demo-videos'),

  use: {
    baseURL: 'http://localhost:3001',
    headless: false,
    viewport: { width: 1920, height: 1080 },

    // Full-screen feel: maximise the browser window
    launchOptions: {
      slowMo: 900,           // 900 ms added to every Playwright action
      args: [
        '--no-sandbox',
        '--start-maximized',
        '--disable-infobars',
      ],
    },

    // Record every test as a 1080p video
    video: { mode: 'on', size: { width: 1920, height: 1080 } },
    // Screenshot at end of every test (thumbnail)
    screenshot: 'on',

    actionTimeout: 30_000,
    navigationTimeout: 30_000,
  },

  webServer: {
    command: 'python -m http.server 3001',
    cwd: path.join(__dirname, '..', 'frontend'),
    port: 3001,
    reuseExistingServer: true,
    timeout: 30_000,
  },
});
