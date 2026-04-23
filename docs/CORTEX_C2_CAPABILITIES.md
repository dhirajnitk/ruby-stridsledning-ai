# CORTEX-C2 — Full Capabilities Reference

**Version:** 1.1.0  
**File:** `frontend/cortex_c2.html`  
**Server:** `http://localhost:8080/frontend/cortex_c2.html`  
**Backend:** `src/agent_backend.py` on port 8000 (optional — graceful offline fallback)  
**Purpose:** Standalone Command & Control (C2) operator console for the CORTEX-1 Reliability-Aware C2 Decision Engine  

---

## 1. Overview

CORTEX-C2 is a browser-based C2 operator console demonstrating NATO-style autonomous engagement authority management for air and missile defence. It combines:

- A deterministic **Weapon-Target Assignment (WTA)** optimiser (greedy MILP approximation)
- A **Monte Carlo Tree Search (MCTS)** COA evaluator producing three alternative Courses of Action
- A **Situation Awareness (SA) Health** gauge driving autonomous/advisory/deferred operating modes
- A **Human-in-the-Loop (HITL)** approval queue and **Manual Override** panel
- A **theater inventory** system tracking SAM rounds and base HP across two geographic theaters
- A **kinematic physics bridge** to the Python backend (radar equations + proportional navigation + 3D evasion)
- An **LLM Analysis** panel via OpenRouter for natural-language tactical assessment
- A **3D kinetic visualisation** link (`kinetic_3d.html`)

The console operates fully in-browser with no external dependencies beyond optional backends.

---

## 2. Layout

The console uses a three-column CSS grid layout with a fixed header, scrollable column bodies, and a fixed footer.

