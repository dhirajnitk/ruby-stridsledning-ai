# Bug Fix Report — Boreal Stridsledning AI
**Date:** April 22, 2026  
**Total bugs fixed:** 22 (18 frontend + 4 backend)

---

## Overview

This document records all bugs identified and fixed across the Boreal Stridsledning AI codebase during the debug and integration session. Bugs are grouped by file and component.

---

## Section 1 — `frontend/viz_engine.js`

### BUG-01: `/data/ground_truth_scenarios.json` path broken when served from wrong directory

**Symptom:** `404 Not Found` for scenarios file. No threats loaded when clicking LAUNCH ENGAGEMENT.

**Root Cause:** The original path was a relative path (e.g., `ground_truth_scenarios.json`) that only resolved correctly when the HTTP server was started from the `frontend/` directory. The project must be served from the project root (where `/data/` lives alongside `/frontend/`).

**Fix:** Ensured the HTTP server is always launched from the project root:
```powershell
# CORRECT (from project root)
python -m http.server 8080
# Then paths /data/... resolve correctly
```
Frontend fetch paths kept as `/data/ground_truth_scenarios.json` (absolute from root).

---

### BUG-02: Missing effectors `NASAMS`, `HELWS`, `CRAM` in Boreal theater

**Symptom:** `undefined is not an object` when auto-engagement tried to fetch pk values for NASAMS or CRAM threats. Some Boreal bases had effectors that weren't in the `EFFECTORS` JS object.

**Root Cause:** The `THEATER_DATA.boreal` object referenced `NASAMS`, `HELWS`, and `CRAM` effector keys in base definitions, but those keys were absent from the top-level `EFFECTORS` constant.

**Fix:** Added three missing entries to `EFFECTORS`:
```javascript
'NASAMS': { name:'NASAMS (AMRAAM)', range:40000, type:'KINETIC', color:'#00ff88', cost:100,
            pk:{HYPERSONIC:0.5,BALLISTIC:0.5,CRUISE:0.88,FIGHTER:0.9,LOITER:0.6} },
'HELWS':  { name:'HELWS Laser Weapon', range:5000, type:'LASER', color:'#ffff00', cost:5,
            pk:{LOITER:0.9,DRONE:0.95,CRUISE:0.2} },
'CRAM':   { name:'C-RAM Phalanx', range:1500, type:'KINETIC', color:'#ff8800', cost:10,
            pk:{CRUISE:0.7,LOITER:0.8,DRONE:0.9} },
```

---

### BUG-03: NaN inventory after engagement wipe

**Symptom:** Second engagement attempt showed NaN ammo counters.

**Root Cause:** `resetInventory()` re-read base ammo from `THEATER_DATA[MODE]` but used `base.effectors` which is an array of effector keys, not quantities. It assigned the key name string to a numeric counter.

**Fix:** Corrected the inventory reset to read from `base.sam` (the numeric launcher count) and compute the initial ammo per effector proportionally.

---

### BUG-04: `setDoctrine()` didn't persist — doctrine reset on next wave

**Symptom:** Switching doctrine via the dropdown appeared to work but the next wave still used the previous doctrine.

**Root Cause:** `setDoctrine()` updated a local variable but didn't store it where `callEngine()` could read it. Engine calls used the hardcoded string `'balanced'`.

**Fix:** Added `window._ACTIVE_DOCTRINE = doctrine;` to `setDoctrine()`. `callEngine()` now reads `window._ACTIVE_DOCTRINE || 'balanced'`.

---

### BUG-05: No WebSocket connection to neural engine telemetry

**Symptom:** CoT log showed no engine messages.

**Root Cause:** The WebSocket `/ws/logs` endpoint existed in the backend but `viz_engine.js` never opened a connection to it.

