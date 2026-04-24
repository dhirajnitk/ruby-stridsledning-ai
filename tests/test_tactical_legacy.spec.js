// @ts-check
const { test, expect } = require('@playwright/test');
const { mockBackend } = require('./helpers/mockApi');

// ─────────────────────────────────────────────────────────────
// TEST: tactical_legacy.html  — Legacy Tactical Display
// ─────────────────────────────────────────────────────────────
test.describe('tactical_legacy.html — Legacy Tactical (boreal)', () => {
  test.beforeEach(async ({ page }) => {
    await mockBackend(page);
    await page.goto('/tactical_legacy.html?mode=boreal');
    await page.waitForSelector('#radarCanvas', { timeout: 6000 });
  });

  // ── Page structure
  test('page has tactical canvas', async ({ page }) => {
    await expect(page.locator('#radarCanvas')).toBeVisible();
  });

  test('theater title shows BOREAL CHESSMASTER by default', async ({ page }) => {
    await expect(page.locator('#theater-title')).toContainText(/BOREAL CHESSMASTER/i);
  });

  // ── Doctrine selectors — primary has all 6 options
  test('primary-doctrine has 6 options', async ({ page }) => {
    const count = await page.locator('#primary-doctrine option').count();
    expect(count).toBe(6);
  });

  test('primary-doctrine options include ECONOMY, AMBUSH, SATURATION', async ({ page }) => {
    const options = await page.locator('#primary-doctrine option').allTextContents();
    const vals = options.map(o => o.toUpperCase());
    expect(vals).toContain('ECONOMY');
    expect(vals).toContain('AMBUSH');
    expect(vals).toContain('SATURATION');
  });

  // ── Secondary doctrine — 7 options (NONE + 6)
  test('secondary-doctrine has 7 options (NONE + 6 doctrines)', async ({ page }) => {
    const count = await page.locator('#secondary-doctrine option').count();
    expect(count).toBe(7);
  });

  test('secondary-doctrine contains ECONOMY, AMBUSH, SATURATION', async ({ page }) => {
    const options = await page.locator('#secondary-doctrine option').allTextContents();
    const vals = options.map(o => o.toUpperCase());
    expect(vals).toContain('ECONOMY');
    expect(vals).toContain('AMBUSH');
    expect(vals).toContain('SATURATION');
  });

  test('can select ECONOMY as primary doctrine', async ({ page }) => {
    await page.locator('#primary-doctrine').selectOption('economy');
    await expect(page.locator('#primary-doctrine')).toHaveValue('economy');
  });

  test('can select SATURATION as secondary doctrine', async ({ page }) => {
    await page.locator('#secondary-doctrine').selectOption('saturation');
    await expect(page.locator('#secondary-doctrine')).toHaveValue('saturation');
  });

  // ── Blend ratio slider
  test('blend-ratio slider exists with default 70', async ({ page }) => {
    const slider = page.locator('#blend-ratio');
    await expect(slider).toBeVisible();
    await expect(slider).toHaveValue('70');
  });

  test('blend-pct label reflects slider value', async ({ page }) => {
    await expect(page.locator('#blend-pct')).toContainText('70');
  });

  test('moving blend slider updates blend-pct display', async ({ page }) => {
    const slider = page.locator('#blend-ratio');
    // Set value via JS and fire input event
    await slider.evaluate(el => {
      el.value = '40';
      el.dispatchEvent(new Event('input'));
    });
    await expect(page.locator('#blend-pct')).toContainText('40');
  });

  // ── Model selector
  test('model-select dropdown is present with 9 options', async ({ page }) => {
    const sel = page.locator('#model-select');
    await expect(sel).toBeVisible();
    const count = await sel.locator('option').count();
    expect(count).toBe(9);
  });

  test('model selector includes ELITE V3.5 option', async ({ page }) => {
    const options = await page.locator('#model-select option').allTextContents();
    const hasElite = options.some(o => o.toUpperCase().includes('ELITE'));
    expect(hasElite).toBeTruthy();
  });

  test('can select supreme3 model', async ({ page }) => {
    await page.locator('#model-select').selectOption('supreme3');
    await expect(page.locator('#model-select')).toHaveValue('supreme3');
  });

  // ── Toggle checkboxes
  test('NEURAL checkbox is checked by default', async ({ page }) => {
    await expect(page.locator('#use-rl')).toBeChecked();
  });

  test('AUTO poll checkbox is checked by default', async ({ page }) => {
    await expect(page.locator('#auto-poll')).toBeChecked();
  });

  test('can toggle DYNAMIC HITL checkbox', async ({ page }) => {
    const cb = page.locator('#dynamic-hitl');
    await expect(cb).not.toBeChecked();
    await cb.check();
    await expect(cb).toBeChecked();
    await cb.uncheck();
    await expect(cb).not.toBeChecked();
  });

  test('can toggle OVERRIDE checkbox', async ({ page }) => {
    await page.locator('#manual-override').check();
    await expect(page.locator('#manual-override')).toBeChecked();
  });

  // ── Action buttons
  test('Spawn, Ambush, Execute AI buttons are visible', async ({ page }) => {
    await expect(page.locator('#btn-threat')).toBeVisible();
    await expect(page.locator('#btn-blind')).toBeVisible();
    await expect(page.locator('#btn-ai')).toBeVisible();
  });

  test('3D VIEW button is visible and links to strategic_3d.html', async ({ page }) => {
    const btn = page.locator('#btn-3d');
    await expect(btn).toBeVisible();
    const onclick = await btn.getAttribute('onclick');
    expect(onclick).toContain('strategic_3d.html');
  });

  test('DATA DNA button is visible', async ({ page }) => {
    await expect(page.locator('#btn-dna')).toBeVisible();
  });

  // ── Nav buttons (all 5 new)
  test('DASHBOARD nav button is present', async ({ page }) => {
    await expect(page.locator('#btn-nav-dash')).toBeVisible();
  });

  test('CORTEX-C2 nav button is present', async ({ page }) => {
    await expect(page.locator('#btn-nav-c2')).toBeVisible();
  });

  test('LIVE VIEW nav button is present', async ({ page }) => {
    await expect(page.locator('#btn-nav-live')).toBeVisible();
  });

  test('KINETIC 3D nav button is present', async ({ page }) => {
    await expect(page.locator('#btn-nav-3dk')).toBeVisible();
  });

  test('PORTAL nav button is present', async ({ page }) => {
    await expect(page.locator('#btn-nav-portal')).toBeVisible();
  });

  // ── SITREP panel
  test('active-posture-label panel renders', async ({ page }) => {
    await expect(page.locator('#active-posture-label')).toBeVisible();
  });

  test('ENGINE TRACE panel renders', async ({ page }) => {
    await expect(page.locator('#ws-output')).toBeVisible();
  });

  test('ws-output shows initial connecting message', async ({ page }) => {
    await expect(page.locator('#ws-output')).toContainText(/Connecting|Neural uplink|SYSTEM/i, { timeout: 4000 });
  });

  // ── Spawn threat on canvas
  test('clicking Spawn button adds a threat and canvas remains visible', async ({ page }) => {
    await page.locator('#btn-threat').click();
    await expect(page.locator('#radarCanvas')).toBeVisible();
  });

  // ── Execute AI fires evaluate_advanced and updates policy-status (mocked)
  test('Execute AI button triggers evaluate and updates policy-status', async ({ page }) => {
    await page.locator('#btn-threat').click(); // spawn one threat first
    await page.locator('#btn-ai').click();
    // policy-status should be updated by the handler after response
    await expect(page.locator('#policy-status')).not.toContainText('STANDBY', { timeout: 8000 });
  });
});

// ─────────────────────────────────────────────────────────────
// TEST: tactical_legacy.html — Sweden mode
// ─────────────────────────────────────────────────────────────
test.describe('tactical_legacy.html — Sweden theater mode', () => {
  test.beforeEach(async ({ page }) => {
    await mockBackend(page);
    await page.goto('/tactical_legacy.html?mode=sweden');
    await page.waitForSelector('#radarCanvas', { timeout: 6000 });
  });

  test('theater title shows SWEDEN AOR', async ({ page }) => {
    await expect(page.locator('#theater-title')).toContainText(/SWEDEN AOR/i);
  });

  test('canvas height is 900 for Sweden', async ({ page }) => {
    const h = await page.locator('#radarCanvas').evaluate(el => el.height);
    expect(h).toBe(900);
  });

  test('nav DASHBOARD button onclick navigates with mode param', async ({ page }) => {
    // The IIFE closes over _m variable. Verify the function navigates to dashboard with mode param
    const btn = page.locator('#btn-nav-dash');
    const onclickFn = await btn.evaluate(el => el.onclick?.toString() || '');
    // Function uses _m var: "window.location.href = 'dashboard.html?mode=' + _m"
    expect(onclickFn).toContain('dashboard.html?mode=');
  });
});