```
┌────────────────────────────────────────────────────────────────────────────┐
│ HEADER: Brand · Model selector · Backend status · Refresh                  │
├──────────────┬────────────────────────────────────────┬────────────────────┤
│ LEFT 220px   │ CENTER flexible                         │ RIGHT 275px        │
│ Scenarios    │ SA-Health gauge + mode pill + metrics   │ Posture            │
│ Inventory    │ Command mode row + theater toggle       │ Threat Summary     │
│ About        │ Reasons                                 │ Recommendation     │
│              │ Tactical Picture SVG                    │ Assurance          │
│              │                                         │ Follow-On          │
│              │                                         │ Kinematic Bridge   │
│              │                                         │ LLM Analysis       │
│              │                                         │ AI Commentary      │
├──────────────┴────────────────────────────────────────┴────────────────────┤
│ HITL APPROVAL QUEUE (shown only when mode = HUMAN-IN-LOOP)                 │
│ MANUAL OVERRIDE PANEL (shown only when mode = MANUAL OVERRIDE)             │
├────────────────────────────────────────────────────────────────────────────┤
│ FOOTER: Courses of Action — 3 COA cards + model badge                      │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Scenarios

Three built-in scenarios demonstrate the three operating modes.

### 3.1 Clean Picture — Three Bombers
- **Threats:** 3 × BALLISTIC (T01→ARK, T02→NVB, T03→HRC)
- **SA-Health:** 82% → **AUTONOMOUS**
- **Complexity:** 0.09 | **Stakes:** 0.83 | **TQI:** 1.00 | **Jamming:** No
- **Demonstrates:** Default MILP assignment, AUTONOMOUS mode, PAC-3 optimality vs BALLISTIC

### 3.2 Swarm with Fast-Mover Breakthrough
- **Threats:** 12 × LOITER drones, 1 × FIGHTER, 1 × HYPERSONIC (F02), 1 × ghost CRUISE (G01)
- **SA-Health:** 76% → **ADVISE**
- **Complexity:** 0.66 | **Jamming:** No | **Ghost tracks:** 1
- **Demonstrates:** Mixed swarm engagement, ghost track ambiguity, ADVISE mode handover to commander

### 3.3 Jammed Sensors + High-Value Threats
- **Threats:** 3 × HYPERSONIC (H01-H03), 2 × CRUISE (C01-C02), 3 × LOITER decoys (DC1-DC3)
- **SA-Health:** 46% → **DEFER**
- **Jamming:** YES | **Decoys:** 3
- **Demonstrates:** EW degradation, SA penalty (−35 for jamming), DEFER mode, decoy vs. real threat discrimination

---

## 4. SA-Health Gauge

### 4.1 Formula

$$SA = \max\!\left(5,\; \min\!\left(99,\; \text{round}\!\left(100 - C_{complexity} \cdot 28 - C_{stakes} \cdot 28 + C_{tqi} \cdot 8 - J_{penalty}\right)\right)\right)$$

Where:
- $C_{complexity}$ = normalised complexity index (0–1)
- $C_{stakes}$ = normalised stakes index (0–1)  
- $C_{tqi}$ = normalised track quality index (0–1)
- $J_{penalty}$ = 35 if jamming active, 0 otherwise

### 4.2 Mode Thresholds

| SA-Health Range | Operating Mode | Color |
|---|---|---|
| 80–99% | **AUTONOMOUS** | Green |
| 55–79% | **ADVISE** | Yellow |
| 5–54% | **DEFER** | Red |

### 4.3 Complexity Index

$$C_{complexity} = \frac{N_{tracks}}{15} + \frac{N_{types} - 1}{4} \cdot 0.3 + \frac{N_{decoy}}{5} \cdot 0.2 + \frac{N_{ghost}}{3} \cdot 0.3$$

clamped to 0–1.

### 4.4 Stakes Index

$$C_{stakes} = \frac{\sum_{threat} v_{threat}}{3 \cdot N \cdot \bar{v}_{max}}$$

clamped to 0–1, where $v_{threat}$ is threat value and $\bar{v}_{max}$ is the maximum per-threat value across all scenario types.

### 4.5 TQI (Track Quality Index)

$$C_{tqi} = 1 - \frac{N_{decoy} + N_{ghost}}{N_{tracks} + 1}$$

---

## 5. COA Generation Engine

### 5.1 Effector Definitions

| Effector | Range (m) | Cost | Pk vs BALLISTIC | Pk vs HYPERSONIC | Pk vs CRUISE | Pk vs LOITER |
|---|---|---|---|---|---|---|
| THAAD | 200,000 | 800 | 0.98 | 0.80 | 0.40 | 0.10 |
| PAC-3 | 120,000 | 400 | 0.95 | 0.70 | 0.95 | 0.80 |
| NASAMS | 40,000 | 100 | 0.50 | 0.50 | 0.88 | 0.60 |
| HELWS | 5,000 | 5 | — | — | 0.20 | 0.90 |
| C-RAM | 1,500 | 10 | — | — | 0.70 | 0.80 |

Range check uses Euclidean distance between base and threat's **target base** (not spawn point) × `UNIT_TO_M` (1,666 m per SVG unit).

### 5.2 Three COA Variants

#### COA-1: RECOMMENDED
- **Score function:** `pk × value − cost × 0.015`  
- **Max assignments per base:** 6  
- Maximises expected damage averted per unit ammunition at current ROE.

#### COA-2: RESERVE CONSERVING  
- **Score function:** `pk × value − cost × 0.35`  
- **Max assignments per base:** 4  
- Heavy cost penalty preserves expensive effectors (THAAD, PAC-3) for follow-on waves. Accepts higher current-wave leak rate.

#### COA-3: RISK MINIMISING  
- **Score function:** `pk × 1000 − cost × 0.001` with Pk floor ≥ 0.70 (assignments with Pk < 0.70 excluded)  
- **Max assignments per base:** 8  
- Minimises per-engagement miss probability. Accepts higher ammo expenditure for reliability. Useful for high-value target scenarios.

### 5.3 Dynamic Pk Scaling (Sensor Quality)

The console now implements a **Sensor-to-Kinetic Feedback Loop**. Effective Pk is scaled by real-time sensor performance:

$$Pk_{effective} = Pk_{nominal} \times Multiplier_{sensor}$$

| Threat Type | Primary Sensor Weighting |
|---|---|
| **BALLISTIC** | Radar (60%) + ESM (40%) |
| **HYPERSONIC** | Radar (50%) + IR/EO (50%) |
| **CRUISE** | Radar (40%) + Fusion (60%) |
| **LOITER** | IR/EO (60%) + Fusion (40%) |
| **FIGHTER** | Radar (70%) + Link-16 (30%) |

### 5.4 Model Profiles (Algorithm Overlays)

The model selector actively swaps the scoring weights used by the greedy WTA algorithm:

| Profile | pkWeight | costWeight | Strategy |
|---|---|---|---|
| **ELITE** | ×1.20 | 0.010 | High-Confidence Aggressive |
| **SUPREME** | ×1.10 | 0.015 | Balanced Neural |
| **TITAN** | ×0.90 | 0.025 | Conservative Ammo-Preserving |
| **HEURISTIC**| ×1.00 | 0.015 | Baseline Heuristic |

### 5.5 Greedy WTA Algorithm

For each COA variant:
1. Build candidate list: all (effector, base, threat) triples where base is within range of threat's target and base has SAM inventory
2. Score each candidate
3. Sort descending by score
4. Greedily assign top candidates, tracking per-base assignment count
5. Compute aggregate metrics: utility, coverage, follow-on risk, engagement count

### 5.6 Metrics Derived per COA

| Metric | Formula |
|---|---|
| **Utility** | Sum of `pk × value` across all assignments |
| **Coverage %** | `threats_assigned / total_real_threats × 100` |
| **Follow-on Risk** | `0.05 + (1 − coverage/100) × 0.6 + (engagements / max_engagements) × 0.2` |
| **Engagement count** | Number of (base, effector) → threat pairs |

---

## 6. Theater Data

### 6.1 Boreal Theater

| ID | Name | SVG Coords | Type | SAM Count | Effectors |
|---|---|---|---|---|---|
| ARK | Arktholm | (251, 57) | HVA | 100 | THAAD, PAC-3, NASAMS, C-RAM |
| NVB | Boden | (119, 197) | BASE | 40 | PAC-3, NASAMS, HELWS |
| HRC | Highridge | (503, 41) | BASE | 30 | THAAD, PAC-3 |
| BWP | Gotland | (695, 227) | BASE | 50 | NASAMS, C-RAM |
| VAL | Valbrek | (854, 128) | HVA | 60 | PAC-3, HELWS |
| NRD | Nordvik | (84, 194) | HVA | 40 | NASAMS, C-RAM |
| MER | Meridia | (735, 725) | HVA | 40 | THAAD, PAC-3, NASAMS |

### 6.2 Sweden Theater

| ID | Name | SVG Coords | Type | SAM Count | Effectors |
|---|---|---|---|---|---|
| STO | Stockholm | (480, 200) | HVA | 80 | THAAD, PAC-3, NASAMS, C-RAM |
| GOT | Gothenburg | (120, 400) | HVA | 60 | PAC-3, NASAMS |
| MAL | Malmö | (190, 540) | HVA | 40 | PAC-3, NASAMS, C-RAM |
| UPP | Uppsala | (510, 135) | BASE | 30 | NASAMS, C-RAM |
| ORE | Örebro | (310, 320) | BASE | 40 | PAC-3, NASAMS |
| SUN | Sundsvall | (570, 70) | BASE | 20 | NASAMS, C-RAM |
| UME | Umeå | (660, 45) | BASE | 20 | NASAMS, HELWS |

Switching theaters via the **BOREAL / SWEDEN** toggle redraws the tactical map, updates the inventory panel with theater-specific labeling (e.g., "Sweden (11 nodes)"), and recomputes sensor quality.

---

## 7. Theater Inventory Management

### 7.1 Inventory State

Each base has three state variables:
- `hp` — base structural integrity (0–100%)
- `sam` — current SAM salvo count (0–max)
- `maxSam` — initial SAM count at scenario start
- `destroyed` — boolean; destroyed bases are marked with strike-through

### 7.2 Inventory Display

Each inventory row shows:
- **Type badge:** `HVA` (green) or `BASE` (blue)
- **Base name** (strike-through if destroyed)
- **HP bar** — green → yellow (50%) → red (25%)
- **SAM bar** — green → yellow (40%) → red (20%)
- **SAM count** text (`N SAM`)

### 7.3 SAM Depletion Events

| Event | SAM Cost |
|---|---|
| HITL approve | Assignment's effector cost (in salvo units, min 1) |
| Manual fire | 1 SAM per engagement regardless of effector |
| Backend engagement | Deducted via HITL approval queue when `OPERATOR_MODE === 'hitl'` |

### 7.4 Replenishment

The **↑ REPLENISH** button calls `replenishAll()`:
- Restores all **non-destroyed** bases to their `maxSam` SAM count
- Restores HP to 100%
- Re-renders the inventory grid
- Adds a feed line to AI Commentary

Destroyed bases (HP=0) are **not** replenished by this operation.

---

## 8. Operator Command Modes

### 8.1 AUTONOMOUS
- System executes COA-1 assignments without commander confirmation
- Posture panel shows "AUTONOMOUS — all assignments executed autonomously"
- No HITL queue, no manual panel visible
- Active button: green-outlined `AUTONOMOUS`

### 8.2 HUMAN-IN-LOOP (HITL)
- System proposes COA-1 but waits for commander confirmation before execution
- **HITL approval queue** appears below the main body
- Each assignment is listed as a separate item with **APPROVE** (green) and **REJECT** (red) buttons
- APPROVE: deducts SAM from the selected base's inventory
- REJECT: marks assignment as rejected, logged to commentary
- Active button: yellow-outlined `HUMAN-IN-LOOP`

### 8.3 MANUAL OVERRIDE
- Commander assigns engagements manually
- **Manual override panel** appears below the main body with three dropdowns:
  - **Threat selector:** all real (non-decoy) inbound tracks
  - **Base selector:** all operational bases with available SAM
  - **Effector selector:** effectors available at selected base
- **⬢ FIRE** button executes the engagement:
  - Rolls against effector's Pk vs. threat type
  - Deducts 1 SAM from the selected base
  - Displays HIT / MISS result with Pk value
  - Logs to AI Commentary
- Active button: red-outlined `MANUAL OVERRIDE`

---

## 9. Tactical Picture SVG

The tactical picture is a 860×560 SVG with four layers:

| Layer | Element | Contents |
|---|---|---|
| `tac-grid` | `<g>` | Light grey grid lines (3H × 3V) |
| `tac-assign-lines` | `<g>` | Orange dashed assignment lines from base to threat spawn |
| `tac-bases` | `<g>` | Hexagon symbols for bases (green=HVA, blue=BASE, grey=destroyed) |
| `tac-threats` | `<g>` | Red circle symbols for threats with threat ID labels |

**Base rendering:**
- HVA: hexagon (`⬡`) with green stroke, HVA label below
- BASE: hexagon with blue stroke, BASE label below
- Destroyed: hexagon with 50% opacity, grey stroke
- Label shows base name + effector stack if SAM > 0

**Threat rendering:**
- Circle symbol with threat ID text
- HYPERSONIC: `var(--red)`
- BALLISTIC: `rgba(248,81,73,0.9)`
- CRUISE: `rgba(227,179,65,0.9)`
- LOITER: `rgba(255,150,50,0.9)`
- FIGHTER: `rgba(220,80,220,0.9)`
- Ghost: greyed out with `?` marker

**Assignment lines:**
- Dashed orange line from base to threat target area
- Animated stroke-dashoffset for movement effect

---

## 10. Kinematic Bridge Panel

When the Python backend (`agent_backend.py`) is running on port 8000, `pollKinematics(sc)` sends a POST to `/evaluate_advanced` and populates the kinematic bridge panel with real physics data:

| Parameter | Description |
|---|---|
| Radar SNR | Signal-to-noise ratio for track detection |
| Detection range | Estimated radar detection range for the engagement |
| Proportional nav gain | PN guidance constant (N = 3–5 typical) |
| Time to intercept | Estimated seconds to intercept point |
| Evasion probability | Probability of threat successfully evading |
| Intercept altitude | Estimated intercept altitude in km |

When offline, the panel shows: *"Engine offline — start Python backend for live kinematics"*

The live indicator dot glows green when backend is responding.

---

## 11. LLM Analysis Panel

See [LLM_INTEGRATION.md](LLM_INTEGRATION.md) for full documentation. Summary:

- **Location:** Right sidebar, below Kinematic Bridge panel
- **Models:** 7 options via OpenRouter (Claude 3.5 Sonnet recommended)
- **Trigger:** Manual click on `▶ ANALYSE` button
- **Input:** Rich tactical prompt built from current scenario, SA metrics, COA summaries, theater inventory
- **Output:** 6-section military assessment streamed token-by-token with blinking cursor
- **Token count & elapsed time** displayed below the response panel
- **API key:** Entered in-panel (type=password), stored in `localStorage` under key `cortex_or_key`
- **Echo:** Completion summary echoed to AI Commentary feed

---

## 12. AI Commentary Feed

The AI Commentary feed (`#ai-commentary`) is a live timestamped event log.

