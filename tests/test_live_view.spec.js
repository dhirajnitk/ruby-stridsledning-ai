// @ts-check
const { test, expect } = require('@playwright/test');
const { mockBackend } = require('./helpers/mockApi');

// ─────────────────────────────────────────────────────────────
// TEST: live_view.html  — Live Kinetic Audit
// ─────────────────────────────────────────────────────────────
test.describe('live_view.html — Live Kinetic View (boreal)', () => {
  test.beforeEach(async ({ page }) => {
    await mockBackend(page);
    await page.goto('/live_view.html?mode=boreal');
    await page.waitForSelector('#base-list', { timeout: 8000 });
    // Wait for THEATER_DATA to populate base cards
    await page.waitForFunction(
      () => document.querySelectorAll('.base-card').length > 0,
      { timeout: 10000 }
    );
  });

  // ── Structure
  test('base panel header is visible', async ({ page }) => {
    await expect(page.locator('#base-panel-header h3')).toBeVisible();
    await expect(page.locator('#base-panel-header h3')).toContainText(/FORTRESS HUB|REGISTRY/i);
  });

  test('base cards are rendered (boreal has 12 nodes)', async ({ page }) => {
    const cards = page.locator('.base-card');
    const count = await cards.count();
    expect(count).toBeGreaterThanOrEqual(10);
  });

  test('at least one HVA base card is rendered', async ({ page }) => {
    const hvaCards = page.locator('.base-card.hva');
    const count = await hvaCards.count();
    expect(count).toBeGreaterThan(0);
  });

  test('clicking a base card marks it active', async ({ page }) => {
    const firstCard = page.locator('.base-card').first();
    await firstCard.click();
    await expect(firstCard).toHaveClass(/active/);
  });

  test('clicking base card updates sel-label text', async ({ page }) => {
    const firstCard = page.locator('.base-card').first();
    await firstCard.click();
    await expect(page.locator('#sel-label')).not.toContainText('SELECT A BASE', { timeout: 3000 });
  });

  test('clicking base card updates lv-base-info', async ({ page }) => {
    const firstCard = page.locator('.base-card').first();
    await firstCard.click();
    await expect(page.locator('#lv-base-info')).not.toContainText('CLICK A BASE TO BEGIN', { timeout: 3000 });
  });

  // ── Weapon selector
  test('weapon selector dropdown is present with 5 options (including random)', async ({ page }) => {
    const sel = page.locator('#lv-sel-weapon');
    await expect(sel).toBeVisible();
    const count = await sel.locator('option').count();
    expect(count).toBe(5); // random + 4 types
  });

  test('can select HYPERSONIC weapon', async ({ page }) => {
    await page.locator('#lv-sel-weapon').selectOption('HYPERSONIC');
    await expect(page.locator('#lv-sel-weapon')).toHaveValue('HYPERSONIC');
  });

  test('can select CRUISE MISSILE weapon', async ({ page }) => {
    await page.locator('#lv-sel-weapon').selectOption('CRUISE');
    await expect(page.locator('#lv-sel-weapon')).toHaveValue('CRUISE');
  });

  // ── Control buttons
  test('SATURATION WAVE button is visible', async ({ page }) => {
    await expect(page.locator('#btn-lv-saturation')).toBeVisible();
    await expect(page.locator('#btn-lv-saturation')).toContainText(/SATURATION/i);
  });

  test('CLEAR THEATRE button is visible', async ({ page }) => {
    await expect(page.locator('#btn-reset')).toBeVisible();
  });

  // ── Nav buttons
  test('DASHBOARD back button is present and links to dashboard', async ({ page }) => {
    const btn = page.locator('#btn-back');
    await expect(btn).toBeVisible();
    await expect(btn).toContainText(/DASHBOARD/i);
  });

  test('3D KINETIC button is present', async ({ page }) => {
    const btns = page.locator('button');
    const texts = await btns.allTextContents();
    const has3d = texts.some(t => t.includes('3D KINETIC') || t.includes('KINETIC'));
    expect(has3d).toBeTruthy();
  });

  test('TACTICAL nav button is present', async ({ page }) => {
    const btns = page.locator('button');
    const texts = await btns.allTextContents();
    expect(texts.some(t => t.includes('TACTICAL'))).toBeTruthy();
  });

  test('PORTAL nav button is present', async ({ page }) => {
    const btns = page.locator('button');
    const texts = await btns.allTextContents();
    expect(texts.some(t => t.includes('PORTAL'))).toBeTruthy();
  });

  // ── 3D canvas
  test('canvas container is present', async ({ page }) => {
    await expect(page.locator('#canvas-container')).toBeVisible();
  });

  // ── CoT feed
  test('CoT feed panel is visible', async ({ page }) => {
    await expect(page.locator('#cot-panel')).toBeVisible();
    await expect(page.locator('#cot-feed')).toBeVisible();
  });

  test('CoT feed has initial info message', async ({ page }) => {
    await expect(page.locator('#cot-feed')).toContainText(/primed|demo|base|intercept/i);
  });

  // ── Weapon legend
  test('weapon legend is rendered with 5 entries', async ({ page }) => {
    const items = page.locator('.wl-item');
    const count = await items.count();
    expect(count).toBe(5);
  });

  // ── View header
  test('view header shows LIVE KINETIC AUDIT', async ({ page }) => {
    await expect(page.locator('#view-header .vtitle')).toContainText(/LIVE KINETIC AUDIT/i);
  });

  test('active model label renders in header', async ({ page }) => {
    await expect(page.locator('#lv-active-model')).toBeAttached();
  });
});

// ─────────────────────────────────────────────────────────────
// TEST: live_view.html — Sweden mode
// ─────────────────────────────────────────────────────────────
test.describe('live_view.html — Sweden theater mode', () => {
  test.beforeEach(async ({ page }) => {
    await mockBackend(page);
    await page.goto('/live_view.html?mode=sweden');
    await page.waitForFunction(
      () => document.querySelectorAll('.base-card').length > 0,
      { timeout: 10000 }
    );
  });

  test('Sweden mode: base cards include Stockholm', async ({ page }) => {
    const texts = await page.locator('.base-card .bc-name').allTextContents();
    const hasStockholm = texts.some(t => t.toUpperCase().includes('STOCKHOLM'));
    expect(hasStockholm).toBeTruthy();
  });

  test('BACK button href contains mode=sweden', async ({ page }) => {
    const btn = page.locator('#btn-back');
    const onclick = await btn.getAttribute('onclick');
    expect(onclick).toContain('MODE');
  });
});
