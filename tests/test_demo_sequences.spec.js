// @ts-check
/**
 * SAAB C2 DEMO SEQUENCES — 5 human-like simulation flows
 *
 * Each sequence is ~60 seconds of realistic operator interaction:
 *   - slowMo: 900 ms per action (set in playwright.demo.config.js)
 *   - Explicit waitForTimeout() calls simulate a human reading / thinking
 *   - expect() assertions verify correct UI state at key moments
 *   - mockBackend() prevents any real port-8000 calls
 *
 * Run:    npx playwright test --config=scratch/playwright.demo.config.js
 * Videos: scratch/demo-videos/<test-slug>/video.webm
 */
const { test, expect } = require('@playwright/test');
const { mockBackend } = require('./helpers/mockApi');

// ─── local alias ───────────────────────────────────────────────────────────
const P = (page, ms) => page.waitForTimeout(ms);

// ═══════════════════════════════════════════════════════════════════════════
// SEQUENCE 1 — STRATEGIC PORTAL OVERVIEW  (~60 s)
// Walk through the portal, toggle SWEDEN/BOREAL theater, explore each card,
// then land on the Strategic Dashboard.
// ═══════════════════════════════════════════════════════════════════════════
test('Sequence 1 — STRATEGIC PORTAL OVERVIEW', async ({ page }) => {
  await mockBackend(page);
  await page.goto('/index.html', { waitUntil: 'domcontentloaded' });

  // [4 s] Operator reads the portal heading
  await expect(page.locator('h1')).toContainText(/PORTAL|STRATEGIC/i);
  await P(page, 4000);

  // Hover over the C2 Console card
  await page.hover('a.opt.c2');
  await P(page, 2500);   // [2.5 s] reading card description

  // Hover over Strategic Dashboard card
  await page.hover('a.opt.primary');
  await P(page, 2500);

  // Hover over the 3D Kinetic — Boreal card
  await page.hover('a[href*="kinetic_3d.html?theater=boreal"]');
  await P(page, 2000);

  // Hover over the 3D Kinetic — Sweden card
  await page.hover('a[href*="kinetic_3d.html?theater=sweden"]');
  await P(page, 2000);

  // ── Theater toggle ──────────────────────────────────────────────────────
  // Switch to SWEDEN — all nav card links gain ?mode=sweden
  await page.locator('#toggle-sweden').click();
  await P(page, 3500);  // [3.5 s] operator sees all hrefs flip

  // Verify SWEDEN is highlighted (cyan)
  await expect(page.locator('#toggle-sweden')).toHaveCSS('color', 'rgb(0, 242, 255)');

  // Switch back to BOREAL
  await page.locator('#toggle-boreal').click();
  await P(page, 3000);  // [3 s]

  await expect(page.locator('#toggle-boreal')).toHaveCSS('color', 'rgb(0, 242, 255)');

  // ── Navigate to CORTEX-C2 ───────────────────────────────────────────────
  await page.locator('a.opt.c2').click();
  await page.waitForLoadState('domcontentloaded');
  await P(page, 5000);  // [5 s] reading the C2 header

  await expect(page.locator('header')).toBeVisible();

  // Navigate back to Portal
  await page.locator('a.nav-back[href="index.html"]').click();
  await page.waitForLoadState('domcontentloaded');
  await P(page, 3000);  // [3 s]

  // ── Navigate to STRATEGIC DASHBOARD ─────────────────────────────────────
  await page.locator('a.opt.primary').click();
  await page.waitForLoadState('domcontentloaded');
  await P(page, 5000);  // [5 s] reading the SVG theater map

  await expect(page.locator('#main-title')).toBeVisible();
  await expect(page.locator('#map-title')).toBeVisible();
  await expect(page.locator('#baltic-map')).toBeVisible();

  // [4 s] Final overview pause before sequence ends
  await P(page, 4000);
});
// Expected total: ~62 s


