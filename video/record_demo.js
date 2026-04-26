/**
 * SAAB CORTEX-1 C2 — Full Demo Video Recorder
 *
 * Sequence (old spine + new views inserted):
 *  ACT 1.  CORTEX Command Portal
 *  ACT 2.  Boreal Strategic Command  ← NEW: model select, doctrine cycle, MARV bézier, MC audit
 *  ACT 3.  Sweden AOR Dashboard      ← NEW
 *  ACT 4.  Kinetic 3D Simulator      (MARV sinusoidal jink + wave)
 *  ACT 5.  Kinetic Chase Pro-Nav     ← NEW (MARV/MIRV S-curves)
 *  ACT 6.  Swarm Physics             ← NEW (3×MARV oblique PAC-3)
 *  ACT 7.  Boreal Tactical A/B/C     (auto engage · HITL CHRONOSTASIS · aggressive saturation)
 *  ACT 8.  Sweden AOR Tactical
 *  ACT 9.  Live View
 *  →       Portal return
 *
 * Run: node video/record_demo.js
 */

const { chromium } = require('playwright');
const path = require('path');

const BASE = 'http://localhost:8000';
const VIDEO_DIR = path.join(__dirname);
const W = 1440, H = 860;

// Utility: smooth mouse pan across coordinates
async function pan(page, x1, y1, x2, y2, steps = 30, delay = 25) {
  for (let i = 0; i <= steps; i++) {
    const x = x1 + ((x2 - x1) * i) / steps;
    const y = y1 + ((y2 - y1) * i) / steps;
    await page.mouse.move(x, y);
    await page.waitForTimeout(delay);
  }
}

// Utility: zoom in with CSS transform on an element, then reset
async function zoomRegion(page, selector, scale, holdMs = 1800) {
  await page.evaluate(
    ({ sel, s }) => {
      const el = document.querySelector(sel);
      if (el) {
        el.style.transition = 'transform 0.6s ease';
        el.style.transformOrigin = 'center center';
        el.style.transform = `scale(${s})`;
      }
    },
    { sel: selector, s: scale }
  );
  await page.waitForTimeout(holdMs);
  await page.evaluate(
    ({ sel }) => {
      const el = document.querySelector(sel);
      if (el) {
        el.style.transform = 'scale(1)';
      }
    },
    { sel: selector }
  );
  await page.waitForTimeout(600);
}

// Utility: highlight an element with a brief glow, then remove
async function spotlight(page, selector, holdMs = 1000) {
  await page.evaluate(
    ({ sel, ms }) => {
      const el = document.querySelector(sel);
      if (!el) return;
      const old = el.style.cssText;
      el.style.outline = '3px solid #00ffff';
      el.style.boxShadow = '0 0 24px 6px rgba(0,255,255,0.55)';
      el.style.transition = 'box-shadow 0.3s, outline 0.3s';
      setTimeout(() => {
        el.style.outline = '';
        el.style.boxShadow = '';
      }, ms);
    },
    { sel: selector, ms: holdMs }
  );
  await page.waitForTimeout(holdMs + 300);
}

