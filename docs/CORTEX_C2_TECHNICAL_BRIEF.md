# CORTEX-C2 — Technical Brief
## SAAB Ruby Stridsledning AI — System Overview

---

## 1. Project Overview

CORTEX-C2 is an AI-powered Command & Control (C2) simulation platform for theater air-missile defense. It demonstrates:

- **Neural tactical decision-making** — trained ML models (GRU, PPO, Transformer) score weapon-target assignments
- **Multi-layer ballistic missile defense doctrine** — THAAD / PAC-3 vs MARVs, NASAMS vs cruise/ballistic
- **Real-time Pro-Nav kinetics** — Web Worker physics at 20 Hz computing Proportional Navigation guidance
- **Geospatial theater visualization** — SVG strategic maps (Boreal and Sweden theaters), animated threat tracks, CesiumJS 3D globe

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────┐
│  FastAPI Backend  (src/agent_backend.py : port 8000)    │
│  • /state          → 12 Boreal base objects (x_km,y_km) │
│  • /theater        → theater geometry + threat config   │
│  • /api/simulate-kinetic-chase?raw=true                 │
│  • /ws/logs        → streaming sitrep WebSocket         │
└───────────────────┬─────────────────────────────────────┘
                    │ HTTP / WS
┌───────────────────▼─────────────────────────────────────┐
│  Frontend  (frontend/)                                  │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │ index.html  │  │ dashboard.html│  │ kinetic_3d.html│ │
│  │ Portal      │  │ Strategic C2  │  │ Three.js r128  │ │
│  └─────────────┘  └──────┬───────┘  └────────────────┘ │
│                           │ viz_engine.js               │
│  ┌─────────────┐  ┌───────▼──────┐  ┌────────────────┐ │
│  │kinetic_chase│  │ live_view.html│  │ strategic_3d   │ │
│  │Pro-Nav sim  │  │ WS log feed  │  │ CesiumJS globe │ │
│  └─────────────┘  └──────────────┘  └────────────────┘ │
│  ┌──────────────────────────────────────────────────┐   │
│  │ swarm_physics.html  ←→  physics_worker.js        │   │
│  │ Web Worker Pro-Nav at 20 Hz                      │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Key Files

| File | Role |
|---|---|
| `src/agent_backend.py` | FastAPI server, ML model inference, scenario runner |
| `frontend/viz_engine.js` | Shared strategic map engine (Boreal + Sweden) |
| `frontend/dashboard.html` | Strategic C2 — threat engagement, inventory, AI scoring |
| `frontend/kinetic_chase.html` | Single-engagement Pro-Nav kinetic sim (backend trajectory) |
| `frontend/swarm_physics.html` | Mass swarm defense — Web Worker physics |
| `frontend/physics_worker.js` | Pro-Nav guidance law, MARV jinking, proximity fuse |
| `frontend/kinetic_3d.html` | Three.js 3D intercept visualization |
| `frontend/strategic_3d.html` | CesiumJS globe with CZML threat overlays |
| `frontend/live_view.html` | WebSocket sitrep log + live engagement feed |
| `frontend/index.html` | CORTEX Command Portal (navigation) |
| `models/` | Trained PyTorch models (Elite V3.5, Supreme V3.1, Titan, etc.) |
| `data/` | Ground truth scenarios, benchmarks, training sets |

---

## 3. Theater Maps

### Boreal Theater (12 Bases)

| Code | Name | Role |
|---|---|---|
| ARK | Arktholm Capital | Command HQ |
| CAL | Callhaven | MARV-1 target |
| SOL | Solano | MARV-2 target |
| MER | Meridia | MARV-3 target |
| NVB | Northern Vanguard Base | Forward SAM |
| HRC | Highridge Command | Eastern SAM |
| BWP | Boreal Watch Post | Sensor picket |
| VAL | Valbrek | Mid-tier defense |
| NRD | Nordvik | Northern defense |
| FWS | Firewatch Station | Radar |
| SRB | Southern Redoubt | Reserve |
| SPB | Spear Point Base | Strike |

### MARV Threat Tracks (animated on strategic map)

| Track | Origin | Target | SVG start→end |
|---|---|---|---|
| MARV-1 | North (x=185, y=10) | CAL Callhaven | → (58, 690) |
| MARV-2 | North (x=430, y=5) | SOL Solano | → (346, 742) |
| MARV-3 | North (x=765, y=10) | MER Meridia | → (735, 725) |

### Sweden Theater (6 Nodes)

