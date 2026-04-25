// @ts-check
/**
 * SAAB DEMO — ~2-Minute End-to-End Video
 *
 * ACT 1  Portal            (~8s)
 * ACT 2  CORTEX C2         (~32s)  doctrine cycle + AI eval + map swap
 * ACT 3  Boreal Live View  (~12s)  saturation wave
 * ACT 4  Boreal Kinetic 3D (~15s)  2 weapon types + HITL approve
 * ACT 5  Boreal Tactical   (~50s)  3 PHASES:
 *          Phase A — AUTO   : spawn 4, AI eval, watch SA health + kills
 *          Phase B — HITL   : enable override, spawn 3, AI → CHRONOSTASIS overlay → Commence
 *          Phase C — AMBUSH : blind wave, disable override, AI → mass kills
 * ACT 6  Sweden Tactical   (~12s)  quick AI eval
 *
 * Run:  npx playwright test --config=scratch/playwright.mega.config.js
 * Out:  scratch/mega-demo/<folder>/video.webm
 */
const { test, expect, request } = require('@playwright/test');
const { liveBackend } = require('./helpers/liveApi');

const P = (page, ms) => page.waitForTimeout(ms);
function waitForApi(page, urlSubstr) {
  return page.waitForResponse(
    r => r.url().includes(urlSubstr) && r.request().method() !== 'OPTIONS',
    { timeout: 45_000 }
  );
}

test.beforeAll(async ({ playwright }) => {
  const ctx = await request.newContext({ baseURL: 'http://localhost:8000' });
  const res = await ctx.get('/health');
  expect(res.status(), 'Backend /health must be 200').toBe(200);
  const body = await res.json();
  console.log(`\n  LIVE BACKEND: mode=${body.mode}  theater=${body.theater}\n`);
  await ctx.dispose();
});

