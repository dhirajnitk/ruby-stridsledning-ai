# CORTEX-C2 Operator Console — Feature Reference

> UNCLASSIFIED · EXERCISE · PROTOTYPE S28

## Overview

`frontend/cortex_c2.html` is the standalone CORTEX-C2 operator console — a single-file, no-framework C2 interface for reliability-aware weapon-target assignment. It is accessible from the main portal (`frontend/index.html`) and links back to the strategic dashboard.

---

## Screens & Navigation

| Entry Point | URL |
|---|---|
| Portal (recommended start) | `http://localhost:8080/frontend/index.html` |
| CORTEX-C2 Console | `http://localhost:8080/frontend/cortex_c2.html` |
| Strategic Dashboard | `http://localhost:8080/frontend/dashboard.html` |
| 3D Kinetic (Boreal) | `http://localhost:8080/frontend/kinetic_3d.html?theater=boreal` |
| 3D Kinetic (Sweden) | `http://localhost:8080/frontend/kinetic_3d.html?theater=sweden` |

---

## Feature Inventory

### 1. Command Mode

Three operator modes selectable via the **Command Mode** buttons:

| Mode | Behaviour |
|---|---|
| **AUTONOMOUS** | AI selects all assignments instantly. No human approval required. |
| **HUMAN-IN-LOOP (HITL)** | AI generates COA assignments. Each COA must be APPROVED or REJECTED by the operator. A ⇄ SWAP button appears on every assignment, allowing weapon/base change before approval. |
| **MANUAL OVERRIDE** | Operator hand-selects Threat → Base → Effector and commits each engagement order individually. |

### 2. Doctrine Selector

Three engagement doctrines, applied **live** to COA scoring:

| Doctrine | Effect |
|---|---|
| **BALANCED** | Standard cost-matrix, 250 km engagement perimeter. Default. |
| **FORTRESS** | HVA (High-Value Asset) target weighting ×10. Defensive overlap priority. Slightly reduced range. |
| **AGGRESSIVE** | Range multiplier ×1.5. Ammunition cost weight halved. Max coverage posture. |

Switching doctrine instantly regenerates all three COA cards.

### 3. Theater Toggle

Two theaters share the same console:

| Theater | Bases | Notes |
|---|---|---|
| **BOREAL** | 21 nodes (ARK, NVB, HRC, BWP, VAL, NRD, MER, etc.) | Default. Fictional Baltic theater. |
| **SWEDEN** | 11 nodes (STO, F21, GOT, MAL, UPP, MUS, F7, etc.) | Swedish Military Installations. Real-world positions. |

The AOR label, inventory grid, and COA engine all update on theater switch.

### 4. Courses of Action (COA) Footer

Three parallel COA cards always displayed:

Each card shows: P.EFFECT · RISK · RESERVE · ENGAGE counters, assignment list, and (in HITL/MANUAL) APPROVE / REJECT / ⇄ SWAP buttons. The card header identifies the active model profile (e.g., "ELITE · Conservative").

### 5. Weapon Swap (HITL / Manual modes)

1. Click **⇄ SWAP** on any assignment in a COA card.
2. The target is **frozen** (highlighted amber) — no other assignment can take it.
3. An inline selector appears: choose a replacement base and effector.
4. Click **✓ CONFIRM SWAP** — the assignment mutates, COA stats recompute, target unfreezes.
5. Click **✕ CANCEL** to abort and unfreeze with no changes.
6. Swap count increments the Engagement Log counter.
7. **Realism Note:** Swapped weapons apply the current **Sensor Quality multiplier** to their nominal Pk.

### 6. Theater Inventory & REPLENISH

Left sidebar shows a live dual-bar grid (HP bar + SAM bar) for all active theater bases.

- Bars degrade as SAMs are consumed via APPROVE / FIRE
- **↑ REPLENISH** button restores all bases to initial SAM counts with a 1.1 s animation

### 7. Sensor Feed Quality

Visual quality bars for 5 sensor modalities:

| Sensor | Degraded by |
|---|---|
| RADAR | Jamming scenario |
| IR/EO | Jamming |
| ESM | — |
| LINK-16 | Jammed sensors scenario |
| FUSION | Composite of above |

Bars degrade when the scenario includes jamming (`sc.jamming = true`).

### 7.1 Pk Scaling Logic

The sensor quality (SQ) now directly influences engagement reliability. The effective Pk for any assignment is computed as:
$$Pk_{effective} = Pk_{nominal} \times Multiplier_{sensor}$$

