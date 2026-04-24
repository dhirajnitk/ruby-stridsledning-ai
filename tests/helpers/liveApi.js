/**
 * liveApi.js — Minimal route helper for LIVE engine tests.
 *
 * Unlike mockApi.js, this does NOT intercept any API calls.
 * Everything hits the real backend at port 8000.
 *
 * Only large binary assets that are irrelevant to the demo are blocked:
 *   - .mp4   (background video — not needed)
 *   - .pth   (PyTorch model weights — the backend already has these)
 *   - llm/proxy — blocked with a graceful fallback if no API key is set;
 *                 the /evaluate_advanced endpoint already generates its own
 *                 heuristic sitrep so the LLM proxy is optional.
 */
async function liveBackend(page) {
  // Block large binary assets only
  await page.route('**/*.mp4',  r => r.abort());
  await page.route('**/*.pth',  r => r.abort());

  // Block the LLM proxy — backend falls back to heuristic sitrep gracefully
  // (avoids a 503 error popping in the console if OPENROUTER_API_KEY is unset)
  await page.route('**/llm/proxy', r => r.fulfill({
    status: 200,
    contentType: 'text/event-stream',
    body: 'data: {"choices":[{"delta":{"content":"[LIVE ENGINE — LLM proxy disabled for demo]"}}]}\n\ndata: [DONE]\n\n',
  }));

  // Everything else (health, theater, state, evaluate_advanced, ws/logs, ...)
  // flows through to the real backend at port 8000 — no interception.
}

module.exports = { liveBackend };