// ===========================================================================
// THE DEMO — one test, one video, ~2 minutes
// ===========================================================================
test('SAAB C2 System Demo — SA Health + HITL + Manual Override (~2 min)', async ({ page }) => {
  await liveBackend(page);

  // -- ACT 1: PORTAL ---------------------------------------------------------
  console.log('\n  == ACT 1: PORTAL ==');
  await page.goto('/index.html', { waitUntil: 'domcontentloaded' });
  await P(page, 1200);
  try { await page.locator('#portal-backend').waitFor({ timeout: 5000 }); } catch {}
  await P(page, 600);
  try { await page.hover('a.opt.c2');                                  await P(page, 700); } catch {}
  try { await page.hover('a[href*="kinetic_3d.html?theater=boreal"]'); await P(page, 600); } catch {}
  try { await page.hover('a[href*="tactical_legacy.html"]');           await P(page, 600); } catch {}

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

  // -- ACT 3: BOREAL LIVE VIEW — saturation wave ----------------------------
  console.log('\n  == ACT 3: BOREAL LIVE VIEW ==');
  await page.goto('/live_view.html?mode=boreal', { waitUntil: 'domcontentloaded' });
  await P(page, 1500);
  await page.locator('#btn-lv-saturation').click();
  await P(page, 5000);

  // -- ACT 4: BOREAL KINETIC 3D — 2 weapons + HITL approve ------------------
  console.log('\n  == ACT 4: BOREAL KINETIC 3D ==');
  await page.goto('/kinetic_3d.html?theater=boreal', { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#hud');
  await P(page, 1500);

  // Fire 2 weapon types
  for (const w of ['HYPERSONIC', 'BALLISTIC']) {
    await page.locator('#sel-weapon').selectOption(w);
    await P(page, 300);
    await page.locator('#btn-fire').click();
    await P(page, 3000);
  }

  // HITL mode — pause + approve intercept
  await page.locator('#sel-mode').selectOption('hitl');
  await P(page, 600);
  await page.locator('#sel-weapon').selectOption('CRUISE');
  await page.locator('#btn-fire').click();
  await P(page, 2000);
  try {
    await page.locator('#btn-approve-k').click({ timeout: 3000 });
    await P(page, 2000);
  } catch {}
  await page.locator('#sel-mode').selectOption('auto');
  await P(page, 400);

  // -- ACT 5: BOREAL TACTICAL — 3-phase SA health + HITL + override demo ----
  console.log('\n  == ACT 5: BOREAL TACTICAL ==');
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
  console.log('\n  [Phase A] AUTO ENGAGE — spawn 4 threats, AI eval, watch kills + SA health');
  for (let i = 0; i < 4; i++) { await page.locator('#btn-threat').click(); await P(page, 350); }
  await P(page, 1800);  // staging window — SA threat count rises

  const tEvalA = waitForApi(page, '/evaluate_advanced');
  await page.locator('#btn-ai').click();
  try {
    const tResA = await tEvalA;
    const tBodyA = await tResA.json();
    console.log(`  [Phase A] score=${tBodyA.strategic_consequence_score}  assignments=${tBodyA.tactical_assignments?.length}`);
  } catch {}
  await P(page, 1000);   // SA health bar drops (threats active)
  await P(page, 3500);   // watch kills — SA threat count→0, kills counter rises, bar goes green

  // ── PHASE B: HITL / MANUAL OVERRIDE — show CHRONOSTASIS freeze overlay ───
  console.log('\n  [Phase B] MANUAL OVERRIDE — spawn 3, AI eval, CHRONOSTASIS freeze, Commence');
  await page.locator('#manual-override').check();   // enable override — SA badge switches to "MANUAL OVERRIDE"
  await P(page, 800);                               // viewer sees badge change

  for (let i = 0; i < 3; i++) { await page.locator('#btn-threat').click(); await P(page, 350); }
  await P(page, 1800);  // staging — SA threat count rises again

  const tEvalB = waitForApi(page, '/evaluate_advanced');
  await page.locator('#btn-ai').click();
  console.log('  [Phase B] Waiting for AI + CHRONOSTASIS overlay...');
  try { await tEvalB; } catch {}
  // Wait for CHRONOSTASIS overlay to appear (freezeTime() called by requestAIOrders)
  try {
    await page.locator('#freeze-overlay').waitFor({ state: 'visible', timeout: 8000 });
    console.log('  [Phase B] CHRONOSTASIS ACTIVE — showing to viewer...');
  } catch { console.log('  [Phase B] freeze overlay not detected — continuing'); }
  await P(page, 3000);  // show CHRONOSTASIS screen: red pulsing border, AI sitrep advice
  // Click Commence — use force:true as insurance if overlay has pointer-events:none
  try {
    await page.locator('#btn-commence').click({ timeout: 5000, force: true });
    console.log('  [Phase B] COMMENCE ENGAGEMENT clicked');
  } catch {
    // Fallback: JS click directly on button
    await page.evaluate(() => document.getElementById('btn-commence')?.click());
    console.log('  [Phase B] COMMENCE via JS fallback');
  }
  await P(page, 2500);  // watch kill explosions — SA kills++ after override-fire
  await page.locator('#manual-override').uncheck();  // back to AUTO
  await P(page, 500);   // SA badge reverts to AUTO ENGAGE

  // ── PHASE C: AMBUSH — blind wave + mass intercept ─────────────────────────
  console.log('\n  [Phase C] AMBUSH WAVE — 8 ghost threats, mass AI intercept');
  await page.locator('#primary-doctrine').selectOption('aggressive');
  await P(page, 400);
  await page.locator('#btn-blind').click();     // spawn 8 ghost threats
  await P(page, 2000);                          // SA health bar drops sharply

  const tEvalC = waitForApi(page, '/evaluate_advanced');
  await page.locator('#btn-ai').click();
  console.log('  [Phase C] Mass intercept AI evaluating...');
  try {
    const tResC = await tEvalC;
    const tBodyC = await tResC.json();
    console.log(`  [Phase C] score=${tBodyC.strategic_consequence_score}  assignments=${tBodyC.tactical_assignments?.length}`);
  } catch {}
  await P(page, 5000);  // watch 8 explosions — kill counter maxes, SA bar goes green

  // -- ACT 6: SWEDEN TACTICAL — quick AI eval --------------------------------
  console.log('\n  == ACT 6: SWEDEN TACTICAL ==');
  await page.goto('/tactical_legacy.html?mode=sweden', { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#radarCanvas');
  await P(page, 1200);
  await page.locator('#primary-doctrine').selectOption('aggressive');
  await P(page, 400);
  await page.locator('#model-select').selectOption('elite');
  await P(page, 400);
  try { await page.locator('#auto-poll').uncheck(); } catch {}
  for (let i = 0; i < 4; i++) { await page.locator('#btn-threat').click(); await P(page, 350); }
  await P(page, 2000);
  const sEvalP = waitForApi(page, '/evaluate_advanced');
  await page.locator('#btn-ai').click();
  console.log('  [SWEDEN] Tactical AI evaluating...');
  try {
    const sRes = await sEvalP;
    const sBody = await sRes.json();
    console.log(`  [SWEDEN] score=${sBody.strategic_consequence_score}`);
  } catch {}
  await P(page, 2500);

  // -- FINISH ----------------------------------------------------------------
  console.log('\n  == DEMO COMPLETE — Returning to Portal ==');
  await page.goto('/index.html', { waitUntil: 'domcontentloaded' });
  await P(page, 1200);
  console.log('\n  DEMO RECORDING COMPLETE\n');
});
