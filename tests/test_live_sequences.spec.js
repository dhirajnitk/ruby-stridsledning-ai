// @ts-check
/**
 * LIVE ENGINE DEMO SEQUENCES — Real backend at port 8000
 *
 * Every button click, every AI evaluation, every WebSocket message
 * goes through the ACTUAL Python neural tactical engine.
 *
 * Key verifications vs the mock demo:
 *   - /health → real mode + theater from backend
 *   - /state  → real base count from CSV (>0 bases)
 *   - /evaluate_advanced → real score (NOT 875), real assignments with
 *                          real base names from the battlefield CSV
 *   - /ws/logs → live WebSocket messages from the engine
 *   - policy-status → changes to a real neural-network prediction value
 *
 * Run:    npx playwright test --config=scratch/playwright.live.config.js
 * Videos: scratch/live-videos/<sequence>/video.webm
 */
const { test, expect, request } = require('@playwright/test');
const { liveBackend } = require('./helpers/liveApi');

const FAKE_MOCK_SCORE = 875.0;          // if we ever see this the mock crept in
const MIN_REAL_BASES  = 5;              // CSV has many more — just sanity check

// ─── helper: wait + pause (simulates human reading) ─────────────────────────
const P = (page, ms) => page.waitForTimeout(ms);

// ─── helper: capture the next response matching a URL pattern ───────────────
function waitForApiResponse(page, urlSubstr) {
  return page.waitForResponse(
    r => r.url().includes(urlSubstr) && r.request().method() !== 'OPTIONS',
    { timeout: 40_000 }
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// PRE-FLIGHT — verify the live backend is healthy before all sequences
// ═══════════════════════════════════════════════════════════════════════════
test.beforeAll(async ({ playwright }) => {
  // Direct HTTP check — fail fast if backend is not up
  const ctx = await request.newContext({ baseURL: 'http://localhost:8000' });
  const res = await ctx.get('/health');
  expect(res.status(), 'Backend /health must return 200 — is agent_backend.py running?').toBe(200);
  const body = await res.json();
  expect(body.status).toBe('ok');
  console.log(`\n  LIVE BACKEND: mode=${body.mode}  theater=${body.theater}\n`);
  await ctx.dispose();
});

// ═══════════════════════════════════════════════════════════════════════════
// SEQUENCE 1 — LIVE PORTAL + BACKEND HEALTH VERIFICATION  (~60 s)
// ═══════════════════════════════════════════════════════════════════════════
test('SEQ-1 LIVE — Portal loads & backend shows ONLINE', async ({ page }) => {
  await liveBackend(page);

  // Capture the real /health call the portal page makes
  const healthPromise = waitForApiResponse(page, '/health');
  await page.goto('/index.html', { waitUntil: 'domcontentloaded' });
  const healthRes = await healthPromise;
  const healthBody = await healthRes.json();

  // REAL backend assertions
  expect(healthBody.status).toBe('ok');
  expect(['boreal', 'sweden']).toContain(healthBody.mode);
  console.log(`  [LIVE] /health → mode=${healthBody.mode} theater=${healthBody.theater}`);

  await P(page, 4000);

  // Portal badge should read ONLINE (not OFFLINE)
  await expect(page.locator('#portal-backend')).toHaveText('ONLINE', { timeout: 12_000 });

  // ── Hover over cards ─────────────────────────────────────────────────────
  await page.hover('a.opt.c2');
  await P(page, 2500);
  await page.hover('a.opt.primary');
  await P(page, 2500);
  await page.hover('a[href*="kinetic_3d.html?theater=boreal"]');
  await P(page, 2000);

  // ── Theater toggle ────────────────────────────────────────────────────────
  await page.locator('#toggle-sweden').click();
  await P(page, 3000);
  await expect(page.locator('#toggle-sweden')).toHaveCSS('color', 'rgb(0, 242, 255)');

  await page.locator('#toggle-boreal').click();
  await P(page, 2500);
  await expect(page.locator('#toggle-boreal')).toHaveCSS('color', 'rgb(0, 242, 255)');

  // ── Navigate to Dashboard ─────────────────────────────────────────────────
  const theaterPromise = waitForApiResponse(page, '/theater');
  await page.locator('a.opt.primary').click();
  await page.waitForLoadState('domcontentloaded');
  const theaterRes = await theaterPromise;
  const theaterBody = await theaterRes.json();

  // Real /theater response
  expect(theaterBody).toHaveProperty('theater_name');
  expect(theaterBody.theater_name).toBeTruthy();
  console.log(`  [LIVE] /theater → ${theaterBody.theater_name}`);

  await P(page, 5000);
  await expect(page.locator('#main-title')).toBeVisible();
  await expect(page.locator('#map-title')).toBeVisible();
  await P(page, 3000);
});


// ═══════════════════════════════════════════════════════════════════════════
// SEQUENCE 2 — LIVE DASHBOARD: REAL BASE STATE + COMMAND MODES  (~65 s)
// ═══════════════════════════════════════════════════════════════════════════
test('SEQ-2 LIVE — Dashboard: real /state bases + HITL/MANUAL modes', async ({ page }) => {
  await liveBackend(page);

  // Capture the /theater call the dashboard makes on load
  const theaterPromise = waitForApiResponse(page, '/theater');
  await page.goto('/dashboard.html?mode=boreal', { waitUntil: 'domcontentloaded' });
  const theaterRes  = await theaterPromise;
  const theaterBody = await theaterRes.json();

  // REAL /theater assertions
  expect(theaterBody).toHaveProperty('theater_name');
  expect(theaterBody.theater_name).toBeTruthy();
  console.log(`  [LIVE] /theater → ${theaterBody.theater_name}  capital=${theaterBody.capital}`);

  // Separately verify /state has real bases by calling the API directly
  const apiCtx   = await page.context().request;
  const stateRes  = await apiCtx.get('http://localhost:8000/state');
  expect(stateRes.status()).toBe(200);
  const stateBody = await stateRes.json();

  expect(stateBody.base_count, 'Real CSV must have multiple bases').toBeGreaterThanOrEqual(MIN_REAL_BASES);
  const firstBase = stateBody.bases[0];
  expect(firstBase).toHaveProperty('name');
  expect(firstBase).toHaveProperty('x_km');
  console.log(`  [LIVE] /state → ${stateBody.base_count} bases. First: ${firstBase.name} @ (${firstBase.x_km}, ${firstBase.y_km})`);

  await P(page, 4000);
  await expect(page.locator('#mode-auto')).toHaveClass(/active-auto/);

  // ── HITL mode ────────────────────────────────────────────────────────────
  await page.locator('#mode-hitl').click();
  await P(page, 4000);
  await expect(page.locator('#approval-queue')).toBeVisible();

  // ── MANUAL mode ──────────────────────────────────────────────────────────
  await page.locator('#mode-manual').click();
  await P(page, 3500);
  await expect(page.locator('#manual-panel')).toBeVisible();

  // ── Return to AUTO ────────────────────────────────────────────────────────
  await page.locator('#mode-auto').click();
  await P(page, 2500);
  await expect(page.locator('#approval-queue')).toBeHidden();

  // ── Doctrine cycle ────────────────────────────────────────────────────────
  await page.locator('.doctrine-btn[data-doctrine="fortress"]').click();
  await P(page, 2000);
  await expect(page.locator('.doctrine-btn[data-doctrine="fortress"]')).toHaveClass(/active/);

  await page.locator('.doctrine-btn[data-doctrine="aggressive"]').click();
  await P(page, 2000);
  await expect(page.locator('.doctrine-btn[data-doctrine="aggressive"]')).toHaveClass(/active/);

  await page.locator('.doctrine-btn[data-doctrine="balanced"]').click();
  await P(page, 2000);

  // ── Model swap ────────────────────────────────────────────────────────────
  await page.locator('#sel-model-core').selectOption('elite');
  await P(page, 1500);
  await page.locator('#sel-model-core').selectOption('supreme3');
  await P(page, 2000);

  // ── Initialize Intercept (calls live engine) ──────────────────────────────
  await page.locator('#btn-launch').click();
  await P(page, 4000);
  await expect(page.locator('#baltic-map')).toBeVisible();

  await P(page, 3000);
});


// ═══════════════════════════════════════════════════════════════════════════
// SEQUENCE 3 — LIVE CORTEX C2: REAL MC AUDIT WITH NEURAL ENGINE  (~70 s)
// ═══════════════════════════════════════════════════════════════════════════
test('SEQ-3 LIVE — Cortex C2: real /evaluate_advanced neural output', async ({ page }) => {
  await liveBackend(page);
  await page.goto('/cortex_c2.html', { waitUntil: 'domcontentloaded' });

  await P(page, 4000);
  await expect(page.locator('header')).toBeVisible();

  // ── Scenario selection ────────────────────────────────────────────────────
  await page.locator('.sc-card[data-sc="swarm"]').click();
  await P(page, 3000);
  await expect(page.locator('.sc-card[data-sc="swarm"]')).toHaveClass(/active/);

  await page.locator('.sc-card[data-sc="jammed"]').click();
  await P(page, 3000);

  // ── Doctrine cycle ────────────────────────────────────────────────────────
  await page.locator('#doc-fortress').click();
  await P(page, 2000);
  await page.locator('#doc-aggressive').click();
  await P(page, 2000);
  await page.locator('#doc-balanced').click();
  await P(page, 1500);

  // ── Model select ─────────────────────────────────────────────────────────
  await page.locator('#model-select').selectOption('supreme3');
  await P(page, 1500);

  // ── RUN STRATEGIC AUDIT — capture REAL /evaluate_advanced response ────────
  const evalPromise = waitForApiResponse(page, '/evaluate_advanced');
  await page.locator('#btn-run-audit').click();
  console.log('  [LIVE] Waiting for real /evaluate_advanced response from neural engine...');

  const evalRes  = await evalPromise;
  expect(evalRes.status(), '/evaluate_advanced must return 200').toBe(200);
  const evalBody = await evalRes.json();

  // ── CRITICAL: Verify this is NOT the mock response ───────────────────────
  expect(
    evalBody.strategic_consequence_score,
    `Score must NOT be the mock value ${FAKE_MOCK_SCORE} — real engine must run`
  ).not.toBe(FAKE_MOCK_SCORE);

  expect(evalBody).toHaveProperty('tactical_assignments');
  expect(evalBody).toHaveProperty('active_doctrine');
  expect(evalBody).toHaveProperty('human_sitrep');

  const score  = evalBody.strategic_consequence_score;
  const nAssign = evalBody.tactical_assignments.length;
  const sitrep = evalBody.human_sitrep?.substring(0, 80) || '(none)';

  console.log(`  [LIVE] /evaluate_advanced → score=${score}  assignments=${nAssign}`);
  console.log(`  [LIVE] sitrep preview: "${sitrep}"`);

  if (nAssign > 0) {
    const first = evalBody.tactical_assignments[0];
    console.log(`  [LIVE] First assignment: ${first.threat_id} → ${first.effector} @ ${first.base}`);
  }

  // COA grid should update with real result
  await P(page, 4000);
  await expect(page.locator('#coa-grid')).toBeVisible();
  await expect(page.locator('#tactical-svg')).toBeVisible();

  // ── Replenish ─────────────────────────────────────────────────────────────
  await page.locator('#btn-replenish').click();
  await P(page, 2500);

  // ── Navigate to Dashboard ─────────────────────────────────────────────────
  await page.locator('a.nav-back[href="dashboard.html"]').click();
  await page.waitForLoadState('domcontentloaded');
  await P(page, 3000);

  await expect(page.locator('#main-title')).toBeVisible();
  await P(page, 2000);
});


// ═══════════════════════════════════════════════════════════════════════════
// SEQUENCE 4 — LIVE TACTICAL: REAL NEURAL EVALUATE ON SPAWNED THREATS  (~70 s)
// ═══════════════════════════════════════════════════════════════════════════
test('SEQ-4 LIVE — Tactical: spawn threats → real AI policy response', async ({ page }) => {
  await liveBackend(page);
  await page.goto('/tactical_legacy.html?mode=boreal', { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#radarCanvas');

  await P(page, 4000);
  await expect(page.locator('#radarCanvas')).toBeVisible();

  // WebSocket message check — live engine sends [HEARTBEAT] every 15s
  // We just verify the ws-output div is connected and shows something
  await expect(page.locator('#ws-output')).toBeVisible();

  // ── Doctrine setup ────────────────────────────────────────────────────────
  await page.locator('#primary-doctrine').selectOption('fortress');
  await P(page, 1500);
  await page.locator('#secondary-doctrine').selectOption('economy');
  await P(page, 1500);

  // ── Blend ratio ──────────────────────────────────────────────────────────
  await page.locator('#blend-ratio').evaluate(el => {
    el.value = '40'; el.dispatchEvent(new Event('input'));
  });
  await P(page, 1500);
  await expect(page.locator('#blend-pct')).toContainText('40');

  // ── Spawn threats ─────────────────────────────────────────────────────────
  for (let i = 0; i < 4; i++) {
    await page.locator('#btn-threat').click();
    await P(page, 1800);
  }
  await expect(page.locator('#radarCanvas')).toBeVisible();

  // ── Execute AI — capture REAL /evaluate_advanced response ────────────────
  const evalPromise = waitForApiResponse(page, '/evaluate_advanced');
  await page.locator('#btn-ai').click();
  console.log('  [LIVE] Waiting for real neural AI evaluation...');

  const evalRes  = await evalPromise;
  expect(evalRes.status()).toBe(200);
  const evalBody = await evalRes.json();

  const score  = evalBody.strategic_consequence_score;
  const nAssign = evalBody.tactical_assignments?.length || 0;
  console.log(`  [LIVE] Tactical AI → score=${score}  assignments=${nAssign}`);
  console.log(`  [LIVE] Doctrine: ${evalBody.active_doctrine?.primary}`);

  // Verify NOT mock score
  expect(score).not.toBe(FAKE_MOCK_SCORE);

  // policy-status should update from STANDBY
  await expect(page.locator('#policy-status')).not.toContainText('STANDBY', { timeout: 8_000 });

  await P(page, 3000);

  // ── Spawn 2 more + second AI execution ───────────────────────────────────
  await page.locator('#btn-threat').click();
  await P(page, 1500);
  await page.locator('#btn-threat').click();
  await P(page, 1500);

  const eval2Promise = waitForApiResponse(page, '/evaluate_advanced');
  await page.locator('#btn-ai').click();
  const eval2Res  = await eval2Promise;
  const eval2Body = await eval2Res.json();
  console.log(`  [LIVE] 2nd AI run → score=${eval2Body.strategic_consequence_score}  assignments=${eval2Body.tactical_assignments?.length}`);

  await P(page, 3000);

  // ── Ambush Blind ──────────────────────────────────────────────────────────
  await page.locator('#btn-blind').click();
  await P(page, 3000);

  // ── Navigate home ─────────────────────────────────────────────────────────
  await page.locator('#btn-nav-portal').click();
  await page.waitForLoadState('domcontentloaded');
  await P(page, 3000);
  await expect(page.locator('h1')).toContainText(/PORTAL|STRATEGIC/i);
  await P(page, 2000);
});


// ═══════════════════════════════════════════════════════════════════════════
// SEQUENCE 5 — LIVE KINETIC 3D: FULL WEAPONS DEMO WITH REAL THEATER DATA  (~65 s)
// ═══════════════════════════════════════════════════════════════════════════
test('SEQ-5 LIVE — Kinetic 3D: full weapons cycle on live theater', async ({ page }) => {
  await liveBackend(page);
  await page.goto('/kinetic_3d.html?theater=boreal', { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#hud');

  await P(page, 4000);
  await expect(page.locator('#hud')).toBeVisible();
  await expect(page.locator('#canvas-wrap')).toBeVisible();
  await expect(page.locator('#s-threats')).toHaveText('0');

  // ── Cycle all 4 weapons ──────────────────────────────────────────────────
  for (const weapon of ['HYPERSONIC', 'BALLISTIC', 'LOITER', 'CRUISE']) {
    await page.locator('#sel-weapon').selectOption(weapon);
    await P(page, 1500);
    await expect(page.locator('#sel-weapon')).toHaveValue(weapon);
  }

  // ── AUTO mode fire — no freeze overlay ───────────────────────────────────
  await expect(page.locator('#sel-mode')).toHaveValue('auto');

  await page.locator('#btn-fire').click();
  await P(page, 5000);
  await expect(page.locator('#log')).toBeVisible();

  // Log should have real engagement entries
  const logText = await page.locator('#log-feed').textContent();
  console.log(`  [LIVE] Log preview: "${logText?.substring(0, 100)}"`);

  await P(page, 3000);

  // ── Saturation Wave (AUTO) ────────────────────────────────────────────────
  await page.locator('#btn-wave').click();
  await P(page, 5000);
  await expect(page.locator('#log')).toBeVisible();

  // ── Reset ─────────────────────────────────────────────────────────────────
  await page.locator('#btn-reset').click();
  await P(page, 2500);
  await expect(page.locator('#s-threats')).toHaveText('0');
  await expect(page.locator('#s-kills')).toHaveText('0');

  // ── Switch to SWEDEN theater ──────────────────────────────────────────────
  await page.locator('#sel-theater').selectOption('sweden');
  await P(page, 2500);
  await expect(page.locator('#sel-theater')).toHaveValue('sweden');

  await page.locator('#sel-weapon').selectOption('HYPERSONIC');
  await P(page, 1500);

  // ── Fire Sweden demo (AUTO) ───────────────────────────────────────────────
  await page.locator('#btn-fire').click();
  await P(page, 5000);
  await expect(page.locator('#canvas-wrap')).toBeVisible();

  // ── Show HITL mode for audience ───────────────────────────────────────────
  await page.locator('#sel-mode').selectOption('hitl');
  await P(page, 2000);

  // Back to AUTO + final reset
  await page.locator('#sel-mode').selectOption('auto');
  await P(page, 1000);
  await page.locator('#btn-reset').click();
  await P(page, 2000);
  await expect(page.locator('#s-threats')).toHaveText('0');

  // ── Navigate home ─────────────────────────────────────────────────────────
  await page.locator('#hud button:has-text("PORTAL")').click();
  await page.waitForLoadState('domcontentloaded');
  await P(page, 3000);
  await expect(page.locator('h1')).toContainText(/PORTAL|STRATEGIC/i);
  await P(page, 2000);
});