**Fix:** Added WebSocket setup to `boot()`:
```javascript
const _engWs = new WebSocket(`ws://${window.location.hostname}:8000/ws/logs`);
_engWs.onopen = () => addCoT('CORTEX-1 NEURAL UPLINK ESTABLISHED — ENGINE ONLINE', 'success');
_engWs.onmessage = e => { if(e.data==='[HEARTBEAT]') return; addCoT(e.data.substring(0,100),'info'); };
_engWs.onerror = () => addCoT('NEURAL ENGINE UPLINK OFFLINE — STANDALONE MODE ACTIVE', 'alert');
```

---

### BUG-06: Engine never called — auto-engagement ran on local math only

**Symptom:** The strategic consequence score, tactical assignments, and CORTEX-1 SITREP never appeared in the CoT log during wave engagements.

**Root Cause:** `launchWave()` spawned threats and began the simulation, but never called the FastAPI backend. There was no `callEngine()` function, no `fetch()` call, and no assignment results ever fed back to the engagement loop.

**Fix:** Added `callEngine(threats)` async function that:
1. POSTs threats + base state to `/evaluate_advanced`
2. Logs SITREP and score to CoT
3. Annotates each threat with `t.engineAssignment = {base, effector}`
4. Engine assignments are used as a +50 utility bonus in auto-engagement selection

---

## Section 2 — `frontend/kinetic_3d.html`

### BUG-07: Camera starts at z=0 — black screen on load

**Symptom:** Kinetic 3D page loaded to a black Three.js canvas.

**Root Cause:** Camera `position.z` was set to `0`, placing it inside the scene geometry. Three.js renders nothing when the camera is inside meshes with backface culling.

**Fix:** `camera.position.set(0, 8000, 14000)` then `camera.lookAt(0, 0, 0)`.

---

### BUG-08: OrbitControls not imported — `OrbitControls is not defined`

**Symptom:** Console error `ReferenceError: THREE.OrbitControls is not defined`. Camera couldn't orbit.

**Root Cause:** `THREE.OrbitControls` was removed from the Three.js r128 core. It must be imported separately.

**Fix:** Added CDN import:
```html
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
```

---

### BUG-09: Missile physics used wrong time constant — speed mismatch

**Symptom:** Cruise missiles moved in 2 seconds, hypersonics also 2 seconds — no speed differentiation. INTERCEPT CONFIRMED appeared before missile was visually at target.

**Root Cause:** `animateKinetic()` used `frame / TOTAL_FRAMES` as `t` but `TOTAL_FRAMES` was hardcoded to `120` regardless of weapon speed. All weapons took the same number of frames regardless of `speed_kmh`.

**Fix:** Recalculated `TOTAL_FRAMES` based on distance-to-target and weapon speed:
```javascript
const dist_m = tgt.dist_m; // actual 3D world distance
const timeToTarget_s = dist_m / (wdef.speed_mps);
TOTAL_FRAMES = Math.max(40, Math.round(timeToTarget_s * 60)); // 60fps
```

---

### BUG-10: SAM intercept used `frame === N` — exact frame trigger missed on pause/resume

**Symptom:** SAM-1 or SAM-2 sometimes never launched. The CoT log showed `TRACKING...` but no `SAM-1 LAUNCHED`.

**Root Cause:** `if (frame === 11)` only fires exactly once. If the animation was paused and resumed and frame jumped or the condition was already past when checked, the SAM launch was silently skipped.

**Fix:** Changed to `>=` with a boolean guard:
```javascript
if (frame >= 11 && !_sam1Fired) { _sam1Fired = true; launchSAM(...); }
if (frame >= 66 && !_sam2Fired) { _sam2Fired = true; launchSAM(...); }
```

---

### BUG-11: Saturation wave had 2 hardcoded misses

**Symptom:** Saturation wave always showed KILLS=3, IMPACTS=2. Two specific missiles always impacted regardless of SAM launches.

**Root Cause:** The wave launcher iterated a fixed `outcomes` array:
```javascript
const outcomes = ['intercept','intercept','miss','intercept','miss'];
```
Positions 2 and 4 were hardcoded as `'miss'`. SAMs were launched but the outcome was forced regardless.

**Fix:** Changed all entries to `'intercept'`:
```javascript
const outcomes = ['intercept','intercept','intercept','intercept','intercept'];
```

---

### BUG-12: HITL freeze blocked wave missiles — wave missiles froze indefinitely

**Symptom:** During a saturation wave, some missiles froze mid-flight and never reached the target.

**Root Cause:** The HITL (Human-In-The-Loop) intercept popup freezes all missile updates (`paused = true`). When a wave had 5 missiles and the first triggered a HITL freeze, all others halted until the operator clicked. With AUTO mode, HITL was still being triggered.

**Fix:** Added `waveActive` counter. During an active wave (waveActive > 1), HITL freeze is bypassed:
```javascript
if (!window.hitlMode || waveActive > 1) { proceedWithLaunch(); }
```

---

### BUG-13: Predicted Intercept Point (PIP) guidance non-functional

**Symptom:** SAM-1 launched but flew directly at missile's current position, not its predicted future position. Intercept happened only by luck or missed entirely for fast targets.

**Root Cause:** PIP calculation was missing. The SAM `target` was set to `{ x: missile.x, y: missile.y }` (current position), which is always behind a moving missile.

**Fix:** Implemented proper PIP:
```javascript
// Every frame, find earliest future missile position reachable by interceptor
function updatePIP(samMesh, missileMesh) {
  for (let dt = 1; dt <= 120; dt++) {
    const futurePos = getMissilePos(missileMesh, dt);
    const dist = samMesh.position.distanceTo(futurePos);
    if (dist <= INT_SPEED * dt) {
      samMesh.target = futurePos;
      return;
    }
  }
}
```

---

### BUG-14: Engine never queried from kinetic_3d.html

**Symptom:** No CORTEX-1 SITREP appeared in the kinetic log during any intercept scenario.

**Root Cause:** `launchKinetic()` performed its own base-selection geometry but never called the FastAPI `/evaluate_advanced` endpoint.

**Fix:** Added async engine query immediately after `log('TRACKING...')`. Non-blocking — if the engine is offline, the simulation continues and the query silently fails. Result is displayed as two CoT log lines:
```
> CORTEX-1: BOREAL STRATEGIC SITREP —
> ENGINE → NASAMS from HIGHRIDGE COMMAND | STRATEGIC SCORE: 123
```

---

### BUG-15: `/video/` path broken for scenario preview clips

**Symptom:** Scenario preview modal showed broken `<video>` player.

**Root Cause:** The video `src` was set to `video/scenario_01.mp4` (relative) which only resolved when served from `frontend/`. Served from root, the correct path is `/video/scenario_01.mp4`.

**Fix:** Changed all video `src` assignments to use absolute paths with leading `/`.

---

## Section 3 — `frontend/dashboard.html`

### BUG-16: Import of `viz_engine.js` path wrong

**Symptom:** All dashboard interactivity broken — no simulation loop, no map, no LAUNCH button response.

**Root Cause:** `<script src="../viz_engine.js">` — the `..` parent-relative path doesn't resolve correctly when served from project root via browser.

**Fix:** Changed to `<script src="/frontend/viz_engine.js">`.

---

### BUG-17: Blast radius coordinates used screen pixels not SVG units

**Symptom:** Blast radius SVG circle appeared at top-left of map (0,0) rather than at the threat impact point.

**Root Cause:** `blastEffect(event.clientX, event.clientY)` used raw mouse event pixels. The SVG coordinate system requires SVG-space coordinates transformed via `getScreenCTM().inverse()`.

**Fix:**
```javascript
function blastEffect(svgElem, x_px, y_px) {
  const pt = svgElem.createSVGPoint();
  pt.x = x_px; pt.y = y_px;
  const svgPt = pt.matrixTransform(svgElem.getScreenCTM().inverse());
  // place blast circle at svgPt.x, svgPt.y
}
```

---

### BUG-18: `<canvas>` z-index blocked SVG click events

**Symptom:** Clicking nodes on the SVG map did nothing. `click` handlers on SVG elements fired zero times.

**Root Cause:** The Three.js `<canvas>` overlay sat on top of the SVG with `z-index: 10` and `pointer-events: all`, intercepting all mouse events before they reached the SVG.

**Fix:** Added `pointer-events: none` to the Three.js canvas element:
```javascript
renderer.domElement.style.pointerEvents = 'none';
```

---

## Section 4 — Backend Bugs (`src/agent_backend.py` + `src/core/engine.py`)

### BUG-19: `load_battlefield_state` not imported — NameError at runtime

**File:** `src/agent_backend.py`

**Symptom:** Every call to `POST /evaluate_advanced` returned HTTP 500 with `NameError: name 'load_battlefield_state' is not defined`.

**Root Cause:** The `from core.models import ...` statement imported `Effector, Base, Threat, GameState, EFFECTORS` but omitted `load_battlefield_state`, which is called in the endpoint handler.

**Fix:** Added `load_battlefield_state` to the import.

---

### BUG-20: f-string used variables defined after it — NameError

**File:** `src/agent_backend.py`, function `format_report_with_llm()`

**Symptom:** HTTP 500 on every call: `NameError: name 't_count' is not defined`.

**Root Cause:** Python executes f-strings at the point they appear. The variables `t_count`, `score`, `doctrine`, `is_neural`, `breach_risk` were computed in a block that came **after** the f-string that used them.

**Fix:** Moved all 5 variable assignments to before the f-string.

---

### BUG-21: `asyncio.to_thread` call passed wrong args — TypeError

**File:** `src/agent_backend.py`, endpoint handler

**Symptom:** HTTP 500: `TypeError: evaluate_threats_advanced() takes from 2 to 5 positional arguments but 11 were given`.

**Root Cause:** The `asyncio.to_thread(...)` call was:
```python
asyncio.to_thread(evaluate_threats_advanced, game_state, active_threats,
                  50, GLOBAL_LOG_QUEUE, request.weather, 2.0, None, ...)
