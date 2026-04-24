// @ts-check
const { test, expect } = require('@playwright/test');
const { mockBackend } = require('./helpers/mockApi');

// ─────────────────────────────────────────────────────────────
// TEST: dashboard.html  — Strategic Dashboard
// ─────────────────────────────────────────────────────────────
test.describe('dashboard.html — Strategic Dashboard (boreal)', () => {
  test.beforeEach(async ({ page }) => {
    await mockBackend(page);
    await page.goto('/dashboard.html?mode=boreal', { waitUntil: 'domcontentloaded' });
  });

  test('page title includes BOREAL', async ({ page }) => {
    await expect(page).toHaveTitle(/BOREAL/i);
  });

  test('main title h1 renders', async ({ page }) => {
    await expect(page.locator('#main-title')).toBeVisible();
    await expect(page.locator('#main-title')).toContainText(/BOREAL|STRATEGIC/i);
  });

  test('map-title shows boreal theater name', async ({ page }) => {
    // viz_engine.js renderMap() replaces #map-title innerText with the theater name
    await expect(page.locator('#map-title')).toBeVisible();
    const text = await page.locator('#map-title').textContent();
    expect(text.toUpperCase()).toContain('BOREAL');
  });

  test('engine status badge is visible', async ({ page }) => {
    await expect(page.locator('#engine-status-badge')).toBeVisible();
  });

  test('engine badge shows ENGINE ONLINE after /theater mock resolves', async ({ page }) => {
    await expect(page.locator('#engine-status-badge')).toContainText(/ENGINE ONLINE/i, { timeout: 8000 });
  });

  // ── Mode buttons
  test('AUTONOMOUS mode button is active by default', async ({ page }) => {
    const btn = page.locator('#mode-auto');
    await expect(btn).toBeVisible();
    await expect(btn).toHaveClass(/active-auto/);
  });

  test('clicking HUMAN-IN-LOOP activates hitl class', async ({ page }) => {
    await page.locator('#mode-hitl').click();
    await expect(page.locator('#mode-hitl')).toHaveClass(/active-hitl/);
    // approval-queue panel should become visible
    await expect(page.locator('#approval-queue')).toBeVisible();
    // auto button should no longer be active
    await expect(page.locator('#mode-auto')).not.toHaveClass(/active-auto/);
  });

  test('clicking MANUAL OVERRIDE activates manual class and shows manual panel', async ({ page }) => {
    await page.locator('#mode-manual').click();
    await expect(page.locator('#mode-manual')).toHaveClass(/active-manual/);
    await expect(page.locator('#manual-panel')).toBeVisible();
    await expect(page.locator('#manual-target')).toBeVisible();
    await expect(page.locator('#manual-effector')).toBeVisible();
    await expect(page.locator('#manual-base')).toBeVisible();
    await expect(page.locator('#btn-manual-fire')).toBeVisible();
  });

  test('switching back to AUTO hides manual-panel and approval-queue', async ({ page }) => {
    await page.locator('#mode-manual').click();
    await page.locator('#mode-auto').click();
    await expect(page.locator('#manual-panel')).toBeHidden();
    await expect(page.locator('#approval-queue')).toBeHidden();
    await expect(page.locator('#mode-auto')).toHaveClass(/active-auto/);
  });

  // ── Doctrine selector
  test('doctrine buttons are rendered (Balanced, Fortress, Aggressive)', async ({ page }) => {
    await expect(page.locator('.doctrine-btn')).toHaveCount(3);
    await expect(page.locator('.doctrine-btn.active')).toContainText(/Balanced/i);
  });

  test('clicking Aggressive doctrine activates it', async ({ page }) => {
    await page.locator('.doctrine-btn[data-doctrine="aggressive"]').click();
    await expect(page.locator('.doctrine-btn[data-doctrine="aggressive"]')).toHaveClass(/active/);
    await expect(page.locator('.doctrine-btn[data-doctrine="balanced"]')).not.toHaveClass(/active/);
  });

  test('clicking Fortress doctrine activates it', async ({ page }) => {
    await page.locator('.doctrine-btn[data-doctrine="fortress"]').click();
    await expect(page.locator('.doctrine-btn[data-doctrine="fortress"]')).toHaveClass(/active/);
  });

  // ── Model selector
  test('Neural Architecture selector is visible with options', async ({ page }) => {
    const sel = page.locator('#sel-model-core');
    await expect(sel).toBeVisible();
    // Should have multiple models
    const count = await sel.locator('option').count();
    expect(count).toBeGreaterThanOrEqual(6);
  });

  test('model selector can be changed to Elite V3.5', async ({ page }) => {
    await page.locator('#sel-model-core').selectOption('elite');
    await expect(page.locator('#sel-model-core')).toHaveValue('elite');
  });

  test('arch-badge updates after model switch (via viz_engine.js setModel)', async ({ page }) => {
    await page.locator('#sel-model-core').selectOption('supreme3');
    await expect(page.locator('#sel-model-core')).toHaveValue('supreme3');
  });

  // ── Mission control
  test('Initialize Intercept and Clear Theatre buttons present', async ({ page }) => {
    await expect(page.locator('#btn-launch')).toBeVisible();
    await expect(page.locator('#btn-reset')).toBeVisible();
  });

  // ── Nav links
  test('CORTEX-C2 nav link is present', async ({ page }) => {
    await expect(page.locator('a[href*="cortex_c2"]')).toBeVisible();
  });

  test('LIVE VIEW nav link is present and has correct href', async ({ page }) => {
    const lv = page.locator('#nav-live-view');
    await expect(lv).toBeVisible();
    const href = await lv.getAttribute('href');
    expect(href).toContain('live_view');
    expect(href).toContain('mode=boreal');
  });

  test('TACTICAL nav link is present', async ({ page }) => {
    const tac = page.locator('#nav-tactical-hdr');
    await expect(tac).toBeVisible();
    const href = await tac.getAttribute('href');
    expect(href).toContain('tactical_legacy');
  });

  test('PORTAL home link is present', async ({ page }) => {
    await expect(page.locator('a[href="index.html"]')).toBeVisible();
  });

  test('3D KINETIC SIM button is present', async ({ page }) => {
    await expect(page.locator('#btn-kinetic-3d')).toBeVisible();
  });

  test('Launch Live 3D Audit button is present', async ({ page }) => {
    await expect(page.locator('#btn-live-audit')).toBeVisible();
  });

  // ── SVG map
  test('SVG tactical map renders', async ({ page }) => {
    await expect(page.locator('#baltic-map')).toBeVisible();
  });

  // ── Threat registry panel
  test('threat-count badge shows', async ({ page }) => {
    await expect(page.locator('#threat-count')).toBeVisible();
  });

  // ── CoT feed
  test('cot-feed panel renders', async ({ page }) => {
    await expect(page.locator('#cot-feed')).toBeVisible();
  });
});

// ─────────────────────────────────────────────────────────────
// TEST: dashboard.html  — Sweden mode
// ─────────────────────────────────────────────────────────────
test.describe('dashboard.html — Sweden theater mode', () => {
  test.beforeEach(async ({ page }) => {
    await mockBackend(page);
    await page.goto('/dashboard.html?mode=sweden', { waitUntil: 'domcontentloaded' });
  });

  test('title changes to SWEDEN STRATEGIC COMMAND', async ({ page }) => {
    await expect(page).toHaveTitle(/SWEDEN/i);
  });

  test('h1 main-title shows SWEDEN STRATEGIC COMMAND', async ({ page }) => {
    await expect(page.locator('#main-title')).toContainText(/SWEDEN/i);
  });

  test('map-title shows sweden theater name', async ({ page }) => {
    await expect(page.locator('#map-title')).toBeVisible();
    const text = await page.locator('#map-title').textContent();
    // renderMap() sets: 'STRATEGIC MAP :: SWEDISH NATIONAL DEFENSE'
    expect(text.toUpperCase()).toMatch(/SWED/);
  });
});
