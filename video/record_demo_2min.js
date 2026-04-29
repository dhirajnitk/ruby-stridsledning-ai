/**
 * SAAB CORTEX-1 C2 — 2 Minute Demo Recorder
 *
 * Sequence:
 *  ACT 1. Portal
 *  ACT 2. CORTEX C2 Strategic Console
 *  ACT 3. Boreal Dashboard / Mirror Sync
 *  ACT 4. Kinetic Chase Pro-Nav
 *  ACT 5. Kinetic 3D Mirror View
 *  ACT 6. Live View
 *  → Portal return
 */

const { chromium } = require('playwright');
const path = require('path');

const BASE = 'http://localhost:8000';
const VIDEO_DIR = path.join(__dirname);
const W = 1440, H = 860;

async function pan(page, x1, y1, x2, y2, steps = 24, delay = 22) {
  for (let i = 0; i <= steps; i++) {
    const x = x1 + ((x2 - x1) * i) / steps;
    const y = y1 + ((y2 - y1) * i) / steps;
    await page.mouse.move(x, y);
    await page.waitForTimeout(delay);
  }
}

async function zoomRegion(page, selector, scale, holdMs = 1200) {
  await page.evaluate(({ sel, s }) => {
    const el = document.querySelector(sel);
    if (el) {
      el.style.transition = 'transform 0.6s ease';
      el.style.transformOrigin = 'center center';
      el.style.transform = `scale(${s})`;
    }
  }, { sel: selector, s: scale });
  await page.waitForTimeout(holdMs);
  await page.evaluate(({ sel }) => {
    const el = document.querySelector(sel);
    if (el) el.style.transform = 'scale(1)';
  }, { sel: selector });
  await page.waitForTimeout(400);
}

async function spotlight(page, selector, holdMs = 700) {
  await page.evaluate(({ sel, ms }) => {
    const el = document.querySelector(sel);
    if (!el) return;
    el.style.outline = '3px solid #00ffff';
    el.style.boxShadow = '0 0 24px 6px rgba(0,255,255,0.55)';
    setTimeout(() => {
      el.style.outline = '';
      el.style.boxShadow = '';
    }, ms);
  }, { sel: selector, ms: holdMs });
  await page.waitForTimeout(holdMs + 200);
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

  // ACT 1 — Portal (~8s)
  console.log('[1] Portal…');
  await page.goto(`${BASE}/index.html`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1800);
  for (const sel of ['a[href*="dashboard"]', 'a[href*="cortex_c2"]', 'a[href*="kinetic_3d"]', 'a[href*="kinetic_chase"]']) {
    try { const el = await page.$(sel); if (el) { await el.hover(); await page.waitForTimeout(350); } } catch (_) {}
  }
  await pan(page, 200, 300, 1200, 500, 18, 24);

  // ACT 2 — CORTEX C2 (~18s)
  console.log('[2] Cortex C2…');
  await page.goto(`${BASE}/cortex_c2.html`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1600);
  await spotlight(page, '#model-select', 700);
  await page.selectOption('#model-select', { label: /elite/i }).catch(() => page.selectOption('#model-select', { index: 0 }));
  await page.waitForTimeout(300);
  await page.click('.sc-card[data-sc="swarm"]');
  await page.waitForTimeout(900);
  for (const d of ['fortress', 'aggressive', 'balanced']) {
    try { await page.click(`#doc-${d}`); await page.waitForTimeout(450); } catch (_) {}
  }
  await spotlight(page, '#btn-run-audit', 600);
  await page.click('#btn-run-audit');
  await page.waitForTimeout(2500);

  // ACT 3 — Boreal Dashboard mirror sync (~20s)
  console.log('[3] Dashboard mirror sync…');
  await page.goto(`${BASE}/dashboard.html?mode=boreal`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1600);
  await page.selectOption('#sel-model-core', 'elite').catch(() => {});
  await page.click('#btn-live-mc').catch(() => {});
  await zoomRegion(page, '#theater-map, svg, .map-wrap, #baltic-map', 1.25, 1100);
  await pan(page, 120, 180, 760, 470, 20, 20);
  await page.waitForTimeout(3500);
  await page.waitForTimeout(1000);

  // ACT 4 — Kinetic Chase (~20s)
  console.log('[4] Kinetic Chase…');
  await page.goto(`${BASE}/kinetic_chase.html?base=10&threat=marv&dir=north&autorun=1`, { waitUntil: 'domcontentloaded' });
  await page.evaluate(() => {
    const cc = document.querySelector('.canvas-container');
    if (cc) cc.scrollIntoView({ behavior: 'smooth', block: 'end' });
  });
  await page.waitForTimeout(5000);
  await spotlight(page, '#hud', 700);
  await zoomRegion(page, 'canvas', 1.28, 4200);
  await pan(page, 50, 100, 650, 300, 18, 24);
  await page.waitForTimeout(1200);

  // ACT 5 — Kinetic 3D (~22s)
  console.log('[5] Kinetic 3D…');
  await page.goto(`${BASE}/kinetic_3d.html`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1600);
  await page.selectOption('#sel-theater', 'boreal').catch(() => {});
  await page.selectOption('#sel-weapon', 'MARV').catch(() => {});
  await page.selectOption('#sel-outcome', 'intercept').catch(() => {});
  await page.waitForTimeout(400);
  await spotlight(page, '#sync-state', 600);
  await page.click('#btn-fire');
  await page.waitForTimeout(3000);
  await page.click('#btn-wave');
  await page.waitForTimeout(6000);
  await pan(page, 200, 260, 1100, 560, 20, 22);
  await page.waitForTimeout(1200);

  // ACT 6 — Live View and return (~16s)
  console.log('[6] Live View…');
  await page.goto(`${BASE}/live_view.html?mode=boreal`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2200);
  await pan(page, 100, 150, 1300, 700, 18, 24);
  await spotlight(page, '.log-container, #log-stream, .live-log, .console-out', 700);
  await page.waitForTimeout(2000);
  await page.goto(`${BASE}/index.html`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1800);

  console.log('[DONE] Closing…');
  await context.close();
  await browser.close();
  console.log(`\n✅  Video saved to: ${VIDEO_DIR}`);
  console.log('Convert: ffmpeg -i video/page@*.webm -c:v libx264 -crf 18 video/cortex_demo_2min.mp4');
})();