The multiplier is a weighted average of relevant sensors based on threat type:
- **BALLISTIC**: Radar (60%) + ESM (40%)
- **HYPERSONIC**: Radar (50%) + IR/EO (50%)
- **CRUISE**: Radar (40%) + Fusion (60%)
- **LOITER**: IR/EO (60%) + Fusion (40%)
- **FIGHTER**: Radar (70%) + Link-16 (30%)

### 8. Decision Window (TTD)

Top-right panel shows **time-to-intercept** in seconds, color-coded:
- Green: >60 s
- Amber: 20–60 s
- Red: <20 s

### 9. LLM Tactical Analysis

Dual-mode LLM integration:

1. **Backend proxy** (preferred): `POST http://localhost:8000/llm/proxy` — requires Python backend running with `OPENROUTER_API_KEY` env var
2. **Direct OpenRouter fallback**: Uses API key stored in `localStorage` as `cortex_or_key`

The API Key row appears automatically when the backend is offline. Supports 7 models:
- Claude 3.5 Sonnet, Claude 3 Haiku
- GPT-4o, GPT-4o mini
- Gemini Pro 1.5, Mistral Large, Llama 3.1 70B

### 10. Circular Radar Scope

Animated SVG radar with:
- 4 range rings (50/100/150 km)
- 12 azimuth spokes
- Rotating sweep line (6 s revolution)
- Threat icons (red, pulsing) and base icons (green)
- Intercept trajectory lines

### 11. Engagement Log

Five counters updated in real-time:

| Counter | Incremented when |
|---|---|
| SAM FIRED | Any APPROVE or FIRE action |
| INTERCEPTS | Estimated hit (Pk roll) |
| MANUAL | Manual Override FIRE |
| HITL APPROVALS | COA APPROVE clicked |
| WEAPON SWAPS | CONFIRM SWAP clicked |

Reset via **↺ RESET** button.

### 12. Demo Scenarios

Three built-in scenarios (left sidebar):

| Scenario | Description |
|---|---|
| Clean picture | 3 bombers, high track quality, AUTONOMOUS mode demo |
| Swarm + fast-mover | 15 tracks, mixed types, ADVISE mode |
| Jammed sensors | Hypersonic + decoys + jamming, DEFER mode |

---

## Key JavaScript API

```javascript
loadScenario(key)          // 'clean' | 'swarm' | 'jammed'
setOpMode(mode)            // 'auto' | 'hitl' | 'manual'
setDoctrine(d)             // 'balanced' | 'fortress' | 'aggressive'
switchTheater(key)         // 'boreal' | 'sweden'
replenishAll()             // Restore all SAM inventory
approveCOACOA(idx)         // Approve COA[0|1|2]
rejectCOACOA(idx)          // Reject COA[0|1|2]
openSwap(coaIdx, assignIdx)    // Start weapon swap UI
confirmSwap(coaIdx, assignIdx) // Commit swap
cancelSwap()               // Cancel swap
askLLM()                   // Trigger LLM analysis
resetEngCounters()         // Reset engagement log
bumpCtr(key)               // Increment a counter programmatically
```

---

## Global State Variables

```javascript
OPERATOR_MODE   // 'auto' | 'hitl' | 'manual'
ACTIVE_THEATER  // 'boreal' | 'sweden'
ACTIVE_DOCTRINE // 'balanced' | 'fortress' | 'aggressive'
_currentSc      // Active scenario object
_currentCoas    // Array of 3 COA objects
_currentSq      // Active sensor quality mapping
_pendingHITL    // HITL queue items
_swapState      // { coaIdx, assignIdx } | null
engCtrs         // { fired, intercepts, manual, hitl, swap }
```

---

## Backend Integration

| Endpoint | Purpose |
|---|---|
| `POST /llm/proxy` | OpenRouter LLM proxy (streaming). Now includes sensor quality context in the prompt. |
| `POST /evaluate_advanced` | Kinematic bridge. Now sends live inventory, doctrine, and model ID for high-fidelity scoring. |
| `GET /health` | Portal backend health check |

Start backend: `python src/agent_backend.py` (requires `.venv_saab`, port 8000)

---

## File Structure

```
frontend/
  cortex_c2.html      ← Main operator console (single file, ~2400 lines)
  dashboard.html      ← Strategic dashboard (viz_engine physics)
  index.html          ← Unified portal (all module links)
  kinetic_3d.html     ← WebGL 3D kinetic simulation
  strategic_3d.html   ← CZML orbital view
  dataset_viewer.html ← Scenario & benchmark browser
  live_view.html      ← Streaming live feed
  tactical_legacy.html← V3 legacy SVG map
  styles.css          ← Shared dark-theme CSS variables
  viz_engine.js       ← Physics + WTA engine (dashboard.html)
src/
  agent_backend.py    ← FastAPI backend (port 8000)
models/               ← PyTorch + numpy model files
data/                 ← Scenarios, benchmarks, installations CSV
```