**Feed line types:**
- Default: dim grey text (`var(--tx3)`)
- `.hl`: bright white — used for CORTEX-1 assessment headers
- `.good`: green — used for HIT results
- `.warn`: yellow/red — used for MISS, errors, LLM warnings

Lines are generated by `renderCommentary(sc, m, coas)` on scenario load and by `_addFeedLine(text, cls)` from all interactive operations.

**Animated rendering:** On scenario load, commentary lines appear with a 120ms stagger delay, giving a real-time assessment feel.

---

## 13. Backend Integration

The Python FastAPI backend at `src/agent_backend.py` exposes one key endpoint:

### POST `/evaluate_advanced`

**Request body:**
```json
{
  "scenario": { ... },
  "model": "elite|supreme|titan|heuristic",
  "operator_mode": "auto|hitl|manual"
}
```

**Response:**
```json
{
  "coa": { "utility": 0.0, "coverage": 0.0, "assignments": [ ... ] },
  "kinematic": {
    "radar_snr": 0.0,
    "detection_range_km": 0.0,
    "pn_gain": 0.0,
    "time_to_intercept_s": 0.0,
    "evasion_probability": 0.0,
    "intercept_altitude_km": 0.0
  }
}
```

`upgradeFromBackend(sc, coa1)` uses the COA response to supplement the in-browser COA with backend-computed scores.  
`pollKinematics(sc)` uses the kinematic block to populate the Kinematic Bridge panel.

