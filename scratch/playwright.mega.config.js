/**
 * SAAB MEGA DEMO CONFIG — One Big Live Video
 *
 * Captures a single end-to-end walkthrough video (~8-10 min) showing:
 *   ACT 1  — Portal navigation (all cards, C2 first)
 *   ACT 2  — CORTEX C2 with real AI eval
 *   ACT 3  — Boreal Dashboard (modes, doctrine, model swap)
 *   ACT 4  — Boreal Live View (saturation wave + auto-wave)
 *   ACT 5  — Boreal Kinetic 3D (weapons cycle + wave)
 *   ACT 6  — Boreal Tactical (spawn threats + AI eval)
 *   ACT 7  — Sweden Theater: portal → dashboard → live → kinetic → tactical
 *
 * Usage:
 *   npx playwright test --config=scratch/playwright.mega.config.js
 *
 * Output:
 *   scratch/mega-demo/<test-folder>/video.webm
 */
const { defineConfig } = require('@playwright/test');
const path = require('path');

const VENV_PYTHON = 'C:\\Users\\dhiraj.kumar\\Downloads\\Saab\\.venv_saab\\Scripts\\python.exe';

module.exports = defineConfig({
  testDir: path.join(__dirname, '..', 'tests'),
  testMatch: '**/test_mega_demo.spec.js',

  timeout: 240_000,   // 4 min — padded demo
  workers: 1,
  retries: 0,

  reporter: [
    ['line'],
    ['html', { outputFolder: path.join(__dirname, 'mega-report'), open: 'never' }],
  ],
  outputDir: path.join(__dirname, 'mega-demo'),

  use: {
    baseURL: 'http://localhost:3001',
    headless: true,
    viewport: { width: 1920, height: 1080 },

    launchOptions: {
      slowMo: 400,
      args: [
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--force-device-scale-factor=1',
        '--disable-web-security',
        '--window-size=1920,1080',
      ],
    },

    video: { mode: 'on', size: { width: 1920, height: 1080 } },
    screenshot: 'off',
    actionTimeout: 30_000,
    navigationTimeout: 30_000,
  },

  webServer: [
    {
      command: `"${VENV_PYTHON}" -m http.server 3001`,
      cwd: path.join(__dirname, '..', 'frontend'),
      port: 3001,
      reuseExistingServer: true,
      timeout: 15_000,
    },
    {
      command: `"${VENV_PYTHON}" src/agent_backend.py`,
      cwd: path.join(__dirname, '..'),
      port: 8000,
      reuseExistingServer: true,
      timeout: 60_000,
      env: { SAAB_MODE: 'boreal', PYTHONUNBUFFERED: '1' },
    },
  ],
});
