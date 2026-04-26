# MARV / MIRV / Dogfight — Technical Deep-Dive

**System:** Boreal Chessmaster v8.3  
**Status:** ✅ FULLY INTEGRATED across all three layers  
**Last Verified:** 2026-04-25  

---

## Executive Summary

The engine handles **four advanced trajectory behaviours** end-to-end:

| Behaviour | Threat Type | Core Problem | Solution Layer |
|-----------|------------|--------------|----------------|
| **MARV** | Ballistic | Terminal-phase evasive jinking degrades interceptor Pk | Pk penalty in rollout + utility boost for early engagement |
| **MIRV** | Ballistic | Single bus splits into N warheads — one interceptor can't cover all | 2-phase utility: pre-release bus kill vs post-release individual warheads |
| **Dogfight** | Fighter | Enemy aircraft can destroy our interceptor | Stochastic WVR resolution with 3 outcomes |
| **RTB** | Fighter | Aircraft can break off and retreat instead of dying | Retreat physics + partial score credit |

---

## 1. Where Each Behaviour Lives

```
┌─────────────────────┐    ┌────────────────────────┐    ┌──────────────────────┐
│   core/models.py    │    │    core/engine.py       │    │    simulation.py      │
│                     │    │                         │    │                      │
│  Threat dataclass:  │───▶│  TacticalEngine:        │    │  SimThreat class:    │
│  • is_marv          │    │  _calculate_utility()   │    │  • move() → jink     │
│  • marv_pk_penalty  │    │  ↳ MARV: +600 early     │    │  • try_release_mirv()│
│  • marv_trigger_km  │    │  ↳ MIRV: +800×N pre-rel │    │  • resolve_dogfight()│
│                     │    │  ↳ DOGFIGHT: range bonus │    │  • RTB retreat path  │
│  • is_mirv          │    │                         │    │                      │
│  • mirv_count       │    │  StrategicMCTS:          │    │  SimulationLoop:     │
│  • mirv_release_km  │    │  _single_rollout()      │    │  tick() checks MIRV  │
│  • mirv_released    │    │  ↳ spawns child threats  │    │  spawns children     │
│                     │    │  ↳ applies MARV penalty  │    │                      │
│  • can_dogfight     │    │  ↳ resolves dogfights    │    │                      │
│  • dogfight_win_prob│    │                         │    │                      │
│  • can_rtb          │    │  _resolve_dogfight()    │    │                      │
└─────────────────────┘    └────────────────────────┘    └──────────────────────┘
```

---

## 2. MARV — Maneuvering Re-entry Vehicle

### What It Models
A ballistic missile that performs **terminal-phase evasive jinking** — random lateral velocity changes that degrade interceptor tracking and Pk.

### How the Engine Handles It

**Layer 1 — Data Model** (`core/models.py:41-43`)
```python
is_marv: bool = False
marv_pk_penalty: float = 0.55          # effective Pk = base_Pk × 0.55
marv_trigger_range_km: float = 80.0    # start manoeuvring within 80 km
```

**Layer 2 — Utility Function** (`core/engine.py:105-116`)

The engine changes the **value function** based on whether the MARV has activated:

```python
if getattr(t, "is_marv", False):
    trigger_km = getattr(t, "marv_trigger_range_km", 80.0)
    if dist > trigger_km:
        # Still in MIDCOURSE — intercept NOW while Pk is nominal
        utility += 600.0   # ← urgency bonus: "shoot before it starts jinking"
    else:
        # Already JINKING — Pk is degraded
        pk_eff = pk * getattr(t, "marv_pk_penalty", 0.55)
        utility += (pk_eff * 400.0)  # ← lower utility reflects reduced confidence
```

> **Key insight:** The engine doesn't just degrade Pk — it **boosts priority for early engagement**. This "Urgency Boost" forces the greedy solver to allocate long-range interceptors (THAAD/PAC-3) **before** the MARV enters its jink zone.

**Layer 3 — Monte Carlo Rollout** (`core/engine.py:247-252`)

During MC simulation, the actual Pk is multiplied by the penalty:

```python
if getattr(t, "is_marv", False):
    dist_to_target = math.hypot(t.x - cap.x, t.y - cap.y)
    if dist_to_target <= getattr(t, "marv_trigger_range_km", 80.0):
        effective_pk *= getattr(t, "marv_pk_penalty", 0.55)
```

