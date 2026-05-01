// @ts-check
/**
 * SAAB OPTIMIZED DEMO — Clear Showcase of Fixed Intercept Behavior
 *
 * This demo focuses on visually demonstrating the intercept fixes:
 * - Dots (threats + interceptors) are now visible throughout chase
 * - Interceptors pursue laterally using 2D Pro-Nav guidance
 * - Mid-theater intercepts fire ~50% into flight path (not at 7% near base)
 * - Kinetic 3D view properly frames all entities (threats, bases, effectors)
 * - Clear collision visualization with cyan blast effects
 *
 * SEQUENCE:
 * ACT 1  Dashboard Overview      (~15s)  Show controls + theater layout
 * ACT 2  Intercept Showcase      (~40s)  Multiple threats with clear mid-theater kills
 * ACT 3  Kinetic 3D Framing      (~35s)  Demonstrate improved camera positioning
 * ACT 4  Saturation Defense      (~30s)  Wave defense with multiple simultaneous intercepts
 * ACT 5  Tactical AI Evaluation  (~25s)  AI assessment with SA health visualization
 *
 * Run:  npx playwright test tests/test_optimized_demo.spec.js --config=scratch/playwright.optimized.config.js
 * Out:  scratch/optimized-demo/<folder>/video.webm
 */
const { spawn } = require('child_process');
const { test, expect, request } = require('@playwright/test');
const { liveBackend } = require('./helpers/liveApi');

const BACKEND_PYTHON = 'C:\\Users\\dhiraj.kumar\\Downloads\\Saab\\.venv_saab\\Scripts\\python.exe';
const BACKEND_CWD = 'C:\\Users\\dhiraj.kumar\\Downloads\\Saab\\ruby-stridsledning-ai';

/**
 * @param {import('@playwright/test').APIRequestContext} ctx
 */
