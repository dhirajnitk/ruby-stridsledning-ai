/**
 * Mock all backend API calls so tests run fully offline (no port 8000 needed).
 * Call await mockBackend(page) before navigating to any page.
 */
async function mockBackend(page) {
  const HEALTH = { status: 'ok', mode: 'boreal', theater: 'BOREAL PASSAGE' };
  const THEATER = { name: 'BOREAL PASSAGE', mode: 'boreal' };
  const STATE = { bases: [], threats: [] };
  const EVAL = {
    tactical_assignments: [
      { threat_id: 'T-01', base: 'NORTHERN VANGUARD', base_name: 'NORTHERN VANGUARD', effector: 'nasams', weapon: 'nasams' },
      { threat_id: 'T-02', base: 'HIGHRIDGE COMMAND',  base_name: 'HIGHRIDGE COMMAND',  effector: 'thaad',  weapon: 'thaad'  },
    ],
    strategic_consequence_score: 875.0,
    rl_prediction: 720.0,
    leaked: 0,
    active_doctrine: {
      primary: 'aggressive',
      secondary: 'none',
      blend_ratio: '70/30',
      flags: { enable_saturation: true, enable_economy: false },
      weights: {},
    },
    human_sitrep: '--- BOREAL SITREP ---\nCORTEX-1 NEURAL EVAL: 2 threats engaged. Score: 875. Doctrine: AGGRESSIVE.',
    mc_metrics: { survival_rate_pct: 82, intercept_rate_pct: 94, mean_score: 875 },
  };

  // REST routes
  await page.route('**/health',             r => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(HEALTH)  }));
  await page.route('**/theater',            r => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(THEATER) }));
  await page.route('**/state',              r => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(STATE)   }));
  await page.route('**/evaluate_advanced',  r => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(EVAL)    }));
  await page.route('**/get_dataset_sample', r => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ scenarios: [] }) }));
  await page.route('**/llm/proxy',          r => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ choices: [{ delta: { content: 'MOCK LLM RESPONSE' } }] }) }));

  // Block WebSocket upgrades cleanly (viz_engine.js handles ws.onerror silently)
  await page.route('**/ws/**',  r => r.abort());
  await page.route('**/*.mp4',  r => r.abort()); // skip video loading
  await page.route('**/*.pth',  r => r.abort()); // model weights not needed for UI
}

module.exports = { mockBackend };