---

## Session 3 Changes (2026-04-24)

### 13. Model Profiles System

Eight tactical models now have distinct scoring profiles in `MODEL_PROFILES` (JS object):

| Model key | pkWeight | costWeight | maxPerBase | minPk | Label |
|-----------|----------|------------|-----------|-------|-------|
| `elite` | 1.20 | 0.010 | 8 | 0.28 | ELITE · Transformer/ResNet |
| `supreme3` | 1.10 | 0.012 | 7 | 0.32 | SUPREME V3.1 · Chronos GRU |
| `supreme2` | 1.00 | 0.015 | 6 | 0.30 | SUPREME V2 · LSTM |
| `titan` | 0.90 | 0.025 | 5 | 0.40 | TITAN · Conservative LSTM |
| `hybrid` | 1.05 | 0.008 | 8 | 0.25 | HYBRID RL · Value-Driven PPO |
| `genE10` | 1.05 | 0.014 | 6 | 0.32 | GENERALIST E10 · Ensemble |
| `heuristic` | 1.00 | 0.015 | 6 | 0.30 | HEURISTIC · Triage-Aware WTA |
| `hBase` | 0.95 | 0.020 | 4 | 0.35 | HEURISTIC V2 · Base Greedy |

Switching the model dropdown calls `onModelChange()`, which immediately regenerates all three COA cards using the new profile weights.

### 14. onModelChange()

New function `onModelChange()` wires the model dropdown to the full COA pipeline:
1. Updates the model badge
2. Regenerates COAs via `generateCOAs()` with the new `MODEL_PROFILES` weights
3. Re-renders COA cards and commentary
4. If HITL mode is active, refreshes the HITL queue

### 15. Backend Payloads — Real Data

`/evaluate_advanced` now receives live battlefield state instead of mocks:

```javascript
state: { bases: activeBases().map(b => {
  const st = inventoryState[b.id] || {};
  return { name, x, y, hp: st.hp ?? 100, inventory: {
    thaad, 'patriot-pac3', nasams, helws, 'c-ram'
  }};
}) },
doctrine_primary: ACTIVE_DOCTRINE,
model_id: <dropdown value>,
sensor_quality: _currentSq || null,
```

### 16. Sweden Theater Scenarios

Three theater-aware scenarios added for the Sweden theater (11 bases: STO, F21, GOT, MAL, UPP, MUS, F7, VXJ, LLA, HRN, KAL):

| Scenario | Description |
|---------|-------------|
| SWEDEN-C · 3 TRACKS | Stockholm approach, 3 bombers, AUTONOMOUS mode |
| SWEDEN-S · 3 TRACKS | F21 Luleå sector, 5 mixed threats + jamming, DEFER mode |
| SWEDEN-M · 9 TRACKS | 9 tracks targeting Stockholm/GOT/Gotland, ADVISE mode |

Theater label now shows `"Sweden (11 nodes)"` / `"Boreal (21 nodes)"` correctly.

### 17. Sensor Quality → Pk Wiring

Sensor quality is now computed once per scenario load (`computeSensorQuality(sc, m)`) and stored in `_currentSq`. It propagates to:

- **COA cards**: Each assignment shows `Pk_nom → Pk_eff` with tooltip formula
- **Weapon SWAP**: `confirmSwap()` applies `getSensorPkMult()` to swapped weapon's Pk
- **Theater switch**: `switchTheater()` recomputes `_currentSq` before regenerating COAs
- **LLM prompt**: Sensor quality block included in `buildTacticalPrompt()`
- **Commentary**: `renderCommentary()` shows per-modality percentages and avg multiplier

### 18. COA Approval — Pk-Weighted Simulation

`approveCOACOA()` now rolls a Pk-weighted Monte Carlo intercept estimate:

```javascript
let hits = 0;
coa.assignments.forEach(a => { if (Math.random() < (a.pk || 0.5)) hits++; });
// hits → increments INTERCEPTS counter
```

### 19. Sensor Quality Cuing Matrix

```
BALLISTIC  : radar 60% + esm 40%
HYPERSONIC : radar 70% + ireo 30%
CRUISE     : radar 50% + ireo 30% + link16 20%
LOITER/DRONE: ireo 60% + radar 30% + link16 10%
FIGHTER    : radar 50% + link16 40% + ireo 10%
Floor      : 0.30 (minimum Pk multiplier regardless of sensor state)
```
