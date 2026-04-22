# Boreal Chessmaster — System Architecture & Neural Engine Integration
**Date:** April 22, 2026  
**Status:** All integrations live and browser-verified

---

## Table of Contents
1. [Architecture Overview](#1-architecture-overview)
2. [Before Integration — What Was Disconnected](#2-before-integration--what-was-disconnected)
3. [After Integration — Full Data Flow](#3-after-integration--full-data-flow)
4. [Component Deep Dives](#4-component-deep-dives)
5. [Neural Engine API Contract](#5-neural-engine-api-contract)
6. [Frontend Integration Points](#6-frontend-integration-points)
7. [Pre-existing Backend Bugs Fixed](#7-pre-existing-backend-bugs-fixed)
8. [Live Test Results](#8-live-test-results)
9. [Running the Stack](#9-running-the-stack)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│  BROWSER                                                                │
│  ┌──────────────────────────┐    ┌──────────────────────────────────┐  │
│  │  dashboard.html          │    │  kinetic_3d.html                 │  │
│  │  (Strategic Map)         │    │  (3D Intercept Simulator)        │  │
│  │                          │    │                                  │  │
│  │  viz_engine.js           │    │  Standalone JS physics engine    │  │
│  │  ├─ 2D SVG threat map    │    │  ├─ Three.js 3D scene            │  │
│  │  ├─ 3D Three.js scene    │    │  ├─ Predicted Intercept Point    │  │
│  │  ├─ Auto-engagement loop │    │  │  guidance (PIP)               │  │
│  │  ├─ BroadcastChannel ────┼────┼─►├─ Salvo SAM-1 + SAM-2         │  │
│  │  │  saab_kinetic_v8      │    │  ├─ Radar lock physics           │  │
│  │  └─ callEngine() ─────── ┼────┼──►└─ Neural engine query         │  │
│  └──────────┬───────────────┘    └──────────────┬───────────────────┘  │
│             │ POST /evaluate_advanced             │ POST /evaluate_advanced
│             │ WS  /ws/logs                        │                      │
└─────────────┼─────────────────────────────────────┼──────────────────────┘
              │                                     │
              ▼  http://localhost:8000              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  FASTAPI BACKEND  (src/agent_backend.py)                                │
│                                                                         │
│  POST /evaluate_advanced                                                │
│  ├─ Accepts: threats[], state.bases[], weather, doctrine, use_rl       │
│  ├─ Calls: core/engine.py → TacticalEngine.get_optimal_assignments()   │
│  │         → StrategicMCTS.run_mcts_rollout()                          │
│  │         → format_report_with_llm() → CORTEX-1 SITREP               │
│  └─ Returns: tactical_assignments[], strategic_score, rl_prediction,   │
│              human_sitrep, active_doctrine                              │
│                                                                         │
│  WS /ws/logs                                                            │
│  └─ Streams: real-time engine telemetry to CoT log                     │
│                                                                         │
│  core/engine.py                                                         │
│  ├─ TacticalEngine: Hungarian-style utility assignment                  │
│  ├─ StrategicMCTS: Monte Carlo rollouts (50 iterations)                │
│  └─ EFFECTORS: PAC-3, NASAMS, THAAD, METEOR, Coyote, LIDS-EW          │
│                                                                         │
│  models/                                                                │
│  ├─ elite_v3_5.pth    (TRANSFORMER-RESNET, Pk 97.8%)                   │
│  ├─ hybrid_rl.pth     (RESNET-128 + RL,    Pk 87.5%)                   │
│  ├─ titan.pth         (SELF-ATTENTION,      Pk 90.8%)                  │
│  ├─ supreme_v3_1.pth  (CHRONOS GRU,         Pk 94.2%)                  │
│  └─ boreal_chronos_gru.pth                                             │
└─────────────────────────────────────────────────────────────────────────┘
              │
              │ Serves at http://localhost:8080 (python -m http.server)
┌─────────────▼───────────────────────────────────────────────────────────┐
│  FILESYSTEM (project root)                                              │
│  /frontend/    dashboard.html, kinetic_3d.html, live_view.html          │
│  /data/        model_benchmarks.json, ground_truth_scenarios.json       │
│  /models/      *.pth PyTorch weights                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Before Integration — What Was Disconnected

Prior to this integration session, all three layers were **completely independent**:

| Component | What it was doing | What it should do |
|---|---|---|
| `agent_backend.py` | Running on port 8000, serving `/evaluate_advanced` | Same, but it was broken (3 bugs caused 500 errors) |
| `viz_engine.js` | Auto-engagement used local JS math only — Pk was a hardcoded number from `MODEL_PROFILES[]` | Call `/evaluate_advanced` per wave, get real engine assignments |
| `kinetic_3d.html` | `launchKinetic()` chose defender base by its own nearest-base geometry | Ask engine which effector to use, display CORTEX-1 SITREP |
| WebSocket `/ws/logs` | Existed in backend, never connected from frontend | Stream engine telemetry into CoT log in real time |
| `setModel()` button | Changed a number displayed on screen | Still same (model switch does not yet hot-reload a `.pth` file — see §6) |

**Why wasn't it connected?** Three pre-existing bugs in `agent_backend.py` caused every call to `/evaluate_advanced` to return HTTP 500, silently. The frontend code also never had `fetch('http://localhost:8000/...')` calls — there was simply no integration code.

---

## 3. After Integration — Full Data Flow

### Wave Engagement Flow (dashboard.html)

```
User clicks LAUNCH ENGAGEMENT
        │
        ▼
startEngagement() in viz_engine.js
  │  Resets stats, inits ammo
  │  calls launchWave()
  │    Loads ground_truth_scenarios.json[currentScenarioIdx]
  │    Spawns Threat objects on SVG map
  │
  └─► callEngine(threats[])   ← NEW: async, non-blocking
        │  POST /evaluate_advanced
        │  body: { state:{bases from BASES[]}, threats[], doctrine }
        │
        ▼
  agent_backend.py /evaluate_advanced
    ├─ load_battlefield_state() if no state provided
    ├─ TacticalEngine.get_optimal_assignments()
    │    Scores all (base × threat × effector) triples
    │    Selects optimal by utility = threat_class_mult × pk × 700
    │    Respects salvo_ratio=2 (each threat gets 2 interceptors)
    ├─ StrategicMCTS.run_mcts_rollout() × 50 iterations
    └─ Returns: { tactical_assignments[], strategic_score, human_sitrep }
        │
        ▼
  callEngine() receives result
    ├─ Logs CORTEX-1 SITREP → addCoT() → CoT panel
    ├─ Logs NEURAL SCORE + LEAKED PROJECTION → addCoT()
    └─ For each assignment: annotates threat.engineAssignment = {base, effector}
        │
        ▼
  updateSimulation() runs at 5Hz
    For each threat, auto-engagement finds best (base, effector) pair:
    ├─ Builds candidates[] = all in-range (base, effector) pairs
    ├─ utility = (pk×100) - (distance/100000) + engineBonus
    │            ↑ engineBonus = +50 if engine recommended this effector
    └─ Picks candidates[0] (highest utility)
```

### Kinetic 3D Flow (kinetic_3d.html)

```
User clicks FIRE DEMO or SATURATION WAVE
        │
        ▼
launchKinetic(theater, weaponKey, outcome)
  │  Spawns missile mesh
  │  Finds 2 closest non-HVA defender bases (defBases[])
  │
  └─► Neural Engine Query (async, non-blocking)   ← NEW
        POST /evaluate_advanced
        body: { state:{defBases as km coords}, threats:[current missile] }
        
        On response:
        ├─ log(`CORTEX-1: ${sitrep}`)
        └─ log(`ENGINE → ${effector} from ${base} | SCORE: ${score}`)
  │
  │  SAM-1 at frame 11 (t=0.05):  from defBases[0]
  │  SAM-2 at frame 66 (t=0.30):  from defBases[1] (SALVO)
  │
  └─► Predicted Intercept Point guidance every frame
        Finds earliest future missile position reachable by interceptor
        at INT_SPEED=18000 m/frame
```

### WebSocket Live Telemetry Flow

```
Backend startup → asyncio task: log_broadcaster()
  Polls GLOBAL_LOG_QUEUE every 100ms
  Broadcasts to all /ws/logs subscribers

viz_engine.js boot() → new WebSocket('ws://localhost:8000/ws/logs')
  onopen:    addCoT('CORTEX-1 NEURAL UPLINK ESTABLISHED — ENGINE ONLINE', 'success')
  onmessage: addCoT(message, 'info')   ← engine telemetry appears in CoT log
  onerror:   addCoT('NEURAL ENGINE UPLINK OFFLINE — STANDALONE MODE ACTIVE', 'alert')
```

---

## 4. Component Deep Dives

### 4.1 `core/engine.py` — TacticalEngine

The weapon-target assignment algorithm is a **greedy utility maximizer** (not true Hungarian — it approximates it by pre-sorting all pairs by utility):

```python
def _calculate_utility(base, threat, effector, weights, flags):
    dist = hypot(base.x - threat.x, base.y - threat.y)
    t_arrival_mins = (dist / threat.speed_kmh) * 60.0

    utility = 150.0
    class_mult = { 'hypersonic': 5.0, 'ballistic': 5.0, 'fighter': 3.5, 'drone': 0.4 }
    utility *= class_mult.get(threat_type, 1.0)

    pk = effector.pk_matrix.get(threat_type, 0.5)
    utility += pk * 700.0        # kill probability dominates
    utility -= effector.cost * 0.8
    if t_arrival_mins < 2.0: utility += 1000.0   # time-critical bonus
    if threat.heading == base.name: utility += 200.0  # direct-approach bonus
    return utility
```

Then `StrategicMCTS.run_mcts_rollout()` runs 50 Monte Carlo simulations of the plan, each sampling probabilistic kill outcomes, computing a final strategic health score.

### 4.2 `viz_engine.js` — Auto-Engagement Engine Bonus

When the neural engine recommends a specific effector for a threat, the local JS auto-engagement loop rewards that choice with +50 utility:

```javascript
const engKey = t.engineAssignment 
    ? (ENGINE_EFF_MAP[MODE]?.[t.engineAssignment.effector] || null) 
    : null;
const engineBonus = (engKey && effKey === engKey) ? 50 : 0;
const utility = (pk * 100) - (dToBase / 100000) + engineBonus;
```

This means: if the neural engine says "use NASAMS" and the local loop also computes NASAMS as best by pk/range, the +50 bonus acts as a tiebreaker. If local geometry strongly favors a different effector (e.g., PAC-3 is 50% closer), local geometry can still override the engine.

### 4.3 Coordinate System

| Context | Unit | Notes |
|---|---|---|
| Boreal theater (SVG/viz) | SVG grid units (0–854 × 0–742) | `1 unit ≈ 1.666 km` |
| Sweden theater (SVG/viz) | km offset from Stockholm | `F21 at (185, 691)` = 185 km east, 691 km north |
| 3D scene | meters | `x_world = svg_x × 1666` |
| Engine (after integration) | SVG units passed directly | Engine EFFECTORS use theater-unit ranges (250–500) |

---

## 5. Neural Engine API Contract

### Request: `POST http://localhost:8000/evaluate_advanced`

```json
{
  "state": {
    "bases": [
      {
        "name": "NORTHERN VANGUARD",
        "x": 119,
        "y": 197,
        "inventory": { "patriot-pac3": 40, "nasams": 20 }
      }
    ]
  },
  "threats": [
    {
      "id": "T1",
      "x": 400,
      "y": 300,
      "speed_kmh": 800,
      "estimated_type": "cruise-missile",
      "threat_value": 60
    }
  ],
  "weather": "clear",
  "doctrine_primary": "balanced",
  "use_rl": true
}
```

**Threat type values:** `cruise-missile`, `hypersonic-pgm`, `ballistic`, `drone`, `fighter`, `decoy`

**Doctrine values:** `balanced`, `aggressive`, `fortress`

### Response

```json
{
  "tactical_assignments": [
    {
      "threat_id": "T1",
      "base": "NORTHERN VANGUARD",
      "effector": "patriot-pac3"
    },
    {
      "threat_id": "T1",
      "base": "NORTHERN VANGUARD",
      "effector": "nasams"
    }
  ],
  "strategic_consequence_score": 123.4,
  "rl_prediction": null,
  "leaked": 0.3,
  "human_sitrep": "--- BOREAL STRATEGIC SITREP ---\nPOSTURE: BALANCED...\nADVISORY: WEAPONS FREE",
  "active_doctrine": {
    "primary": "balanced",
    "secondary": "none",
    "blend_ratio": "50/50"
  }
}
```

**Effector keys returned:** `patriot-pac3`, `nasams`, `thaad`, `meteor`, `iris-t-sls`, `coyote-block2`, `lids-ew`

### WebSocket: `ws://localhost:8000/ws/logs`

Streams newline-terminated strings:
- `[STRAT] Monitoring Boreal sector... NEURAL BRAIN: STANDBY` — idle pulse every 8s
- `[HEARTBEAT]` — keep-alive every 15s (filtered by frontend)
- Custom log messages from engine evaluation runs

---

## 6. Frontend Integration Points

### 6.1 `ENGINE_EFF_MAP` — Backend-to-Frontend Effector Translation

The backend uses `patriot-pac3`, `nasams` etc. The frontend uses `PAC3`, `NASAMS` etc. A translation map bridges them:

```javascript
const ENGINE_EFF_MAP = {
  boreal: {
    'patriot-pac3': 'PAC3',
    'nasams':       'NASAMS',
    'thaad':        'THAAD',
    'iris-t-sls':   'PAC3',
    'coyote-block2':'COYOTE2',
    'meteor':       'PAC3',
    'lids-ew':      'COYOTE3'
  },
  sweden: {
    'patriot-pac3': 'LV-103',
    'nasams':       'LV-103',
    'iris-t-sls':   'E98',
    'meteor':       'METEOR',
    'saab-nimbrix': 'NIMBRIX',
    'lids-ew':      'LIDS-EW'
  }
};
```

### 6.2 Model Selection (`setModel()`)

The dropdown model selector currently only changes the displayed Pk number in the HUD and the `ACTIVE_MODEL.pk` value used for accuracy display. It does **not** reload a different `.pth` file in the backend.

To fully link model selection to the backend:
1. Add a `selected_model` field to the `/evaluate_advanced` request schema
2. In `agent_backend.py`, load and cache the corresponding `.pth` from `/models/`
3. Run the PyTorch model's forward pass in `evaluate_threats_advanced()`

The current `RL_MODEL = lambda x: torch.tensor([0.85])` stub in `engine.py` returns a fixed value — it is a placeholder for the real neural forward pass.

### 6.3 Doctrine Sync

`setDoctrine()` in viz_engine.js now stores the selected doctrine in `window._ACTIVE_DOCTRINE`. Every `callEngine()` call reads this and passes it as `doctrine_primary` in the POST body. The backend's `DoctrineManager.get_blended_profile()` uses it to adjust utility weights.

---

## 7. Pre-existing Backend Bugs Fixed

These bugs caused every call to `/evaluate_advanced` to return HTTP 500 before this session:

| # | File | Bug | Error Type | Fix |
|---|---|---|---|---|
| 1 | `agent_backend.py` | `asyncio.to_thread(evaluate_threats_advanced, ..., GLOBAL_LOG_QUEUE, request.weather, 2.0, ...)` — passed Queue object as `salvo_ratio`, then 7 extra positional args the function doesn't accept | `TypeError: takes from 2 to 5 positional arguments but 11 were given` | Rewrote call with correct 5 positional args + `weather=` kwarg |
| 2 | `agent_backend.py` | `load_battlefield_state` used in the endpoint but never imported (only `Effector, Base, Threat, GameState, EFFECTORS` were imported) | `NameError: name 'load_battlefield_state' is not defined` | Added to import: `from core.models import ..., load_battlefield_state` |
| 3 | `agent_backend.py` | `format_report_with_llm()` used `t_count`, `score`, `doctrine`, `is_neural` inside an f-string, but all 4 were defined **after** the f-string | `NameError: name 't_count' is not defined` at f-string evaluation | Moved all 4 variable assignments to before the f-string |
| 4 | `core/engine.py` | `EFFECTORS` dict called `Effector(name, range_km, speed_kmh, pk_dict, cost)` but the dataclass field order is `(name, speed_kmh, cost_weight, range_km, pk_matrix)` — so `range_km` received the pk dict | `TypeError: '>' not supported between instances of 'float' and 'dict'` in `dist > eff_def.range_km` | Fixed positional arg order to match dataclass definition |

---

## 8. Live Test Results

All tests run in the browser via Playwright automation:

### Test 1: FIRE DEMO (single CRUISE missile)
```
> BOREAL KINETIC 3D READY — SELECT THEATER AND FIRE DEMO
> TRACKING CRUISE → HIGHRIDGE COMMAND
> SAM-1 LAUNCHED from HIGHRIDGE COMMAND
> CORTEX-1: BOREAL STRATEGIC SITREP ---        ← Neural engine SITREP
> ENGINE → NASAMS from HIGHRIDGE COMMAND | STRATEGIC SCORE: 123   ← Engine assignment
> NEUTRALIZED CRUISE — INTERCEPT CONFIRMED

Stats: FIRED=1, KILLS=1, IMPACTS=0
```

### Test 2: SATURATION WAVE (5 simultaneous missiles)
```
> SATURATION WAVE INBOUND — MULTI-VECTOR ENGAGEMENT
> TRACKING CRUISE → NORTHERN VANGUARD
> TRACKING HYPERSONIC → NORDVIK
> TRACKING LOITER → VALBREK
> TRACKING BALLISTIC → BOREAL WATCH POST
> TRACKING CRUISE → CALLHAVEN
> SAM-1 LAUNCHED from NORTHERN VANGUARD
> SAM-1 LAUNCHED from NORTHERN VANGUARD
> SAM-1 LAUNCHED from BOREAL WATCH POST
> SAM-1 LAUNCHED from SOUTHERN REDOUBT
> SAM-1 LAUNCHED from SPEAR POINT BASE
> NEUTRALIZED CRUISE — INTERCEPT CONFIRMED
> NEUTRALIZED HYPERSONIC — INTERCEPT CONFIRMED
> NEUTRALIZED LOITER — INTERCEPT CONFIRMED
> NEUTRALIZED BALLISTIC — INTERCEPT CONFIRMED
> NEUTRALIZED CRUISE — INTERCEPT CONFIRMED

Stats: FIRED=5, KILLS=5, IMPACTS=0
```

### Test 3: Backend API Direct
```
POST /evaluate_advanced (3 threats: cruise, hypersonic, drone)

Assignments:
  T2 (hypersonic) → nasams      from SPEAR POINT BASE
  T2 (hypersonic) → patriot-pac3 from SPEAR POINT BASE
  T1 (cruise)     → nasams      from SPEAR POINT BASE
  T1 (cruise)     → patriot-pac3 from SPEAR POINT BASE

Strategic Score: 69.69
Sitrep: AGGRESSIVE mode engaged. 4 vectors acquired.
```

---

## 9. Running the Stack

### Start both services (run from project root)

```powershell
$venv = "C:\Users\dhiraj.kumar\Downloads\Saab\.venv_saab\Scripts\python.exe"

# Backend — FastAPI on port 8000
$env:PYTHONPATH = "$PWD\src"
& $venv "src\agent_backend.py"

# In a second terminal — Frontend HTTP server on port 8080
& $venv -m http.server 8080
```

### URLs

| URL | Description |
|---|---|
| `http://localhost:8080/frontend/dashboard.html` | Strategic command dashboard (Boreal mode) |
| `http://localhost:8080/frontend/dashboard.html?mode=sweden` | Strategic dashboard (Sweden mode) |
| `http://localhost:8080/frontend/live_view.html` | Live kinetic audit view |
| `http://localhost:8080/frontend/kinetic_3d.html?theater=boreal` | 3D intercept simulator |
| `http://localhost:8000/docs` | FastAPI Swagger UI |
| `ws://localhost:8000/ws/logs` | WebSocket engine telemetry |

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `PYTHONPATH` | Yes | Must include `src/` so `core.*` imports resolve |
| `OPENROUTER_API_KEY` | Optional | Enables Gemini-2.0-flash SITREP. Falls back to local heuristic if unset |
| `SAAB_MODE` | Optional | `sweden` or `boreal` (default). Controls CSV base loading |
