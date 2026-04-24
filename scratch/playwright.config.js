// Playwright config — SAAB Stridsledning UI Test Suite
// Serves frontend/ on port 3001 via Python http.server
// All backend API calls to port 8000 are mocked inside each test.

const path = require('path');

module.exports = {
  testDir: path.join(__dirname, '..', 'tests'),
  timeout: 35000,
  retries: 0,

  use: {
    headless: true,
    baseURL: 'http://localhost:3001',
    actionTimeout: 12000,
    screenshot: 'only-on-failure',
    video: 'off',
  },

  reporter: [
    ['list'],
    ['html', { outputFolder: path.join(__dirname, 'playwright-report'), open: 'never' }],
  ],

  webServer: {
    command: 'python -m http.server 3001',
    cwd: path.join(__dirname, '..', 'frontend'),
    url: 'http://localhost:3001',
    reuseExistingServer: true,
    timeout: 12000,
  },
};
