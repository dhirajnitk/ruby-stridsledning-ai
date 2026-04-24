// @ts-check
const { test, expect } = require('@playwright/test');
const { mockBackend } = require('./helpers/mockApi');

// ─────────────────────────────────────────────────────────────
// TEST: index.html  — Strategic Portal (Cortex UI)
// ─────────────────────────────────────────────────────────────
test.describe('index.html — Strategic Portal', () => {
  test.beforeEach(async ({ page }) => {
    await mockBackend(page);
    await page.goto('/index.html');
  });

  test('page title is correct', async ({ page }) => {
    await expect(page).toHaveTitle(/CORTEX COMMAND PORTAL/i);
  });

  test('heading STRATEGIC PORTAL is visible', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('STRATEGIC PORTAL');
  });

  test('CORTEX-C2 card is present and links to cortex_c2.html', async ({ page }) => {
    const link = page.locator('a[href*="cortex_c2"]').first();
    await expect(link).toBeVisible();
    await expect(link).toContainText(/CORTEX-C2/i);
  });

  test('Strategic Dashboard card links to dashboard.html', async ({ page }) => {
    const link = page.locator('a[href*="dashboard"]').first();
    await expect(link).toBeVisible();
    await expect(link).toContainText(/Dashboard/i);
  });

  test('3D Kinetic — Boreal and Sweden cards present', async ({ page }) => {
    await expect(page.locator('a[href*="kinetic_3d.html?theater=boreal"]')).toBeVisible();
    await expect(page.locator('a[href*="kinetic_3d.html?theater=sweden"]')).toBeVisible();
  });

  test('BOREAL theater toggle is active by default', async ({ page }) => {
    const bBtn = page.locator('#toggle-boreal');
    await expect(bBtn).toBeVisible();
    // Active boreal button should have blue styling
    const color = await bBtn.evaluate(el => el.style.color);
    expect(color).toBe('rgb(0, 242, 255)');
  });

  test('SWEDEN toggle switches theater, updates link hrefs', async ({ page }) => {
    await page.locator('#toggle-sweden').click();
    // Dashboard link should now carry ?mode=sweden
    const dashHref = await page.locator('[data-theater-href="dashboard.html"]').getAttribute('href');
    expect(dashHref).toContain('mode=sweden');
    // Switching back to boreal works
    await page.locator('#toggle-boreal').click();
    const hrefBack = await page.locator('[data-theater-href="dashboard.html"]').getAttribute('href');
    expect(hrefBack).toContain('mode=boreal');
  });

  test('backend status becomes ONLINE after mocked /health resolves', async ({ page }) => {
    const badge = page.locator('#portal-backend');
    await expect(badge).toHaveText(/ONLINE/i, { timeout: 5000 });
  });

  test('Live Kinetic View card links to live_view.html', async ({ page }) => {
    const link = page.locator('a[href*="live_view"]');
    await expect(link).toBeVisible();
  });

  test('Tactical Legacy card links to tactical_legacy.html', async ({ page }) => {
    const link = page.locator('a[href*="tactical_legacy"]');
    await expect(link).toBeVisible();
  });

  test('Dataset Viewer card is present', async ({ page }) => {
    await expect(page.locator('a[href*="dataset_viewer"]')).toBeVisible();
  });

  test('sys-bar shows system info', async ({ page }) => {
    const sysBar = page.locator('.sys-bar');
    await expect(sysBar).toBeVisible();
    await expect(sysBar).toContainText(/CORTEX-1/i);
  });
});