async function ensureBackend(ctx) {
  try {
    const res = await ctx.get('/health', { timeout: 5_000 });
    if (res.ok()) return null;
  } catch {}

  const backend = spawn(BACKEND_PYTHON, ['src/agent_backend.py'], {
    cwd: BACKEND_CWD,
    env: {
      ...process.env,
      SAAB_MODE: 'boreal',
      PYTHONUNBUFFERED: '1',
    },
    stdio: 'ignore',
    windowsHide: true,
  });

  for (let attempt = 0; attempt < 30; attempt += 1) {
    try {
      const res = await ctx.get('/health', { timeout: 5_000 });
      if (res.ok()) return backend;
    } catch {}
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  backend.kill();
  throw new Error('Backend did not become ready on http://127.0.0.1:8000');
}

/**
 * @param {import('@playwright/test').Page} page
 * @param {number} ms
 */
const P = (page, ms) => page.waitForTimeout(ms);

/**
 * @param {import('@playwright/test').Page} page
 * @param {string} selector
 * @param {number} [ms=400]
 */
const clickAndPause = async (page, selector, ms = 400) => {
  await page.locator(selector).click();
  await P(page, ms);
};

/**
 * @param {import('@playwright/test').Page} page
 * @param {string} selector
 * @param {string} value
 * @param {number} [ms=400]
 */
const selectAndPause = async (page, selector, value, ms = 400) => {
  await page.locator(selector).selectOption(value);
  await P(page, ms);
};

let backendProcess;

test.beforeAll(async ({ playwright }) => {
  const ctx = await request.newContext({ baseURL: 'http://127.0.0.1:8000' });
  backendProcess = await ensureBackend(ctx);
  const res = await ctx.get('/health');
  const body = await res.json();
  console.log(`\n  LIVE BACKEND: mode=${body.mode}  theater=${body.theater}\n`);
  await ctx.dispose();
});

test.afterAll(() => {
  if (backendProcess) {
    backendProcess.kill();
  }
});

// ===========================================================================
// OPTIMIZED DEMO — Focus on intercept fixes and clear visual demonstration
// ===========================================================================
test('SAAB Optimized Demo — Intercept Showcase', async ({ page }) => {
  test.setTimeout(240_000);
  await liveBackend(page);

  // -- ACT 1: DASHBOARD OVERVIEW ---------------------------------------------
  console.log('\n  == ACT 1: DASHBOARD OVERVIEW ==');
  await page.goto('/dashboard.html?mode=boreal', { waitUntil: 'domcontentloaded' });
  await P(page, 1200);
  
  // Show the theater layout
  try {
    await page.locator('#svg-container').hover();
    await P(page, 500);
  } catch {}
  
  // Highlight key controls
  try {
    await page.locator('#doctrine-balanced').hover();
    await P(page, 300);
    await page.locator('#btn-launch').hover();
    await P(page, 300);
  } catch {}

  // -- ACT 2: INTERCEPT SHOWCASE — Clear mid-theater kills ------------------
  console.log('\n  == ACT 2: INTERCEPT SHOWCASE (Mid-Theater Kills) ==');
  await page.goto('/live_view.html?mode=boreal', { waitUntil: 'domcontentloaded' });
  await P(page, 1200);
  
  // Fire CRUISE missile - watch full chase sequence
  console.log('  [Demo] Firing CRUISE missile - watch interceptor chase');
  await selectAndPause(page, '#lv-sel-weapon', 'CRUISE', 250);
  await P(page, 300);
  await page.locator('.base-card').first().click();
  await P(page, 5000); // Full intercept sequence with visible cyan circle chase
  
  // Fire BALLISTIC - higher altitude but 2D lateral intercept
  console.log('  [Demo] Firing BALLISTIC missile - 2D lateral intercept');
  await selectAndPause(page, '#lv-sel-weapon', 'BALLISTIC', 250);
  await page.locator('.base-card').first().click();
  await P(page, 5500); // Watch interceptor ignore altitude difference
  
  // Fire HYPERSONIC - fast threat with proportional navigation
  console.log('  [Demo] Firing HYPERSONIC - Pro-Nav guidance demo');
  await selectAndPause(page, '#lv-sel-weapon', 'HYPERSONIC', 250);
  await page.locator('.base-card').first().click();
  await P(page, 4500);

  // -- ACT 3: KINETIC 3D FRAMING — Improved camera positioning --------------
  console.log('\n  == ACT 3: KINETIC 3D VIEW (Improved Camera Framing) ==');
  await page.goto('/kinetic_3d.html?theater=boreal', { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#hud');
  await P(page, 1500);
  
  // Fire a variety of threats to show full 3D coverage
  console.log('  [Demo] Testing 3D camera framing with east spawn → west bases');
  
  for (const weapon of ['CRUISE', 'BALLISTIC', 'HYPERSONIC']) {
    await selectAndPause(page, '#sel-weapon', weapon, 200);
    await selectAndPause(page, '#sel-outcome', 'intercept', 200);
    await clickAndPause(page, '#btn-fire', weapon === 'BALLISTIC' ? 4000 : 3500);
  }
  
  // Show MARV with improved framing
  await selectAndPause(page, '#sel-weapon', 'MARV', 200);
  await selectAndPause(page, '#sel-outcome', 'intercept', 200);
  await clickAndPause(page, '#btn-fire', 4500);

  // -- ACT 4: SATURATION DEFENSE — Multiple simultaneous intercepts ---------
  console.log('\n  == ACT 4: SATURATION WAVE (Multiple Simultaneous Intercepts) ==');
  await page.goto('/live_view.html?mode=boreal', { waitUntil: 'domcontentloaded' });
  await P(page, 1200);
  
  // Set mixed threat types
  await selectAndPause(page, '#lv-sel-weapon', 'CRUISE', 150);
  await P(page, 300);
  
  // Launch saturation wave
  console.log('  [Demo] Launching saturation wave - watch multiple cyan intercepts');
  await clickAndPause(page, '#btn-lv-saturation', 1500);
  await P(page, 6000); // Watch multiple interceptors engage simultaneously
  
  // Launch second wave for extended demonstration
  await clickAndPause(page, '#btn-lv-saturation', 1500);
  await P(page, 5000);

  // -- ACT 5: TACTICAL AI EVALUATION — SA Health Visualization --------------
  console.log('\n  == ACT 5: TACTICAL AI (SA Health + Evaluation) ==');
  await page.goto('/tactical_legacy.html?mode=boreal', { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#radarCanvas');
  await P(page, 1500);
  
  // Set doctrine and model
  await page.locator('#primary-doctrine').selectOption('balanced');
  await P(page, 400);
  await page.locator('#model-select').selectOption('elite');
  await P(page, 400);
  
  // Disable auto-poll for controlled demo
  try { await page.locator('#auto-poll').uncheck(); } catch {}
  await P(page, 300);
  
  // Spawn threats
  console.log('  [Demo] Spawning threats + AI evaluation');
  for (let i = 0; i < 4; i++) {
    await page.locator('#btn-threat').click();
    await P(page, 400);
  }
  await P(page, 1200);
  
  // Run AI evaluation
  await page.locator('#btn-ai').click();
  await P(page, 1500);
  
  // Watch intercepts and SA health recovery
  console.log('  [Demo] Watching SA health update during intercepts');
  await P(page, 6000);
  
  console.log('\n  == DEMO COMPLETE ==\n');
});