(async () => {
  const browser = await chromium.launch({
    headless: false,
    args: ['--start-maximized', '--disable-infobars'],
    slowMo: 0,
  });

  const context = await browser.newContext({
    viewport: { width: W, height: H },
    recordVideo: { dir: VIDEO_DIR, size: { width: W, height: H } },
  });

  const page = await context.newPage();

  // ═══════════════════════════════════════════════════════════════════
  // ACT 1 — CORTEX COMMAND PORTAL  (~8s)
  // ═══════════════════════════════════════════════════════════════════
  console.log('[1] Portal…');
  await page.goto(`${BASE}/index.html`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  for (const sel of [
    'a[href*="dashboard"]', 'a[href*="cortex_c2"]',
    'a[href*="kinetic_3d"]', 'a[href*="kinetic_chase"]',
    'a[href*="swarm"]', 'a[href*="live_view"]'
  ]) {
    try { const el = await page.$(sel); if (el) { await el.hover(); await page.waitForTimeout(480); } } catch (_) {}
  }
  await pan(page, 200, 300, 1200, 500, 25, 35);
  await page.waitForTimeout(600);

  // ═══════════════════════════════════════════════════════════════════
  // ACT 2 — CORTEX C2 STRATEGIC CONSOLE  (~22s)
  // cortex_c2.html: model select · SWARM scenario · doctrine cycle ·
  //   MARV bézier map animation · MC audit · theater toggle Boreal→Sweden→Boreal
  // ═══════════════════════════════════════════════════════════════════
  console.log('[2] Cortex C2 Strategic Console…');
  await page.goto(`${BASE}/cortex_c2.html`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);

  // Select ELITE V3.5 model
  await spotlight(page, '#model-select', 800);
  await page.selectOption('#model-select', { label: /elite/i }).catch(
    () => page.selectOption('#model-select', { index: 0 })
  );
  await page.waitForTimeout(500);

  // Load SWARM ATTACK scenario
  console.log('  → Loading SWARM scenario…');
  try {
    const swarmCard = await page.$('.sc-card[data-sc="swarm"]');
    if (swarmCard) { await spotlight(page, '.sc-card[data-sc="swarm"]', 600); await swarmCard.click(); await page.waitForTimeout(1200); }
  } catch (_) {}

  // Doctrine cycling: Fortress → Aggressive → Balanced
  for (const d of ['fortress', 'aggressive', 'balanced']) {
    try {
      const btn = await page.$(`#doc-${d}, .doc-btn[id*="${d}"]`);
      if (btn) { await btn.click(); await page.waitForTimeout(700); }
    } catch (_) {}
  }

  // Run Strategic Audit (MC)
  try {
    const auditBtn = await page.$('#btn-run-audit');
    if (auditBtn) {
      await spotlight(page, '#btn-run-audit', 700);
      await auditBtn.click();
      await page.waitForTimeout(3500);
    }
  } catch (_) {}

  // Scroll down to show COT feed / assignments panel
  await page.evaluate(() => window.scrollBy(0, 300));
  await page.waitForTimeout(1000);
  await pan(page, 100, 400, 1300, 600, 30, 35);
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(500);

  // ═══════════════════════════════════════════════════════════════════
  // THEATER TOGGLE: Boreal Strategic Map → Sweden → back via dashboard
  // ═══════════════════════════════════════════════════════════════════
  console.log('[2b] Boreal dashboard → theater toggle → Sweden…');
  await page.goto(`${BASE}/dashboard.html?mode=boreal`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1800);
  // Select ELITE + cycle doctrine on dashboard too
  await page.selectOption('#sel-model-core', 'elite').catch(() => {});
  for (const d of ['fortress', 'aggressive', 'balanced']) {
    try {
      const btn = await page.$(`button[data-doctrine="${d}"], .doctrine-btn[data-doctrine="${d}"]`);
      if (btn) { await btn.click(); await page.waitForTimeout(500); }
    } catch (_) {}
  }
  // MARV bézier animation on map
  await zoomRegion(page, '#theater-map, svg, .map-wrap, #baltic-map', 1.4, 1500);
  await pan(page, 80, 200, 680, 480, 35, 30);
  console.log('  → MARV bézier + PAC-3 arc animation…');
  await page.waitForTimeout(7000);
  // Hover ENGAGE deep-links
  for (const sel of ['#btn-engage-marv1', '#btn-engage-marv2', '#btn-engage-marv3', 'a[href*="swarm_physics"]']) {
    try { const el = await page.$(sel); if (el) { await el.hover(); await page.waitForTimeout(450); } } catch (_) {}
  }
  // MC audit
  try {
    const mcBtn = await page.$('#btn-live-mc');
    if (mcBtn) { await spotlight(page, '#btn-live-mc', 700); await mcBtn.click(); await page.waitForTimeout(3000); }
  } catch (_) {}
  await page.waitForTimeout(400);

  // Theater toggle: navigate to Sweden mode
  console.log('  → Theater toggle: Boreal → Sweden AOR…');
  await page.goto(`${BASE}/dashboard.html?mode=sweden`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  await pan(page, 80, 120, 1350, 120, 22, 40);
  await zoomRegion(page, '#theater-map, svg, .map-wrap, #baltic-map', 1.35, 1500);
  await page.waitForTimeout(800);
  // Toggle back to Boreal
  await page.goto(`${BASE}/dashboard.html?mode=boreal`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1200);

  // ═══════════════════════════════════════════════════════════════════
  // ACT 3 — SWEDEN AOR STRATEGIC COMMAND  (full scene ~7s)
  // ═══════════════════════════════════════════════════════════════════
  console.log('[3] Sweden AOR Strategic Command…');
  await page.goto(`${BASE}/dashboard.html?mode=sweden`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1800);
  await pan(page, 80, 120, 1350, 120, 25, 40);
  await zoomRegion(page, '#theater-map, svg, .map-wrap, #baltic-map', 1.4, 1800);
  await pan(page, 1350, 120, 80, 600, 25, 40);
  await page.waitForTimeout(600);

  // ═══════════════════════════════════════════════════════════════════
  // ACT 4 — KINETIC CHASE — PRO-NAV S-CURVES  (~15s)
  // ═══════════════════════════════════════════════════════════════════
  console.log('[4] Kinetic Chase — Pro-Nav S-curves…');
  await page.goto(`${BASE}/kinetic_chase.html?base=10&threat=marv&dir=north&autorun=1`, { waitUntil: 'networkidle' });
  await page.evaluate(() => {
    const cc = document.querySelector('.canvas-container');
    if (cc) cc.scrollIntoView({ behavior: 'smooth', block: 'end' });
  });
  await page.waitForTimeout(5500);
  await pan(page, 50, 100, 650, 300, 25, 40);
  await spotlight(page, '#hud', 900);
  await zoomRegion(page, 'canvas', 1.35, 5500);
  await spotlight(page, '#hud', 700);
  await page.waitForTimeout(500);

  // ═══════════════════════════════════════════════════════════════════
  // ACT 5 — SWARM PHYSICS — 3×MARV OBLIQUE PAC-3  (~14s)
  // ═══════════════════════════════════════════════════════════════════
  console.log('[5] Swarm Physics — 3×MARV oblique PAC-3…');
  await page.goto(`${BASE}/swarm_physics.html`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  console.log('  → MARV-1→CALLHAVEN, MARV-2→SOLANO, MARV-3→MERIDIA…');
  await pan(page, 100, 100, 750, 550, 30, 35);
  await page.waitForTimeout(1800);
  console.log('  → PAC-3 MSE salvo: oblique head-on geometry…');
  await pan(page, 750, 200, 100, 500, 28, 35);
  await page.waitForTimeout(2000);
  await zoomRegion(page, 'canvas', 1.4, 4000);
  await page.waitForTimeout(600);

  // ═══════════════════════════════════════════════════════════════════
  // ACT 6 — BOREAL KINETIC 3D SIMULATOR  (~20s)
  // ═══════════════════════════════════════════════════════════════════
  console.log('[6] Kinetic 3D — Three.js theater…');
  await page.goto(`${BASE}/kinetic_3d.html`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2200);
  await page.selectOption('#sel-weapon', 'MARV').catch(() => {});
  await page.selectOption('#sel-outcome', 'intercept').catch(() => {});
  await page.selectOption('#sel-theater', 'boreal').catch(() => {});
  await page.waitForTimeout(400);

  const cx = W / 2, cy = H / 2;
  await page.mouse.move(cx - 200, cy); await page.mouse.down();
  await pan(page, cx - 200, cy, cx + 200, cy + 30, 40, 25); await page.mouse.up();
  await page.waitForTimeout(500);

  console.log('  → MARV #1: sinusoidal jink + SAM Pro-Nav arc…');
  await page.click('#btn-fire');
  await page.mouse.move(cx - 150, cy + 50); await page.mouse.down();
  await pan(page, cx - 150, cy + 50, cx + 80, cy - 20, 35, 35); await page.mouse.up();
  await page.waitForTimeout(4500);
  await page.click('#btn-fire');
  await page.waitForTimeout(2500);
  console.log('  → Saturation wave…');
  await page.click('#btn-wave');
  await pan(page, 200, 300, 1200, 500, 35, 30);
  await page.waitForTimeout(4000);

  // ═══════════════════════════════════════════════════════════════════
  // ACT 7 — BOREAL TACTICAL DISPLAY
  //   PHASE A: Autonomous  |  PHASE B: HITL + CHRONOSTASIS  |  PHASE C: Saturation
  // ═══════════════════════════════════════════════════════════════════
  console.log('[7] Boreal Tactical — Phase A…');
  await page.goto(`${BASE}/tactical_legacy.html?mode=boreal`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1800);
  await page.selectOption('#sel-model', 'elite').catch(() => {});
  await spotlight(page, '#sel-model', 600);

  for (let i = 0; i < 4; i++) { await page.click('#btn-threat'); await page.waitForTimeout(280); }
  await page.waitForTimeout(1200);
  await spotlight(page, '#sa-mode-badge, .sa-mode, #mode-badge', 700);
  await page.click('#btn-ai');
  await page.waitForTimeout(4500);

  console.log('[7] Boreal Tactical — Phase B (HITL + CHRONOSTASIS)…');
  await page.check('#manual-override');
  await page.waitForTimeout(400);
  await spotlight(page, '#sa-mode-badge, .sa-mode, #mode-badge', 600);
  for (let i = 0; i < 3; i++) { await page.click('#btn-threat'); await page.waitForTimeout(320); }
  await page.waitForTimeout(900);
  await page.click('#btn-ai');
  await page.waitForTimeout(2800);
  console.log('  → CHRONOSTASIS: commander reviewing intercept plan…');
  await page.waitForTimeout(1600);
  try { await page.click('#btn-commence', { timeout: 2500 }); } catch (_) {}
  await page.waitForTimeout(3000);

  console.log('[7] Boreal Tactical — Phase C (Saturation ambush)…');
  await page.uncheck('#manual-override').catch(() => {});
  await page.selectOption('#primary-doctrine', 'aggressive').catch(() => {});
  await page.waitForTimeout(400);
  await page.click('#btn-blind');
  await page.waitForTimeout(1400);
  await page.click('#btn-ai');
  await page.waitForTimeout(3500);
  await spotlight(page, '#sa-kills, .kill-counter, #kills-count', 900);

  // ═══════════════════════════════════════════════════════════════════
  // ACT 8 — SWEDEN AOR TACTICAL  (~8s)
  // ═══════════════════════════════════════════════════════════════════
  console.log('[8] Sweden AOR Tactical…');
  await page.goto(`${BASE}/tactical_legacy.html?mode=sweden`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1800);
  await spotlight(page, '#theater-title, h1, .theater-label', 700);
  for (let i = 0; i < 4; i++) { await page.click('#btn-threat'); await page.waitForTimeout(280); }
  await page.waitForTimeout(1000);
  await page.click('#btn-ai');
  await page.waitForTimeout(3200);

  // ═══════════════════════════════════════════════════════════════════
  // ACT 9 — LIVE VIEW  (~6s)
  // ═══════════════════════════════════════════════════════════════════
  console.log('[9] Live View…');
  await page.goto(`${BASE}/live_view.html`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2500);
  await pan(page, 100, 150, 1300, 700, 30, 35);
  await spotlight(page, '.log-container, #log-stream, .live-log, .console-out', 900);
  await page.waitForTimeout(1500);

  // ═══════════════════════════════════════════════════════════════════
  // PORTAL RETURN
  // ═══════════════════════════════════════════════════════════════════
  console.log('[→] Return to Portal…');
  await page.goto(`${BASE}/index.html`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2800);

  console.log('[DONE] Closing — video will be saved…');
  await context.close();
  await browser.close();

  console.log(`\n✅  Video saved to: ${VIDEO_DIR}`);
  console.log('Convert: ffmpeg -i video/page@*.webm -c:v libx264 -crf 18 video/cortex_demo.mp4');
})();
