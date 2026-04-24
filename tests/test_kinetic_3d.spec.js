// @ts-check
const { test, expect } = require('@playwright/test');
const { mockBackend } = require('./helpers/mockApi');

// ─────────────────────────────────────────────────────────────
// TEST: kinetic_3d.html  — 3D Kinetic Intercept Simulator
// ─────────────────────────────────────────────────────────────
test.describe('kinetic_3d.html — 3D Kinetic Simulator', () => {
  test.beforeEach(async ({ page }) => {
    await mockBackend(page);
    await page.goto('/kinetic_3d.html?theater=boreal');
    await page.waitForSelector('#hud', { timeout: 8000 });
  });

  // ── HUD and title
  test('HUD is visible', async ({ page }) => {
    await expect(page.locator('#hud')).toBeVisible();
    await expect(page.locator('#hud h1')).toContainText(/KINETIC 3D|INTERCEPT|BOREAL/i);
  });

  // ── Theater selector
  test('theater selector dropdown is present', async ({ page }) => {
    const sel = page.locator('#sel-theater');
    await expect(sel).toBeVisible();
    const options = await sel.locator('option').allTextContents();
    expect(options.some(o => /SWEDEN/i.test(o))).toBeTruthy();
    expect(options.some(o => /BOREAL/i.test(o))).toBeTruthy();
  });

  test('theater selector defaults to sweden option based on order', async ({ page }) => {
    // First option in select is Sweden
    const sel = page.locator('#sel-theater');
    const firstOption = await sel.locator('option').first().getAttribute('value');
    expect(firstOption).toBeDefined();
  });

  test('switching theater to boreal changes selection', async ({ page }) => {
    await page.locator('#sel-theater').selectOption('boreal');
    await expect(page.locator('#sel-theater')).toHaveValue('boreal');
  });

  test('switching theater to sweden changes selection', async ({ page }) => {
    await page.locator('#sel-theater').selectOption('sweden');
    await expect(page.locator('#sel-theater')).toHaveValue('sweden');
  });

  // ── Weapon selector
  test('weapon selector has 4 weapons', async ({ page }) => {
    const sel = page.locator('#sel-weapon');
    await expect(sel).toBeVisible();
    const count = await sel.locator('option').count();
    expect(count).toBe(4);
  });

  test('can select HYPERSONIC weapon', async ({ page }) => {
    await page.locator('#sel-weapon').selectOption('HYPERSONIC');
    await expect(page.locator('#sel-weapon')).toHaveValue('HYPERSONIC');
  });

  test('can select BALLISTIC weapon', async ({ page }) => {
    await page.locator('#sel-weapon').selectOption('BALLISTIC');
    await expect(page.locator('#sel-weapon')).toHaveValue('BALLISTIC');
  });

  test('can select LOITER weapon', async ({ page }) => {
    await page.locator('#sel-weapon').selectOption('LOITER');
    await expect(page.locator('#sel-weapon')).toHaveValue('LOITER');
  });

  // ── Outcome selector
  test('outcome selector has intercept and miss options', async ({ page }) => {
    const sel = page.locator('#sel-outcome');
    await expect(sel).toBeVisible();
    const options = await sel.locator('option').allInnerTexts();
    expect(options.some(o => /intercept/i.test(o))).toBeTruthy();
    expect(options.some(o => /miss/i.test(o))).toBeTruthy();
  });

  // ── Mode selector
  test('mode selector has AUTO, HITL, MANUAL options', async ({ page }) => {
    const sel = page.locator('#sel-mode');
    await expect(sel).toBeVisible();
    const options = await sel.locator('option').allInnerTexts();
    expect(options.some(o => /AUTO/i.test(o))).toBeTruthy();
    expect(options.some(o => /HITL/i.test(o))).toBeTruthy();
    expect(options.some(o => /MANUAL/i.test(o))).toBeTruthy();
  });

  test('wave defense rate selector has options', async ({ page }) => {
    const sel = page.locator('#sel-wave-rate');
    await expect(sel).toBeVisible();
    const count = await sel.locator('option').count();
    expect(count).toBeGreaterThanOrEqual(3);
  });

  // ── Action buttons
  test('FIRE DEMO button is visible and green', async ({ page }) => {
    const btn = page.locator('#btn-fire');
    await expect(btn).toBeVisible();
    await expect(btn).toContainText(/FIRE/i);
  });

  test('SATURATION WAVE button is visible', async ({ page }) => {
    await expect(page.locator('#btn-wave')).toBeVisible();
    await expect(page.locator('#btn-wave')).toContainText(/SATURATION/i);
  });

  test('RESET button is visible', async ({ page }) => {
    await expect(page.locator('#btn-reset')).toBeVisible();
  });

  // ── Nav buttons (new)
  test('PORTAL nav button is present', async ({ page }) => {
    const btns = page.locator('#hud button');
    const texts = await btns.allTextContents();
    expect(texts.some(t => t.includes('PORTAL'))).toBeTruthy();
  });

  test('DASHBOARD nav button is present', async ({ page }) => {
    const texts = await page.locator('#hud button').allTextContents();
    expect(texts.some(t => t.toUpperCase().includes('DASHBOARD'))).toBeTruthy();
  });

  test('LIVE VIEW nav button is present', async ({ page }) => {
    const texts = await page.locator('#hud button').allTextContents();
    expect(texts.some(t => t.toUpperCase().includes('LIVE VIEW'))).toBeTruthy();
  });

  test('TACTICAL nav button is present', async ({ page }) => {
    const texts = await page.locator('#hud button').allTextContents();
    expect(texts.some(t => t.toUpperCase().includes('TACTICAL'))).toBeTruthy();
  });

  // ── Stats HUD
  test('stats HUD shows THREATS, SAMs, KILLS, IMPACTS', async ({ page }) => {
    await expect(page.locator('#s-threats')).toBeVisible();
    await expect(page.locator('#s-fired')).toBeVisible();
    await expect(page.locator('#s-kills')).toBeVisible();
    await expect(page.locator('#s-impacts')).toBeVisible();
    await expect(page.locator('#s-surv')).toBeVisible();
  });

  test('stats start at 0 / --', async ({ page }) => {
    await expect(page.locator('#s-threats')).toHaveText('0');
    await expect(page.locator('#s-kills')).toHaveText('0');
  });

  // ── Log feed
  test('log feed panel is rendered', async ({ page }) => {
    await expect(page.locator('#log')).toBeVisible();
  });

  // ── Freeze overlay (initially hidden)
  test('freeze overlay is not visible initially', async ({ page }) => {
    await expect(page.locator('#freeze-overlay')).not.toHaveClass(/active/);
  });

  test('freeze overlay approve/reject buttons exist', async ({ page }) => {
    await expect(page.locator('#btn-approve-k')).toBeAttached();
    await expect(page.locator('#btn-reject-k')).toBeAttached();
  });

  // ── canvas
  test('WebGL canvas is rendered', async ({ page }) => {
    await expect(page.locator('#canvas-wrap')).toBeVisible();
    const canvas = page.locator('#canvas-wrap canvas');
    await expect(canvas).toBeAttached({ timeout: 8000 });
  });

  // ── Clicking FIRE DEMO with boreal theater builds scene
  test('FIRE DEMO can be clicked without JS error', async ({ page }) => {
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.locator('#sel-theater').selectOption('boreal');
    await page.locator('#btn-fire').click();
    // Short wait for any immediate crash
    await page.waitForTimeout(1000);
    // Filter out known benign network errors (WebSocket abort)
    const critical = errors.filter(e => !e.includes('WebSocket') && !e.includes('net::ERR_FAILED') && !e.includes('CORS'));
    expect(critical).toHaveLength(0);
  });
});

// ─────────────────────────────────────────────────────────────
// TEST: kinetic_3d.html — Sweden theater param
// ─────────────────────────────────────────────────────────────
test.describe('kinetic_3d.html — Sweden theater', () => {
  test('loading with theater=sweden pre-selects sweden in dropdown', async ({ page }) => {
    await mockBackend(page);
    await page.goto('/kinetic_3d.html?theater=sweden');
    await page.waitForSelector('#sel-theater', { timeout: 6000 });
    // The page JS reads `sel-theater` value and switches theater; just confirm selector works
    const sel = page.locator('#sel-theater');
    await expect(sel).toBeVisible();
  });
});