Both calls are fire-and-forget — backend offline does not prevent local COA generation.

### Backend Start Command

```powershell
& "C:\Users\dhiraj.kumar\Downloads\Saab\.venv_saab\Scripts\python.exe" -m uvicorn src.agent_backend:app --host 0.0.0.0 --port 8000
```

---

## 14. Model Selector

The top-right model selector feeds `updateModelBadge()`, which updates the `model-badge` in the COA footer. **Crucially**, it now swaps the active `MODEL_PROFILE` used by the in-browser COA algorithm:

| Option | Label | pkWeight | costWeight | minPk |
|---|---|---|---|---|
| `elite` | ELITE V3.5 | ×1.20 | 0.010 | 0.28 |
| `supreme` | SUPREME V3.1 | ×1.10 | 0.015 | 0.35 |
| `titan` | TITAN · LSTM | ×0.90 | 0.025 | 0.40 |
| `heuristic`| HEURISTIC | ×1.00 | 0.015 | 0.30 |

- **pkWeight**: Multiplier for engagement utility.
- **costWeight**: Penalty factor for ammunition expenditure.
- **minPk**: The minimum reliable Pk floor for the model's strategy.

---

## 15. Navigation & External Links

| Destination | How to reach |
|---|---|
| Main dashboard (`dashboard.html`) | Left sidebar → About → "→ Main Dashboard (viz_engine)" |
| 3D Kinetic visualisation (`kinetic_3d.html`) | Center panel → "↗ 3D KINETIC" button |
| OpenRouter model list | [https://openrouter.ai/models](https://openrouter.ai/models) |

---

## 16. Technology Stack

| Component | Technology |
|---|---|
| Layout | CSS Grid (3-column fixed + flexible center) |
| Fonts | Inter (UI), JetBrains Mono (data/code) via Google Fonts |
| Icons/symbols | Unicode (no icon library dependency) |
| SA-Health gauge | SVG `<circle>` with `stroke-dasharray` animation |
| Tactical Picture | SVG with dynamic DOM manipulation |
| LLM integration | Browser `fetch()` + ReadableStream SSE parsing |
| Backend calls | `fetch()` POST to FastAPI |
| State persistence | `localStorage` (API key only) |
| No build tool | Pure HTML/CSS/JavaScript — no bundler, no framework |

---

## 17. Running CORTEX-C2 Locally

### Prerequisites

- Python 3.9+ (for the HTTP server and optional backend)
- Virtual environment at `C:\Users\dhiraj.kumar\Downloads\Saab\.venv_saab`

### Step 1: Start the static file server

```powershell
$venv = "C:\Users\dhiraj.kumar\Downloads\Saab\.venv_saab\Scripts\python.exe"
Start-Process -FilePath $venv `
  -ArgumentList "-m","http.server","8080" `
  -WorkingDirectory "C:\Users\dhiraj.kumar\Downloads\Saab\ruby-stridsledning-ai" `
  -WindowStyle Minimized
```

### Step 2: Open in browser

```
http://localhost:8080/frontend/cortex_c2.html
```

### Step 3 (Optional): Start the Python backend

```powershell
& $venv -m uvicorn src.agent_backend:app --host 0.0.0.0 --port 8000
```

### Step 4 (Optional): Add OpenRouter API key

1. Scroll right sidebar to **LLM Analysis · OpenRouter**
2. Enter `sk-or-v1-...` key in the password field
3. Click **SAVE**
4. Load any scenario → click **▶ ANALYSE**

---

## 18. Verified Test Results

All three scenarios verified against expected SA / mode / COA values:

| Scenario | SA-Health | Mode | COA-1 Coverage | COA-1 Utility | Follow-on Risk |
|---|---|---|---|---|---|
| Clean (3 BALLISTIC) | 82% | AUTONOMOUS | 100% | 228 | 0.05 |
| Swarm (15 tracks) | 76% | ADVISE | 100% | variable | 0.05–0.35 |
| Jammed (HVA + decoys) | 46% | DEFER | ≤100% | variable | >0.15 |

Jammed scenario correctly triggers DEFER at SA=46% (SA formula includes −35 jamming penalty). Previously this was incorrectly showing AUTONOMOUS — fixed by adding explicit `jammingSAPenalty` to the SA formula.