| Code | Name |
|---|---|
| STO | Stockholm |
| GOT | Gotland |
| KRL | Karlskrona |
| UPP | Uppsala |
| GBG | Gothenburg |
| LUL | Luleå |

---

## 4. Weapon Doctrine — MARV/MIRV Intercept

MARVs (Maneuvering Re-entry Vehicles) use terminal-phase evasive maneuvers. Only kinetic upper-tier systems can achieve meaningful Pk:

### Boreal Effectors

| System | MARV Pk | MIRV Pk | Note |
|---|---|---|---|
| **THAAD** | **0.80** | 0.75 | Primary upper-tier |
| **PAC-3 MSE** | **0.75** | 0.70 | City-defense terminal |
| NASAMS | 0.12 | 0.10 | AMRAAM — wrong altitude/speed class |
| HELWS (Laser) | 0.00 | 0.00 | Cannot engage ballistic targets |
| C-RAM Phalanx | 0.00 | 0.00 | Short-range only |
| RTX Coyote B2+ | 0.00 | 0.00 | C-UAS only |
| Merops / Coyote B3 | 0.00 | 0.00 | C-UAS only |

### Sweden Effectors

| System | MARV Pk | MIRV Pk | Note |
|---|---|---|---|
| **LV-103 (PAC-3 MSE)** | **0.75** | 0.70 | Primary upper-tier |
| E98 (IRIS-T SLS) | 0.04 | 0.04 | Too slow, wrong alt |
| Nimbrix | 0.00 | 0.00 | C-UAS only |
| LIDS-EW | 0.00 | 0.00 | EW jammer |
| Meteor (Air-to-Air) | 0.15 | 0.10 | Limited anti-ballistic |

> **Doctrine**: `wdef.type = 'MARV'` (not `'BALLISTIC'`) ensures `pk['MARV']` is looked up, not `pk['BALLISTIC']`. Auto-engagement only assigns THAAD/PAC-3 to MARV threats.

---

## 5. Pro-Nav Physics Engine

### Parameters

| Parameter | Value | Description |
|---|---|---|
| `DT` | 0.1 s | Physics timestep per tick |
| Tick interval | 50 ms | Real-time clock (~20 Hz) |
| Physics speed | 2× real-time | 0.1s physics / 0.05s real |
| `FUSE` | 3000 m | Proximity detonation radius |
| MARV speed | 1200–1600 m/s | Terminal phase |
| PAC-3 speed | 1800→3200 m/s | Launch→booster-max |
| NASAMS speed | 1200→2500 m/s | |
| PAC-3 maxG | 50 G | Maneuver limit |
| NASAMS maxG | 25 G | |
| MARV jinkMag | 80–150 m/s | Realistic terminal jink |
| MARV jinkFreq | 1.2–2.2 s | Between jink events |

### Guidance Law

```
PN acceleration command = N × Vc × λ̇

where:
  N    = navigation constant (5.0 for PAC-3, 4.0 for NASAMS)
  Vc   = closing velocity (m/s)
  λ̇   = line-of-sight rate (rad/s)

Heading update: θ += (a_cmd / v) × DT
Velocity: vx = v·cos(θ),  vy = v·sin(θ)
```

### Intercept Geometry

- **Head-on / oblique**: Interceptors launch from co-located city batteries, initial heading aimed at MARV's current position → direct climb toward target, not vertical tail-chase
- **Proximity check**: Done both before AND after position update to catch high-speed passes within one tick

### MARV Jink Model

```js
if (t.isMarv && distToBase < t.triggerRange) {
    // Every jinkFreq physics seconds, apply perpendicular velocity component
    perpAngle = heading ± 90° ± random(0.5 rad)
    currentJink = { x: jinkMag × cos(perpAngle), y: jinkMag × sin(perpAngle) }
    // Applied each tick: actualVel = vel + currentJink
}
```

### Why Previous Simulation Missed

| Old Value | Bug | Fixed Value |
|---|---|---|
| `jinkMag = 1200 m/s` | Composite MARV speed = 2780 m/s at 26° off-axis; Pro-Nav saturated at 40G | `jinkMag = 80–150 m/s` |
| `proximity fuse = 800 m` | At 430 m/tick closing, 900m→470m in one tick — just barely triggers | `fuse = 3000 m` |
| `heading = π/2` (straight up) | Tail-chase geometry; interceptor had to turn 30–40° before closing | `heading = atan2(dy, dx)` toward MARV |
| `setInterval` not cleared | Each `launchSwarm()` stacked a new physics loop (double/triple speed) | `clearInterval` before new loop |

