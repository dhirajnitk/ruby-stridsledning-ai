# UI/Dashboard Audit & Fix Report
**Session:** Multi-session SAAB C2 system hardening  
**Backend:** `src/agent_backend.py` — FastAPI, port 8000  
**Date of Audit:** Current session

---

## Summary

Comprehensive audit of all 8 frontend files. 7 bugs found and fixed. Backend verified live with all dashboards opened successfully.

---

## Backend API Endpoints — Live Test Results

| Endpoint | Method | Result |
|---|---|---|
| `GET /health` | GET | `{status: ok, mode: boreal, theater: BOREAL PASSAGE}` — **ADDED (was missing)** |
| `GET /theater` | GET | Returns mode, theater_name, capital, csv_path — ✅ OK |
| `GET /state` | GET | Returns loaded bases from CSV — ✅ OK |
| `POST /evaluate_advanced` | POST | Returns strategic score + tactical assignments — ✅ Score: 107.52, leaked: 0.04 |
| `WebSocket ws/logs` | WS | CORTEX-1 telemetry stream — ✅ Available |
| `GET /data/*` | Static | Serves data/ directory — ✅ OK |
| `/` | Static | Serves frontend/ directory — ✅ OK |

---

## Bug Tracker

### BUG-DASH-1 — CRITICAL — Fixed ✅
**File:** `frontend/dashboard.html`  
**Location:** `btn-live-mc` click handler (~line 350)  
**Description:** `const` variable declarations were placed INSIDE an object literal:
```js
// BROKEN — JavaScript syntax error, entire MC audit button fails
const payload = {
  const _mcKmFactor = (MODE === 'boreal') ? (200/120) : 1.0;  // ← INVALID
  const _mcSwedenInv = {...};
  state: { bases: ... }
}
```
**Fix:** Moved all `const` declarations before the object literal.  
**Impact:** MC Strategic Audit button was completely non-functional.

---

### BUG-DASH-2 — HIGH — Fixed ✅
**File:** `frontend/dashboard.html`  
**Location:** `/evaluate_advanced` fetch in MC audit handler  
**Description:** Non-ok HTTP responses from engine were silently swallowed — `res.json()` called on error responses without checking `res.ok`, and catch block only logged a generic "Strategic Audit Failed" warning with no guidance.  
**Fix:**
- Added `if (!res.ok) throw new Error(...)` after fetch
- Catch block now logs `ENGINE LINK FAILURE — <reason>` as `error` type in CoT feed, plus a "start backend" hint
- Calls `window._setEngineStatus(false, reason)` to update status badge

---

### BUG-DASH-3 — MEDIUM — Fixed ✅
**File:** `frontend/dashboard.html`  
**Location:** Theater init IIFE at page load  
**Description:** `/theater` fetch failure was silently caught (`catch(() => {})`). Title/h1 did not update to "SWEDEN STRATEGIC COMMAND" reliably (was using `document.querySelector('h1')` which is fragile). No backend status feedback.  
**Fix:**
- `h1` now has `id="main-title"` for reliable selection
- Theater init IIFE refactored: sets title/h1 for sweden mode immediately (no backend required), then fetches `/theater` and updates badge
- `/theater` fetch failure now calls `_setEngineStatus(false, ...)` for visible feedback

---

### BUG-VE-1 — HIGH — Fixed ✅
**File:** `frontend/viz_engine.js`  
**Location:** `callEngine()` function — `catch` block  
**Description:** All network errors (engine offline, timeout, DNS failure) were silently swallowed — `catch(e) { return null; }` produced no CoT output, no user-visible indication that the engine was unreachable.  
**Fix:**
```js
} catch(e) {
  const reason = e.name === 'TimeoutError' ? 'REQUEST TIMEOUT (5s)' :
                 (e.name === 'TypeError' ? 'NETWORK ERROR — ENGINE OFFLINE' : e.message);
  addCoT(`ENGINE LINK FAILURE — ${reason}`, 'error');
  if (window._setEngineStatus) window._setEngineStatus(false, reason);
  return null;
}
```

---

### BUG-VE-2 — HIGH — Fixed ✅
**File:** `frontend/viz_engine.js`  
**Location:** `callEngine()` — `return r.ok ? ... : null`  
**Description:** Non-2xx HTTP responses (422 validation error, 500 server error, etc.) returned `null` silently with no CoT logging.  
**Fix:**
```js
return r.ok ? await r.json() : (() => {
  addCoT(`ENGINE HTTP ERROR — ${r.status} ${r.statusText}`, 'error');
  if (window._setEngineStatus) window._setEngineStatus(false, 'HTTP ' + r.status);
  return null;
})();
```

