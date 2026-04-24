# BOREAL FRONTEND-ENGINE INTEGRATION SPEC (V5.0)

**Last Updated:** 2026-04-24 — MARV/MIRV/Dogfight physics, Live View V6

This document codifies the integration between the **Boreal Frontend Suite** and the **Neural Tactical Engine**.

---

## 1. ARCHITECTURE — MIRROR LOGIC

The Boreal system uses **Mirror Logic**: the JavaScript simulation in the browser is a faithful replica of the Python physics engine, so every visual event corresponds to a real engine calculation.

| Layer | Technology | Role |
|---|---|---|
| **Master Oracle** | Python (`core/engine.py`) | Canonical physics — Pk matrix, utility scoring, MCTS rollouts |
| **Mirror Engine** | JavaScript (`viz_engine.js`) | Replicates physics visually in-browser (Three.js + OrbitControls) |
| **Inference Link** | FastAPI (`agent_backend.py`) | `POST /evaluate_advanced` — connects browser to Python engine |
| **Event Bridge** | `window._addCoTHook` | viz_engine.js fires hook after every CoT event — live_view.html listens |
| **Cross-Dashboard Sync** | `BroadcastChannel('saab_kinetic_v8')` | Real-time message passing between open tabs |

---

## 2. WEAPON TYPE SUPPORT MATRIX

| Weapon | Python flag | JS WEAPONS key | Kinetic 3D | viz_engine | Live View |
|---|---|---|---|---|---|
| Cruise Missile | `estimated_type='cruise-missile'` | `CRUISE` | ✅ | ✅ | ✅ |
| Hypersonic | `estimated_type='hypersonic-pgm'` | `HYPERSONIC` | ✅ | ✅ | ✅ |
| Loitering Munition | `estimated_type='drone'` | `LOITER` | ✅ | ✅ | ✅ |
| Ballistic | `estimated_type='ballistic'` | `BALLISTIC` | ✅ | ✅ | ✅ |
| **MARV** | `is_marv=True` | `MARV` | ✅ jink physics | ✅ jink physics | ✅ |
| **MIRV** | `is_mirv=True, mirv_count=3` | `MIRV` | ✅ bus sep. | ✅ child spawn | ✅ |
| **Fighter/Dogfight** | `can_dogfight=True` | `FIGHTER_DOG` | ✅ KILL/RTB/EW | ✅ stochastic | ✅ |

---

## 3. LIVE VIEW V6 — NEW COMPONENTS

```
live_view.html V6 (April 2026)
├─ Scoreboard: kills / leaks / total — polls stats{} every 500ms
├─ Event Banner: full-width flash for MARV jink, MIRV sep, dogfight outcomes
├─ Threat Telemetry Panel (200px right sidebar)
│   ├─ Per-threat card: weapon type, MARV/MIRV/dogfight state badge
│   ├─ Travel progress bar (_frame / _totalFrames)
│   └─ Dead threats shown dimmed until removed
├─ CoT Feed (200px, timestamped, colour-coded by event type)
│   ├─ orange = MARV events
│   ├─ red    = MIRV events
│   └─ cyan   = Dogfight events
├─ Auto-Wave Mode: fires random threat every 6 seconds
└─ window._addCoTHook: receives viz_engine.js CoT events for banner/telem sync
```

---

## 4. NEURAL CHAIN-OF-THOUGHT (CoT)

The frontend translates neural weights to tactical strings:

| Weight Vector | CoT String |
|---|---|
| `[0.8, 0.1, 0.1]` | `BALANCED → KINETIC DOMAIN PRIORITY: SAM INTERCEPT ACTIVE` |
| `[0.1, 0.8, 0.1]` | `AGGRESSIVE → EW DOMAIN PRIORITY: SWARM JAMMING ACTIVE` |
| `[0.1, 0.1, 0.8]` | `FORTRESS → CAPITAL RESERVE ACTIVE: HOLDING KINETICS` |
| MIRV pre-release detected | `MIRV BUS — COMMIT THAAD BEFORE 150KM` |
| MARV jink activated | `MARV TERMINAL JINK — Pk DEGRADED 45%` |
| Dogfight outcome | `DOGFIGHT: KILL / RTB / ENEMY WIN` |

---

## 5. DATASET VIEWER — CHRONOS 60

- **File:** `data/training/strategic_mega_corpus/chronos_60_maneuver.npz`
- **Shape:** `(200, 10, 15)` — 200 scenarios × 10 timesteps × 15 features
- **Backend:** `/get_dataset_sample` time-averages features to 15-D vector
- **Display:** Chart.js radar chart, MCTS oracle weight pills, strategic score

---

## 6. API CONTRACT SUMMARY

```
POST /evaluate_advanced  → tactical assignments + strategic score + sitrep
GET  /get_dataset_sample → CHRONOS 60 NPZ sample (15-D feature vector)
WS   /ws/logs            → real-time engine telemetry stream
GET  /health             → {"status":"ok", "model":"...", "theater":"..."}
```

**THE BOREAL SUITE IS FULLY INTEGRATED — MARV/MIRV/DOGFIGHT PHYSICS LIVE.** 🇸🇪🛡️