**Layer 4 — Live Simulation** (`simulation.py:168-180`)

The `SimThreat.move()` method adds random lateral velocity once the trigger range is reached:

```python
if self.marv_active:
    jink_per_tick = (self.marv_jink_mag_kmh / 3600.0) * 10.0
    self.x += self.vx + random.uniform(-jink_per_tick, jink_per_tick)
    self.y += self.vy + random.uniform(-jink_per_tick, jink_per_tick)
```

### Test Results (500 rollouts)
| Threat | Kill Rate | Expected |
|--------|-----------|----------|
| Standard Ballistic | ~85% | PAC-3 Pk = 0.85 |
| MARV Ballistic (penalty 0.45) | ~38% | 0.85 × 0.45 = 38.3% |

**Confirmed:** MARV reduces effective Pk by ~47pp.

### How the NN Adapts
The neural model doesn't directly see `is_marv` in its 15-D feature vector. Instead, the MARV's effect is captured indirectly:
- **Higher `threat_value`** → inflates the value normalization features
- **Utility boost** → the greedy geometry engine auto-escalates to THAAD/long-range shots
- **Neural Autonomy** (Elite V3.5 only) → the transformer detects high-value + high-speed signatures and triggers salvo escalation

> **Gap:** The NN could be improved by adding a `marv_detected` binary feature to the input vector, allowing the model to learn the "shoot early" pattern directly rather than relying on the geometry engine's utility boost.

---

## 3. MIRV — Multiple Independently Targetable Re-entry Vehicles

### What It Models
A single missile bus carrying **N warheads** (typically 3) that separate at a configurable range from the target. Pre-release, killing the bus destroys all warheads. Post-release, each warhead becomes an independent threat.

### The 2-Phase Doctrine

**Phase 1 — Pre-Release (Bus Kill)**

```python
# engine.py:131-138
if getattr(t, "is_mirv", False) and not getattr(t, "mirv_released", False):
    if dist > release_km:
        # Pre-release: killing bus kills all warheads — HIGHEST PRIORITY
        utility += 800.0 * mirv_n   # e.g., 800 × 5 = 4,000 utility
```

### The "Threat Multiplier"
The `800.0 * mirv_n` bonus acts as a **dynamic threat multiplier**. A bus with 5 warheads is weighted **5x more heavily** than a standard missile, ensuring that the assignment algorithm (Hungarian) always prioritizes the "Bus Kill" above all other tactical activity.

### Automatic Salvo Escalation (Aggressive Posture)
To ensure robust defense, the engine automatically shifts to an **Aggressive Posture** when a MIRV bus is detected in the swarm:

```python
# engine.py:344-346
if any(getattr(t, "is_mirv", False) and not getattr(t, "mirv_released", False) for t in threats):
    neural_salvo_ratio = max(neural_salvo_ratio, 2.0)
```

This ensures the system commits **multiple interceptors (2.0 ratio)** to the bus simultaneously, providing redundancy to guarantee a kill before separation occurs.

**Phase 2 — Post-Release (Individual Warheads)**

```python
# engine.py:206-233 (_single_rollout)
if dist_to_cap <= getattr(t, "mirv_release_range_km", 150.0):
    t.mirv_released = True
    child_val = t.threat_value / max(1, t.mirv_count)
    for i, tgt_base in enumerate(targets):
        child = Threat(
            id=f"{t.id}-MRV{i}",
            speed_kmh=t.speed_kmh * 1.2,   # warheads are faster
            estimated_type="ballistic",
            threat_value=child_val,
        )
```

After release:
- Bus becomes **inert** (marked as hit)
- Each warhead is a **separate BALLISTIC threat** targeting a random base
- Warheads inherit 1/N of the parent's threat value
- Warheads are 20% faster than the bus (re-entry acceleration)

### How SAMs Target Post-Release Warheads
Each warhead enters the normal greedy assignment pipeline. Since they're individual `ballistic` type threats:
- **PAC-3** (Pk 0.85 vs ballistic, 120km range) handles them
- **NASAMS** (Pk 0.5 vs ballistic, 40km range) serves as backup
- The engine must allocate **one interceptor per warhead** — a 3-warhead MIRV requires 3× the ammo