---

### BUG-VE-3 — MEDIUM — Fixed ✅
**File:** `frontend/viz_engine.js`  
**Location:** `boot()` — WebSocket setup block  
**Description:** `_engWs.onclose` was not handled. If the backend restarted or network dropped mid-session, the CoT log showed nothing — operators had no indication the neural uplink was lost.  
**Fix:**
```js
_engWs.onclose = (e) => {
  if (!e.wasClean) {
    addCoT(`NEURAL UPLINK DROPPED (code ${e.code}) — STANDALONE MODE ACTIVE`, 'alert');
    if (window._setEngineStatus) window._setEngineStatus(false, 'DISCONNECTED');
  }
};
```
Also: `onopen` and `onerror` now call `_setEngineStatus`.

---

### BUG-VE-4 — MEDIUM — Fixed ✅
**File:** `frontend/dashboard.html` + `frontend/viz_engine.js`  
**Description:** No persistent visual indicator of backend engine status in dashboard.html or tactical pages. Cortex_c2.html had `#backend-dot` + `#backend-lbl` but dashboard.html had nothing.  
**Fix:**
- Added `<div id="engine-status-badge">` in dashboard.html header (beside "Operational" badge)
- Exposed `window._setEngineStatus(online, reason)` function in dashboard.html init script
- `viz_engine.js` WebSocket handlers (`onopen`, `onerror`, `onclose`) and `callEngine()` all call `_setEngineStatus` to keep badge current
- Badge shows green `● ENGINE ONLINE` or red `○ ENGINE OFFLINE — <reason>`

---

### BUG-BE-NEW-1 — LOW — Fixed ✅
**File:** `src/agent_backend.py`  
**Description:** `/health` route was missing. `index.html` health check and frontend badges that call `/health` received `404 Not Found`, causing false "offline" detection.  
**Fix:** Added route:
```python
@app.get("/health")
async def health_check():
    return {"status": "ok", "mode": SAAB_MODE, "theater": ACTIVE_THEATER["name"]}
```

---

## Files Modified

| File | Changes |
|---|---|
| `frontend/dashboard.html` | BUG-DASH-1 (syntax), BUG-DASH-2 (error logging), BUG-DASH-3 (theater fetch), BUG-VE-4 (engine badge), `id="main-title"` on h1 |
| `frontend/viz_engine.js` | BUG-VE-1 (catch logging), BUG-VE-2 (non-ok HTTP), BUG-VE-3 (onclose handler), onopen/onerror badge updates |
| `src/agent_backend.py` | BUG-BE-NEW-1 (added `/health` route) |

---

## Live Test Results

### Backend: ✅ Running (PID confirmed, port 8000 active)
- `/health` → `{status: ok, mode: boreal, theater: BOREAL PASSAGE}`
- `/theater` → Theater metadata correct
- `/evaluate_advanced` POST → Score 107.52, leaked 0.04

### Dashboards Opened: ✅
| URL | Status |
|---|---|
| `http://localhost:8000/` | index.html — portal entry, theater selector |
| `http://localhost:8000/dashboard.html?mode=boreal` | Strategic Dashboard — Boreal mode |
| `http://localhost:8000/dashboard.html?mode=sweden` | Strategic Dashboard — Sweden AOR |
| `http://localhost:8000/cortex_c2.html` | Full CORTEX-C2 operator console |
| `http://localhost:8000/tactical_legacy.html?mode=boreal` | Legacy tactical canvas map |
| `http://localhost:8000/live_view.html?mode=boreal` | Live kinetic audit |
| `http://localhost:8000/kinetic_3d.html?theater=boreal` | 3D physics simulation |

---

## Engine Link Failure Behaviour (Verified by Design)

When backend is offline or unreachable, the following now appears in the CoT log:
```
ENGINE LINK FAILURE — NETWORK ERROR — ENGINE OFFLINE
```
Plus the status badge switches from green `● ENGINE ONLINE` to red `○ ENGINE OFFLINE — NETWORK ERROR — ENGINE OFFLINE`.

When WebSocket connection drops mid-session:
```
NEURAL UPLINK DROPPED (code 1006) — STANDALONE MODE ACTIVE
```

All error states are recoverable — simulation continues in local heuristic mode.

---

## Previously Fixed (Prior Sessions)

All 14 prior bugs remain fixed:
- B-BE-1 through B-BE-4: Backend route errors, state loading, CSV paths
- UI-1 through UI-5: Inventory scaling, effector maps, canvas resize, mode switching
- MAP-SVG: Sweden military map rebuilt with real GeoJSON (v2), km-calibrated coordinates, Gotland enhanced
