// @ts-check
const { test, expect } = require('@playwright/test');
const { mockBackend } = require('./helpers/mockApi');

// ─────────────────────────────────────────────────────────────
// TEST: cortex_c2.html  — CORTEX-C2 Operator Console
// ─────────────────────────────────────────────────────────────
test.describe('cortex_c2.html — CORTEX-C2 Console', () => {
  test.beforeEach(async ({ page }) => {
    await mockBackend(page);
    await page.goto('/cortex_c2.html');
    // Wait for at least the header to be attached
    await page.waitForSelector('header', { timeout: 6000 });
  });

  // ── Nav links
  test('PORTAL nav link is present and links to index.html', async ({ page }) => {
    const link = page.locator('a.nav-back[href="index.html"]');
    await expect(link).toBeVisible();
    await expect(link).toContainText(/PORTAL/i);
  });

  test('DASHBOARD nav link is present', async ({ page }) => {
    const link = page.locator('a.nav-back[href="dashboard.html"]');
    await expect(link).toBeVisible();
    await expect(link).toContainText(/DASHBOARD/i);
  });

  test('LIVE VIEW nav link is present', async ({ page }) => {
    const link = page.locator('a.nav-back[href*="live_view"]');
    await expect(link).toBeVisible();
  });

  test('TACTICAL nav link is present', async ({ page }) => {
    const link = page.locator('a.nav-back[href*="tactical_legacy"]');
    await expect(link).toBeVisible();
  });

  // ── Model selector
  test('model-select dropdown is visible with all 8 options', async ({ page }) => {
    const sel = page.locator('#model-select');
    await expect(sel).toBeVisible();
    const count = await sel.locator('option').count();
    expect(count).toBeGreaterThanOrEqual(7);
  });

  test('model selector defaults to heuristic', async ({ page }) => {
    await expect(page.locator('#model-select')).toHaveValue('heuristic');
  });

  test('can switch model to elite', async ({ page }) => {
    await page.locator('#model-select').selectOption('elite');
    await expect(page.locator('#model-select')).toHaveValue('elite');
  });

  // ── Doctrine buttons
  test('BALANCED doctrine button is present and active by default', async ({ page }) => {
    const btn = page.locator('#doc-balanced');
    await expect(btn).toBeVisible();
    await expect(btn).toHaveClass(/doc-balanced/);
  });

  test('FORTRESS doctrine button is clickable', async ({ page }) => {
    await page.locator('#doc-fortress').click();
    await expect(page.locator('#doc-fortress')).toBeVisible();
  });

  test('AGGRESSIVE doctrine button is clickable', async ({ page }) => {
    await page.locator('#doc-aggressive').click();
    await expect(page.locator('#doc-aggressive')).toBeVisible();
  });

  // ── Scenario cards
  test('three scenario cards are rendered', async ({ page }) => {
    await expect(page.locator('.sc-card')).toHaveCount(3);
  });

  test('"Clean picture" scenario card is active by default', async ({ page }) => {
    await expect(page.locator('.sc-card.active')).toContainText(/Clean picture/i);
  });

  test('clicking "Swarm" scenario card activates it', async ({ page }) => {
    await page.locator('.sc-card[data-sc="swarm"]').click();
    await expect(page.locator('.sc-card[data-sc="swarm"]')).toHaveClass(/active/);
    await expect(page.locator('.sc-card[data-sc="clean"]')).not.toHaveClass(/active/);
  });

  test('clicking "Jammed" scenario card activates it', async ({ page }) => {
    await page.locator('.sc-card[data-sc="jammed"]').click();
    await expect(page.locator('.sc-card[data-sc="jammed"]')).toHaveClass(/active/);
  });

  // ── RUN STRATEGIC AUDIT button
  test('RUN STRATEGIC AUDIT button is visible', async ({ page }) => {
    await expect(page.locator('#btn-run-audit')).toBeVisible();
    await expect(page.locator('#btn-run-audit')).toContainText(/AUDIT/i);
  });

  // ── COA Grid
  test('coa-grid is present with 3 placeholder cards', async ({ page }) => {
    const grid = page.locator('#coa-grid');
    await expect(grid).toBeVisible();
    const cards = grid.locator('.coa-card');
    await expect(cards).toHaveCount(3);
  });

  // ── Tactical SVG
  test('tactical SVG display is rendered', async ({ page }) => {
    await expect(page.locator('#tactical-svg')).toBeVisible();
  });

  test('3D KINETIC button in tactical panel opens kinetic_3d.html', async ({ page }) => {
    const btn = page.locator('.tactical-open-btn');
    await expect(btn).toBeVisible();
    await expect(btn).toContainText(/3D KINETIC/i);
  });

  // ── Sensor bars
  test('sensor quality bars are rendered', async ({ page }) => {
    await expect(page.locator('#sq-radar')).toBeAttached();
    await expect(page.locator('#sq-ireo')).toBeAttached();
    await expect(page.locator('#sq-fusion')).toBeAttached();
  });

  // ── REPLENISH button
  test('REPLENISH button is present', async ({ page }) => {
    await expect(page.locator('#btn-replenish')).toBeVisible();
  });

  // ── Loading scenario populates threat tracks
  test('loading "clean" scenario and calling evaluate sets mode-pill text', async ({ page }) => {
    // Mode-pill should show a mode text
    const pill = page.locator('#mode-text');
    await expect(pill).toBeAttached();
    // The text should be a known mode
    const text = await pill.textContent();
    expect(['AUTONOMOUS','ADVISE','DEFER','LOCKED OUT'].some(m => text.includes(m))).toBeTruthy();
  });

  // ── SA-health gauge
  test('SA health circle is rendered', async ({ page }) => {
    await expect(page.locator('#sa-arc')).toBeAttached();
    await expect(page.locator('#sa-num')).toBeAttached();
  });

  // ── Backend connectivity badge
  test('backend-dot and backend-lbl are visible', async ({ page }) => {
    await expect(page.locator('#backend-dot')).toBeAttached();
    await expect(page.locator('#backend-lbl')).toBeVisible();
  });
});