### Test Results (200 rollouts, 1 interceptor on bus only)
| Metric | Value |
|--------|-------|
| Avg leaked warheads | ~2.5 of 3 |
| Max leaked | 3 |

**Confirmed:** Single interceptor on bus post-release cannot cover child warheads. The engine correctly escalates pre-release priority.

### Value Function Impact
The MIRV utility bonus of `800 × N` warheads creates a **discontinuity** in the value landscape:
- At 151km: utility = 2,400 (bus kill saves everything)
- At 149km: utility = 100 (bus already released, only residual value)

This cliff incentivizes the engine to **frontload** THAAD/PAC-3 against MIRV buses.

---

## 4. Dogfight / RTB — Fighter Aircraft Engagement

### What It Models
Enemy fighter aircraft that can **engage our interceptors in WVR combat**. Three possible outcomes with configurable probabilities:

### Stochastic Resolution (`engine.py:175-197`)

```python
@staticmethod
def _resolve_dogfight(t, eff, rollout_score):
    r = random.random()
    if r < t.dogfight_win_prob:
        return False, -(t.threat_value * 1.0), "ENEMY_WIN"
    elif t.can_rtb and r < (t.dogfight_win_prob + ...):
        return True, t.threat_value * 0.05, "RTB"
    else:
        return True, t.threat_value * 0.2, "KILL"
```

| Outcome | Probability (default) | Score Impact | Effect |
|---------|----------------------|--------------|--------|
| **ENEMY_WIN** | 30% | −threat_value | Our interceptor lost, threat continues |
| **RTB** | ~28% | +5% value | Enemy retreats, mission aborted |
| **KILL** | ~42% | +20% value | Clean kill |

### RTB Retreat Physics (`simulation.py:182-187`)
```python
if self.is_retreating:
    self._recompute_velocity(self.rtb_speed_kmh, self.origin_x, self.origin_y)
    self.x += self.vx
    self.y += self.vy
```
The fighter recalculates its velocity vector to fly **away** from the battle area toward its origin point (500km behind starting position).

### Value Function for Dogfight
The utility function applies a **range bonus** for long-range shots:
```python
# engine.py:131-138
if getattr(t, "can_dogfight", False):
    range_bonus = min(eff_def.range_km / 100.0, 5.0) * 200.0
    utility += range_bonus * (1.0 - dog_prob)
```
This means Meteor (150km range) gets a massive priority boost over short-range effectors, because engaging at BVR avoids the merge entirely.

### Test Results (1,000 engagements, dogfight_win_prob=0.30)
| Outcome | Count | Percentage |
|---------|-------|------------|
| KILL | ~420 | 42% |
| RTB | ~280 | 28% |
| ENEMY_WIN | ~300 | 30% |

**Confirmed:** Enemy win rate matches configured probability within ±3%.

---

## 5. How Different Trajectories Affect the NN

### UPDATED: NN Now Sees Trajectory Flags (18-D Feature Vector)

The feature vector has been **expanded from 15-D to 18-D** (`extract_rl_features()` in `core/engine.py`):
```
[num_threats, avg_dist, min_dist, total_value,
 fighters, sams, drones, cap_sams,
 weather_bin, blend,
 west_threats, east_threats, ammo_stress, dist_norm, val_norm,
 has_marv, has_mirv, total_mirv_warheads]   ← NEW (features 15-17)
```

### How the 18-D Vector Drives Weapon Selection
The update from 15-D to 18-D provides the AI with specific "trajectory vision" that informs effector prioritization:

| Index | Feature | Tactical Impact on Weapon Selection |
| :--- | :--- | :--- |
| **15** | `has_marv` | Signals **Urgency Shift**. The AI learns to fire long-range assets (SAMP/T, Patriot) immediately while the MARV is in its stable midcourse phase. |
| **16** | `has_mirv` | Signals **Efficiency Opportunity**. If a bus is detected, the AI shifts doctrine to prioritize this single target above all others to prevent warhead separation. |
| **17** | `total_mirv_warheads` | Signals **Weighting Scale**. A bus with 5 warheads is treated as 5x more dangerous, forcing the AI to commit multiple salvos (Salvo Ratio 2.0+). |