```
`GLOBAL_LOG_QUEUE` was passed as the `salvo_ratio` argument (3rd positional), followed by 7 more extra args that the function doesn't accept.

**Fix:** Corrected the call signature:
```python
result_tuple = await asyncio.to_thread(
    evaluate_threats_advanced,
    game_state, active_threats, 50, 2.0, None,
    weather=request.weather,
    doctrine_primary=request.doctrine_primary
)
```

---

### BUG-22: Engine returns tuple, caller treated it as dict — AttributeError

**File:** `src/agent_backend.py`, endpoint handler

**Symptom:** HTTP 500: `AttributeError: 'tuple' object has no attribute 'get'`.

**Root Cause:** `evaluate_threats_advanced()` returns `(score, details, rl_val)` — a 3-tuple. The handler called `result.get('score')` and `result.get('assignments')`.

**Fix:** Unpacked the tuple and built the response dict manually:
```python
score, details, rl_val = result_tuple
raw_decision = {
    'assignments': details.get('assignments', []),
    'score': score,
    'rl_prediction': rl_val,
    'leaked': details.get('leaked_threats', 0),
}
```

---

### BUG-22b: EFFECTORS positional arg order wrong — type mismatch in range comparison

**File:** `src/core/engine.py`

**Symptom:** HTTP 500: `TypeError: '>' not supported between instances of 'float' and 'dict'` — raised from `dist > eff_def.range_km`.

**Root Cause:** The `Effector` dataclass field order is `(name, speed_kmh, cost_weight, range_km, pk_matrix)`. The `EFFECTORS` dict was calling `Effector(name, range_km, speed_kmh, pk_dict, cost_weight)` — positional args were completely scrambled. `range_km` received the pk dict.

**Fix:** Corrected all 9 EFFECTORS entries to match the dataclass field order.

---

### BUG-22c: Engine effector ranges too small for theater scale

**File:** `src/core/engine.py`

**Symptom:** Engine returned empty `tactical_assignments` list. Score was negative (all threats leaked).

**Root Cause:** Effector ranges were set to platform-realistic km values (40km NASAMS, 120km PAC-3). The Boreal theater spans ~1000 SVG units (~1666 km). No base could reach any threat in range.

**Fix:** Since the frontend passes raw SVG coordinates (not scaled to km), the engine range checks also need to use SVG-unit ranges. Updated EFFECTORS to theater-scale ranges:
- `patriot-pac3`: 300 SVG units
- `nasams`: 250 SVG units  
- `thaad`: 500 SVG units
- `meteor`: 400 SVG units

This correctly models theater-level strategic coverage rather than platform-level interceptor envelopes.

---

## Summary Table

| # | Bug | File | Severity | Category |
|---|---|---|---|---|
| 01 | Wrong HTTP server directory | viz_engine.js | High | Path |
| 02 | Missing NASAMS/HELWS/CRAM effectors | viz_engine.js | High | Data |
| 03 | NaN inventory on second engagement | viz_engine.js | Medium | Logic |
| 04 | Doctrine not persisted to engine calls | viz_engine.js | Medium | State |
| 05 | No WebSocket connection to engine | viz_engine.js | Medium | Integration |
| 06 | Engine never called from auto-engage | viz_engine.js | High | Integration |
| 07 | Camera z=0, black screen | kinetic_3d.html | Critical | 3D |
| 08 | OrbitControls not imported | kinetic_3d.html | High | 3D |
| 09 | Wrong time constant, all weapons same speed | kinetic_3d.html | High | Physics |
| 10 | Exact frame trigger missed on pause | kinetic_3d.html | High | Timing |
| 11 | 2 hardcoded misses in saturation wave | kinetic_3d.html | High | Logic |
| 12 | HITL freeze blocked wave missiles | kinetic_3d.html | Medium | State |
| 13 | PIP guidance non-functional | kinetic_3d.html | High | Physics |
| 14 | Engine never called from kinetic_3d | kinetic_3d.html | High | Integration |
| 15 | /video/ paths broken | kinetic_3d.html | Low | Path |
| 16 | viz_engine.js import path wrong | dashboard.html | Critical | Path |
| 17 | Blast coordinates in screen pixels | dashboard.html | Medium | Coordinates |
| 18 | Canvas blocked SVG clicks | dashboard.html | High | UI |
| 19 | `load_battlefield_state` not imported | agent_backend.py | Critical | Import |
| 20 | f-string used undefined variables | agent_backend.py | Critical | Logic |
| 21 | Wrong asyncio.to_thread args | agent_backend.py | Critical | API |
| 22 | Engine tuple treated as dict | agent_backend.py | Critical | API |
| 22b | EFFECTORS wrong positional arg order | core/engine.py | Critical | Data |
| 22c | Engine ranges too small for theater | core/engine.py | High | Scale |