// ═══════════════════════════════════════════════════════════════════════════
// SEQUENCE 2 — DASHBOARD COMMAND MODE WORKFLOW  (~60 s)
// Demonstrate AUTONOMOUS → HITL → MANUAL → back to AUTO,
// then cycle through all five doctrine buttons and swap the AI model.
// ═══════════════════════════════════════════════════════════════════════════
test('Sequence 2 — DASHBOARD COMMAND MODE WORKFLOW', async ({ page }) => {
  await mockBackend(page);
  await page.goto('/dashboard.html?mode=boreal', { waitUntil: 'domcontentloaded' });

  // [4 s] Operator surveys the dashboard
  await P(page, 4000);

  await expect(page.locator('#mode-auto')).toHaveClass(/active-auto/);
  await expect(page.locator('#main-title')).toBeVisible();

  // ── Switch to HUMAN-IN-LOOP ──────────────────────────────────────────────
  await page.locator('#mode-hitl').click();
  await P(page, 4000);  // [4 s] approval queue slides in — operator reviews it

  await expect(page.locator('#approval-queue')).toBeVisible();
  await expect(page.locator('#mode-hitl')).toHaveClass(/active-hitl/);

  // ── Switch to MANUAL OVERRIDE ────────────────────────────────────────────
  await page.locator('#mode-manual').click();
  await P(page, 4000);  // [4 s] manual panel visible — operator reads target selectors

  await expect(page.locator('#manual-panel')).toBeVisible();
  await expect(page.locator('#manual-target')).toBeVisible();
  await expect(page.locator('#manual-effector')).toBeVisible();
  await expect(page.locator('#manual-base')).toBeVisible();

  // Operator examines the fire button
  await page.hover('#btn-manual-fire');
  await P(page, 2000);

  // ── Return to AUTONOMOUS ─────────────────────────────────────────────────
  await page.locator('#mode-auto').click();
  await P(page, 2500);  // approval queue / manual panel both hide

  await expect(page.locator('#approval-queue')).toBeHidden();
  await expect(page.locator('#manual-panel')).toBeHidden();

  // ── Doctrine selector cycle ──────────────────────────────────────────────
  // FORTRESS
  await page.locator('.doctrine-btn[data-doctrine="fortress"]').click();
  await P(page, 2000);
  await expect(page.locator('.doctrine-btn[data-doctrine="fortress"]')).toHaveClass(/active/);

  // AGGRESSIVE
  await page.locator('.doctrine-btn[data-doctrine="aggressive"]').click();
  await P(page, 2000);
  await expect(page.locator('.doctrine-btn[data-doctrine="aggressive"]')).toHaveClass(/active/);

  // Back to BALANCED
  await page.locator('.doctrine-btn[data-doctrine="balanced"]').click();
  await P(page, 2500);
  await expect(page.locator('.doctrine-btn[data-doctrine="balanced"]')).toHaveClass(/active/);

  // ── Model selector ───────────────────────────────────────────────────────
  await page.locator('#sel-model-core').selectOption('elite');
  await P(page, 1500);
  await page.locator('#sel-model-core').selectOption('titan');
  await P(page, 1500);
  await page.locator('#sel-model-core').selectOption('supreme3');
  await P(page, 2000);
  await expect(page.locator('#sel-model-core')).toHaveValue('supreme3');

  // ── Initialize Intercept ─────────────────────────────────────────────────
  await page.locator('#btn-launch').click();
  await P(page, 4000);  // [4 s] intercept animation running

  await expect(page.locator('#baltic-map')).toBeVisible();

  // [3 s] Final overview
  await P(page, 3000);
});
// Expected total: ~62 s


// ═══════════════════════════════════════════════════════════════════════════
// SEQUENCE 3 — CORTEX C2 STRATEGIC AUDIT  (~60 s)
// Browse all three scenario cards, cycle doctrines, run the Monte Carlo
// audit, review the COA grid and inventory, then navigate away.
// ═══════════════════════════════════════════════════════════════════════════
test('Sequence 3 — CORTEX C2 STRATEGIC AUDIT', async ({ page }) => {
  await mockBackend(page);
  await page.goto('/cortex_c2.html', { waitUntil: 'domcontentloaded' });

  // [4 s] Operator reads the console overview
  await P(page, 4000);

  await expect(page.locator('header')).toBeVisible();

  // ── Scenario selection ───────────────────────────────────────────────────
  // CLEAN AIRSPACE (default active)
  await page.hover('.sc-card[data-sc="clean"]');
  await P(page, 2000);

  // SWARM WITH FAST-MOVER
  await page.locator('.sc-card[data-sc="swarm"]').click();
  await P(page, 3000);  // [3 s] inventory + radar update
  await expect(page.locator('.sc-card[data-sc="swarm"]')).toHaveClass(/active/);

  // JAMMED SENSORS
  await page.locator('.sc-card[data-sc="jammed"]').click();
  await P(page, 3000);  // [3 s] jammed scenario loads
  await expect(page.locator('.sc-card[data-sc="jammed"]')).toHaveClass(/active/);

  // ── Doctrine cycle ───────────────────────────────────────────────────────
  const docDesc = page.locator('#doctrine-desc');
  const initial = await docDesc.textContent();

  await page.locator('#doc-fortress').click();
  await P(page, 2500);
  await expect(docDesc).not.toHaveText(initial);

  await page.locator('#doc-aggressive').click();
  await P(page, 2000);

  await page.locator('#doc-balanced').click();
  await P(page, 2000);

  // ── Model selector ───────────────────────────────────────────────────────
  await page.locator('#model-select').selectOption('supreme3');
  await P(page, 1500);
  await expect(page.locator('#model-select')).toHaveValue('supreme3');

  // ── RUN STRATEGIC AUDIT ──────────────────────────────────────────────────
  await page.locator('#btn-run-audit').click();
  await P(page, 4000);  // [4 s] MC simulation runs → COA grid populates

  await expect(page.locator('#coa-grid')).toBeVisible();
  await expect(page.locator('#tactical-svg')).toBeVisible();

  // [3 s] Operator reviews the COA recommendations
  await P(page, 3000);

  // ── REPLENISH inventory ──────────────────────────────────────────────────
  await page.locator('#btn-replenish').click();
  await P(page, 2500);
  await expect(page.locator('#inventory-grid')).toBeVisible();

  // ── Navigate to DASHBOARD ────────────────────────────────────────────────
  await page.locator('a.nav-back[href="dashboard.html"]').click();
  await page.waitForLoadState('domcontentloaded');
  await P(page, 4000);  // [4 s] back at dashboard

  await expect(page.locator('#main-title')).toBeVisible();

  // [2 s] Final pause
  await P(page, 2000);
});
// Expected total: ~57 s