> With the 18-D vector, the NN can now **directly learn** patterns like "commit THAAD early when MIRV is detected" and "prioritize long-range Meteor when dogfighters are present."

---

## 6. Training Pipeline for MARV/MIRV

### The "Tactical Problem Generator" (`src/generate_marv_mirv_data.py`)
Instead of random points, the generator simulates realistic flight behaviors:
- **MARV:** Spawns ballistic threats that remain nominal until the `trigger_range` (60–120 km), then begin terminal maneuvers.
- **MIRV:** Spawns a "Bus" that splits into 2–5 independent warheads at `release_range`.
- **Dogfighters:** Spawns aircraft with aggressive WVR engagement probabilities.

### The MCTS Oracle Loop
Every generated scenario is passed through a high-intensity Monte Carlo Tree Search. The Oracle determines the mathematically optimal weapon allocation (e.g., "Fire two Patriots at the MIRV bus now to save 5 targets later"). These optimal decisions become the labels the AI learns.

Threat distribution: ~30% MARV/MIRV/Dogfight, ~70% standard threats.

### Step 2: Train/Fine-Tune Models
```powershell
python src/neural_trainer.py
```
- Phase 1: Train on original corpus (if available)
- Phase 2: Fine-tune on MARV/MIRV dataset with `strict=False` weight loading (handles 15→18 dim change)
- Saves V2 models as `models/boreal_{name}_v2.pth`

### Step 3: Test
```powershell
python src/test_advanced_trajectories.py
```

---

## 7. Frontend Integration (cortex_c2.html)

### New Scenarios Added
| Scenario | Key | Threats | Purpose |
|----------|-----|---------|---------|
| **MIRV Bus Strike** | `mirv` | 2 MIRV buses (3 warheads each) + 2 MARV escorts + cruise + decoy | Tests 2-phase intercept doctrine |
| **MARV Terminal Manoeuvre** | `marv` | 4 MARV ballistics (Pk 0.40–0.55) + 1 dogfighter + 1 hypersonic | Tests early-intercept priority |

### COA Engine Changes
- `buildCandidates()` now applies **MARV Pk penalty** to engagement candidates
- `buildCandidates()` now applies **MIRV utility boost** (800 × N warheads) to threat value
- Candidate objects carry `isMirv`, `isMarv`, `isDogfight` flags for downstream analysis

---

## 8. Running the Tests

```powershell
cd c:\Users\dhiraj.kumar\Downloads\Saab\ruby-stridsledning-ai
python src/test_advanced_trajectories.py
```

This runs all 6 tests:
1. **MARV Pk Degradation** — 500 rollouts comparing standard vs MARV ballistic
2. **MIRV Bus Separation** — 200 rollouts showing warhead leakage
3. **Dogfight Outcome Distribution** — 1,000 engagements verifying probability calibration
4. **Live MARV Trajectory** — 12-tick jink simulation with position trace
5. **Live MIRV Separation** — tick-by-tick bus release and warhead spawning
6. **Live Dogfight/RTB** — intercept resolution with retreat physics

---

## 9. Integration Status Matrix

| Component | MARV | MIRV | Dogfight | RTB |
|-----------|------|------|----------|-----|
| `core/models.py` (Threat dataclass) | ✅ | ✅ | ✅ | ✅ |
| `core/engine.py` (Utility function) | ✅ | ✅ | ✅ | — |
| `core/engine.py` (MC rollout) | ✅ | ✅ | ✅ | ✅ |
| `core/engine.py` (18-D features) | ✅ | ✅ | ✅ | — |
| `simulation.py` (SimThreat physics) | ✅ | ✅ | ✅ | ✅ |
| `simulation.py` (SimulationLoop) | — | ✅ | — | ✅ |
| `test_advanced_trajectories.py` | ✅ | ✅ | ✅ | ✅ |
| `generate_marv_mirv_data.py` | ✅ | ✅ | ✅ | — |
| `neural_trainer.py` (V2 fine-tune) | ✅ | ✅ | ✅ | — |
| Frontend `cortex_c2.html` scenarios | ✅ | ✅ | ✅ | — |
| Frontend `buildCandidates()` Pk/val | ✅ | ✅ | — | — |

> **All critical paths are now integrated.** The only remaining gap is RTB visualization in the frontend (retreat trajectory rendering).