---

## 6. Swarm Physics UI

### Auto-Engage Sequence

Page load → **1.2s** → `launchSwarm()` → **3s delay** → `fireSalvo()`

No manual buttons required. Weapons/effectors loaded from Boreal doctrine.

### Threat Configuration

| ID | Type | Target | Speed |
|---|---|---|---|
| MARV-1 | MARV (jinking) | CALLHAVEN (x=−20km) | 1200–1600 m/s |
| MARV-2 | MARV (jinking) | SOLANO (x=0) | 1200–1600 m/s |
| MARV-3 | MARV (jinking) | MERIDIA (x=+20km) | 1200–1600 m/s |
| CRS-1 | Cruise | CALLHAVEN | 500–750 m/s |
| CRS-2 | Cruise | MERIDIA | 500–750 m/s |
| BAL-1 | Ballistic | SOLANO | 500–750 m/s |

### Interceptor Response (Doctrine-Driven)

| Threat | Interceptor | Count | From |
|---|---|---|---|
| MARV-1/2/3 | PAC-3 MSE (cyan) | 2 per MARV | Co-located city battery |
| Cruise/Ballistic | NASAMS (green) | 1 per threat | Nearest battery |

### Canvas Coordinate System

```
mapX(x_meters) = 400 + (x / 60000) × 390    // x: −60km=0px … +60km=800px
mapY(y_meters) = 560 − (y / 80000) × 540    // y: 0km=560px(bottom) … 80km=0px(top)
```

---

## 7. ML Models

| Model | File | Architecture | Notes |
|---|---|---|---|
| Elite V3.5 | `elite_v3_5.pth` | Deep ensemble | Best MC accuracy 74.5% |
| Supreme V3.1 | `supreme_v3_1.pth` | GRU + attention | Chronos-enhanced |
| Supreme V2 | `supreme_v2.pth` | GRU | Legacy baseline |
| Titan | `titan.pth` | Transformer | Large parameter count |
| Hybrid RL | `hybrid_rl.pth` | PPO actor-critic | Reinforcement fine-tuned |
| Generalist E10 | `generalist_e10.pth` | Wide MLP | Broad scenario coverage |
| Boreal Chronos | `boreal_chronos_gru.pth` | GRU with time-embed | Theater-specific |

Models are loaded in `agent_backend.py`. Dashboard dropdown selects active model at inference time.

---

## 8. API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/state` | GET | Returns 12 Boreal bases: `[{name, x_km, y_km, hp, sam_count}, ...]` |
| `/theater` | GET | Theater geometry, threat definitions |
| `/api/simulate-kinetic-chase` | POST | Pro-Nav trajectory simulation |
| `/api/simulate-kinetic-chase?raw=true` | POST | Returns trajectory re-centred on SAM origin (0,0) |
| `/ws/logs` | WS | Streaming sitrep / engagement log |

---

## 9. Demo Video Structure (2 min)

| Scene | Duration | Page | Key Feature |
|---|---|---|---|
| 1 | ~12s | `index.html` | CORTEX Command Portal, hover cards |
| 2 | ~35s | `dashboard.html?mode=boreal` | Animated MARV-1/2/3 tracks, inventory, AI model selector |
| 3 | ~15s | `dashboard.html?mode=sweden` | Sweden theater, LV-103 PAC-3 doctrine |
| 4 | ~25s | `kinetic_3d.html` | Three.js 3D intercept animation |
| 5 | ~25s | `kinetic_chase.html` | MARV-1 → Callhaven live engagement, Pro-Nav curved pursuit |
| 6 | ~12s | `live_view.html` | WebSocket sitrep log stream |
| 7 | ~15s | `strategic_3d.html` | CesiumJS Baltic theater globe |
| 8 | ~20s | `swarm_physics.html` | Mass saturation: 3 MARVs vs PAC-3 MSE (oblique intercept) |

---

## 10. Running the System

```powershell
# Start backend (from project root)
C:\Users\dhiraj.kumar\Downloads\Saab\.venv_saab\Scripts\python.exe src/agent_backend.py

# Server starts on http://localhost:8000
# Frontend served as static files from /frontend/

# Record demo video
node video/record_demo.js

# Convert to MP4
ffmpeg -i video/<latest>.webm output.mp4
```

---

*Generated: 2026-04-26 | CORTEX-C2 SAAB Stridsledning AI*
