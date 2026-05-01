// @ts-check
/**
 * SAAB MEGA DEMO — Enhanced End-to-End Video
 *
 * ACT 1  Portal + Dashboard  (~20s)  navigation + new deep links
 * ACT 2  CORTEX C2           (~30s)  doctrine cycle + AI eval + map swap
 * ACT 3  Boreal Live View    (~35s)  weapon selector + saturation wave + auto-wave
 * ACT 4  Boreal Kinetic 3D   (~55s)  all threat classes + HITL approve + saturation
 * ACT 5  Boreal Kinetic Chase (~20s)  MARV deep-link autorun
 * ACT 6  Boreal Tactical     (~35s)  override + ambush wave
 *
 * Run:  npx playwright test --config=scratch/playwright.mega.config.js
 * Out:  scratch/mega-demo/<folder>/video.webm
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

/**
 * @param {import('@playwright/test').Page} page
 * @param {string} urlSubstr
 */
function waitForApi(page, urlSubstr) {
  return page.waitForResponse(
    /**
     * @param {import('@playwright/test').Response} r
     */
    r => r.url().includes(urlSubstr) && r.request().method() !== 'OPTIONS',
    { timeout: 45_000 }
  );
}

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
// THE DEMO — one test, one video, enhanced feature tour
// ===========================================================================
test('SAAB Mega Demo — enhanced feature tour', async ({ page }) => {
  test.setTimeout(420_000);
  await liveBackend(page);

  // -- ACT 1: PORTAL ---------------------------------------------------------
  console.log('\n  == ACT 1: PORTAL ==');
  await page.goto('/index.html', { waitUntil: 'domcontentloaded' });
  await P(page, 600);
  try { await page.locator('#portal-backend').waitFor({ timeout: 5000 }); } catch {}
  await P(page, 250);
  try { await page.hover('a.opt.c2');                     await P(page, 250); } catch {}
  try { await page.hover('a[href*="live_view.html"]');   await P(page, 250); } catch {}
  try { await page.hover('a[href*="kinetic_3d.html"]');  await P(page, 250); } catch {}
  try { await page.hover('a[href*="kinetic_chase.html"]'); await P(page, 250); } catch {}

  // Show the new dashboard entry points and deep links.
  console.log('\n  == ACT 1B: DASHBOARD ==');
  await page.goto('/dashboard.html?mode=boreal', { waitUntil: 'domcontentloaded' });
  await P(page, 900);
  try { await page.locator('#nav-live-view').hover(); await P(page, 250); } catch {}
  try { await page.locator('#btn-kinetic-3d').hover(); await P(page, 250); } catch {}
  try { await page.locator('#btn-live-audit').hover(); await P(page, 250); } catch {}
  try { await page.locator('#btn-engage-marv1').hover(); await P(page, 250); } catch {}
  try { await page.locator('#btn-engage-marv2').hover(); await P(page, 250); } catch {}
  try { await page.locator('#btn-engage-marv3').hover(); await P(page, 250); } catch {}
  await page.locator('#nav-live-view').scrollIntoViewIfNeeded().catch(() => {});
  await P(page, 300);
  await page.goto('/live_view.html?mode=boreal', { waitUntil: 'domcontentloaded' });
  await P(page, 800);

  // -- ACT 2: CORTEX C2 — strategic command + doctrine cycle + AI -----------
  console.log('\n  == ACT 2: CORTEX C2 ==');
  await page.goto('/cortex_c2.html', { waitUntil: 'domcontentloaded' });
  await P(page, 1500);
  try { await page.locator('#backend-dot').waitFor({ timeout: 5000 }); } catch {}
  await P(page, 400);

  // Scenario + doctrine cycle (fortress → aggressive → balanced)
  try { await page.locator('[data-sc="swarm"]').click(); await P(page, 600); } catch {}
  await page.locator('#doc-fortress').click();  await P(page, 700);
  await page.locator('#doc-aggressive').click(); await P(page, 700);
  await page.locator('#doc-balanced').click();   await P(page, 500);

  await page.locator('#model-select').selectOption('elite');
  await P(page, 400);

  // Run AI evaluation
  const evalP = waitForApi(page, '/evaluate_advanced');
  await page.locator('#btn-run-audit').click();
  console.log('  [LIVE] Waiting for /evaluate_advanced ...');
  const evalRes = await evalP;
  const evalBody = await evalRes.json();
  console.log(`  [LIVE] C2 score=${evalBody.strategic_consequence_score}  assignments=${evalBody.tactical_assignments?.length}`);
  await P(page, 2500);

  // Theater map swap demo
  try { await page.locator('#thr-sweden').click(); await P(page, 1000); } catch {}
  try { await page.locator('#thr-boreal').click(); await P(page, 1000); } catch {}

  // -- ACT 3: BOREAL LIVE VIEW — weapon selector + saturation wave ----------
  console.log('\n  == ACT 3: BOREAL LIVE VIEW ==');
  await page.goto('/live_view.html?mode=boreal', { waitUntil: 'domcontentloaded' });
  await P(page, 1500);
  for (const idx of [0, 1, 2, 3, 4]) {
    const cards = page.locator('.base-card');
    if (await cards.count() > idx) {
      await cards.nth(idx).click();
      await P(page, 250);
    }
  }
  for (const weapon of ['CRUISE', 'HYPERSONIC', 'LOITER', 'BALLISTIC', 'MARV', 'MIRV', 'FIGHTER_DOG']) {
    await selectAndPause(page, '#lv-sel-weapon', weapon, 150);
  }
  await clickAndPause(page, '#btn-lv-saturation', 3200);
  await clickAndPause(page, '#btn-auto-wave', 1800);
  await clickAndPause(page, '#btn-auto-wave', 600);

  // -- ACT 4: BOREAL KINETIC 3D — all weapon classes + HITL approve ---------
  console.log('\n  == ACT 4: BOREAL KINETIC 3D ==');
  await page.goto('/kinetic_3d.html?theater=boreal', { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#hud');
  await P(page, 1500);

  // Fire the full weapon family so the 3D page shows the newer classes too.
  for (const w of ['CRUISE', 'HYPERSONIC', 'LOITER', 'BALLISTIC', 'MARV', 'MIRV', 'FIGHTER_DOG']) {
    await selectAndPause(page, '#sel-weapon', w, 250);
    await clickAndPause(page, '#btn-fire', w === 'LOITER' ? 1800 : 1400);
  }

  await clickAndPause(page, '#btn-wave', 2400);

  // HITL mode — pause + approve intercept
  await selectAndPause(page, '#sel-mode', 'hitl', 600);
  await selectAndPause(page, '#sel-weapon', 'CRUISE', 250);
  await clickAndPause(page, '#btn-fire', 1800);
  try {
    await page.locator('#btn-approve-k').click({ timeout: 3000 });
    await P(page, 2000);
  } catch {}
  await selectAndPause(page, '#sel-mode', 'auto', 400);

  // -- ACT 5: BOREAL KINETIC CHASE — MARV deep-link autorun -----------------
  console.log('\n  == ACT 5: BOREAL KINETIC CHASE ==');
  await page.goto('/kinetic_chase.html?v=20260428b&base=10&threat=marv&dir=north&autorun=1', { waitUntil: 'domcontentloaded' });
  await P(page, 5000);

  // -- ACT 6: BOREAL TACTICAL — override + ambush demo ----------------------
  console.log('\n  == ACT 6: BOREAL TACTICAL ==');
  await page.goto('/tactical_legacy.html?mode=boreal', { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#radarCanvas');
  await P(page, 1500);
  await page.locator('#primary-doctrine').selectOption('fortress');
  await P(page, 400);
  await page.locator('#model-select').selectOption('elite');
  await P(page, 400);
  // Disable auto-poll so we fully control AI timing
  try { await page.locator('#auto-poll').uncheck(); } catch {}
  await P(page, 300);

  // ── PHASE A: AUTO ENGAGE — show SA health updating ────────────────────────
  console.log('\n  [Phase A] AUTO ENGAGE — spawn 3 threats, AI eval, watch kills + SA health');
  for (let i = 0; i < 3; i++) { await page.locator('#btn-threat').click(); await P(page, 300); }
  await P(page, 1500);  // staging window — SA threat count rises

  const tEvalA = waitForApi(page, '/evaluate_advanced');
  await page.locator('#btn-ai').click();
  try {
    const tResA = await tEvalA;
    const tBodyA = await tResA.json();
    console.log(`  [Phase A] score=${tBodyA.strategic_consequence_score}  assignments=${tBodyA.tactical_assignments?.length}`);
  } catch {}
  await P(page, 900);   // SA health bar drops (threats active)
  await P(page, 2800);  // watch kills — SA threat count→0, kills counter rises, bar goes green

  // ── PHASE B: HITL / MANUAL OVERRIDE — show CHRONOSTASIS freeze overlay ───
  console.log('\n  [Phase B] MANUAL OVERRIDE — spawn 2, AI eval, CHRONOSTASIS freeze, Commence');
  await page.locator('#manual-override').check();   // enable override — SA badge switches to "MANUAL OVERRIDE"
  await P(page, 800);                               // viewer sees badge change

  for (let i = 0; i < 2; i++) { await page.locator('#btn-threat').click(); await P(page, 300); }
  await P(page, 1400);  // staging — SA threat count rises again

  const tEvalB = waitForApi(page, '/evaluate_advanced');
  await page.locator('#btn-ai').click();
  console.log('  [Phase B] Waiting for AI + CHRONOSTASIS overlay...');
  try { await tEvalB; } catch {}
  // Wait for CHRONOSTASIS overlay to appear (freezeTime() called by requestAIOrders)
  try {
    await page.locator('#freeze-overlay').waitFor({ state: 'visible', timeout: 8000 });
    console.log('  [Phase B] CHRONOSTASIS ACTIVE — showing to viewer...');
  } catch { console.log('  [Phase B] freeze overlay not detected — continuing'); }
  await P(page, 2200);  // show CHRONOSTASIS screen: red pulsing border, AI sitrep advice
  // Click Commence — use force:true as insurance if overlay has pointer-events:none
  try {
    await page.locator('#btn-commence').click({ timeout: 5000, force: true });
    console.log('  [Phase B] COMMENCE ENGAGEMENT clicked');
  } catch {
    // Fallback: JS click directly on button
    await page.evaluate(() => document.getElementById('btn-commence')?.click());
    console.log('  [Phase B] COMMENCE via JS fallback');
  }
  await P(page, 1800);  // watch kill explosions — SA kills++ after override-fire
  try {
    await page.locator('#manual-override').uncheck({ force: true });
  } catch {
    await page.evaluate(() => {
      const el = document.getElementById('manual-override');
      if (!el) return;
      el.checked = false;
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
    });
  }
  await P(page, 500);   // SA badge reverts to AUTO ENGAGE

  // ── PHASE C: AMBUSH — blind wave + mass intercept ─────────────────────────
  console.log('\n  [Phase C] AMBUSH WAVE — mass ghost threats, mass AI intercept');
  await page.locator('#primary-doctrine').selectOption('aggressive');
  await P(page, 400);
  await page.locator('#btn-blind').click();     // spawn 8 ghost threats
  await P(page, 1600);                          // SA health bar drops sharply

  const tEvalC = waitForApi(page, '/evaluate_advanced');
  await page.locator('#btn-ai').click();
  console.log('  [Phase C] Mass intercept AI evaluating...');
  try {
    const tResC = await tEvalC;
    const tBodyC = await tResC.json();
    console.log(`  [Phase C] score=${tBodyC.strategic_consequence_score}  assignments=${tBodyC.tactical_assignments?.length}`);
  } catch {}
  await P(page, 3600);  // watch 6 explosions — kill counter rises, SA bar goes green

  // -- FINISH ----------------------------------------------------------------
  console.log('\n  == DEMO COMPLETE — Returning to Portal ==');
  await page.goto('/index.html', { waitUntil: 'domcontentloaded' });
  await P(page, 1200);
  console.log('\n  DEMO RECORDING COMPLETE\n');
});