// ═══════════════════════════════════════════════════════════════════════════
// SEQUENCE 4 — TACTICAL LEGACY MULTI-THREAT ENGAGEMENT  (~65 s)
// Set doctrine, spawn 4 threats one by one, execute the AI,
// fire a blind ambush, then adjust blend ratio and navigate home.
// ═══════════════════════════════════════════════════════════════════════════
test('Sequence 4 — TACTICAL LEGACY MULTI-THREAT ENGAGEMENT', async ({ page }) => {
  await mockBackend(page);
  await page.goto('/tactical_legacy.html?mode=boreal', { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#radarCanvas');

  // [4 s] Operator scans the radar display
  await P(page, 4000);

  await expect(page.locator('#radarCanvas')).toBeVisible();
  await expect(page.locator('#ws-output')).toBeVisible();

  // ── Doctrine setup ────────────────────────────────────────────────────────
  await page.locator('#primary-doctrine').selectOption('fortress');
  await P(page, 1500);
  await expect(page.locator('#primary-doctrine')).toHaveValue('fortress');

  await page.locator('#secondary-doctrine').selectOption('economy');
  await P(page, 1500);

  // Enable DYNAMIC HITL
  await page.locator('#dynamic-hitl').check();
  await P(page, 1500);
  await expect(page.locator('#dynamic-hitl')).toBeChecked();

  // ── Blend ratio adjustment ────────────────────────────────────────────────
  await page.locator('#blend-ratio').evaluate(el => {
    el.value = '40';
    el.dispatchEvent(new Event('input'));
  });
  await P(page, 2000);  // [2 s] watch blend-pct readout change
  await expect(page.locator('#blend-pct')).toContainText('40');

  // ── Spawn threats one by one ──────────────────────────────────────────────
  // Threat 1
  await page.locator('#btn-threat').click();
  await P(page, 2500);  // [2.5 s] dot appears on radar

  // Threat 2
  await page.locator('#btn-threat').click();
  await P(page, 2000);

  // Threat 3
  await page.locator('#btn-threat').click();
  await P(page, 2000);

  // Threat 4
  await page.locator('#btn-threat').click();
  await P(page, 2500);  // [2.5 s] four bogeys now tracked

  await expect(page.locator('#radarCanvas')).toBeVisible();

  // ── Execute AI ───────────────────────────────────────────────────────────
  await page.locator('#btn-ai').click();
  await P(page, 4000);  // [4 s] policy runs — status changes from STANDBY

  await expect(page.locator('#policy-status')).not.toContainText('STANDBY');

  // ── Spawn two more threats ────────────────────────────────────────────────
  await page.locator('#btn-threat').click();
  await P(page, 1500);
  await page.locator('#btn-threat').click();
  await P(page, 1500);

  // ── Execute AI again ──────────────────────────────────────────────────────
  await page.locator('#btn-ai').click();
  await P(page, 3000);

  // ── AMBUSH BLIND ─────────────────────────────────────────────────────────
  await page.locator('#btn-blind').click();
  await P(page, 3000);  // [3 s] ambush wave animation

  await expect(page.locator('#radarCanvas')).toBeVisible();

  // ── Swap model ────────────────────────────────────────────────────────────
  await page.locator('#model-select').selectOption('elite');
  await P(page, 1500);
  await expect(page.locator('#model-select')).toHaveValue('elite');

  // ── Navigate home ─────────────────────────────────────────────────────────
  await page.locator('#btn-nav-portal').click();
  await page.waitForLoadState('domcontentloaded');
  await P(page, 3000);  // [3 s] back at portal

  await expect(page.locator('h1')).toContainText(/PORTAL|STRATEGIC/i);

  // [2 s] Final pause
  await P(page, 2000);
});
// Expected total: ~65 s


// ═══════════════════════════════════════════════════════════════════════════
// SEQUENCE 5 — KINETIC 3D FULL WEAPONS DEMO  (~65 s)
// Open Kinetic 3D, cycle every weapon, fire a BOREAL demo,
// launch a saturation wave, reset stats, switch to SWEDEN theater,
// fire again, then navigate back to the portal.
// ═══════════════════════════════════════════════════════════════════════════
test('Sequence 5 — KINETIC 3D FULL WEAPONS DEMO', async ({ page }) => {
  await mockBackend(page);
  await page.goto('/kinetic_3d.html?theater=boreal', { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#hud');

  // [4 s] Operator admires the 3D theater
  await P(page, 4000);

  await expect(page.locator('#hud')).toBeVisible();
  await expect(page.locator('#canvas-wrap')).toBeVisible();
  await expect(page.locator('#s-threats')).toHaveText('0');

  // ── Cycle all 4 weapons ──────────────────────────────────────────────────
  // HYPERSONIC
  await page.locator('#sel-weapon').selectOption('HYPERSONIC');
  await P(page, 2000);
  await expect(page.locator('#sel-weapon')).toHaveValue('HYPERSONIC');

  // BALLISTIC
  await page.locator('#sel-weapon').selectOption('BALLISTIC');
  await P(page, 1500);

  // LOITERING MUNITION
  await page.locator('#sel-weapon').selectOption('LOITER');
  await P(page, 1500);

  // Back to CRUISE (default-first)
  await page.locator('#sel-weapon').selectOption('CRUISE');
  await P(page, 1500);

  // ── Stay in AUTO mode for fire demo (HITL would show freeze overlay) ────
  await expect(page.locator('#sel-mode')).toHaveValue('auto');

  // ── FIRE BOREAL DEMO (AUTO — no freeze overlay) ───────────────────────────
  await page.locator('#btn-fire').click();
  await P(page, 5000);  // [5 s] intercept animation plays

  await expect(page.locator('#log')).toBeVisible();

  // [3 s] Operator watches engagement stats
  await P(page, 3000);

  // ── SATURATION WAVE (AUTO mode — no freeze) ───────────────────────────────
  await page.locator('#btn-wave').click();
  await P(page, 5000);  // [5 s] wave sweeps the theater
  await expect(page.locator('#log')).toBeVisible();

  // ── RESET ────────────────────────────────────────────────────────────────
  await page.locator('#btn-reset').click();
  await P(page, 2500);

  await expect(page.locator('#s-threats')).toHaveText('0');
  await expect(page.locator('#s-kills')).toHaveText('0');

  // ── Switch to SWEDEN theater ──────────────────────────────────────────────
  await page.locator('#sel-theater').selectOption('sweden');
  await P(page, 2500);  // [2.5 s] theater geometry reloads
  await expect(page.locator('#sel-theater')).toHaveValue('sweden');

  // Select HYPERSONIC for Sweden
  await page.locator('#sel-weapon').selectOption('HYPERSONIC');
  await P(page, 1500);

  // Keep AUTO mode for Sweden fire (no freeze overlay)
  await expect(page.locator('#sel-mode')).toHaveValue('auto');

  // ── FIRE SWEDEN DEMO (AUTO) ───────────────────────────────────────────────
  await page.locator('#btn-fire').click();
  await P(page, 5000);  // [5 s] Sweden intercept plays
  await expect(page.locator('#canvas-wrap')).toBeVisible();

  // ── Switch to HITL to show mode to audience, then back to AUTO for reset ──
  await page.locator('#sel-mode').selectOption('hitl');
  await P(page, 2000);
  await expect(page.locator('#sel-mode')).toHaveValue('hitl');

  // Return to AUTO before reset (avoids any freeze overlay on btn-reset)
  await page.locator('#sel-mode').selectOption('auto');
  await P(page, 1000);

  // ── Final RESET ───────────────────────────────────────────────────────────
  await page.locator('#btn-reset').click();
  await P(page, 2000);
  await expect(page.locator('#s-threats')).toHaveText('0');

  // ── Navigate home via PORTAL button ──────────────────────────────────────
  await page.locator('#hud button:has-text("PORTAL")').click();
  await page.waitForLoadState('domcontentloaded');
  await P(page, 3000);  // [3 s] back at portal

  await expect(page.locator('h1')).toContainText(/PORTAL|STRATEGIC/i);

  // [2 s] End of demo
  await P(page, 2000);
});
// Expected total: ~65 s
