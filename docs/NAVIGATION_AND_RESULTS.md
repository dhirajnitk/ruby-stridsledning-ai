# CORTEX Command Portal — Navigation & Usage Guide

> UNCLASSIFIED · EXERCISE · PROTOTYPE S28

## Portal Entry Point

Open `http://localhost:8080/frontend/index.html` — this is the recommended start point for all sessions.

The portal provides direct links to all six modules and shows a live backend status indicator.

---

## Module Overview

```
┌─────────────────────────────────────────────────────────┐
│              CORTEX COMMAND PORTAL                      │
│                                                         │
│  ┌────────────────┐  ┌────────────────────────────┐    │
│  │  CORTEX-C2     │  │  STRATEGIC DASHBOARD       │    │
│  │  console       │  │  viz_engine physics sim    │    │
│  └────────────────┘  └────────────────────────────┘    │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐     │
│  │ 3D Boreal│  │3D Sweden │  │  Strategic 3D    │     │
│  │ WebGL    │  │ WebGL    │  │  CZML/Cesium     │     │
│  └──────────┘  └──────────┘  └──────────────────┘     │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐     │
│  │ Dataset  │  │ Live View│  │ Tactical Legacy  │     │
│  │ Viewer   │  │ Backend  │  │ V3 SVG Map       │     │
│  └──────────┘  └──────────┘  └──────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

---

## C2 Operator Workflow (CORTEX-C2)

### Step 1 — Select Command Mode
Choose your operational posture at the top of the center column:

- **AUTONOMOUS**: Hands-free AI assignment. Good for demos and benchmarking.
- **HUMAN-IN-LOOP**: AI proposes, commander approves/rejects. Adds the SWAP feature.
- **MANUAL OVERRIDE**: Full commander control. Select each Threat → Base → Effector.

### Step 2 — Select Doctrine
The doctrine bar below the header sets engagement weighting:

- **BALANCED**: Standard. Best for most scenarios.
- **FORTRESS**: HVA priority. Use when defending capital or high-value nodes.
- **AGGRESSIVE**: Max coverage. Use when you have surplus inventory.

### Step 3 — Select Theater
Toggle **BOREAL** or **SWEDEN** to switch the active theater. The inventory grid, COA engine, and tactical radar all update immediately.

### Step 4 — Load a Scenario
Click one of the three Demo Scenario cards in the left sidebar. COAs are generated immediately.

### Step 5 — Review COA Cards (footer)
Three COA strategies are always displayed:
- Review P.EFFECT / RISK / RESERVE / ENGAGE metrics
- In HITL mode: click **APPROVE** to commit, **REJECT** to pass, **⇄ SWAP** to swap weapons before approval
- In MANUAL mode: use the override panel directly

### Step 6 — LLM Analysis (optional)
Click **▶ ANALYSE** in the right sidebar for AI tactical commentary. If the backend is offline, enter your OpenRouter API key when prompted.

### Step 7 — Replenish if Needed
If SAM counts run low, click **↑ REPLENISH** in the Theater Inventory section.

---

## Theater Design Rationale

Both BOREAL and SWEDEN theaters are accessible from the same CORTEX-C2 console via the toggle buttons. This is the correct design because:

1. **Operational realism**: A single C2 operator handles the full AOR — not separate systems per region.
2. **Inventory continuity**: Replenishment, SAM consumption, and doctrine state persist across theater switches.
3. **Comparison**: Operators can switch theaters mid-exercise to compare assignment strategies.
4. **Simplicity**: One interface to learn, not two.

The Strategic Dashboard (`dashboard.html`) uses URL parameters (`?mode=boreal` / `?mode=sweden`) and always shows the full Baltic theater SVG regardless.

---

## Starting the Backend

```powershell
# From workspace root
.venv_saab\Scripts\python.exe src/agent_backend.py
# Listens on port 8000
```

Required for:
- LLM proxy (OPENROUTER_API_KEY env var needed)
- Kinematic bridge scoring

Optional — all C2 features work offline using local COA engine and direct OpenRouter fallback.

---

## Starting the HTTP Server

```powershell
# From workspace root
.venv_saab\Scripts\python.exe -m http.server 8080
# Then open http://localhost:8080/frontend/index.html
```

---

## Cross-Page Links (all verified)

| From | Link | Destination |
|---|---|---|
| `index.html` | CORTEX-C2 Console card | `cortex_c2.html` |
| `index.html` | Strategic Dashboard card | `dashboard.html` |
| `index.html` | 3D Kinetic Boreal card | `kinetic_3d.html?theater=boreal` |
| `index.html` | 3D Kinetic Sweden card | `kinetic_3d.html?theater=sweden` |
| `index.html` | Strategic 3D card | `strategic_3d.html` |
| `cortex_c2.html` header | ← DASHBOARD | `dashboard.html` |
| `cortex_c2.html` about | → Main Dashboard | `dashboard.html` |
| `cortex_c2.html` center | ↗ 3D KINETIC | `kinetic_3d.html?theater=boreal` |
| `dashboard.html` header | CORTEX-C2 ↗ | `cortex_c2.html` |

---

## Session Results Summary

This section documents the outcomes of the CORTEX-C2 development sprint.

### Naming Convention
- Console renamed from **NIMBUS-C2** → **CORTEX-C2** across all files
- File renamed: `nimbus_c2.html` → `cortex_c2.html`
- All cross-file links updated

### Features Built & Verified

| Feature | Status | Notes |
|---|---|---|
| Command Mode (AUTO/HITL/MANUAL) | ✅ | All 3 modes functional |
| Weapon Swap (⇄ SWAP) | ✅ | Freeze → select → confirm flow |
| COA Cards (3-strategy) | ✅ | P.EFFECT/RISK/RESERVE/ENGAGE metrics |
| Theater Toggle (Boreal↔Sweden) | ✅ | AOR header + inventory updates |
| Doctrine Selector | ✅ | Balanced/Fortress/Aggressive — live COA re-scoring |
| Engagement Log Counters | ✅ | FIRED/INTERCEPTS/MANUAL/HITL/SWAPS |
| Theater Inventory + REPLENISH | ✅ | Dual HP+SAM bars, 1.1 s animation |
| Sensor Feed Quality Bars | ✅ | RADAR/IR/ESM/LINK-16/FUSION |
| Decision Window TTD | ✅ | Color-coded countdown |
| Circular Radar Scope | ✅ | Animated sweep, range rings |
| LLM Integration | ✅ | Backend proxy + direct OpenRouter fallback |
| API Key management | ✅ | Stored in localStorage as `cortex_or_key` |
| Portal (index.html) | ✅ | All 6 modules linked with backend status |
| ZULU Clock | ✅ | Live UTC |
| Cross-page navigation | ✅ | All links verified |

### Models Supported

| Key | Name |
|---|---|
| `elite` | Elite V3.5 · TRANSFORMER-RESNET |
| `supreme3` | Supreme V3.1 · GRU (Chronos) |
| `supreme2` | Supreme V2 · Legacy |
| `titan` | Titan · LSTM |
| `hybrid` | Hybrid RL V8.4 |
| `genE10` | Generalist E10 |
| `heuristic` | Heuristic (Triage-Aware) — default |
| `hBase` | Heuristic V2 (Base) |
