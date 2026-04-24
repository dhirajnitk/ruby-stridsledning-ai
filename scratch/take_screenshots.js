/**
 * Full-resolution screenshot capture script.
 * Runs headless Chromium at 1920x1080, saves PNGs to docs/video_prompts/
 */
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const BASE = path.resolve(__dirname, '../docs/video_prompts');
const BASE_URL = 'http://localhost:3001';

async function shot(page, filePath) {
  // Ensure directory exists
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  await page.screenshot({ path: filePath });
  console.log('  ✓', path.relative(BASE, filePath));
}

async function goto(page, url, wait = 3000) {
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 20000 });
  await page.waitForTimeout(wait);
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();

  // ── Scenario 01: Portal ────────────────────────────────────────────────────
  console.log('\n[S01] Portal + Dashboard + Live View');
  await goto(page, `${BASE_URL}/index.html`, 2000);
  await shot(page, `${BASE}/scenario_01/clip01_portal_main.png`);

  await goto(page, `${BASE_URL}/dashboard.html?mode=boreal`, 3000);
  await shot(page, `${BASE}/scenario_01/clip02_dashboard_boreal.png`);
  await page.evaluate(() => window.scrollTo(0, 300));
  await page.waitForTimeout(800);
  await shot(page, `${BASE}/scenario_01/clip03_dashboard_active_engagement.png`);
  await page.evaluate(() => window.scrollTo(0, 600));
  await page.waitForTimeout(800);
  await shot(page, `${BASE}/scenario_01/clip04_dashboard_mid_engagement.png`);

  await goto(page, `${BASE_URL}/live_view.html?mode=boreal`, 3500);
  await shot(page, `${BASE}/scenario_01/clip05_live_view_idle.png`);
  // Fire a saturation wave
  await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const w = btns.find(b => /saturation/i.test(b.textContent));
    if (w) w.click();
  });
  await page.waitForTimeout(2000);
  await shot(page, `${BASE}/scenario_01/clip06_live_view_active.png`);
  await shot(page, `${BASE}/scenario_01/clip07_live_view_engaged.png`);

  // ── Scenario 02: MIRV ─────────────────────────────────────────────────────
  console.log('\n[S02] MIRV');
  await goto(page, `${BASE_URL}/kinetic_3d.html?theater=boreal`, 3500);
  await shot(page, `${BASE}/scenario_02/clip01_kinetic3d_idle.png`);
  await page.selectOption('select:nth-of-type(2)', '💥 MIRV (3-Warhead Bus)');
  await page.waitForTimeout(500);
  await shot(page, `${BASE}/scenario_02/clip02_mirv_launch.png`);
  await page.click('button:has-text("FIRE DEMO")');
  await page.waitForTimeout(2500);
  await shot(page, `${BASE}/scenario_02/clip03_mirv_midphase.png`);
  await page.waitForTimeout(3000);
  await shot(page, `${BASE}/scenario_02/clip04_mirv_separation.png`);

  // ── Scenario 03: MARV ─────────────────────────────────────────────────────
  console.log('\n[S03] MARV');
  await goto(page, `${BASE_URL}/kinetic_3d.html?theater=boreal`, 3500);
  await shot(page, `${BASE}/scenario_03/clip01_marv_launch.png`);
  await page.selectOption('select:nth-of-type(2)', '⚡ MARV (Maneuvering RV)');
  await page.click('button:has-text("FIRE DEMO")');
  await page.waitForTimeout(2500);
  await shot(page, `${BASE}/scenario_03/clip02_marv_jink.png`);
  await page.waitForTimeout(3000);
  await shot(page, `${BASE}/scenario_03/clip03_marv_intercept.png`);

  // ── Scenario 04: Dogfight ─────────────────────────────────────────────────
  console.log('\n[S04] Dogfight');
  await goto(page, `${BASE_URL}/kinetic_3d.html?theater=boreal`, 3500);
  await page.selectOption('select:nth-of-type(2)', '✈ FIGHTER w/ Dogfight');
  await page.waitForTimeout(500);
  await shot(page, `${BASE}/scenario_04/clip01_dogfight_launch.png`);
  await page.click('button:has-text("FIRE DEMO")');
  await page.waitForTimeout(2500);
  await shot(page, `${BASE}/scenario_04/clip02_dogfight_merge.png`);
  await page.waitForTimeout(3000);
  await shot(page, `${BASE}/scenario_04/clip03_dogfight_outcome.png`);

  // ── Scenario 05: Saturation ───────────────────────────────────────────────
  console.log('\n[S05] Saturation Assault');
  await goto(page, `${BASE_URL}/kinetic_3d.html?theater=boreal`, 3500);
  await shot(page, `${BASE}/scenario_05/clip01_saturation_launch.png`);
  await page.click('button:has-text("SATURATION WAVE")');
  await page.waitForTimeout(2500);
  await shot(page, `${BASE}/scenario_05/clip02_saturation_mid.png`);
  await page.waitForTimeout(4000);
  await shot(page, `${BASE}/scenario_05/clip03_saturation_complete.png`);

  // Live view saturation for S05
  await goto(page, `${BASE_URL}/live_view.html?mode=boreal`, 3500);
  await shot(page, `${BASE}/scenario_05/clip04_live_view_saturation.png`);
  await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const w = btns.find(b => /saturation/i.test(b.textContent));
    if (w) w.click();
  });
  await page.waitForTimeout(2500);
  await shot(page, `${BASE}/scenario_05/clip05_live_view_mid.png`);
  await shot(page, `${BASE}/scenario_05/clip06_live_view_scoreboard.png`);

  // ── Scenario 06: Hypersonic ───────────────────────────────────────────────
  console.log('\n[S06] Hypersonic');
  await goto(page, `${BASE_URL}/kinetic_3d.html?theater=boreal`, 3500);
  await page.selectOption('select:nth-of-type(2)', 'HYPERSONIC GLIDE');
  await page.waitForTimeout(500);
  await shot(page, `${BASE}/scenario_06/clip01_hypersonic_launch.png`);
  await page.click('button:has-text("FIRE DEMO")');
  await page.waitForTimeout(3000);
  await shot(page, `${BASE}/scenario_06/clip02_hypersonic_terminal.png`);

  // ── Scenario 07: Cortex C2 ────────────────────────────────────────────────
  console.log('\n[S07] Cortex C2');
  await goto(page, `${BASE_URL}/cortex_c2.html?mode=boreal`, 4000);
  await shot(page, `${BASE}/scenario_07/clip01_c2_console_idle.png`);
  await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const hitl = btns.find(b => /hitl|human/i.test(b.textContent));
    if (hitl) hitl.click();
  });
  await page.waitForTimeout(1500);
  await shot(page, `${BASE}/scenario_07/clip02_c2_hitl_mode.png`);
  await page.evaluate(() => window.scrollTo(0, 400));
  await page.waitForTimeout(800);
  await shot(page, `${BASE}/scenario_07/clip03_c2_assignment_queue.png`);
  await page.evaluate(() => window.scrollTo(0, 800));
  await page.waitForTimeout(800);
  await shot(page, `${BASE}/scenario_07/clip04_c2_sitrep.png`);

  // ── Scenario 08: Sweden / Gotland ─────────────────────────────────────────
  console.log('\n[S08] Sweden/Gotland');
  await goto(page, `${BASE_URL}/kinetic_3d.html?theater=sweden`, 4000);
  await shot(page, `${BASE}/scenario_08/clip01_sweden_theater_idle.png`);
  await page.click('button:has-text("SATURATION WAVE")');
  await page.waitForTimeout(2500);
  await shot(page, `${BASE}/scenario_08/clip02_gotland_saturation.png`);
  await page.waitForTimeout(3500);
  await shot(page, `${BASE}/scenario_08/clip03_gotland_defense.png`);
  await page.waitForTimeout(3500);
  await shot(page, `${BASE}/scenario_08/clip04_gotland_complete.png`);

  // ── Scenario 09: Strategic 3D + Dataset Viewer ────────────────────────────
  console.log('\n[S09] Strategic 3D + Dataset Viewer');
  await goto(page, `${BASE_URL}/strategic_3d.html`, 4000);
  await shot(page, `${BASE}/scenario_09/clip01_strategic3d_load.png`);
  await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const b = btns.find(b => /load|czml|scenario|boreal/i.test(b.textContent));
    if (b) b.click();
  });
  await page.waitForTimeout(2000);
  await shot(page, `${BASE}/scenario_09/clip02_strategic3d_czml.png`);
  await page.waitForTimeout(2000);
  await shot(page, `${BASE}/scenario_09/clip03_strategic3d_hostile_manifest.png`);
  await page.waitForTimeout(2000);
  await shot(page, `${BASE}/scenario_09/clip04_strategic3d_intercept.png`);

  await goto(page, `${BASE_URL}/dataset_viewer.html`, 4000);
  await shot(page, `${BASE}/scenario_09/clip05_dataset_viewer.png`);
  await page.evaluate(() => window.scrollTo(0, 500));
  await page.waitForTimeout(800);
  await shot(page, `${BASE}/scenario_09/clip06_dataset_viewer_loaded.png`);

  // ── Scenario 10: Final Stand ──────────────────────────────────────────────
  console.log('\n[S10] Final Stand');
  await goto(page, `${BASE_URL}/kinetic_3d.html?theater=boreal`, 3500);
  await shot(page, `${BASE}/scenario_10/clip01_final_stand_wave.png`);
  // Degraded defense for drama
  await page.evaluate(() => {
    const sels = document.querySelectorAll('select');
    if (sels[4]) { sels[4].value = 'WAVE: DEGRADED'; sels[4].dispatchEvent(new Event('change')); }
  });
  await page.click('button:has-text("SATURATION WAVE")');
  await page.waitForTimeout(2500);
  await shot(page, `${BASE}/scenario_10/clip02_final_stand_results.png`);
  await page.waitForTimeout(3500);
  await shot(page, `${BASE}/scenario_10/clip03_final_stand_allkills.png`);
  await page.waitForTimeout(3500);
  await shot(page, `${BASE}/scenario_10/clip04_final_stand_complete.png`);

  await browser.close();
  console.log('\n✅ All screenshots captured.\n');
})().catch(err => { console.error(err); process.exit(1); });
